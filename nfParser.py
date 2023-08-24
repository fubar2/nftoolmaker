"""
            split into bits - test file, test name, test parameter values for each test

            if comma separators between the start and end ], split and give all the same name - it has no meaning as everything's positional here

             input = [
        [ id:'test', single_end:false ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
        false,
        false,
        false
    ]

     otherwise perhaps build the list by appending from individual =

workflow test_hmmer_eslreformat_afa {

    input = [
        [ id:'test' ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz')      // Change to params.test_data syntax after the data is included in ./tests/config/test_data.config
    ]

    hmm   = file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz')

    HMMER_HMMALIGN ( input, hmm )

    HMMER_ESLREFORMAT_AFA ( HMMER_HMMALIGN.out.sthlm )
}

#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { HMMER_HMMSEARCH } from '../../../../../modules/nf-core/hmmer/hmmsearch/main.nf'

workflow test_hmmer_hmmsearch {

    input = [
        [ id:'test', single_end:false ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
        false,
        false,
        false
    ]

    HMMER_HMMSEARCH ( input )
}

workflow test_hmmer_hmmsearch_optional {

    input = [
        [ id:'test', single_end:false ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
        true,
        true,
        true
    ]

    HMMER_HMMSEARCH ( input )
}


"""
from pyparsing import * # that's what she said
import string


def tests():
    """
    these were built with each subexpression
    """
    ts = "file(params.test_data[homo_sapiens][illumina][test_genome_vcf],', 'checkIfExists:', 'true),"
    print(nftestURL.parse_string(ts))
    ts = "  file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),"
    print(realtestURL.parse_string(ts))
    ts = "include { HMMER_HMMSEARCH } from '../../../../../modules/nf-core/hmmer/hmmsearch/main.nf'"
    print(includeTestname.parse_string(ts))
    ts = " [ id:'test', single_end:false ], // meta map"
    print(mapexpr.parse_string(ts))
    ts = "    input = ["
    paramname.parse_string(ts)
    ts =  """[ id:'test', single_end:false ], // meta map
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
            false,
            false,
            false"""
    res = paramexpr.scan_string(ts)
    print([x for x in res])
    #[(ParseResults(["id:'test',", 'single_end:false'], {}), 0, 44), (ParseResults(['https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz'], {}), 53, 186), (ParseResults(['https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz'], {}), 196, 331), (ParseResults(['false'], {}), 341, 346), (ParseResults(['false'], {}), 356, 361), (ParseResults(['false'], {}), 371, 376)]
    ts = """
        input = [
            [ id:'test' ], // meta map
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz')      // Change to params.test_data syntax after the data is included in ./tests/config/test_data.config
        ]"""
    res = paramexpr.scan_string(ts)
    print([x for x in res])
    #[(ParseResults(['input'], {}), 9, 14), (ParseResults(["id:'test'"], {}), 31, 57), (ParseResults(['https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz'], {}), 70, 288)]



nftestURL = Suppress(Literal("file(params.test_data[")) + Word(alphanums + "(':/_+[].-") +  Suppress(",',") + Suppress(restOfLine))
nftestURL.setName("nftestURL")
realtestURL = Suppress(Literal("file('")) + Word(alphanums + "(:/_+[].-") +  Suppress("',")[...] + Suppress(restOfLine)
realtestURL.setName("realtestURL")
paramname = Word(alphanums) + Suppress("=") + Suppress("[")
paramname.setName("paramname")
paramVal = Word(alphanums)
paramVal.setName("paramVal")
includeTestname = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z_]")) + Suppress("}")
mapexpr = Suppress("[") + OneOrMore(Word(alphanums, alphanums + "':,_")) + Suppress("]") + Suppress(",") + Suppress(restOfLine)
mapexpr.setName("mapexpr")
paramexpr = OneOrMore(nftestURL) ^ OneOrMore(realtestURL) ^ OneOrMore(mapexpr) ^ OneOrMore(paramVal)

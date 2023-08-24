# ross lazarus August 2023
# for parsing nf-core test texts written in their DDL
# to replace fugly string hacking

from pyparsing import * # that's what she said
import string

nftesttext = """#!/usr/bin/env nextflow
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

def tests():
    """
    these were built with each subexpression
    """
    ts = " file(params.test_data['homo_sapiens']['illumina']['test_genome_vcf'], checkIfExists: true),"
    print(nftestURL.parse_string(ts))
    ts = "    file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),"
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
    ts = """ SURVIVOR_FILTER_BED (
            input_bed,
            51,
            10001,
            0.01,
            10
        )
    """
    nftestcall.parse_string(ts)
    ts = """
            [ id:'test', single_end:false ], // meta map
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
            true,
            true,
            true
    """
    allparam = OneOrMore(paramexpr)
    print(allparam.parse_string(ts))
    ts = """    input = [
            [ id:'test', single_end:false ], // meta map
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
            true,
            true,
            true
        ]
    """
    testparams.parse_string(ts)
    ts = """workflow test_hmmer_hmmsearch_optional {
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
    print(nftest.parse_string(nftesttext))


stuffInUrls = alphanums + ":/_+[].-?&"

# some utility DSL syntax
shebang = "#" + Word(alphanums + "#!/_.") + Word(alphanums + "./") # #!/usr/bin/env nextflow
dsl = "nextflow" + OneOrMore(Word(alphanums + "./[]")) + Literal("=")[...] + restOfLine # nextflow.enable.dsl = 2
# test parameter types
nftestURL = Suppress(Literal("file(params.test_data")) + Word(alphanums + "['-_.]") + Suppress(",") + Suppress(restOfLine)
realtestURL = Suppress(Literal("file('")) + Word(stuffInUrls) + Suppress("'") +  Suppress(",")[...] + Suppress(restOfLine)
paramVal = Word(alphanums) + Suppress(Literal(",")[0,1]) #+ Suppress(restOfLine)
paramname = Word(alphanums) + Suppress("=") + Suppress("[")
includeTestname = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z_]")) + Suppress("}") + Suppress(restOfLine)
mapexpr = "[" + OneOrMore(Word(alphanums, alphanums + "':,_")) + "]" + Suppress(ZeroOrMore(",")) + Suppress(restOfLine) # // meta map is really annoying
nftestcall = Word(alphas + '_') + Suppress("(") + OneOrMore((Word(alphanums + "._-") + Suppress(Literal(",")[0,1]))) + ')' + Suppress(restOfLine) #  HMMER_HMMSEARCH ( input )
# composite components
paramexpr = OneOrMore(Group(mapexpr))) ^ OneOrMore(nftestURL) ^ OneOrMore(realtestURL) ^  OneOrMore(paramVal)
testparams = paramname + OneOrMore(paramexpr) + Suppress("]")
nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(testparams) + OneOrMore(nftestcall) + Suppress("}"))
# and all together now...
nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group( OneOrMore(nftestname))
# that's what we have so far - will try parsing every test nf file to find all the missing bits - like stubs...



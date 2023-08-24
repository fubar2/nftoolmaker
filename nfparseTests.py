# ross lazarus August 2023
# for parsing nf-core test texts written in their DDL
# to replace fugly string hacking

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

oh dear. this failed
#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { ABACAS } from '../../../../modules/nf-core/abacas/main.nf'

workflow test_abacas {

    input = [ [ id:'test', single_end:false ], // meta map
              file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
            ]

    fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)

    ABACAS ( input, fasta )
}

"""


import sys
import os
from pyparsing import * # yes,  I know but that's what the package author recommends



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
    ts = """
    input = [ [ id:'test', single_end:false ], // meta map
              file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
            ]

    fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)

    ABACAS ( input, fasta )
    """
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



testroot = "tests/modules/nf-core"
# pyparsing restOfLine is just the ticket sometimes.
inUrls = alphanums + ":/_+[].-?&"
# some utility DSL syntax - unsuppress it if you care
shebang = Suppress("#" + Word(alphanums + "#!/_.") + Word(alphanums + "./") + restOfLine) # #!/usr/bin/env nextflow
dsl = Suppress("nextflow" + OneOrMore(Word(alphanums + "./[]")) + Literal("=")[...]) + restOfLine # nextflow.enable.dsl = 2
# test parameter types
nftestURL = Suppress(Literal("file(params.test_data")) + Word(alphanums + "['-_.]") + Suppress(",") + Suppress(restOfLine)
realtestURL = Suppress(Literal("file('")) + Word(inUrls) + Suppress("'") +  Suppress(",")[...] + Suppress(restOfLine)
paramVal = Word(alphanums) + Suppress(Literal(",")[0,1]) #+ Suppress(restOfLine)
paramname = Word(alphanums) + Suppress("=") + Suppress("[")
includeTestname = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z_]")) + Suppress("}") + Suppress(restOfLine)
nftestcall = Word(alphas + '_') + Suppress("(") + OneOrMore((Word(alphanums + "._-") + Suppress(Literal(",")[0,1]))) + ')' + Suppress(restOfLine) #  HMMER_HMMSEARCH ( input )
# composite components
mapping = "[" + OneOrMore(Word(alphanums, alphanums + "':,_")) + "]" + Suppress(ZeroOrMore(",")) + Suppress(restOfLine)
paramexpr = OneOrMore(nftestURL) ^ OneOrMore(realtestURL) ^  OneOrMore(paramVal)
testparams = paramname + OneOrMore(paramexpr)
mapparams = paramname + mapping + ZeroOrMore(testparams) + Suppress("]")
nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(mapparams) +  ZeroOrMore(testparams) + OneOrMore(nftestcall) + Suppress("}"))
# and all together now...
nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group(OneOrMore(nftestname))
# print(nftest.parse_string(nftesttext))
# that's what we have so far - will try parsing every test nf file to find all the missing bits - like stubs...
# >>> nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group( OneOrMore(nftestname))
# >>> print(nftest.parse_string(nftesttext))
# [['#', '!/usr/bin/env', 'nextflow'], ['nextflow', '.enable.dsl', '=', ' 2'], 'HMMER_HMMSEARCH', [['test_hmmer_hmmsearch', 'input', ['[', "id:'test',", 'single_end:false', ']'],
#  'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/da
# ta/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'false', 'false', 'false', 'HMMER_HMMSEARCH', 'input', ')'], ['test_hmmer_hmmsearch_optional', 'input', ['[', "id:'test',", 'single_e
# nd:false', ']'], 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-dat
# asets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'true', 'true', 'true', 'HMMER_HMMSEARCH', 'input', ')']]]




ts = """
workflow test_abacas {

    input = [ [ id:'test', single_end:false ], // meta map
              file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
            ]

    fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)

    ABACAS ( input, fasta )
}
"""
print([x for x in paramexpr.scan_string(ts)])
ts = """
    input = [ [ id:'test', single_end:false ], // meta map
              file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
            ]

    fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)

    ABACAS ( input, fasta )
    """
print([x for x in nftestname.scan_string(ts)])
sys.exit()
tests()
mod = sys.argv[1]
scriptpath = os.path.join(foo.testroot,mod,'main.nf')
s = open(scriptpath, 'r').read()
p = nftest.parse_string(nftesttext)
print(p)
ts = """#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { ABACAS } from '../../../../modules/nf-core/abacas/main.nf'

workflow test_abacas {

    input = [ [ id:'test', single_end:false ], // meta map
              file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
            ]

    fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)

    ABACAS ( input, fasta )
}

"""
print(nftest.parse_string(nftesttext))

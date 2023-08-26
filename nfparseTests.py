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

now simpler
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2
include { ABACAS } from '../../../../modules/nf-core/abacas/main.nf'
workflow test_abacas {
file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
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
    print("big one", nftest.parse_string(nftesttext))
    ts = " file(params.test_data['homo_sapiens']['illumina']['test_genome_vcf'], checkIfExists: true),"
    print(nftestURL.parse_string(ts))
    ts = "    file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),"
    print(realtestURL.parse_string(ts))
    ts = "include { HMMER_HMMSEARCH } from '../../../../../modules/nf-core/hmmer/hmmsearch/main.nf'"
    print(includetest.parse_string(ts))
    ts =  """
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
            file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
            false,
            false,
            false
    """
    res = OneOrMore(paramexpr).parse_string(ts)
    print(res)
    #[(ParseResults(["id:'test',", 'single_end:false'], {}), 0, 44), (ParseResults(['https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz'], {}), 53, 186), (ParseResults(['https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz'], {}), 196, 331), (ParseResults(['false'], {}), 341, 346), (ParseResults(['false'], {}), 356, 361), (ParseResults(['false'], {}), 371, 376)]
    ts = """
    input = [ [ id:'test', single_end:false ], // meta map
              file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
            ]

    fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)

    ABACAS ( input, fasta )
    """
    print("testbodyparams", OneOrMore(testbodyparams.parse_string(ts)))
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
    ts = """
        fasta = [ [ id:'test', single_end:false ], // meta map
                  file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true),
        ]

        model = "precursor"

        minlength = 10

        minprobability = "0.7"

        AMPIR ( fasta, model, min_length, min_probability )
        """
    print(OneOrMore(testbodyparams).parse_string(ts))
    ts = """#!/usr/bin/env nextflow

    nextflow.enable.dsl = 2

    include { AMPIR } from '../../../../modules/nf-core/ampir/main.nf'

    workflow test_ampir {

        fasta = [ [ id:'test', single_end:false ], // meta map
                  file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true),
        ]

        model = "precursor"

        min_length = 10

        min_probability = "0.7"

        AMPIR ( fasta, model, min_length, min_probability )
    }
    """
    print(nftest.parse_string(nftesttext))
    ts = """
     workflow test_mlst {

        input = [ [ id:'test', single_end:false ], // meta map
                  file("https://raw.githubusercontent.com/nf-core/test-datasets/bactmap/genome/NCTC13799.fna", checkIfExists: true) ]

        MLST ( input )
    }


            """
    print(nftestname.parse_string(ts))



testroot = "tests/modules/nf-core"
optionalmstart = Suppress(Literal("[")[0,1])
optionalmend = Suppress(Literal("]")[0,1])
anyquote = Suppress(Literal("'") | Literal('"'))
paramWord = Word(alphanums + "_.-'" + '"')
paramNameWord = Word(alphanums + "_-.")
optionalcomma = Suppress(Literal(",")[0,1])
inUrls = alphanums + ":/_+[].-?&'" + '"'
# some utility DSL syntax - unsuppress it if you care
shebang = Suppress("#" + Word(alphanums + "#!/_.") + Word(alphanums + "./") + restOfLine) # #!/usr/bin/env nextflow
dsl = Suppress("nextflow" + OneOrMore(Word(alphanums + "./[]")) + Literal("=")[...]) + restOfLine # nextflow.enable.dsl = 2
# test parameter types
nftestcall = Word(srange("[A-Z_]")) + Suppress("(") + OneOrMore(paramNameWord + optionalcomma) + ')' + Suppress(restOfLine)
includetest = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z_]")) + Suppress("}") + Suppress(restOfLine)
includeTests = OneOrMore(includetest)
nftestURL = Suppress(Literal("file(params.test_data")) + Word(alphanums + '"' + "['-_.]")  + Suppress(",")  + Suppress(ZeroOrMore(Word(alphanums + ":_.-"))) + Suppress(")")
realtestURL = Suppress(Literal("file(")) + Word(inUrls) +  Suppress(",") + Suppress(ZeroOrMore(Word(alphanums + ":_.-"))) + Suppress(")")
paramVal = paramWord + optionalcomma #+ Suppress(restOfLine)
paramname = paramNameWord + Suppress("=") #+ NotAny("[") # hope none have [ ] around them
# composite components
paramexpr = nftestURL | realtestURL | paramVal
simpleparam = paramname + paramexpr + optionalcomma
testbodyparams = nftestcall ^ simpleparam
nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(testbodyparams) + Suppress("}"))
# and all together now...
nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + includeTests + Group(OneOrMore(nftestname))

# print(nftest.parse_string(nftesttext))
# that's what we have so far - will try parsing every test nf file to find all the missing bits - like stubs...
# >>> nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group( OneOrMore(nftestname))
# >>> print(nftest.parse_string(nftesttext))
# [['#', '!/usr/bin/env', 'nextflow'], ['nextflow', '.enable.dsl', '=', ' 2'], 'HMMER_HMMSEARCH', [['test_hmmer_hmmsearch', 'input', ['[', "id:'test',", 'single_end:false', ']'],
#  'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/da
# ta/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'false', 'false', 'false', 'HMMER_HMMSEARCH', 'input', ')'], ['test_hmmer_hmmsearch_optional', 'input', ['[', "id:'test',", 'single_e
# nd:false', ']'], 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-dat
# asets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'true', 'true', 'true', 'HMMER_HMMSEARCH', 'input', ')']]]

if len(sys.argv) > 1:
    mod = sys.argv[1]
    scriptpath = os.path.join(foo.testroot,mod,'main.nf')
    s = open(scriptpath, 'r').read()
    p = nftest.parse_string(nftesttext)
    print(p)
else:
    print('nothing on nfcommandline') #tests()

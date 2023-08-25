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
from pyparsing.exceptions import ParseException

class nextflowParser():

    def __init__(self):
        """
        """
        self.testroot = "tests/modules/nf-core"
        paramWord = Word(alphanums + "_.-'" + '"')
        paramNameWord = Word(alphanums + "_-.")
        optionalcomma = Suppress(Literal(",")[0,1])
        # pyparsing restOfLine is just the ticket sometimes.
        inUrls = alphanums + ":/_+[].-?&"
        # some utility DSL syntax - unsuppress it if you care
        shebang = Suppress("#" + Word(alphanums + "#!/_.") + Word(alphanums + "./") + restOfLine) # #!/usr/bin/env nextflow
        dsl = Suppress("nextflow" + OneOrMore(Word(alphanums + "./[]")) + Literal("=")[...]) + restOfLine # nextflow.enable.dsl = 2
        # test parameter types
        includetest = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z_]")) + Suppress("}") + Suppress(restOfLine)
        includeTests = OneOrMore(includetest)
        nftestURL = Suppress(Literal("file(params.test_data")) + Word(alphanums + '"' + "['-_.]") + Suppress(",")  + Suppress(ZeroOrMore(Word(alphanums + ":_.-"))) + Suppress(")") + Suppress(restOfLine)
        realtestURL = Suppress(Literal("file('")) + Word(inUrls) + Suppress("'") +  Suppress(",") + Suppress(ZeroOrMore(Word(alphanums + ":_.-"))) + ")" + Suppress(restOfLine)
        paramVal = paramWord + optionalcomma #+ Suppress(restOfLine)
        paramname = paramNameWord + Suppress("=")
        nftestcall = Word(srange("[A-Z_]")) + Suppress("(") + OneOrMore(paramNameWord + optionalcomma) + ')' + Suppress(restOfLine)
        #  HMMER_HMMSEARCH ( input )
        # composite components
        mapping = "[" + Literal(" ")[...] + "[" + OneOrMore(Word(alphanums, alphanums + "':,_")) + "]" + Suppress(restOfLine)
        paramexpr = nftestURL | realtestURL | paramVal
        simpleparam = paramname + paramexpr + optionalcomma
        mapparam = paramname + mapping + OneOrMore(paramexpr + optionalcomma) + Suppress("]")
        testbodyparams = nftestcall | mapparam | simpleparam
        nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(testbodyparams) + Suppress("}"))
        # and all together now...
        self.nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + includeTests + Group(OneOrMore(nftestname))
        # print(nftest.parse_string(nftesttext))
        # that's what we have so far - will try parsing every test nf file to find all the missing bits - like stubs...
        # >>> nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group( OneOrMore(nftestname))
        # >>> print(nftest.parse_string(nftesttext))
        # [['#', '!/usr/bin/env', 'nextflow'], ['nextflow', '.enable.dsl', '=', ' 2'], 'HMMER_HMMSEARCH', [['test_hmmer_hmmsearch', 'input', ['[', "id:'test',", 'single_end:false', ']'],
        #  'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/da
        # ta/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'false', 'false', 'false', 'HMMER_HMMSEARCH', 'input', ')'], ['test_hmmer_hmmsearch_optional', 'input', ['[', "id:'test',", 'single_e
        # nd:false', ']'], 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-dat
        # asets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'true', 'true', 'true', 'HMMER_HMMSEARCH', 'input', ')']]]

        # self.testroot = "tests/modules/nf-core"
        # # nextflow comments are a feature of the language that took a while to finesse.
        # # pyparsing restOfLine is just the ticket sometimes.
        # inUrls = alphanums + ":/_+[].-?&"
        # # some utility DSL syntax
        # shebang = Suppress("#" + Word(alphanums + "#!/_.") + Word(alphanums + "./") + restOfLine) # #!/usr/bin/env nextflow
        # dsl = Suppress("nextflow" + OneOrMore(Word(alphanums + "./[]")) + Literal("=")[...] + restOfLine) # nextflow.enable.dsl = 2
        # # test parameter types
        # nftestURL = Suppress(Literal("file(params.test_data")) + Word(alphanums + "['-_.]") + Suppress(",") + Suppress(restOfLine)
        # realtestURL = Suppress(Literal("file('")) + Word(inUrls) + Suppress("'") +  Suppress(",")[...] + Suppress(restOfLine)
        # paramVal = Word(alphanums) + Suppress(Literal(",")[0,1]) #+ Suppress(restOfLine)
        # paramname = Word(alphanums) + Suppress("=") + Suppress("[")
        # includeTestname = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z_]")) + Suppress("}") + Suppress(restOfLine)
        # mapexpr = "[" + OneOrMore(Word(alphanums, alphanums + "':,_")) + "]" + Suppress(ZeroOrMore(",")) + Suppress(restOfLine)
        # nftestcall = Word(alphas + '_') + Suppress("(") + OneOrMore((Word(alphanums + "._-") + Suppress(Literal(",")[0,1]))) + ')' + Suppress(restOfLine) #  HMMER_HMMSEARCH ( input )
        # # composite components
        # paramexpr = Suppress(OneOrMore(Group(mapexpr))) ^ OneOrMore(nftestURL) ^ OneOrMore(realtestURL) ^  OneOrMore(paramVal)
        # testparams = paramname + OneOrMore(paramexpr) + Suppress("]")
        # nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(testparams) + OneOrMore(nftestcall) + Suppress("}"))
        # # and all together now...
        # self.nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group(OneOrMore(nftestname))
        # # print(nftest.parse_string(nftesttext))
        # # that's what we have so far - will try parsing every test nf file to find all the missing bits - like stubs...
        # # >>> nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group( OneOrMore(nftestname))
        # # >>> print(nftest.parse_string(nftesttext))
        # # [['#', '!/usr/bin/env', 'nextflow'], ['nextflow', '.enable.dsl', '=', ' 2'], 'HMMER_HMMSEARCH', [['test_hmmer_hmmsearch', 'input', ['[', "id:'test',", 'single_end:false', ']'],
        # #  'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/da
        # # ta/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'false', 'false', 'false', 'HMMER_HMMSEARCH', 'input', ')'], ['test_hmmer_hmmsearch_optional', 'input', ['[', "id:'test',", 'single_e
        # # nd:false', ']'], 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-dat
        # # asets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'true', 'true', 'true', 'HMMER_HMMSEARCH', 'input', ')']]]

    def Parse(self, s):
        parsed = self.nftest.parse_string(s)
        return parsed

foo = nextflowParser()
spath = sys.argv[1]
s = open(spath, 'r').read()
try:
    p = foo.Parse(s)
    print(spath, 'PARSED!')
except:
    print(spath, 'failed to parse')
    sys.exit(666)



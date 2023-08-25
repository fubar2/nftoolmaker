# ross lazarus August 2023
# for parsing nf-core test texts written in their DDL
# to replace fugly string hacking

nftesttext = """
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


class nextflowParser():

    def __init__(self):
        """
        now much simpler with prefiltering
        """
        self.testroot = "tests/modules/nf-core"
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
        ts = """workflow test_abacas {
tpname1 = file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)
ABACAS ( input, fasta )
}
        """
        #OneOrMore(testbodyparams).parse_string(ts)
        nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(testbodyparams) + Suppress("}"))
        # and all together now...
        self.nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + includeTests + Group(OneOrMore(nftestname))
        #print(self.nftest.parse_string(nftesttext))
        #print([x for x in nftestname.scan_string(ts)])
        # print(nftest.parse_string(nftesttext))
        # that's what we have so far - will try parsing every test nf file to find all the missing bits - like stubs...
        # >>> nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group( OneOrMore(nftestname))
        # >>> print(nftest.parse_string(nftesttext))
        # [['#', '!/usr/bin/env', 'nextflow'], ['nextflow', '.enable.dsl', '=', ' 2'], 'HMMER_HMMSEARCH', [['test_hmmer_hmmsearch', 'input', ['[', "id:'test',", 'single_end:false', ']'],
        #  'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/da
        # ta/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'false', 'false', 'false', 'HMMER_HMMSEARCH', 'input', ')'], ['test_hmmer_hmmsearch_optional', 'input', ['[', "id:'test',", 'single_e
        # nd:false', ']'], 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-dat
        # asets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'true', 'true', 'true', 'HMMER_HMMSEARCH', 'input', ')']]]

    def simplifyTest(self, script):
        """
        remove junk like        [ id:'test', single_end:false ], // meta map
        """
        news = []
        skipNextrbracket = False
        tpname = None
        ss = script.split('\n')
        for i,row in enumerate(ss):
            if len(row.strip()) > 0:
                rows = row.split()
                if rows[0] == "]" and skipNextrbracket:
                    skipNextrbracket = False
                elif "//" in rows: # hope they always use a space otherwise https:// is a problem?
                    if "id:'test'," in rows:
                        skipNextrbracket = True ## this leaves nameless parameters
                        tpname = rows[0] # first name
                        nparam = 1
                    else:
                        wor = rows[::-1]
                        print(wor)
                        wor = wor.split("//",1)[1] # break at last one in case http:
                        res = ' '.join(wor[::-1])
                        news.append(res)
                else:
                    if skipNextrbracket:
                        rows.insert(0, "=")
                        rows.insert(0, 'tpname%d' % nparam)
                        nparam += 1
                    news.append(' '.join(rows))
        newss = '\n'.join(news)
        print(newss)
        return newss

    def Parse(self, s):
        ss = self.simplifyTest(s)
        print('ss=', ss)
        parsed = self.nftest.parse_string(ss)
        return parsed

foo = nextflowParser()
if len(sys.argv) > 1:
    spath = sys.argv[1]
    s = open(spath, 'r').read()
    try:
        p = foo.Parse(s)
        print(spath, 'PARSED!')
    except:
        print(spath, 'failed to parse')
        sys.exit(666)
else:
    print('no parameter')



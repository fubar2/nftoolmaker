# ross lazarus August 2023
# for parsing nf-core test texts written in their DDL
# to replace fugly string hacking

nftesttext = """
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

import sys
import os
from pyparsing import * # yes,  I know but that's what the package author recommends

class cleanUpTests():
    """
    remove junk like        [ id:'test', single_end:false ], // meta map
    and take care of single parameters with gratuitous brackets and groups of parameters in brackets that need to all be renamed
    for each 'workflow' segement ending in }, find the very last ] and deal with each parameter symbol in between that has an = after it.
    """

    def __init__(self, script):
        """
        """
        self.simplified = None
        nestedItems = nestedExpr("[", "]")
        self.nested = OneOrMore(Word(alphanums + "_") + "=" + Group(originalTextFor(nestedItems)))
        s = self.removeComments(script)
        ss = s.split('\n') # parse as rows - punt!
        tnames = []
        ttexts = []
        indx = 0
        tlen = len(ss)
        print(tlen)
        while indx < tlen:
            row = ss[indx]
            rows = row.split()
            indx += 1
            if rows[0] == "workflow": # find the name and {
                tname = rows[1]
                if len(rows) > 3:
                    thistext = [' '.join(rows[3:])]
                else:
                    thistext = []
                tnames.append(tname)
                noend = True
                while noend and indx < tlen:
                    row = ss[indx]
                    indx += 1
                    rows = row.split()
                    if "}" in rows:
                        rbi = rows.index("}")
                        rows[rbi] = "\n}"
                        noend = False
                    else:
                        thistext += rows

                simpler = self.oneTest(thistext)
                # print('++++++++++++++simpler:', simpler)
                ttexts.append("workflow %s {\n%s\n" %(tname, simpler))
            else:
                ttexts.append(row) # neutral fluff
        self.simplified = '\n'.join(ttexts)

    def oneTest(self, tokelist):
        """
        deal with a single workflow foo { } segment
0 ['input_vcf', '=', "[ [ id:'test' ], file(params.test_data['homo_sapiens']['genome']['genome_chain_gz'], checkIfExists: true) ]"]
1 ['dict', '=', "[ [ id:'genome' ], file(params.test_data['homo_sapiens']['genome']['genome_dict'], checkIfExists: true), file('https://testcaseraw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true) ]"]
2 ['chain', '=', "[ [ id:'genome' ], file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true) ]"]
3 ['fasta', '=', "[ [ id:'genome' ], file(params.test_data['homo_sapiens']['genome']['genome_fasta'], checkIfExists: true) ]"]

        """
        s = ' '.join(tokelist)
        # afterlastbracket = len(s) -s[::-1].index('(')
        # tail = s[(afterlastbracket - 2):]
        # head = s[:(afterlastbracket - 4)]
        # print('\n***head', head, '\ntail', tail)
        paramNameWord = Word(alphanums + "_-.")
        nftestcall = Word(srange("[A-Z_]")) + Suppress("(") + OneOrMore(paramNameWord + ZeroOrMore(",")) + ')' + Suppress(restOfLine)
        useless =  Suppress(Literal('checkIfExists:') | Literal('true)') + ZeroOrMore(",") | nftestcall)
        gobbledegook = OneOrMore(Word(alphanums + ":-_'") + ZeroOrMore(","))
        badmeta = Suppress( OneOrMore("[") + gobbledegook + SkipTo("]") + OneOrMore("]") + ZeroOrMore(","))
        badbracket = Suppress("]")
        good = Word(printables)
        cleanmeta = OneOrMore(badmeta | badbracket | useless | good)
        #simpler = self.nested.parseString(head)
        simpler = cleanmeta.parseString(s).asList()
        #print('raw', simpler)
        #simpler = [str(x) for x in simpler]
        #print('### simpler', simpler)
        #clean = self.nested.parseString(simpler)#hmmm
        #print('### clean!:', clean)
        res = []
        nrow = len(simpler)
        i =1
        while i < nrow:
            thing = simpler[i]
            if thing == "=":
                pname = simpler[i-1]
                if simpler[i+1].startswith('file('):
                    term = "%s = %s)" % (pname, simpler[i+1].replace(",", ''))
                else:
                    term = "%s = %s" % (pname, thing)
                res.append(term)
                i += 2
            else:
                if i < (nrow -2) and (simpler[i+1] == "="):
                    pname = simpler[i]
                    i += 1
                else:
                    if thing.startswith('file('):
                        term = '%s%d = %s)' % (pname, i, thing)
                    else:
                        term = '%s%d = %s' % (pname, i, thing)
                    res.append(term)
                    i += 1
        simpler = ' \n'.join(res)
        #print('simpler:', simpler)
        return simpler

    def removeComments(self, s):
        ss = s.split("\n")
        ss = [x.strip() for x in ss if len(x.strip()) > 0]
        news = []
        for i, row in enumerate(ss):
            rows = row.split()
            if "//" in rows:
                wor = row[::-1]
                wor = wor.split("//", 1)[1]  # break at last one in case http:
                res = wor[::-1]
                news.append(res)
            else:
                news.append(row)
        return '\n'.join(news) # string

    def test(self):
        """
        """
        s1 = """
workflow test_picard_liftovervcf_stubs {
input_vcf = [ [ id:'test' ],
file(params.test_data['homo_sapiens']['genome']['genome_chain_gz'], checkIfExists: true)
]
dict = [ [ id:'genome' ],
file(params.test_data['homo_sapiens']['genome']['genome_dict'], checkIfExists: true),
file('https://testcaseraw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true)
]
chain = [ [ id:'genome' ],
file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true)
]
fasta = [ [ id:'genome' ],
file(params.test_data['homo_sapiens']['genome']['genome_fasta'], checkIfExists: true)
]
PICARD_LIFTOVERVCF ( input_vcf, dict, fasta, chain )
}
        """
        simp = cleanUpTests(s)
        print("@@@@",simp.simplified)



class nextflowParser():

    def __init__(self):
        """
        now much simpler with prefiltering
        """
        self.testroot = "tests/modules/nf-core"
        anyquote = Suppress(Literal("'") | Literal('"'))
        paramWord = Word(alphanums + "+=_.-'" + '"')
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
        nftestURL = Suppress(Literal("file(params.test_data")) + Word(alphanums + '"' + "['-_.]")  + Suppress(ZeroOrMore(")"))
        realtestURL = Suppress(Literal("file(")) + Word(inUrls) +  Suppress(",") + Suppress(ZeroOrMore(Word(alphanums + ":_.-"))) + Suppress(")")
        paramVal = paramWord + optionalcomma #+ Suppress(restOfLine)
        paramname = paramNameWord + Suppress("=")
        # composite components
        paramexpr = nftestURL | realtestURL | paramVal
        simpleparam = OneOrMore(paramname + paramexpr)
        testbodyparams = nftestcall ^ simpleparam
        ts = """workflow test_abacas {
tpname1 = file(params.test_data['sarscov2']['illumina']['scaffolds_fasta'], checkIfExists: true)
fasta = file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)
ABACAS ( input, fasta )
}
        """
        #OneOrMore(testbodyparams).parse_string(ts)
        nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(testbodyparams) + Suppress(ZeroOrMore("}")))
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



    def Parse(self, s, modname):
        cleaner = cleanUpTests(s)
        ss = cleaner.simplified
        # print("modname=", modname, "\ns=", s, '\nss=', ss)
        parsed = self.nftest.parse_string(ss)
        return parsed

foo = nextflowParser()
if len(sys.argv) > 1:
    spath = sys.argv[1]
    modname = os.path.split(spath)[1]
    s = open(spath, 'r').read()
    try:
        p = foo.Parse(s, modname)
        print(spath, 'PARSED!')
    except:
        print(spath, 'failed to parse', s, "boohoo" )
        sys.exit(666)
else:
    foo = cleanUpTests(nftesttext)
    print("Cleaned test case=",foo.simplified)

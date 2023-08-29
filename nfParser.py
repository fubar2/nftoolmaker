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
failed = """
#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { DIAMOND_MAKEDB } from '../../../../../modules/nf-core/diamond/makedb/main.nf'
include { DIAMOND_BLASTX } from '../../../../../modules/nf-core/diamond/blastx/main.nf'
include { MEGAN_DAA2INFO } from '../../../../../modules/nf-core/megan/daa2info/main.nf'

workflow test_megan_daa2info {

db = [ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true) ]
fasta = [ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['genome_fasta'], checkIfExists: true) ]
out_ext = 'daa'
blast_columns = []
megan_summary = true

DIAMOND_MAKEDB ( db )
DIAMOND_BLASTX ( [ [id:'test'], fasta ], DIAMOND_MAKEDB.out.db, out_ext, blast_columns )
MEGAN_DAA2INFO ( DIAMOND_BLASTX.out.daa, megan_summary )
}
"""
failed = """
#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { NANOPLOT  } from '../../../../modules/nf-core/nanoplot/main.nf'

workflow test_nanoplot_summary {
    def input = []
    input = [ [ id:'test' ],
            [ file(params.test_data['sarscov2']['nanopore']['test_sequencing_summary'], checkIfExists: true) ] ]

    NANOPLOT ( input )
}

workflow test_nanoplot_fastq {
    def input = []
    input = [ [ id:'test' ],
            [ file(params.test_data['sarscov2']['nanopore']['test_fastq_gz'], checkIfExists: true) ] ]

    NANOPLOT ( input )
}

"""
import sys
import os
from pyparsing import * # yes,  I know but that's what the package author recommends

debug = True

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
        s = self.removeComments(script)
        ss = s.split('\n') # parse as rows - punt!
        tnames = []
        ttexts = []
        indx = 0
        tlen = len(ss)
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
                        if not row.startswith('def '):
                            thistext += rows
                simpler = self.oneTest(thistext)
                if debug:
                    print('++++++++++++++simpler:', simpler)
                ttexts += simpler
        self.simplified = '\n'.join(ttexts)

    def getTVals(self, s):
        """
        this took a few tries
        returns a list of param values for a test
        """
        LB,RB = map(Suppress,"[]")
        anyquote = Suppress(Literal("'") | Literal('"'))
        paramWord = Word(alphanums + "+_.-'" + '"')
        paramNameWord = Word(alphanums + "_-.")
        optionalcomma = Suppress(Literal(",")[0,1])
        namedpar = Suppress(paramNameWord + "=") + paramWord
        nftestcall = Suppress( Word(srange("[A-Z0-9_]")) +("(") + OneOrMore(Word(printables,excludeChars=')')) + ')' + restOfLine)
        inUrls = alphanums + ":/_+[].-?&'" + '"'
        # some utility DSL syntax - unsuppress it if you care
        shebang = Suppress("#" + Word(alphanums + "#!/_.") + Word(alphanums + "./") + restOfLine) # #!/usr/bin/env nextflow
        dsl = Suppress("nextflow" + OneOrMore(Word(alphanums + "./[]")) + Literal("=")[...] + restOfLine) # nextflow.enable.dsl = 2
        includetest = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z0-9_]")) + Suppress("}") + Suppress(restOfLine)
        sidcore = Combine((Literal("[ id:") | Literal("[id:")) + Word(printables,excludeChars=']' )) + OneOrMore( Word(printables,excludeChars='] ')) + "]"
        sid = Suppress( sidcore) + restOfLine
        psidcore = Combine((Literal("[ id:") | Literal("[id:") | Literal("[[id:") ) + Word(printables,excludeChars=']' )) + ZeroOrMore( Word(printables,excludeChars='] '))
        psid =  Suppress(paramNameWord + "=" + "[" + psidcore + (Literal("]") | Literal("],")) + ZeroOrMore(",")) + restOfLine
        # chain = [ [ id:'genome' ],
        sid.set_name("sid")
        notsid = shebang | dsl | includetest | psid | sid | namedpar | nftestcall | originalTextFor(restOfLine)
        notb = LB | RB | Suppress("}") | Word(printables) + restOfLine
        ss =  notsid.scanString(s)
        l = [x[0].asList()[0] for x in ss if len(x[0]) > 0]
        l = '\n'.join(l)
        ssb = notb.scanString(l)
        ll = [x[0].asList()[0] for x in ssb if len(x[0]) > 0]
        ll = [x.strip(', ') for x in ll]
        return ll


    def oneTest(self, tokelist):
        """
        deal with a single workflow foo { } segment
>>> nested = OneOrMore(Word(alphanums + "_-") + "=" + Group(originalTextFor(nestedItems | Word(alphanums + ".-'" + '"'))))
>>> nested.parseString(failed)
(['db', '=', (["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true) ]"], {}), 'fasta', '=', (["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['genome_fasta'], checkIfExists: true) ]"], {}), 'out_ext', '=', (["'daa'"], {}), 'blast_columns', '=', (['[]'], {}), 'megan_summary', '=', (['true'], {})], {})

s.asList()

['db', '=', ["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true) ]"], 'fasta', '=', ["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['genome_fasta'], checkIfExists: true) ]"], 'out_ext', '=', ["'daa'"], 'blast_columns', '=', ['[]'], 'megan_summary', '=', ['true']]


        """
        s = ' '.join(tokelist)
        if debug:
            print('----s', s)
        simpler = self.getTVals(s)
        if debug:
            print('----------s',simpler)
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














class cleanUpTests1():
    """
    remove junk like        [ id:'test', single_end:false ], // meta map
    and take care of single parameters with gratuitous brackets and groups of parameters in brackets that need to all be renamed
    for each 'workflow' segement ending in }, find the very last ] and deal with each parameter symbol in between that has an = after it.
    """

    def __init__(self, script):
        """
        """
        self.returnjunk = False # return shebang and other useless dreck
        self.simplified = None
        s = self.removeComments(script)
        ss = s.split('\n') # parse as rows - punt!
        tnames = []
        ttexts = []
        indx = 0
        tlen = len(ss)
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
                if debug:
                    print('++++++++++++++simpler:', simpler)
                if self.returnjunk:
                    ttexts.append("workflow %s {\n%s\n" %(tname, simpler))
                else:
                    ttexts.append(simpler)
            else:
                if self.returnjunk:
                    ttexts.append(row) # neutral fluff
        self.simplified = '\n'.join(ttexts)


    def oneTest(self, tokelist):
        """
        deal with a single workflow foo { } segment
>>> nested = OneOrMore(Word(alphanums + "_-") + "=" + Group(originalTextFor(nestedItems | Word(alphanums + ".-'" + '"'))))
>>> nested.parseString(failed)
(['db', '=', (["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true) ]"], {}), 'fasta', '=', (["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['genome_fasta'], checkIfExists: true) ]"], {}), 'out_ext', '=', (["'daa'"], {}), 'blast_columns', '=', (['[]'], {}), 'megan_summary', '=', (['true'], {})], {})

s.asList()

['db', '=', ["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true) ]"], 'fasta', '=', ["[ file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['genome_fasta'], checkIfExists: true) ]"], 'out_ext', '=', ["'daa'"], 'blast_columns', '=', ['[]'], 'megan_summary', '=', ['true']]


        """
        s = ' '.join(tokelist)
        paramWord = Word(alphanums + "+=_.-'" + '"')
        paramNameWord = Word(alphanums + "_-.")
        optionalcomma = Suppress(Literal(",")[0,1])
        ignoredefs = "def" + paramNameWord + "=" + Word(printables)
        nftestcall = Word(srange("[A-Z0-9_-]")) + Suppress("(") + OneOrMore(Word(alphanums + "'.:-_[]") + ZeroOrMore(",")) + ')'
        nestedItems = nestedExpr("[", "]")
        notnested =  ~Literal("[") + Group(originalTextFor(Word(alphanums + "[]().-'_,: " + '"')))
        nested = OneOrMore(Word(alphanums + "_-") + "=" + (notnested | originalTextFor(OneOrMore(nestedItems ))))
        cleannest = Suppress(nftestcall) | nested
        useless =  Suppress(Literal('checkIfExists:') | Literal('true)') + ZeroOrMore(",") | nftestcall | ignoredefs)
        gobbledegook = OneOrMore(Word(alphanums + ":-_'") + ZeroOrMore(","))
        badmeta = Suppress( OneOrMore("[") + gobbledegook + SkipTo("]") + OneOrMore("]") + ZeroOrMore(","))
        badbracket = Suppress("]")
        good = Word(printables)
        cleanmeta = OneOrMore(badmeta | badbracket | useless | good)
        if debug:
            print('----s', s)
        simpler = tokelist #cleannest.parseString(s).asList()
        if debug:
            print('----------s',simpler)
        res = []
        for i, expr in enumerate(simpler): # remove bogus brackets
            if type(expr) == type([]): # fix a list
                subexpr = []
                for j, y in enumerate(expr):
                    if y.startswith("[") and y.endswith("]"):
                        if len(y) == 2: # bogus empty nest
                            y = "None"
                        else:
                            y = y[1:-1] # drop bogus []
                    subexpr.append(y)
                res += subexpr
            else:
                res.append(expr)
        if debug:
            print('after denesting', res)
        simpler = cleanmeta.parseString(' '.join(res)).asList()
        if debug:
            print('after cleanmeta', simpler)
        res = []
        nrow = len(simpler)
        i =0
        while i < nrow:
            thing = simpler[i]
            if (i+1) < nrow and simpler[i+1] == "=":
                pname = thing
                term = "%s = None" % pname # nulls at ends
                expr = simpler[i+2]
                if expr == "[]":
                    expr = "None"
                if expr.startswith('file('):
                    term = "%s = %s)" % (pname, expr.replace(",", ''))
                else:
                    term = "%s = %s" % (pname, expr)
                i += 3
                res.append(term)
                if debug:
                    print('1 inner term', term, 'thing', thing, "i", i)
            elif thing == "=":
                i += 1
            else:
                term = "%s_%d = None" % (pname,i) # nulls at ends
                if thing == "[]":
                    thing = "None"
                if thing.startswith('file('):
                    term = "%s_%d = %s)" % (pname, i, thing.replace(",", ''))
                else:
                    if thing.endswith(','):
                        thing = thing[:-1]
                    term = "%s_%d = %s" % (pname, i, thing)
                i += 1
                res.append(term)
                if debug:
                    print('2 inner thing, term', term, 'thing', thing, 'i', i)
        simpler = ' \n'.join(res)
        if debug:
            print('processed res:', simpler)
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
        nftestcall = Word(srange("[A-Z0-9_]")) + Suppress("(") + OneOrMore(paramNameWord + optionalcomma) + ')' + Suppress(restOfLine)
        includetest = Suppress(Literal("include")) + Suppress("{") + Word(srange("[A-Z0-9_]")) + Suppress("}") + Suppress(restOfLine)
        includeTests = Suppress(OneOrMore(includetest))
        nftestURL = Suppress(Literal("file(params.test_data")) + Word(alphanums + '"' + "['-_.]")  + Suppress(ZeroOrMore(")"))
        realtestURL = Suppress(Literal("file(")) + Word(inUrls) +  Suppress(",") + Suppress(ZeroOrMore(Word(alphanums + ":_.-"))) + Suppress(")")
        paramVal = paramWord + optionalcomma #+ Suppress(restOfLine)
        paramname = paramNameWord + Suppress("=")
        # composite components
        paramexpr = nftestURL | realtestURL | paramVal
        simpleparam = OneOrMore(paramname + paramexpr)
        testbodyparams = nftestcall ^ simpleparam
        nftestname = Group(Suppress(Literal("workflow")) + Word(alphanums + "_") + Suppress("{") +  OneOrMore(testbodyparams) + Suppress(ZeroOrMore("}")))
        # and all together now...
        nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + includeTests + Group(OneOrMore(nftestname))
        self.nftest = nftest
        """
        Can try to parse the entire test but it's a fool's errand - only need the test parameters - the rest is useless bumpf.
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
         """


    def Parse(self, s, modname):
        cleaner = cleanUpTests(s)
        ss = cleaner.simplified
        # print("modname=", modname, "\ns=", s, '\nss=', ss)
        # parsed = self.nftest.parse_string(ss)
        return ss


if __name__ == "__main__":
    foo = nextflowParser()
    if len(sys.argv) > 1:
        spath = sys.argv[1]
        modname = os.path.split(spath)[1]
        s = open(spath, 'r').read()
        try:
            p = foo.Parse(s, modname)
            print(spath, 'PARSED!', p)
        except:
            print(spath, 'failed to parse', s, "boohoo" )
            sys.exit(666)
    else:
        foo = cleanUpTests(failed)
        print("Cleaned test case=",foo.simplified)

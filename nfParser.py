# ross lazarus August 2023
# for parsing nf-core test texts written in their DDL
# to replace fugly string hacking

nftesttext = """
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2
include { HMMER_HMMSEARCH } from '../../../../../modules/nf-core/hmmer/hmmsearch/main.nf'
workflow test_hmmer_hmmsearch {
    input = [
        [ id:'test', single_end:false ],
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
ampir = """
#!/usr/bin/env nextflow

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

failed2 = """
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

debug = False

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
        ttexts = []
        indx = 0
        tlen = len(ss)
        while indx < tlen:
            row = ss[indx]
            rows = row.split()
            indx += 1
            if len(row) > 0 and rows[0] == "workflow": # find the name and {
                tname = rows[1]
                if len(rows) > 3:
                    thistext = [' '.join(rows[3:])]
                else:
                    thistext = []
                noend = True
                while noend and indx < tlen:
                    row = ss[indx].strip()
                    indx += 1
                    if not (row.startswith('def ') or (row.startswith("//"))):
                        rows = row.split()
                        if debug:
                            print('rows:', rows)
                        if "}" in row:
                            rbi = row.index("}")
                            if rbi == 0:
                                rows = []
                                row = ""
                                noend = False
                        if len(rows) > 1:
                            if rows[1] == "=":
                                rows = rows[2:]
                                row = ' '.join(rows)
                                if len(rows) > 0 and rows[0] == "[]":
                                    rows[0] = "None"
                                    row = rows[0]
                            elif rows[1] == "(":
                                rows = []
                                row = ""
                            if "file(" in row and "checkIfExists" in row:
                                iy = row.index('file(')
                                ix = row.index("checkIfExists")
                                row = row[iy:ix]
                                rows = row.split()
                        started  = None
                        ended = None
                        for ri, elem in enumerate(rows):
                            if elem.startswith("id:"):
                                started = ri
                            elif elem.startswith(']'):
                                if started and not ended:
                                    ended = ri
                        if started:
                            if started > 0:
                                started -= 1
                            if ended:
                                rows = rows[:started] + rows[ended:]
                                if debug:
                                    print('newrows', rows)
                            else:
                                rows = []
                            if debug:
                                print('id cleanup', rows, 'start,end', started, ended)
                        nob = []
                        if len(rows) > 0:
                            for x in rows:
                                if x.endswith(','):
                                    x = x[:-1]
                                if not (x.startswith("[") or x.startswith("]")):
                                    nob.append(x)
                        if len(nob) > 0:
                            thistext += nob
                            if debug:
                                print('________________row:', nob)
                        else:
                            if debug:
                                print('gobbled', row)
                if debug:
                    print("*********onetest", thistext)
                ttexts.append(thistext)
        self.simplified = ttexts


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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        spath = sys.argv[1]
        modname = os.path.split(spath)[1]
        s = open(spath, 'r').read()
        foo = cleanUpTests(s)
        ss = foo.simplified
        print(spath, 'PARSED!', ss)
        # except:
            # print(spath, 'failed to parse', s, "boohoo" )
            # sys.exit(666)
    else:
        foo = cleanUpTests(ampir)
        print('ampir',foo.simplified)
        foo = cleanUpTests(failed)
        print('nono',foo.simplified)
        foo = cleanUpTests(nftesttext)
        print('nf',foo.simplified)
        foo = cleanUpTests(failed2)
        print('failed2',foo.simplified)

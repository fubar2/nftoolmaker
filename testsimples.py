from pyparsing import *

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
                    thistext += rows

                simpler = self.oneTest(thistext)
                print('++++++++++++++simpler:', simpler)
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
        afterlastbracket = len(s) -s[::-1].index(']')
        tail = s[afterlastbracket:]
        head = s[:afterlastbracket]
        print('\n***head', head, '\ntail', tail)
        useless =  Suppress(Literal('checkIfExists:') | Literal('true)') + ZeroOrMore(",") )
        gobbledegook = OneOrMore(Word(alphanums + ":-_'") + ZeroOrMore(","))
        badmeta = Suppress( OneOrMore("[") + gobbledegook + SkipTo("]") + OneOrMore("]") + ZeroOrMore(","))
        badbracket = Suppress("]")
        good = Word(printables)
        cleanmeta = OneOrMore(badmeta | badbracket | useless | good)
        #simpler = self.nested.parseString(head)
        simpler = cleanmeta.parseString(head).asList()
        print('raw', simpler)
        #simpler = [str(x) for x in simpler]
        print('### simpler', simpler)
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
        simpler = ' \n'.join(res) + "\n" + tail
        print('simpler:', simpler)
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


if __name__ == "__main__":
    s = """#!/usr/bin/env nextflow
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

    s1 = """
#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { PICARD_COLLECTHSMETRICS } from '../../../../../modules/nf-core/picard/collecthsmetrics/main.nf'

workflow test_picard_collecthsmetrics {

    input = [
        [ id:'test', single_end:false ], // meta map
        file(params.test_data['sarscov2']['illumina']['test_paired_end_sorted_bam'], checkIfExists: true),
        file(params.test_data['sarscov2']['illumina']['test_paired_end_sorted_bam_bai'], checkIfExists: true),
        file(params.test_data['sarscov2']['genome']['baits_interval_list'], checkIfExists: true),
        file(params.test_data['sarscov2']['genome']['targets_interval_list'], checkIfExists: true)
        ]

    fasta = [[id:'genome'], file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)]
    fai   = [[id:'genome'], file(params.test_data['sarscov2']['genome']['genome_fasta_fai'], checkIfExists: true)]
    dict  = [[id:'genome'], file(params.test_data['sarscov2']['genome']['genome_dict'], checkIfExists: true)]

    PICARD_COLLECTHSMETRICS ( input, fasta, fai, dict )
}

workflow test_picard_collecthsmetrics_nofasta {

    input = [
        [ id:'test', single_end:false ], // meta map
        file(params.test_data['sarscov2']['illumina']['test_paired_end_sorted_bam'], checkIfExists: true),
        file(params.test_data['sarscov2']['illumina']['test_paired_end_sorted_bam_bai'], checkIfExists: true),
        file(params.test_data['sarscov2']['genome']['baits_interval_list'], checkIfExists: true),
        file(params.test_data['sarscov2']['genome']['targets_interval_list'], checkIfExists: true)
        ]

    PICARD_COLLECTHSMETRICS ( input, [[:],[]], [[:],[]], [[:],[]] )
}

workflow test_picard_collecthsmetrics_bed_input {

    input = [
        [ id:'test', single_end:false ], // meta map
        file(params.test_data['sarscov2']['illumina']['test_paired_end_sorted_bam'], checkIfExists: true),
        file(params.test_data['sarscov2']['illumina']['test_paired_end_sorted_bam_bai'], checkIfExists: true),
        file(params.test_data['sarscov2']['genome']['baits_bed'], checkIfExists: true),
        file(params.test_data['sarscov2']['genome']['test_bed'], checkIfExists: true)
        ]

    fasta = [[id:'genome'], file(params.test_data['sarscov2']['genome']['genome_fasta'], checkIfExists: true)]
    fai =   [[id:'genome'], file(params.test_data['sarscov2']['genome']['genome_fasta_fai'], checkIfExists: true)]
    dict  = [[id:'genome'], file(params.test_data['sarscov2']['genome']['genome_dict'], checkIfExists: true)]

    PICARD_COLLECTHSMETRICS ( input, fasta, fai, dict )
}
    """
    foo = cleanUpTests(s)
    print(foo.simplified)
    print(foo.test())

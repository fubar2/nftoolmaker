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
        print(tlen)
        while indx < tlen:
            row = ss[indx]
            rows = row.split()
            indx += 1
            print('+++rows',rows)
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
                        noend = False
                    thistext += rows
                print('++++++++++++++this', thistext)
                simp = self.oneTest(thistext)
                simps = '/n'.join(simp)
                ttexts.append(simps)
                print('++++++++++++++t', ttexts)
            else:
                ttexts.append(row) # neutral fluff
        self.simplified = '\n'.join(ttexts)

    def oneTest(self, tokelist):
        """
        deal with a single workflow foo { } segment
        """
        afterlastbracket = len(tokelist) - tokelist[::-1].index(']')
        tail = tokelist[afterlastbracket:]
        head = tokelist[:afterlastbracket]
        print('head', head, 'tail', tail)
        simpler = self.simplify(head)
        simpler += tail
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

    def deBracketElements(self, ltarget, rtarget, s, i):
        """
        parse [foo = bar] as [foo, bar]
        foo = [[bar]] ditto
        foo = [[bar][[zot][boo][gong]] etc

        """
        more = True
        lens = len(s)
        indx = i  # assume [ is gone
        thisexpr = []
        nlayers = 0
        while indx< lens and more:
            if s[indx][0] not in [rtarget, ltarget]:
                thisexpr.append(s[indx])
                indx += 1
            elif s[indx] == rtarget:  # end subexpression
                more = 0  # stop
                indx += 1
            else:  # must be new sublist = ltarget
                indx += 1
                if indx < lens:
                    j, subex, more, nlayers = self.deBracketElements(ltarget, rtarget, s, indx)
                    indx = j
                    thisexpr += subex
                    nlayers += 1
        print("stb end expr", thisexpr, indx, more, nlayers)
        return indx, thisexpr, more, nlayers

    def simplify(self, tokes):
        """
        comments are gone
        look for nested parameters and deal with them
        """
        outs = []
        indx = 0
        lens = len(tokes)
        pname = None
        stopme = False
        more = True
        while indx < lens and more:
            token = tokes[indx]
            if token.startswith("["):
                indx += 1
                if indx < lens:
                    j, newstuff, more, nlayers = self.deBracketElements("[", "]", tokes, indx)
                    indx = j
                    print("## prenewstuff", newstuff, indx, 'nlayers', nlayers)
                    ns = newstuff[0].split()
                    for k, stuff in enumerate(ns):
                        if k > 0:
                            ns[k] = '%s%d = %s' % (pname, k, stuff)
                    newstuff = ' '.join(ns)
                    print("## newstuff", newstuff, indx, stopme)
                    outs.append(newstuff)
            elif token != "]":
                outs.append(token)
                if token == "=":
                    pname = tokes[indx - 1]  #
                    print('found pname', pname)
                indx += 1
            else: #
                print('odd. Token = ] at indx', indx, 'in', tokes)
                indx += 1
        return outs



s = """
workflow test_picard_liftovervcf_stubs {
input_vcf = [ [ id:'test' ],
file(params.test_data['homo_sapiens']['genome']['genome_chain_gz'], checkIfExists: true)
]
dict = [ [ id:'genome' ],
file(params.test_data['homo_sapiens']['genome']['genome_dict'], checkIfExists: true)
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
print(simp.simplified)

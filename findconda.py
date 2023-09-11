# scan all galaxy iuc/bgruening tools for conda


import argparse
import copy
import lxml.etree as ET
import os
import subprocess
from bs4 import BeautifulSoup

toolds = ["/home/ross/rossgit/galaxytools/tools"] #, "/home/ross/rossgit/tools-iuc/tools"]


class nfModDeps():
    """
    """
    def __init__(self, corepath):
        modlist = os.listdir(corepath)
        self.packages = {}
        for i,d in enumerate(modlist):
            self.convertd(os.path.join(corepath, d))

    def getlinestart(self, flag):
        lstart = [x.strip() for x in self.nftext if x.strip().startswith(flag)]
        return lstart


    def makePackages(self, cs):
            """
            "conda-forge::r-ampir=1.1.0"
            or
            container "docker.io/nfcore/cellrangermkfastq:7.1.0"
            """
            creq = None
            if "::" in cs:
                c = cs.replace('"', "").split("::")[1].strip()
                req = [c]
                creq = ",".join(req)
            else:
                if cs.strip().lower().startswith("container"):
                    creq = cs.split()[1]
                else:
                    print('@@@@@ Cannot parse requirements ',cs, 'into container or Conda packages')
            return creq


    def amod(self, mod, dlist):
        toolname = os.path.split(mod)[1]
        tex = [x for x in dlist if x.endswith('.nfcore') or x.endswith('.nf')][0]
        if len(tex) > 0:
            self.nftext = open(tex,'r').readlines()
            cond = self.getlinestart("conda")
            cont = self.getlinestart("container")
            if len(cond) > 0:
                ps = self.makePackages(cond[0])
            else:
                ps = self.makePackages(cont[0])
            if self.packages.get(ps, None):
                p = self.packages[ps]
                p.append(mod)
                self.packages[ps] = p
            else:
                self.packages[ps] = [mod,]
        else:
            print('no nfcore file with dependencies found for', mod, 'in', dlist)

    def convertd(self, d):
        """one
        """
        if os.path.isdir(d):
            dlist = os.listdir(d)
        else:
            print("dlist", d, "is not a directory")
            return
        bpath, dname = os.path.split(d)
        dlist = [os.path.join(bpath,dname,x) for x in dlist]
        #print('## convertd dlist',dlist,'for d',d)
        fnames = [x.split('/')[-1] for x in dlist]
        if "meta.yml" in fnames or "main.nf" in fnames or "main.nfcore" in fnames:
            self.amod(d, dlist)
        else:
            for adir in [x for x in dlist if os.path.isdir(x)]:
                moddir = os.listdir(adir)
                moddir = [os.path.join(adir, x) for x in moddir]
                self.convertd(adir)



class getToolReqs:

    def __init__(self):
        self.galconda = {}
        self.galcont = {}
        self.tokens = {}
        self.parser = ET.XMLParser(remove_blank_text=True)

    def parseReqs(self, dep, atr,  tname):
        # [<requirement type="package" version="@TOOL_VERSION@">flye</requirement>]
        typ = atr.get('type', None)
        ver = atr.get('version', None)
        if ver:
            if self.tokens.get(ver, None):
                ver = self.tokens[ver]
        deps = "%s:%s" % (dep, ver)
        if typ == "package":
            if self.galconda.get(deps, None):
                g = self.galconda[deps]
                g.append(tname)
                self.galconda[dep] = g
            else:
                self.galconda[deps] = [
                    tname,
                ]
        else:
            if self.galcont.get(deps, None):
                g = self.galcont[deps]
                g.append(tname)
                self.galcont[dep] = g
            else:
                self.galcont[deps] = [
                    tname,
                ]

    def parse(self, xp, tname):
        # try:
            # tree = ET.parse(xp, self.parser)
        # except ET.XMLSyntaxError:
            # print(
                # "### Tool xml parse error - %s cannot be parsed as xml by element tree\n"
                # % xp
            # )
            # tree = None
           # reqs = root.xpath("//requirement")
       with open(xp, 'r') as mfile:
            mtext = mfile.read()
        tsoup = BeautifulSoup(mtext,'lxml', features="xml")
        if tsoup:
            tooldir = os.path.split(xp)[0]
            macs = tsoup.find_all("import")
            for m in macs:
                mname = m.text
                with open(os.path.join(tooldir,mname)) as mfile:
                    mtext = mfile.read()
                msoup = BeautifulSoup(mtext,'lxml', features="xml")
                mtokes = msoup.find_all('token')
                # [<token name="@TOOL_VERSION@">2.9.1</token>, <token name="@SUFFIX_VERSION@">0</token>]
                for mt in mtokes:
                    k = mt.attrs
                    name = k['name']
                    val = mt.text
                    self.tokens[name] = val
                mreq = msoup.find_all('requirement')
                for mt in mreq:
                    dep = mt.text
                    k = mt.attrs # {'type': 'package', 'version': '@TOOL_VERSION@'}
                    self.parseReqs(dep, k, tname)
            req = tsoup.find_all('requirement')
            if req:
                for mt in req:
                    dep = mt.text
                    k = mt.attrs # {'type': 'package', 'version': '@TOOL_VERSION@'}
                    self.parseReqs(dep, k, tname)

                # # [<requirement type="package" version="@TOOL_VERSION@">flye</requirement>]
                # self.parseReqs(mreqs, tname)
                # mtext = [x.replace("'",'"') for x in mtext] # yes, cdata makes the parser fail
                # mtree = ET.parse(mtext, self.parser)
                # mroot = mtree.getroot()
                # tokes = mroot.xpath("//token")
                # for t in tokes:
                    # v = t.text
                    # if v:
                        # v = v.strip()
                    # try:
                        # n = t.attrib["name"]
                        # self.tokens[n] = v
                    # except:
                       # print('~~~~ no name for token')
                # mreqs = mroot.xpath('//requirements')
                # self.parseReqs(mreqs, tname)
            # print('&&&&&&&&&&&tokens=', self.tokens)
            # # the xml macro expansions are not needed for galaxyxml
            # # but tokens are essential for requirements if used.
            # reqs = root.xpath("//requirement")
            # self.parseReqs(reqs, tname)

    def trawl(self, tooldir):
        tdlist = os.listdir(tooldir)
        for ttool in tdlist:
            atool = os.path.join(tooldir, ttool)
            if os.path.isdir(atool):
                tname = os.path.split(atool)[1]
                xpect = "%s.xml" % tname
                xmlpath = os.path.join(atool, xpect)
                dd = os.listdir(atool)
                if xpect in dd:
                    g = self.parse(xmlpath, tname)
                else:
                    xfiles = [
                        x
                        for x in dd
                        if os.path.splitext(x)[1] == ".xml"
                        and os.path.splitext(x)[0].startswith(tname)
                    ]
                    if len(xfiles) == 0:
                        print(
                            "~~~no",
                            xpect,
                            " or any ",
                            tname,
                            " prefixed xml files found for",
                            atool,
                            "in dd",
                            dd,
                        )
                    else:
                        for xpect in xfiles:
                            xmlpath = os.path.join(atool, xpect)
                            g = self.parse(xmlpath, tname)

if __name__ == "__main__":
    n = nfModDeps(corepath)
    print('++++++++++++++npackages',n.packages)
    nf = list(n.packages.keys())
    nfd = [x.split("=")[0] for x in nf if x and len(x) > 0]
    g = getToolReqs()
    for tpath in toolds:
        g.trawl(tpath)
        #print('tpath', toolds[0], 'conda', g.galconda, 'containers', g.galcont)
    gf = list(g.galconda.keys())
    gd = [x.split(':')[0] for x in gf]
    nftodo = []
    print('--------------gd',gd,len(gd))
    for i, k in enumerate(nf):
        if k:
            nft = k.split('=')[0]
            if nft in gd:
                already.append('%s in %s' % (nft, n.packages[k]))
            else:
                nftodo.append('%s in %s' % (nft, n.packages[k]))
    print('whitelist=', sorted(nftodo), len(nftodo))
    print('already=', sorted(already), len(already))

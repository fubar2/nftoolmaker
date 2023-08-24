# ross lazarus
# august 2023
# scan nf-core modules for scripts
import os

def getsection(self, flag):
    insect = False
    inquote = False
    sect = []
    for x in self.nftext:
        if x.lstrip().startswith(flag):
            insect = True
        else:
            if insect:
                if  x.strip() == '"""':
                    if inquote:
                        sect.append(x.strip())
                        inquote = False
                        insect = False
                    else:
                        inquote = True
                if x.strip() == '':
                    if not inquote:
                        insect = False
            if insect:
                sect.append(x.strip())
    return '\n'.join(sect)

def getlinestart(self,  flag):
    lstart = [x.lstrip() for x in self.nftext if x.lstrip().startswith(flag)]
    return lstart


allscripts = []
sins = open('nfscripts.txt','w')
nf = '../nfcore_modules/modules/nf-core' # assume in nftoolmaker next door
for (root,dirs,files) in os.walk(nf, topdown=True):
    ourfiles = [x for x in files if x.endswith('.nf')]
    print('ourfiles', ourfiles, 'root', root, 'dirs=', dirs, 'files=', files)
    for n in ourfiles:
        np = os.path.join(root,n)
        nfs = open(np,'r').readlines()
        nfs.insert(0,'## %s\n' % np)
        allscripts += nfs
        print(dirs)
sins.write(''.join(allscripts))
sins.close()

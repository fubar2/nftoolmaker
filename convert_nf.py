# script to run nftoolmaker on nf-core modules
# assumes is in a venv with planemo/bioblend/galaxyxml and there's a toolfactory running with the right
# admin key in the toolfactoryclass.py

import argparse
import os
import subprocess

corepath = '../nfcore_modules/modules/nf-core'
cl = ["python", "nftoolmaker.py",  "--tool_dir", "."]

def amod(mod, dlist):

    toolgz = '%s_nfmod_tool.tar.gz' % mod
    print('dlist=', dlist, 'mod=',mod, 'toolgz=',toolgz)
    yam = [x for x in dlist if x.endswith('.yml')][0]
    tex = [x for x in dlist if x.endswith('.nfcore') or x.endswith('.nf')][0]
    acl = cl + ["--nftext", tex, "--nfyml",yam, "--toolgz", toolgz]
    p = subprocess.run(acl)
    if p.returncode:
        print('Got', p.returncode, "from", ' '.join(acl))

def convertd(d):
    """one
    """
    dlist = os.listdir(os.path.join(corepath,d))
    dlist = [os.path.join(corepath, d, x) for x in dlist]
    print('dlist',dlist,'for d',d)
    fnames = [x.split('/')[-1] for x in dlist]
    if "meta.yml" in fnames:
        amod(d, dlist)
    else:
        for adir in dlist:
            moddir = os.listdir(adir)
            moddir = [os.path.join(corepath, adir, x) for x in moddir]
            print('adir =', adir, 'moddir', moddir, 'dlist=', dlist)
            amod(d, moddir)


parser = argparse.ArgumentParser()
a = parser.add_argument
a("--mod", default = None, required=False)
args = parser.parse_args()
modlist = os.listdir(corepath)

if args.mod and args.mod in modlist:
    convertd(args.mod)
else:
    for i,d in enumerate(modlist):
        print(i,d)
        convertd(d)


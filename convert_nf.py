# script to run nftoolmaker on nf-core modules
# assumes is in a venv with planemo/bioblend/galaxyxml and there's a toolfactory running with the right
# admin key in the toolfactoryclass.py

import argparse
import os
import subprocess

corepath = '../nfcore_modules/modules/nf-core'
cl = ["python", "nftoolmaker.py",  "--tool_dir", "."]

def amod(mod, dlist):

    yam = [x for x in dlist if x.endswith('.yml')][0]
    tex = [x for x in dlist if x.endswith('.nfcore') or x.endswith('.nf')][0]
    toolgz = '%s_nfmod_tool.tar.gz' % os.path.split(yam)[1]
    acl = cl + ["--nftext", tex, "--nfyml",yam, "--toolgz", toolgz]
    print('### amod calling nftoolmaker with', acl)
    p = subprocess.run(acl)
    if p.returncode:
        print('amod Got', p.returncode)

def convertd(d):
    """one
    """
    dlist = os.listdir(d)
    bpath, dname = os.path.split(d)
    dlist = [os.path.join(bpath,dname,x) for x in dlist]
    print('## convertd dlist',dlist,'for d',d)
    fnames = [x.split('/')[-1] for x in dlist]
    if "meta.yml" in fnames:
        amod(d, dlist)
    else:
        for adir in dlist:
            moddir = os.listdir(adir)
            moddir = [os.path.join(adir, x) for x in moddir]
            print('calling convertd with adir =', adir, 'moddir', moddir)
            convertd(adir)


parser = argparse.ArgumentParser()
a = parser.add_argument
a("--mod", default = None, required=False)
args = parser.parse_args()
modlist = os.listdir(corepath)

if args.mod and args.mod in modlist:
    convertd(os.path.join(corepath, args.mod))
else:
    for i,d in enumerate(modlist):
        convertd(os.path.join(corepath, d))


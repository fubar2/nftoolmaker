# script to run nftoolmaker on nf-core modules
# assumes is in a venv with planemo/bioblend/galaxyxml and there's a toolfactory running with the right
# admin key in the toolfactoryclass.py

import argparse
import os
import subprocess

corepath = '../nfcore_modules/modules/nf-core'


def amod(mod, dlist,args):

    y = [x for x in dlist if x.endswith('.yml')]
    y +=  [x for x in dlist if x.endswith('.yaml')]
    if len(y) > 0:
        yam = y[0]
        tex = [x for x in dlist if x.endswith('.nfcore') or x.endswith('.nf')][0]
        acl =  ["python", "nftoolmaker.py",  "--galaxy_root", args.galaxy_root, "--toolfactory_dir",
  "%s/local_tools/toolfactory" % args.galaxy_root, "--nftest", "--nftext", tex, "--nfyml", yam, "--collpath",  "%s/local_tools/TF/%s" % (args.galaxy_root, os.path.split(mod)[1])]
        print('### amod ', mod, 'calling nftoolmaker with', acl)
        p = subprocess.run(acl)
        print('### stdout ', p.stdout, 'stderr', p.stderr)
    else:
        print("******* mod', mod, 'has no yml in", dlist, "so cannot parse")

def convertd(d, args):
    """one
    """
    dlist = os.listdir(d)
    bpath, dname = os.path.split(d)
    dlist = [os.path.join(bpath,dname,x) for x in dlist]
    #print('## convertd dlist',dlist,'for d',d)
    fnames = [x.split('/')[-1] for x in dlist]
    if "meta.yml" in fnames or "main.nf" in fnames or "main.nfcore" in fnames:
        amod(d, dlist, args)
    else:
        for adir in [x for x in dlist if os.path.isdir(x)]:
            moddir = os.listdir(adir)
            moddir = [os.path.join(adir, x) for x in moddir]
            print('calling convertd with adir =', adir, 'moddir', moddir)
            convertd(adir, args)


parser = argparse.ArgumentParser()
a = parser.add_argument
a("--mod", default = None, required=False)
a("--galaxy_root", default = None, required=True)
args = parser.parse_args()
modlist = os.listdir(corepath)

if args.mod:
    if args.mod in modlist:
        convertd(os.path.join(corepath, args.mod), args)
    else:
        print('Cannot find module', args.mod)
else:
    for i,d in enumerate(modlist):
        convertd(os.path.join(corepath, d, args))


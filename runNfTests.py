# script to run nfParser.py on nf-core tests


import argparse
import os
import subprocess

corepath = '../nfcore_modules/tests/modules/nf-core/'

def amod(mod, dlist, logfile):

    tex = [x for x in dlist if x.endswith('.nfcore') or x.endswith('.nf')][0]
    acl = ["python", "nfParser.py", tex]
    p = subprocess.run(acl).returncode
    if logfile:
        logfile.write('module %s returned %d\n' % (mod, p))
    #print(mod, p)


def convertd(d, logfile):
    """one
    """
    dlist = os.listdir(d)
    bpath, dname = os.path.split(d)
    dlist = [os.path.join(bpath,dname,x) for x in dlist]
    #print('## convertd dlist',dlist,'for d',d)
    fnames = [x.split('/')[-1] for x in dlist]
    if len([x for x in fnames if x.endswith(".yml")]) > 0:
        amod(d, dlist, logfile)
    else:
        for adir in dlist:
            try:
                moddir = os.listdir(adir)
                moddir = [os.path.join(adir, x) for x in moddir]
                #print('calling convertd with adir =', adir, 'moddir', moddir)
                convertd(adir, logfile)
            except:
                print('### convertd not listing', adir)

parser = argparse.ArgumentParser()
a = parser.add_argument
a("--mod", default = None, required=False)
args = parser.parse_args()
modlist = os.listdir(corepath)
i = 0
if args.mod and args.mod in modlist:
    convertd(os.path.join(corepath, args.mod), None)
else:
    outf = open('parseNfTests.log','w')
    for i,d in enumerate(modlist):
        res = convertd(os.path.join(corepath, d), outf)


# script to run nftoolmaker on nf-core modules
# assumes is in a venv with planemo/bioblend/galaxyxml and there's a toolfactory running with the right
# admin key in the toolfactoryclass.py

import argparse
import os
import subprocess

corepath = '../nfcore_modules/modules/nf-core'

whitelist = ['abacas', 'admixture', 'affy', 'agat', 'agrvate', 'allelecounter', 'ampcombi', 'ampir', 'amps', 'angsd', 'arcashla', 'ariba', 'ashlar', 'ataqv', 'authentict', 'backsub', 'bacphlip', 'bamaligncleaner', 'bamcmp', 'bamtools', 'bbmap', 'bclconvert', 'bioawk', 'biobambam', 'biscuit', 'bismark', 'cadd', 'calder2', 'canu', 'cellpose', 'clippy', 'clonalframeml', 'cmseq', 'cnvpytor', 'cooler', 'crumble', 'csvtk', 'custom', 'damageprofiler', 'dastool', 'dedup', 'deeparg', 'deepbgc', 'deepcell', 'deeptools', 'dragmap', 'dragonflye', 'dshbio', 'duphold', 'ectyper', 'eido', 'eigenstratdatabasetools', 'eklipse', 'elprep', 'emmtyper', 'endorspy', 'epang', 'expansionhunter', 'expansionhunterdenovo', 'falco', 'famsa', 'faqcs', 'fastk', 'fcs', 'ffq', 'fgbio', 'flye', 'fq', 'fqtk', 'galah', 'gamma', 'gangstr', 'ganon', 'gappa', 'gawk', 'gecco', 'gem2', 'genmap', 'genmod', 'genotyphi', 'gfaffix', 'gget', 'glimpse', 'glimpse2', 'glnexus', 'gnu', 'goat', 'goleft', 'gridss', 'gstama', 'gunc', 'gunzip', 'hapibd', 'hicap', 'hlala', 'hmmcopy', 'hmtnote', 'hpsuissero', 'ichorcna', 'icountmini', 'igv', 'iphop', 'islandpath', 'ismapper', 'isoseq3', 'kaiju', 'kat', 'kmcp', 'leehom', 'lissero', 'macrel', 'mafft', 'manta', 'mapad', 'mapdamage2', 'maxquant', 'mcquant', 'mcroni', 'md5sum', 'methyldackel', 'midas', 'mindagap', 'miranda', 'mitohifi', 'mmseqs', 'mobsuite', 'motus', 'msisensor', 'msisensor2', 'msisensorpro', 'mtnucratio', 'muscle', 'nanolyse', 'nanomonsv', 'nextgenmap', 'nfc', 'ngmaster', 'ngmerge', 'ngsbits', 'nucmer', 'paftools', 'pairix', 'pairtools',  'paraclu', 'pasty', 'pbbam', 'pbccs', 'pbptyper', 'peddy', 'peka', 'phantompeakqualtools', 'phispy', 'pindel', 'pints', 'pirate', 'platypus', 'pmdtools', 'preseq', 'prodigal', 'pydamage', 'pyrodigal', 'racon', 'rasusa', 'rgi', 'rhocall', 'rsem', 'rtgtools', 'salmon', 'sam2lca', 'sambamba', 'samtools', 'scimap', 'scramble', 'segemehl', 'seqsero2', 'sequencetools', 'sequenzautils', 'seroba', 'sexdeterrmine', 'sgdemux', 'shasum', 'shigatyper', 'shigeifinder', 'shinyngs', 'simpleaf', 'sistr', 'smncopynumbercaller', 'smoothxg', 'smoove', 'snpdists', 'snpsift', 'snpsites', 'somalier', 'sortmerna', 'spaceranger', 'spatyper', 'sratools', 'ssuissero', 'stadeniolib', 'staphopiasccmec', 'stranger', 'subread', 'survivor', 'svaba', 'svdb', 'svtk', 'svtyper', 'tabix', 'tailfindr', 'taxpasta', 'tbprofiler', 'tiara', 'tiddit', 'trimgalore', 'trimmomatic', 'ultra', 'ultraplex', 'umicollapse', 'umitools', 'universc', 'upd', 'varlociraptor', 'vcf2db', 'vcflib', 'verifybamid', 'vrhyme', 'wgsim', 'whamg', 'wisecondorx']

def amod(mod, dlist, args):
    toolname = os.path.split(mod)[1]
    white = [x for x in whitelist if toolname.startswith(x)]
    if len(white) == 0:
        return
    y = [x for x in dlist if x.endswith('.yml')]
    y +=  [x for x in dlist if x.endswith('.yaml')]

    if len(y) > 0:
        yam = y[0]
        tex = [x for x in dlist if x.endswith('.nfcore') or x.endswith('.nf')][0]
        acl =  ["python", "nftoolmaker.py",  "--galaxy_root", args.galaxy_root, "--toolfactory_dir",  "%s/local_tools/toolfactory" % args.galaxy_root, "--nftest", "--nftext", tex, "--nfyml", yam, "--collpath",  "%s/local_tools/%s" % (args.galaxy_root, toolname)]
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
        convertd(os.path.join(corepath, d), args)


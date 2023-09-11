# script to run nftoolmaker on nf-core modules
# assumes is in a venv with planemo/bioblend/galaxyxml and there's a toolfactory running with the right
# admin key in the toolfactoryclass.py

import argparse
import os
import subprocess

corepath = '../nfcore_modules/modules/nf-core'

whitelist= ['abacas', 'abi', 'abricate', 'access', 'adapterremovalfixprefix', 'admixture', 'agrvate', 'align', 'allelecounter', 'ampcombi', 'ampir', 'amps', 'amrfinderplus', 'analyze', 'ancestry', 'annotate', 'annotsv', 'antismashlite', 'antismashlitedownloaddatabases', 'antitarget', 'app', 'applybqsr', 'applyvarcal', 'aria2', 'ascat', 'ashlar', 'assemblyscan', 'assesssignificance', 'ataqv', 'backsub', 'bacphlip', 'baftest', 'balance', 'bamaligncleaner', 'bamcmp', 'bamcoverage', 'bammarkduplicates2', 'bammerge', 'bamsormadup', 'bases2fastq', 'basicpy', 'batch', 'bbduk', 'bbnorm', 'bbsplit', 'bcl2fastq', 'bclconvert', 'bedclip', 'bedgraphtobigwig', 'bedtobigbed', 'bigwigaverageoverbed', 'bioawk', 'biohansel', 'biscuitblaster', 'bracken', 'bsconv', 'build', 'buildcustom',  'cadd', 'calculateexpression', 'calder2', 'call', 'callcnvs', 'callduplexconsensusreads', 'caller', 'callmolecularconsensusreads', 'callvariants', 'ccurve', 'cdhit', 'cdhitest', 'cellpose', 'centrifuge',  'chromap',
'chromograph', 'chunk', 'classify', 'clippy', 'cload', 'clonalframeml', 'clumpify', 'cluster', 'clusteranalysis', 'clusteridentifier', 'cnnscorevariants',  'combinebrackenoutputs', 'combinekreports',
'concordance', 'cons', 'construct', 'contamination', 'contigs', 'convert', 'convertinversion', 'coreograph', 'count', 'countsvtypes','coverage', 'createpon', 'createtsv', 'crumble', 'daa2info', 'damageprofiler', 'databases', 'datametrics', 'dbnsfp', 'deam2cont', 'deconstruct', 'dedup', 'deeparg', 'deepvariant', 'determinegermlinecontigploidy', 'dnamodelapply', 'dnascope', 'docounts', 'dragonflye', 'draw', 'dump', 'duphold', 'easysearch', 'ectyper', 'eigenstratsnpcoverage', 'eklipse',
'emmtyper', 'endorspy', 'endtoend', 'epiread', 'esearch', 'estimatealignmentproperties', 'esummary', 'examineassign', 'examinegraft', 'examineheattree', 'expansionhunter',  'exportsegments', 'extractunbinned', 'extractvariants', 'falco', 'faqcs', 'fargene', 'fastawindows', 'fasterqdump', 'fastk','fcsadaptor', 'fcsgx', 'ffq', 'filterbed',
'filterconsensusreads', 'filtergff3', 'findmitoreference', 'flip', 'fq2bam', 'fqtk', 'freec', 'freec2bed', 'freec2circos', 'galah', 'gamma', 'gangstr', 'gather', 'gccounter', 'gcwiggle',
'gem2bedmappability', 'gemindexer', 'gemmappability', 'gender', 'genemetrics', 'generate', 'generatemap', 'genescopefk', 'genomegenerate', 'genotype', 'germline', 'germlinecnvcaller', 'getgeo', 'getref', 'gfaffix',
'gget', 'glnexus', 'gridss', 'groupreadsbyumi', 'gsea', 'gtf2featureannotation', 'guidetree', 'gvcftyper', 'hapibd', 'haplocheck', 'haplotyper', 'happy', 'hashtable', 'hicap', 'hicpca', 'hpsuissero', 'idxdepth', 'image', 'importreaddepth', 'indelrealigner', 'index', 'indexsplit', 'installannotations', 'intervalfile', 'islandpath', 'ismapper', 'jupyternotebook', 'justrma', 'kaiju', 'kaiju2krona',
'kaiju2table', 'katcomp', 'katgc', 'kraken2', 'kreport', 'kreport2krona', 'layout', 'lcextrap', 'leehom', 'lfq', 'liftover', 'ligate', 'lima', 'linkbins', 'lint', 'lissero',
'maltextract', 'mapcounter', 'mapdamage2', 'mapper', 'mashtree', 'mbias', 'mcmicro', 'mcquant', 'mcroni', 'mem', 'merge', 'mergecg', 'mergecheckm', 'merquryfk', 'mesmer', 'metagene', 'mindagap', 'miranda',
'mkarv', 'mkfastq', 'mkgtf', 'mkref', 'mkvdjref', 'models', 'msi', 'msisomatic', 'mtnucratio', 'multi', 'multibamsummary', 'multicut', 'multigrmpy', 'multivcfanalyzer', 'mummer', 'muscle', 'nanolyse',
'ncbigenomedownload', 'ncm', 'newref', 'nextgenmap', 'ngmaster', 'ngmerge', 'normaldb', 'normalize', 'normalizebymedian', 'nucmer', 'oncocnv', 'pairix', 'paraclu', 'parse', 'partition', 'pasty', 'pbccs', 'pbmerge',
'pbptyper', 'peaks', 'peddy', 'pedfilter', 'peka', 'phantompeakqualtools', 'phase', 'phasecommon', 'phaserare', 'phispy', 'phyloflash', 'pileup', 'pileupcaller', 'pindel', 'pipeline', 'pirate', 'pixelclassification',
'place', 'plasmidid', 'platypus', 'ploidyplot', 'plotcorrelation', 'plotfingerprint', 'plotheatmap', 'plotpca', 'plotprofile', 'pmd', 'polyacleanup', 'polymut', 'postprocessgermlinecnvcalls', 'predict', 'prefetch',
'preloadedkrakenuniq', 'preparegraph', 'preparereference', 'preprocess', 'prepy', 'prinseqplusplus', 'profile', 'pyrodigal', 'qc', 'qcat', 'quant', 'query', 'rasusa', 'raxmlng', 'rdtest2vcf', 'readcounter',
'readwriter', 'realignertargetcreator', 'recal', 'recon', 'ref', 'reference', 'refine', 'relate', 'report', 'restrict', 'rgi', 'rma2info', 'rocplot', 'samplegender', 'scan', 'score', 'scramble',
'search', 'segment', 'select', 'sendsketch', 'seqret', 'seqsero2', 'sexdeterrmine', 'sgdemux', 'shigatyper', 'shigeifinder', 'sigxls', 'sistr', 'sketch', 'slimfastq', 'smncopynumbercaller', 'smoothxg','snpeff', 'somatic',  'sortmerna', 'spatyper',  'splitreference', 'squeeze', 'sratoolsncbisettings', 'ssuissero','staphopiasccmec', 'starsolo', 'staticdifferential', 'staticexploratory','stitch', 'stranger', 'sv', 'svaba', 'svtyper', 'switch', 'table', 'tailfindr', 'target',
'taxannotate', 'taxonsearch', 'tiara', 'tnscope', 'trimbam', 'trimmomatic', 'tsv2exprofiledb', 'tumoronly', 'typing', 'ultraplex', 'umicollapse', 'unchop', 'unifiedgenotyper', 'uniquekmers', 'universc', 'validatefomcomponents', 'varcal', 'variantbam', 'vcf', 'vcf2bed', 'vcf2db', 'vcf2paragraph', 'vcfbreakmulti', 'vcfconcatenate', 'vcfeval', 'vcffilter', 'vcftools',
'vcfuniq', 'vdj', 'verifybamid', 'verifybamid2','vrhyme', 'wfmash', 'wgsim', 'wgsmetrics', 'whamg', 'wigtobigwig', 'xtract', 'zipperbams', 'zoomify']

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
    if os.path.isdir(d)
        dlist = os.listdir(d)
    else:
        print("dlist", dlist, "is not a directory")
        return
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


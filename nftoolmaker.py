# nftoolmaker.py
# ross lazarus
# august 2023
# exploring nf-core modules as potential Galaxy tools
# halted: too much work - needs the DSL to be parsed for the script templating.
# working kind of september 21 but not worth trying all modules
# maybe just save the testdata URI and parameters plus the TF command line as artifacts
# then make a TF tool to generate a tool based on that command line so it can be fixed.


import argparse
import json
import os
import pathlib
import sys
import subprocess
import tempfile
import yaml


import copy

import logging

import re
import shlex
import shutil

import sys
import tarfile
import tempfile
import time
from urllib.parse import urlparse
from bioblend import galaxy
from bioblend import ConnectionError

import galaxyxml.tool as gxt
import galaxyxml.tool.parameters as gxtp

import lxml.etree as ET

from nfParser import  cleanUpTests
from toolfactory import Tool_Factory

logger = logging.getLogger(__name__)
FILTERCHARS = "[]{}'"
debug = False
blacklist = ['hmtnote_annotate', 'mobsuite_recon']

class ParseNFMod:
    """
    mostly not working well parser and Galaxy tool xml generator for nf-core module scripts and metadata.
    Harder than is worth. Easy to deal with templating the script by writing it and then running it at run time.
    Problem is that there are things in the DDL preceding the script and they need to be introspected
    to set the templated variables. I think I give up
    Tackling that - need to substitute our output name for the right ${prefix}.ext so use the extension Luke
    """

    def __init__(self, nft, nfy, args):
        self.infileurls = []
        self.status = None
        self.canTest = True # build even if false?
        self.testParamList = None
        self.testURLprefix = "https://raw.githubusercontent.com/nf-core/test-datasets/"
        self.modroot = os.path.split(nfargs.nftext)[0]
        self.tool_name = nfy["name"].replace("'",'').lower().strip()
        self.tfcl = ["--parampass", "embednfmod"]
        if args.nftest: # default is not
            self.tfcl.append("--nftest")
        self.local_tools = os.path.join(args.galaxy_root, "local_tools")
        self.cl_coda = [ "--galaxy_root", args.galaxy_root, "--toolfactory_dir", args.toolfactory_dir, "--tfcollection", args.collpath]
        # if args.nftest:
                # self.local_tools = os.path.join(args.galaxy_root, "local_tools")
                # self.repdir = os.path.join(self.local_tools, "TF", self.tool_name)
                # self.toold = os.path.join(self.local_tools, self.tool_name)
                # self.tooltestd = os.path.join(self.toold, "test-data")
                # self.cl_coda = [ "--galaxy_root", args.galaxy_root, "--toolfactory_dir", args.toolfactory_dir, "--tfcollection", args.collpath]
        # else
        # pathlib.Path(self.toold).mkdir(parents=True, exist_ok=True)
        # pathlib.Path(self.tooltestd).mkdir(parents=True, exist_ok=True)
        # pathlib.Path(self.repdir).mkdir(parents=True, exist_ok=True)
        pathlib.Path('tfcl').mkdir(parents=True, exist_ok=True)
        self.scriptPrefixSubs = {}
        self.nftext = nft
        if "secret 'SENTIEON_LICENSE_" in ' '.join(nft):
            print("!!!!!!!!!!!!!!! Refusing to build a tool for a proprietary licenced binary !!!!!!!!!!!!!!!!!!!!")
            self.status = "notOS"
        self.nfyaml = nfy
        self.args = args
        self.localTestFile =  "nfgenomicstestdata.txt"
        self.setTestFiles() # setup crosswalk for test downloads
        if args.nftest: # default is not
            self.tfcl.append("--nftest")
        self.inparamnames = []
        self.outparamnames = []
        self.inputpar = []
        nfyin = nfy.get("input", None)
        print('nfy[input]', nfyin)
        if not nfyin:
            print('### refusing to build a tool without inputs found in yaml')
            sys.exit(0)
        for d in nfy["input"]:
            pname = list(d.keys())[0]
            ptype = d[pname]["type"]
            if ptype != "map":
                self.inputpar.append(d)
        for indx, inpdict in enumerate(self.inputpar): # need these for tests
            # the test names can be different. Go figure.
            pname = list(inpdict.keys())[0]
            self.inparamnames.append(pname)
        self.inparamcount = len(self.inparamnames) # needed to select a test using them all - bugger anything else - too hard to match up names
        self.getTestInfo()

        if self.testParamList:
            if self.inparamcount != len(self.testParamList):
                print("### inparamcount = ", self.inparamcount, 'but there are', len(self.testParamList), 'test parameters in', self.testParamList)
                self.status = "paramcount"
        else:
              print("### no test parameters in", self.tool_name)
              self.status = "paramcount"
        self.makeMeta()
        stub = self.getsection("stub:")  # not all have these - no idea what they're for
        for indx, inpdict in enumerate(self.inputpar):
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]["type"]
            if ptype == "map":
                print("Ignoring map specified as input %s" % str(inpdict))
            elif ptype.startswith("file"): # one case has files
                self.makeInfile(inpdict,indx)
            elif ptype == "string":
                self.makeString(inpdict, indx)
            elif ptype == "val":
                self.makeFlag(inpdict, indx)
            elif ptype in ["number", "integer"]:
                self.makeNum(inpdict, indx)
            else:
                print("### unknown input type encountered in %s" % str(inpdict))
        for inpdict in nfy["output"]:
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]["type"]
            if ptype.startswith("file"): # one case has files:
                tfdict = self.makeOutfile(inpdict)
            elif ptype == "map":
                print("Ignoring map specified as output %s" % str(inpdict))
            else:
                print("### unknown output type encountered in %s" % str(inpdict))
        self.scriptExe = self.makeScript(self.getsection("script:"))
        cond = self.getlinestart("conda")
        cont = self.getlinestart("container")
        if len(cond) > 0:
            self.makePackages(cond[0])
        else:
            self.makePackages(cont[0])
        self.tfcl += self.cl_coda
        self.tfcl = [x for x in self.tfcl if x.strip() > ""]

    def setTestFiles(self):
        td = open(self.localTestFile, "r").readlines()
        td = [x.strip() for x in td]
        td = [
            "/".join(x.strip().split("/")[1:]) for x in td
        ]  # remove bogus "branches/"LA
        file_dict = {}
        totdups = 0
        for x in td:
            lastbit = x.split('/')[-1].strip()
            if file_dict.get(lastbit,None):
                file_dict[lastbit].append(x) # fugly but assume the files are the same if same name
                totdups += 1
            else:
                file_dict[lastbit] = [x] # fugly but assume the files are the same if same name
        self.file_dict = file_dict


    def getTestInfo(self):
        """ read tests and parse into a list of sets of params using nfParser
        """
        self.setTestFiles()
        if '_' in self.tool_name: # ridiculous hack for multi tool modules
            submod = self.tool_name.replace('_','/') # punt
            testything = "../nfcore_modules/tests/modules/nf-core/%s/main.nf" % submod
        else:
            testything = "../nfcore_modules/tests/modules/nf-core/%s/main.nf" % self.tool_name
        if os.path.exists(testything):
            nftesttext = open(testything, "r").read()
            clean = cleanUpTests(nftesttext)
            tests = clean.simplified
            print(testything, 'PARSED! =', tests)
            self.testok = True
            if type(tests[0]) == type([]):
                self.testParamList = tests[0]
            else:
                self.testParamList = tests
        else:
            nftest = None
            print(
                "#### bad news - no test data because testything",
                testything,
                "not found",
            )

    def failtool(self, toold, failtype):
        """
        move to failed
        """
        toolbase = os.path.split(toold)[0]
        faildir = os.path.join(toolbase, failtype)
        if not os.path.exists(faildir):
            os.makedirs(faildir, exist_ok=True)
        src = toold
        dest = os.path.join(faildir, self.tool_name)
        newpath = shutil.copytree(src, dest)
        print("$$$$$ copied failed tool", self.tool_name,'from', src, "to", dest)
        if failtype != "whitelist":
            self.tf.update_toolconf(remove=True)
        logging.shutdown()
        sys.exit(0)

    def uri_validator(self, x):
        try:
            result = urlparse(x)
            return True
        except:
            return False

    def fixTDPath(self, p):
        """
        replace file paths with real urls
        """
        res = []
        if p.startswith('file(param'):
                testfpath = (
                    p.split("[", 1)[1]
                    .split(",")[0]
                    .replace("][", "/")
                    .replace("'", "")
                )  # 'candidatus_portiera_aleyrodidarum/genome/proteome_fasta'
                tfilename = testfpath.split('/')[-1].replace('_','.').replace(']','')
                # so much evil, pointless obfuscation and indirection
                # because we can.
                tstart = '/'.join(testfpath.split('/')[:-1])
                testfpath = os.path.join(tstart, tfilename)
                # 'candidatus_portiera_aleyrodidarum/genome/proteome.fasta'
                foundpaths = self.file_dict.get(tfilename, None)
                if not foundpaths:
                    print(
                        "test specifier",
                        testfpath,
                        "not found in directory of the test repository. Please run the updater",
                    )
                    self.canTest = False
                    foundpath = p
                else:
                    foundpath = self.testURLprefix + foundpaths[0]
        else: #'file(https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz,'
            foundpath = p.replace('file(','').replace(',','').replace(')','')
        validated = self.uri_validator(foundpath)
        if not validated:
            print('!!!!!!!!!!!!!!!!!!!!! TDPath foundpath', foundpath, 'is not a valid URL so this module test code should be fixed',args.nftex)
        if debug:
            print('fixTDPath returning', foundpath)
        return foundpath, validated


    def fixParamFormat(self,pfmt):
        """
this is a nasty rabbit hole with a fugly kludge
Need a lookup table for all the possibilities
can be a comma sep list but need to be Galaxy datatypes only

a grep for the idiom ${prefix} in the entire nf-core module text corpus was converted into the following list of extensions they seem to have.
Some are bogus but the short ones might be genuine. Problem is that formats need to match Galaxy's expectations.

nftypes = [ 'BedGraph', 'CollectMultipleMetrics', 'IS', 'IS_compare', 'IS_compare/output', 'R', 'abacas', 'afa', 'agp', 'alignment_summary_metrics', 'all', 'alleleCount', 'aln', 'asm', 'assembly_summary', 'back_chain', 'bai', 'ballgown', 'bam', 'base_distribution_by_cycle_metrics', 'bcf', 'bcf"', 'bed', 'bed"', 'bedGraph', 'bedGraph"', 'bedgraph"', 'bedpe', 'bg', 'bigBed', 'bigWig', 'bin', 'biom', 'bw', 'clustered', 'clw"', 'cnn', 'cns', 'cool', 'coords', 'count', 'coverage_metrics', 'cpn', 'crai', 'cram', 'csi', 'csi"', 'csv', 'csv"', 'cutoffs', 'd4', 'db', 'dbtype', 'delta', 'dict', 'dnd', 'domtbl"', 'embl', 'fa', 'fa;', 'faa', 'fas', 'fasta', 'fastq', 'fastq"', 'ffn', 'flagstat', 'fmask-all"', 'fmask-rf"', 'fna', 'fsa', 'gbff', 'gbk', 'gem', 'genepred', 'gfa', 'gff', 'gff3', 'gmask-all"', 'gmask-rf"', 'gtf', 'gtf"', 'gz', 'gz"', 'gz":', 'gz;', 'hdf5', 'hist', 'hmm', 'html', 'html"', 'ibf', 'idx', 'idxstats', 'igv":', 'index', 'insert_size_metrics', 'interval_list', 'interval_list"', 'intervals', 'json', 'junction', 'lca', 'list', 'loci', 'log', 'lookup', 'maf', 'mappability', 'mash_stats', 'mate1', 'mate2', 'mcool', 'megan"', 'meryldb', 'metrics', 'mpileup', 'mpileup"', 'msf"', 'narrowPeak', 'npz', 'og', 'out', 'paf', 'paf"', 'par', 'pdf', 'ped', 'phyi"', 'phyloFlash', 'phys"', 'pmask-all"', 'pmask-rf"', 'png', 'png"', 'pretext', 'profile', 'pytor', 'quality_by_cycle_metrics', 'quality_distribution_metrics', 'recal', 'recall":', 'refflat', 'refmap', 'report', 'rna_metrics', 'roh', 'sai', 'sam', 'score', 'screen', 'sdf', 'seg', 'simplified', 'sizes', 'snf', 'somalier', 'source', 'stat', 'stats', 'sthlm', 'sto"', 'summary', 'svg', 'tab', 'table', 'table"', 'table":', 'tax', 'tbi', 'tbi"', 'tbl', 'tbl"', 'tif', 'tiff', 'tiling', 'tmap', 'tracking', 'tranches', 'tre', 'tree"', 'tsv', 'tsv"', 'txt', 'txt"', 'txt":', 'unc', 'vcf', 'vcf"', 'version', 'vg', 'vgi"', 'wig', 'wig"', 'xg', 'xml', 'zip', ]

Now have a working hmmer_align xml and test data as a result of manual editing.
Need to make the generator use the right parameter names - it's tricky because fiddling the nf-core script text is a bit of a fool's errand - the whole project is really.
pattern: "*.{fna.gz,faa.gz,fasta.gz,fa.gz}"

        """
        swaps = {'faa':'fasta', 'hmmer':'hmm3', 'hmm':'hmm3', 'sthlm.gz':"stockholm", 'sthlm': "stockholm", "fa": "fasta",
            "hmm.gz": "hmm3", "hm.gz": "hmm3", "abacas*":"txt", "tsv": "tabular"}
        fastaspawn = ['fna.gz','faa.gz','fasta.gz','fa.gz', 'faa', 'fa', ]
        fixedfmt = []
        for f in pfmt.split(','):
            f = f.strip()
            if f in fastaspawn:
                if not 'fasta' in fixedfmt:
                    fixedfmt.append('fasta')
            elif swaps.get(f, None):
                f = swaps[f]
                if not f in fixedfmt:
                    fixedfmt.append(f)
            else:
                print('info: non-substituted format',f,'encountered in the input ppattern', pfmt)
                fixedfmt.append(f)
        s = list(set(fixedfmt))
        return ','.join(s)

    def saveTestdata(self,pname, testDataURL):
        """
        may need to be ungzipped and in test folder
        """
        res = 0
        localpath = os.path.join(self.tooltestd, "%s_sample" % pname)
        print("#### save", testDataURL, 'for', pname, 'to', localpath)
        if not os.path.exists(localpath):
            cl = ["wget", "--timeout", "5", "--tries", "2", "-O", localpath, testDataURL]
            if testDataURL.endswith('.gz'): # major kludge as usual...
                gzlocalpath = "%s.gz" % localpath
                cl = ["wget", "-q", "--timeout", "5", "--tries", "2", "-O", gzlocalpath, testDataURL, "&&", "rm", "-f", localpath, "&&", "gunzip", gzlocalpath]
            p = subprocess.run(' '.join(cl), shell = True)
            if p.returncode:
                print("Got", p.returncode, "from executing", " ".join(cl))
        else:
            print('Not re-downloading', localpath)
        return res

    def makeFlag(self, inpdict, indx):
        """
        boolean command line flag
        """
        print('flag indx',indx, self.testParamList)
        pdict = {}
        if indx > (len(self.testParamList) - 1):
            print('Makeflag parameter', indx, 'beyond length of parsed test parameters', self.testParamList,'so cannot test')
            self.canTest = False
            pval = "missing"
        else:
            pval = self.testParamList[indx]
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        ptype = inpdict[pname]["type"]
        if ptype == "val":
            pdict["type"] = "clflag"
        else:
            print('Unexpected type (not "val") encountered in makeFlag', ptype)
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["value"] = pval
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["repeat"] = "0"
        self.tfcl.append("--additional_parameters")
        self.tfcl.append(json.dumps(pdict))


    def makeInfile(self, inpdict, indx):
        """
        {'faa': {'type': 'file', 'description': 'FASTA file containing amino acid sequences', 'pattern': '*.{faa,fasta}'}}

        need --input_files '{"name": "/home/ross/rossgit/galaxytf/database/objects/d/d/4/dataset_dd49e13c-bd4d-4f8b-8eaa-863483d021f6.dat", "CL": "input_tab", "format": "tabular", "label": "Tabular input file to plot", "help": "If 5000+ rows, html output will fail, but png will work.", "required": "required"}'
        Need to copy testfile from localpath to the target tool test-dir
        """
        print('infileindx', indx, self.testParamList)
        pdict = {}
        pid = list(inpdict.keys())[0]
        ppath = pid
        validated = False
        if indx > (len(self.testParamList) - 1):
            print('Infile parameter', indx, 'beyond length of parsed test parameters', self.testParamList,'so cannot test')
            self.canTest = False
            tdURL = "missing"
        else:
            rawf = self.testParamList[indx]
            tdURL, validated = self.fixTDPath(rawf)
        if not validated:
            self.status = "badurl"
        self.infileurls.append(tdURL)
        if not ppath:
            ppath = pid
        plabel = inpdict[pid]["description"].replace('\n',' ')
        ppattern = inpdict[pid].get("pattern", "txt")
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        if ppattern.startswith('*'): # why? "*.{fna.gz,faa.gz,fasta.gz,fa.gz}"
            ppattern = ppattern[2:]
        fps = self.fixParamFormat(ppattern) # kludge so Galaxy doesn't get confused.
        #self.scriptPrefixSubs[pfmt] = "$%s" % pname # will be substituted in configfile
        pdict["URL"] = tdURL # so TF can download to test-data
        pdict["CL"] = pid
        pdict["name"] = pid
        pdict["format"] = fps
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["required"] = "0"
        self.tfcl.append("--input_files")
        self.tfcl.append(json.dumps(pdict))
        #self.saveTestdata(pid, tdURL)

    def makeOutfile(self, inpdict):
        """
        need  --output_files '{"name": "htmlout", "format": "html", "CL": "", "test": "sim_size:5000", "label": "Plotlytabular $title on $input_tab.element_identifier" , "when": [ "when input=outputimagetype value=small_png format=png" , "when input=outputimagetype value=large_png format=png" ] }'

        TODO: make a format lookup table or otherwise map all the dozens of extensions
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        ppattern = inpdict[pname].get("pattern", "missing")
        if ppattern == "versions.yml":
            return  # ignore these artifacts
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        if len(','.split(ppattern)) > 1:
            print('!!!!!! warning in makeOutfile for %s - ppattern %s is multiple - using the first in case ${prefix} rears its ugly head' % (pid, ppattern))
            pfmt = ','.split(ppattern)[0]
        else:
            pfmt = ppattern
        if pfmt.startswith('*'): # these imply ${prefix}.
            pfmt = pfmt[2:] # drop *.
        self.scriptPrefixSubs[pfmt] = "$%s" % pname # will be substituted in configfile
        pfmt = self.fixParamFormat(pfmt) # kludge so Galaxy doesn't get confused.
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["format"] = pfmt
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["test"] = "sim_size:1000"  # arbitrary hackery
        self.tfcl.append("--output_files")
        self.tfcl.append(json.dumps(pdict))

    def makeString(self, inpdict, indx):
        """
        need something like --additional_parameters '{"name": "xcol", "value": "petal_length", "label": "x axis for plot", "help": "Select the input tabular column for the horizontal plot axis", "type": "datacolumn","CL": "xcol","override": "", "repeat": "0", "multiple": "", "dataref": "input_tab"}'
        """
        print('str indx',indx, self.testParamList)
        pdict = {}
        if indx > (len(self.testParamList) -1) :
            print('Infile parameter', indx, 'beyond length of parsed test parameters', self.testParamList,'so cannot test')
            self.canTest = False
            pval = "missing"
        else:
            pval = self.testParamList[indx]
        pname = list(inpdict.keys())[0]
        ppattern = inpdict[pname].get("pattern", "missing")
        plabel = inpdict[pname]["description"].replace('\n',' ')
        if ppattern.startswith("{") and ppattern.endswith("}"):
            # is a select comma separated list
            self.makeSelect(inpdict, indx)
        else:
            pdict["type"] = "text"
            pdict["CL"] = pname
            pdict["name"] = pname
            pdict["value"] = pval
            pdict["help"] = ""
            pdict["label"] = plabel
            pdict["repeat"] = "0"
            self.tfcl.append("--additional_parameters")
            self.tfcl.append(json.dumps(pdict))

    def makeNum(self, inpdict, indx):
        """
        need something like --additional_parameters '{"name": "xcol", "value": "petal_length", "label": "x axis for plot", "help": "Select the input tabular column for the horizontal plot axis", "type": "datacolumn","CL": "xcol","override": "", "repeat": "0", "multiple": "", "dataref": "input_tab"}'
        """
        pdict = {}
        print('num indx',indx, self.testParamList)
        if indx > len(self.testParamList):
            print('Infile parameter', indx, 'beyond length of parsed test parameters', self.testParamList,'so cannot test')
            self.canTest = False
            pval = "missing"
        else:
            pval = self.testParamList[indx]
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        ptype = inpdict[pname]["type"]
        if ptype == "number":
            pdict["type"] = "float"
        else:
            pdict["type"] = "integer"
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["value"] = pval.replace('"', "")
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["repeat"] = "0"
        self.tfcl.append("--additional_parameters")
        self.tfcl.append(json.dumps(pdict))

    def makeSelect(self, inpdict, indx):
        """--selecttext_parameters '{"name":"outputimagetype", "label":"Select the output format for this plot image. If over 5000 rows of data, HTML breaks browsers, so your job will fail. Use png only if more than 5k rows.", "help":"Small and large png are not interactive but best for many (+10k) points. Stand-alone HTML includes 3MB of javascript. Short form HTML gets it the usual way so can be cut and paste into documents.", "type":"selecttext","CL":"image_type","override":"","value": [ "short_html" , "long_html" , "large_png" , "small_png" ], "texts": [ "Short HTML interactive format" ,  "Long HTML for stand-alone viewing where network access to libraries is not available." ,  "Large (1920x1200) png image - not interactive so hover column ignored" ,  "small (1024x768) png image - not interactive so hover column ignored"  ] }
        "{precursor,mature}" is a ppattern
        """
        print('sel indx',indx, self.testParamList)
        pdict = {}
        if indx > len(self.testParamList[0]):
            print('Infile parameter', indx, 'beyond length of parsed test parameters', self.testParamList,'so cannot test')
            self.canTest = False
            pval = "missing"
        else:
            pval = self.testParamList[0][indx]
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        ppattern = inpdict[pname]["pattern"]
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})  # remove {}
        texts = ppattern.split(",")
        ptype = inpdict[pname]["type"]
        pdict["type"] = "selecttext"
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["help"] = ""
        pdict["override"] = ""
        pdict["label"] = plabel
        pdict["texts"] = texts # should be comma separated values...
        pdict["value"] = texts
        self.tfcl.append("--selecttext_parameters")
        self.tfcl.append(json.dumps(pdict))

    def makeMeta(self):
        """
        --tool_name and so on from yaml
        """
        self.tfcl.append("--tool_name")
        self.tfcl.append(self.tool_name)
        self.tfcl.append("--user_email")
        self.tfcl.append("toolfactory@galaxy.org")
        # self.tfcl.append("--citations %s") TODO fix toolfactory citation handling - currently ignored :(
        nft = self.nfyaml["tools"][0]
        t = nft[list(nft.keys())[0]]
        helptext = ["%s: %s\n" % (x, t[x]) for x in t.keys()]
        helpf, self.helpPath = tempfile.mkstemp(
            suffix=".help", prefix="nftoolmaker", dir=None, text=True
        )
        with open(self.helpPath, "w") as f:
            f.write("\n".join(helptext))
            f.write("\n")
        self.tfcl.append("--help_text")
        self.tfcl.append(self.helpPath)
        self.tfcl.append("--tool_desc")
        self.tfcl.append(t["description"].replace('\n',' '))
        self.tfcl.append("--tool_version")
        self.tfcl.append("0.01")
        self.tfcl.append("--edit_additional_parameters")

    def makePackages(self, cs):
        """
        "conda-forge::r-ampir=1.1.0"
        or
        container "docker.io/nfcore/cellrangermkfastq:7.1.0"
        """
        if "::" in cs:
            c = cs.replace('"', "").split("::")[1].strip()
            req = [c]
            if self.scriptExe:
                self.tfcl.append("--sysexe")
                self.tfcl.append(self.scriptExe.strip())
            creq = ",".join(req)
            self.tfcl.append("--packages")
            self.tfcl.append(creq)
        else:
            if cs[0].strip().lower() == "container":
                self.tfcl.append("--container")
                self.tfcl.append(cs.split[1])
            else:
                print('@@@@@ Cannot parse requirements ',cs, 'into container or Conda packages for ', self.tool_name)

    def makeScript(self, ss):
        """
        script is delimited by triple "
        need to do some serious skullduggery <- does not work well so substitute for = in Rscript
        to convert all the ${prefix}.xxx into something more helpful - like real output names
        Only clue is from the yaml - where pattern gives the extension: "*.{faa}" or "*.tsv'
        so use that extension to change the script - substitute any ${prefix}.foo with $inputfoo

        TODO: substitute right parameter names

        oh dear. gzip isn't in the container is it? Let's just remove | gzip -c > every time we see it
        script:
        template 'affy_justrma.R'


        """
        sexe = None
        if 'template' in ss:
            templatedir = os.path.join(self.modroot, 'templates')
            tlist = os.listdir(templatedir)
            tfile = os.path.join(templatedir, tlist[0])
            try:
                s = open(tfile,'r').read()
            except:
                print('Cannot find template', tfile, 'in', tlist)
                sys.stderr.write('@@@@ cannot find a script in %s so cannot build' % self.tool_name)
        else:
            sss = ss.split('"""')
            if len(sss) < 2:
                sys.stderr.write('@@@@ cannot find a script in %s so cannot build' % self.tool_name)
                sys.exit(0)
            else:
                 s = sss[1]
        for pfmt in self.scriptPrefixSubs.keys():
            subme = self.scriptPrefixSubs[pfmt]
            s = s.replace('${prefix}.%s' % pfmt, subme)
        ss = s.split("\n")  # first shebang line maybe
        ss = [x.strip() for x in ss if x.strip() > ""]
        sfirst = ss[0]
        fiddled = []
        if sfirst.startswith("#!"):
            sexe = sfirst.split(" ")[1]
            if sexe == "Rscript":
                s = s.replace("<-", "=")
        else:
            fixargs = False
            sexe = 'bash' # assume is a bash script?
            for i, row in enumerate(ss): # replace bogus // with proper /
                row = row.strip()
                if "$args" in row: # this is such a kludge - who knows what the mad fuckers do with $args.
                    fiddled.append('### nf-core $args has been removed by nftoolmaker.py\n')
                    fixargs = True
                elif row.rstrip().endswith(r'\\'):
                    ss[i] = ss[i][:-1]
                elif 'gzip' in row:
                    row = row.replace('| gzip -c ','')
                    ss[i] = row
                    fiddled.append('### f| gzip -c removed by nftoolmaker.py\n')
                elif row.startswith('mv '): # comment out as will fail probably
                    ss[i] = '## %s commented out by nftoolmaker as it will probably break' % ss[i]
                elif row.startswith('gzip ') or row.startswith('gunzip'): # comment out as will fail probably
                    ss[i] = '## %s commented out by nftoolmaker as it will probably break' % ss[i]
                elif row.startswith('def ') : # hmmm - temp $ variable?
                    rows = row.split() # def foo = bar
                    fiddled.append("$%s = %s" % (rows[1], rows[2]))
                    ss[i] = '## %s replaced with definition by nftoolmaker.py' % row
            if fixargs:
                ss = [x for x in ss if not "$args" in x]
            s = '\n'.join(ss)
        s = s.replace('"${task.process}"', '"${task_process}"')
        s = ''.join(fiddled) + s
        sfile, self.scriptPath = tempfile.mkstemp(prefix=self.tool_name)
        with open(self.scriptPath, 'w') as f:
            f.write(s)
            f.write("\n")
        self.tfcl.append("--script_path")
        self.tfcl.append(self.scriptPath)
        return sexe

    def getsection(self, flag):
        insect = False
        sect = []
        for x in self.nftext:
            if x.lstrip().startswith(flag):
                insect = True
            else:
                if insect:
                    if x.strip().endswith("}"):
                        insect = False
                    else:
                        if x.startswith('description:'):
                            x = x.replace('\n',' ')
                        sect.append(x.strip())
        return "\n".join(sect)

    def getlinestart(self, flag):
        lstart = [x.lstrip() for x in self.nftext if x.lstrip().startswith(flag)]
        return lstart

if __name__ == "__main__":

    def prepargs(clist):
        anotherparser = argparse.ArgumentParser()
        a = anotherparser.add_argument
        a("--nftest", action="store_true", default=False)
        a("--script_path", default=None)
        a("--sysexe", default=None)
        a("--packages", default=None)
        a("--tool_name", default="newtool")
        a("--input_files", default=[], action="append")
        a("--output_files", default=[], action="append")
        a("--user_email", default="Unknown")
        a("--bad_user", default=None)
        a("--help_text", default=None)
        a("--tool_desc", default=None)
        a("--toolfactory_dir", default=None)
        a("--tool_version", default="0.01")
        a("--citations", default=None)
        a("--cl_suffix", default=None)
        a("--cl_prefix", default=None)
        a("--cl_override", default=None)
        a("--test_override", default=None)
        a("--additional_parameters", action="append", default=[])
        a("--selecttext_parameters", action="append", default=[])
        a("--selectflag_parameters", action="append", default=[])
        a("--edit_additional_parameters", action="store_true", default=False)
        a("--parampass", default="positional")
        a("--tfcollection", default="toolgen")
        a("--galaxy_root", default="./nfmod_tools")
        a("--collection", action="append", default=[])
        a("--include_tests", default=False, action="store_true")
        a("--install_flag", action="store_true", default=False)
        a("--admin_only", default=True, action="store_true")
        a("--tested_tool_out", default=None)
        a("--tool_conf_path", default="config/tool_conf.xml")  # relative to $__root_dir__
        a("--container", default=None,required=False)
        a("--xtra_files",
            default=[],
            action="append",
        )  # history data items to add to the tool base directory
        args = anotherparser.parse_args(clist)
        return args


    parser = argparse.ArgumentParser()
    a = parser.add_argument
    a("--nftest", action="store_true", default=False)
    a("--nftext", required=True)
    a("--nfyml", required=True)
    a("--collpath", default="toolgen")
    a("--toolfactory_dir", required=True, help="Path to the toolfactory directory on the local Galaxy - needed for utility scripts")
    a("--galaxy_root", required=True, help="Path to local Galaxy to run planemo tests")
    nfargs = parser.parse_args()
    nft = open(nfargs.nftext, "r").readlines()
    nfy = open(nfargs.nfyml, "r")
    nfym = yaml.safe_load(nfy)
    nfmod = ParseNFMod(nft, nfym, nfargs)
    if nfmod.status:
        print('#### got status', nfmod.status, 'not building')
        sys.exit(1)
    print('@@@@@@nftoolmaker building', nfmod.tool_name)
    collpath = nfargs.collpath
    cl = nfmod.tfcl
    jcl = json.dumps(' '.join(cl))
    with open(os.path.join('tfcl', 'ToolFactoryCL_%s.txt' % nfmod.tool_name), 'w') as fout:
        fout.write(jcl)
    args = prepargs(cl)
    assert (
        args.tool_name
    ), "## This nf-core module ToolFactory cannot build a tool without a tool name. Please supply one."
    logfilename = os.path.join('tfcl', "nfmodToolFactory_make_%s_log.txt" % args.tool_name)
    if not os.path.exists(collpath):
        os.makedirs(collpath, exist_ok=True)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfilename, mode="w")
    fformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(fformatter)
    logger.addHandler(fh)
    nfmod.tf = Tool_Factory(args)
    nfmod.tf.makeTool()
    nfmod.toold = nfmod.tf.toold
    #tf.writeTFyml()
    if nfargs.nftest:
        nfmod.tf.writeShedyml()
        res = nfmod.tf.update_toolconf()
        if res:
            logger.error("###### update toolconf failed - is the galaxy server needed for tests available?")
            nfmod.failtool(nfmod.tf.toold,"failinstall")
        else:
            if nfmod.tf.condaenv and len(nfmod.tf.condaenv) > 0:
                iret = nfmod.tf.install_deps()
                if iret:
                    logger.error("Toolfactory unable to installed deps - failed to build")
                    nfmod.failtool(nfmod.tf.toold, 'faildeps')
                else:
                    testret = nfmod.tf.planemo_local_test()
                    logger.debug("Toolfactory finished test")
                    if int(testret) > 0:
                        logger.error("ToolFactory tool build and test failed. :(")
                        logger.info(
                            "This is usually because the supplied script or dependency did not run correctly with the test inputs and parameter settings"
                        )
                        logger.info("when tested with galaxy_tool_test.  Error code:%d." % int(testret))
                        logger.info(
                            "The 'i' (information) option shows how the ToolFactory was called, stderr and stdout, and what the command line was."
                        )
                        logger.info(
                            "Expand (click on) any of the broken (red) history output titles to see that 'i' button and click it"
                        )
                        logger.info(
                            "Make sure it is the same as your working test command line and double check that data files are coming from and going to where they should"
                        )
                        logger.info(
                            "In the output collection, the tool xml <command> element must be the equivalent of your working command line for the test to work"
                        )
                        nfmod.failtool(nfmod.tf.toold,"failtest")
                        #tf.makeToolTar(1)
                    else:
                        self.tf.makeToolTar()
                        nfmod.failtool(nfmod.tf.toold, "whitelist")
    logging.shutdown()

# nftoolmaker.py
# ross lazarus
# august 2023
# exploring nf-core modules as potential Galaxy tools
# halted: too much work - needs the DSL to be parsed for the script templating.

import argparse
import json
import os
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

from bioblend import galaxy
from bioblend import ConnectionError

import galaxyxml.tool as gxt
import galaxyxml.tool.parameters as gxtp

import lxml.etree as ET

from toolfactoryclass import Tool_Factory

logger = logging.getLogger(__name__)
"""

"""
FILTERCHARS = "[]{}'"


class ParseNFMod:
    """
    failed attmpt to build a parser and Galaxy tool xml generator for nf-core module scripts and metadata.
    Harder than is worth. Easy to deal with templating the script by writing it and then running it at run time.
    Problem is that there are things in the DDL preceding the script and they need to be introspected
    to set the templated variables. I think I give up
    Tackling that - need to substitute our output name for the right ${prefix}.ext so use the extension Luke
    """

    def __init__(self, nft, nfy, args):
        self.chainedtestout = 'chainedtests.xls'
        f = open(self.chainedtestout,'w')
        f.close()
        self.testURLprefix = "https://raw.githubusercontent.com/nf-core/test-datasets/"
        self.tool_name = nfy["name"].replace("'",'').lower().strip()
        self.tool_dir = os.path.join(args.galaxy_root,'local_tools', self.tool_name)
        self.cl_coda = ["--tested_tool_out", args.toolgz, "--galaxy_root", args.galaxy_root, "--toolfactory_dir", args.toolfactory_dir, "--tfcollection", args.collpath]
        self.tooltest_dir = os.path.join(self.tool_dir, 'test-data') # for test input files to go
        os.makedirs(self.tool_dir, exist_ok=True)
        os.makedirs(self.tooltest_dir, exist_ok=True)
        self.scriptPrefixSubs = {}
        self.nfTests = [] # will ignore multiples but collect all
        self.nftext = nft
        self.nfyaml = nfy
        self.args = args
        self.localTestFile =  "nfgenomicstestdata.txt"
        self.setTestFiles()
        self.tfcl = ["--parampass", "embednfmod"]
        self.inparamnames = []
        self.outparamnames = []
        for indx, inpdict in enumerate(nfy["input"]): # need these for tests
            # the test names can be different. Go figure.
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]["type"]
            if ptype != "map":
                self.inparamnames.append(pname)
        self.inparamcount = len(self.inparamnames) # needed to select a test using them all - bugger anything else - too hard to match up names
        self.getTestInfo()
        self.usetest = self.nfTests[0]
        for i, t in enumerate(self.nfTests): # self.nfTests.append([tname, tparamnames, tparamvalues])
            if len(t[1]) == self.inparamcount:
                self.usetest = t
                break
        self.makeMeta()
        stub = self.getsection("stub:")  # not all have these - no idea what they're for
        indx = 0
        for indx, inpdict in enumerate(nfy["input"]):
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]["type"]
            if ptype == "map":
                print("Ignoring map specified as input %s" % str(inpdict))
            elif ptype == "file":
                (tname, tparamnames, tparamvalues) = self.usetest
                print('############ tests=', self.usetest, 'pname',pname, 'i', indx, 'inpdict', inpdict, 'inparamnames', self.inparamnames)
                realindex =  self.inparamnames.index(pname)
                localfile = tparamvalues[realindex] # we hope...
                self.makeInfile(inpdict,indx, localfile)
                indx += 1
            elif ptype == "string":
                self.makeString(inpdict, indx)
                indx += 1
            elif ptype == "val":
                self.makeFlag(inpdict, indx)
                indx += 1
            elif ptype in ["number", "integer"]:
                self.makeNum(inpdict, indx)
                indx += 1
            else:
                print("### unknown input type encountered in %s" % str(inpdict))
        for inpdict in nfy["output"]:
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]["type"]
            if ptype == "file":
                tfdict = self.makeOutfile(inpdict)
            elif ptype == "map":
                print("Ignoring map specified as output %s" % str(inpdict))
            else:
                print("### unknown output type encountered in %s" % str(inpdict))
        self.scriptExe = self.makeScript(self.getsection("script:"))
        self.makePackages(self.getlinestart("conda"))
        self.tfcl += self.cl_coda
        self.tfcl = [x for x in self.tfcl if x.strip() > ""]




    def setTestFiles(self):
        td = open(self.localTestFile, "r").readlines()
        td = [x.strip() for x in td]
        td = [
            "/".join(x.strip().split("/")[1:]) for x in td
        ]  # remove bogus "branches/"
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


    def nfParseTests(self, nftesttext):
        """
        extract test parameters from the test nf text
    shlex.split(shite)

    ['#!/usr/bin/env', 'nextflow', 'nextflow.enable.dsl', '=', '2', 'include', '{', 'SURVIVOR_FILTER', 'as', 'SURVIVOR_FILTER_NO_BED}', 'from', '../../../../../modules/nf-core/survivor/filter/main.nf', 'include', '{', 'SURVIVOR_FILTER', 'as', 'SURVIVOR_FILTER_BED}', 'from', '../../../../../modules/nf-core/survivor/filter/main.nf', 'workflow', 'test_survivor_filter_no_bed', '{', 'input_no_bed', '=', '[', '[', 'id:test],', '//', 'meta', 'map', 'file(params.test_data[homo_sapiens][illumina][test_genome_vcf],', 'checkIfExists:', 'true),', '[]', ']', 'SURVIVOR_FILTER_NO_BED', '(', 'input_no_bed,', '51,', '10001,', '0.01,', '10', ')', '}', 'workflow', 'test_survivor_filter', '{', 'input_bed', '=', '[', '[', 'id:test],', '//', 'meta', 'map', 'file(params.test_data[homo_sapiens][illumina][test_genome_vcf],', 'checkIfExists:', 'true),', 'file(params.test_data[homo_sapiens][genome][genome_bed],', 'checkIfExists:', 'true)', ']', 'SURVIVOR_FILTER_BED', '(', 'input_bed,', '51,', '10001,', '0.01,', '10', ')', '}']

    includes have an alternative form - ['include', '{', 'AMPIR', '}', 'from']
['#!/usr/bin/env', 'nextflow', 'nextflow.enable.dsl', '=', '2', 'include', '{', 'AMPIR', '}', 'from', '../../../../modules/nf-core/ampir/main.nf', 'workflow', 'test_ampir', '{', 'fasta', '=', '[', '[', 'id:test,', 'single_end:false', '],', '//', 'meta', 'map', 'file(params.test_data[candidatus_portiera_aleyrodidarum][genome][proteome_fasta],', 'checkIfExists:', 'true),', ']', 'model', '=', 'precursor', 'min_length', '=', '10', 'min_probability', '=', '0.7', 'AMPIR', '(', 'fasta,', 'model,', 'min_length,', 'min_probability', ')', '}']


    keywords - cannot assume linestart.
    "include",
    "workflow"
    modname.uppercase()

    includes contain the workflow test names
    workflow { to } has the test file and test name to match up
    Inside the workflow the workflow name signals a section with parameter names to use in order inside parentheses.

    TODO make sure localpath is test-data and matches the test parameter name

        """
        def getTestdataPath(indx, w):
            tparam = w[indx]
            while not w[indx].startswith('file(') and not w[indx] in ["}", "]"]:
                 indx += 1
            #  file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true),
            if w[indx].startswith('file(param'):
                testfpath = (
                    w[indx].split("[", 1)[1]
                    .split(",")[0]
                    .replace("][", "/")
                    .replace("'", "")
                )  # 'candidatus_portiera_aleyrodidarum/genome/proteome_fasta'
                tfilename = testfpath.split('/')[-1].replace('_','.')
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
                    sys.exit(3)
                foundpath = self.testURLprefix + foundpaths[0]
            else: #'file(https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz,'
                foundpath = w[indx].replace('file(','').replace(',','').replace(')','')
            return (indx, foundpath)

        def parseATest(w, testNames):
            """
            split into bits - test file, test name, test parameter values for each test

            if comma separators between the start and end ], split and give all the same name - it has no meaning as everything's positional here

             input = [
        [ id:'test', single_end:false ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
        false,
        false,
        false
    ]

     otherwise perhaps build the list by appending from individual =

workflow test_hmmer_eslreformat_afa {

    input = [
        [ id:'test' ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz')      // Change to params.test_data syntax after the data is included in ./tests/config/test_data.config
    ]

    hmm   = file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz')

    HMMER_HMMALIGN ( input, hmm )

    HMMER_ESLREFORMAT_AFA ( HMMER_HMMALIGN.out.sthlm )
}


            """
            tname = w[0]
            tparamvalues = [] # indexed by test param name k
            indx = 0
            lw = len(w)
            while indx < lw:
                if w[indx] in testNames: # is a test command line at end
                    indx += 2
                    tparamnames = []
                    while not w[indx] == ")" and not w[indx] == "}":
                        tparamnames.append(w[indx].replace(',','')) # shlex...
                        indx += 1
                elif indx < (lw -1) and w[indx+1] == "=": # start of a test parameter
                    pname = w[indx].replace(',','') # shlex...
                    indx += 1
                    if w[indx+1] == "[": # mapping start - often a single file parameter but could be a simple comma separated list
                        mess = []
                        while indx < lw and w[indx] != "]": # brittle - last is alone whereas mapping ends are usually "]," in shlex
                            mess.append(w[indx]
                            indx += 1

                        (indx, v) = getTestdataPath(indx, w)
                        indx += 1
                    else:
                        v = w[indx+1].strip() # simples
                        if v.startswith('file('):
                            v = v.replace('file(','').replace(')','')
                        indx += 2
                        tparamvalues.append(v)
                else:
                    indx += 1
            return (tname, tparamnames, tparamvalues)

        kw = ["include", "workflow"]
        nfshlex = shlex.split(nftesttext)
        testNames = []
        nfwf = []
        ne = len(nfshlex)
        indx = 0
        while indx < ne:
            e = nfshlex[indx]
            if e == "workflow": # all to }
                awf = []
                indx += 1
                while nfshlex[indx] != "}":
                    awf.append(nfshlex[indx])
                    indx += 1
                nfwf.append(awf)
            elif e == "include":
                if nfshlex[indx+3] == '}':  # includes have an alternative form - ['include', '{', 'AMPIR', '}', 'from']
                    aninc = nfshlex[indx + 2]
                    indx += 4
                else:
                    aninc = nfshlex[indx+4].replace('}', '') # shlex does this
                    indx += 4
                testNames.append(aninc)
                if not aninc.startswith(self.tool_name.upper()):
                    print(self.tool_name, 'has a chained test from', aninc)
                    s = "%s\t%s\n" % (self.tool_name, aninc.lower())
                    with open(self.chainedtestout, 'a') as f:
                        f.write(s)
                    sys.exit(9)
            else:
                indx += 1
        for w in nfwf:
            (tname, tparamnames, tparamvalues) = parseATest(w,testNames)
        self.nfTests.append([tname, tparamnames, tparamvalues])

    def getTestInfo(self):
        """ read tests and parse
        """
        self.setTestFiles()
        if '_' in self.tool_name: # ridiculous hack for multi tool modules
            submod = self.tool_name.replace('_','/') # punt
            testything = "tests/modules/nf-core/%s/main.nf" % submod
        else:
            testything = "tests/modules/nf-core/%s/main.nf" % self.tool_name
        if os.path.exists(testything):
            nftesttext = open(testything, "r").read()
            self.nfParseTests(nftesttext)
            # produces self.nftests - dict  {"tname" : tname, "tparamnames":tparamnames, "tparamvalues":tparamvalues}
        else:
            nftest = None
            print(
                "#### bad news - no test data because testything",
                testything,
                "not found",
            )

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
            "hmm.gz": "hmm3", "hm.gz": "hmm3", }
        fastaspawn = ['fna.gz','faa.gz','fasta.gz','fa.gz', 'faa', 'fa', ]
        fixedfmt = []
        for f in pfmt.split(','):
            f = f.strip()
            if f in fastaspawn:
                if not 'fasta' in fixedfmt:
                    fixedfmt.append('fasta')
            elif swaps.get(f, None):
                if not f in fixedfmt:
                    fixedfmt.append(swaps[f])
            else:
                print('info: non-substituted format',f,'encountered in the input ppattern', pfmt)
                fixedfmt.append(f)
        return ','.join(fixedfmt)

    def saveTestdata(self, pname, testDataURL):
        """
        may need to be ungzipped and in test folder
        """
        localpath = os.path.abspath(os.path.join(self.tooltest_dir, "%s_sample" % pname))
        if not os.path.exists(localpath):
            cl = ["wget", "-O", localpath, testDataURL]
            if testDataURL.endswith('.gz'): # major kludge as usual...
                gzlocalpath = "%s.gz" % localpath
                cl = ["wget", "-q", "-O", gzlocalpath, testDataURL, "&&", "rm", "-f", localpath, "&&", "gunzip", gzlocalpath]
            p = subprocess.run(' '.join(cl), shell = True)
            if p.returncode:
                print("Got", p.returncode, "from executing", " ".join(cl))
                sys.exit(3)
        else:
            print('Not re-downloading', localpath)

    def makeFlag(self, inpdict, indx):
        """
        boolean command line flag
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        [tname, tparamnames, tparamvalues] = self.nfTests[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        ptype = inpdict[pname]["type"]
        if ptype == "val":
            pdict["type"] = "clflag"
        else:
            print('Unexpected type (not "val") encountered in makeFlag', ptype)
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["value"] = tparamvalues[indx].replace('"', "")
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["repeat"] = "0"
        self.tfcl.append("--additional_parameters")
        self.tfcl.append(json.dumps(pdict))

    def makeInfile(self, inpdict, indx, testURL):
        """
        {'faa': {'type': 'file', 'description': 'FASTA file containing amino acid sequences', 'pattern': '*.{faa,fasta}'}}

        need --input_files '{"name": "/home/ross/rossgit/galaxytf/database/objects/d/d/4/dataset_dd49e13c-bd4d-4f8b-8eaa-863483d021f6.dat", "CL": "input_tab", "format": "tabular", "label": "Tabular input file to plot", "help": "If 5000+ rows, html output will fail, but png will work.", "required": "required"}'
        Need to copy testfile from localpath to the target tool test-dir
        """
        pdict = {}
        pid = list(inpdict.keys())[0]
        ppath = pid
        [tname, tparamnames, tparamvalues] = self.usetest
        pindex = self.inparamnames.index(pid)
        tdURL = tparamvalues[pindex]
        if not ppath:
            ppath = pid
        plabel = inpdict[pid]["description"].replace('\n',' ')
        ppattern = inpdict[pid]["pattern"]
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        if ppattern.startswith('*'): # why? "*.{fna.gz,faa.gz,fasta.gz,fa.gz}"
            ppattern = ppattern[2:]
        fps = self.fixParamFormat(ppattern) # kludge so Galaxy doesn't get confused.
        #self.scriptPrefixSubs[pfmt] = "$%s" % pname # will be substituted in configfile
        pdict["CL"] = pid
        pdict["name"] = pid
        pdict["format"] = fps
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["required"] = "0"
        self.tfcl.append("--input_files")
        self.tfcl.append(json.dumps(pdict))
        self.saveTestdata(pid, tdURL)

    def makeOutfile(self, inpdict):
        """
        need  --output_files '{"name": "htmlout", "format": "html", "CL": "", "test": "sim_size:5000", "label": "Plotlytabular $title on $input_tab.element_identifier" , "when": [ "when input=outputimagetype value=small_png format=png" , "when input=outputimagetype value=large_png format=png" ] }'

        TODO: make a format lookup table or otherwise map all the dozens of extensions
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        ppattern = inpdict[pname]["pattern"]
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
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        [tname, tparamnames, tparamvalues] = self.nfTests[0]
        if ppattern.startswith("{") and ppattern.endswith("}"):
            # is a select comma separated list
            self.makeSelect(inpdict)
        else:
            pdict["type"] = "text"
            pdict["CL"] = pname
            pdict["name"] = pname
            pdict["value"] = tparamvalues[indx]
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
        pname = list(inpdict.keys())[0]
        [tname, tparamnames, tparamvalues] = self.nfTests[0]
        plabel = inpdict[pname]["description"].replace('\n',' ')
        ptype = inpdict[pname]["type"]
        if ptype == "number":
            pdict["type"] = "float"
        else:
            pdict["type"] = "integer"
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["value"] = tparamvalues[indx].replace('"', "")
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["repeat"] = "0"
        self.tfcl.append("--additional_parameters")
        self.tfcl.append(json.dumps(pdict))

    def makeSelect(self, inpdict):
        """--selecttext_parameters '{"name":"outputimagetype", "label":"Select the output format for this plot image. If over 5000 rows of data, HTML breaks browsers, so your job will fail. Use png only if more than 5k rows.", "help":"Small and large png are not interactive but best for many (+10k) points. Stand-alone HTML includes 3MB of javascript. Short form HTML gets it the usual way so can be cut and paste into documents.", "type":"selecttext","CL":"image_type","override":"","value": [ "short_html" , "long_html" , "large_png" , "small_png" ], "texts": [ "Short HTML interactive format" ,  "Long HTML for stand-alone viewing where network access to libraries is not available." ,  "Large (1920x1200) png image - not interactive so hover column ignored" ,  "small (1024x768) png image - not interactive so hover column ignored"  ] }
        "{precursor,mature}" is a ppattern
        """
        pdict = {}
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
        pdict["texts"] = texts  # should be comma separated values...
        pdict["value"] = pdict["texts"]
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
        """
        c = cs[0].replace('"', "").split("::")[1].strip()
        req = [c]
        if self.scriptExe:
            self.tfcl.append("--sysexe")
            self.tfcl.append(self.scriptExe.strip())
        creq = ",".join(req)
        self.tfcl.append("--packages")
        self.tfcl.append(creq)

    def makeScript(self, scrip):
        """
        script is delimited by triple "
        need to do some serious skullduggery <- does not work well so substitute for = in Rscript
        to convert all the ${prefix}.xxx into something more helpful - like real output names
        Only clue is from the yaml - where pattern gives the extension: "*.{faa}" or "*.tsv'
        so use that extension to change the script - substitute any ${prefix}.foo with $inputfoo

        TODO: substitute right parameter names

        oh dear. gzip isn't in the container is it? Let's just remove | gzip -c > every time we see it

        """
        sexe = None
        s = scrip.split('"""')[1]
        for pfmt in self.scriptPrefixSubs.keys():
            subme = self.scriptPrefixSubs[pfmt]
            s = s.replace('${prefix}.%s' % pfmt, subme)
        ss = s.split("\n")  # first shebang line maybe
        ss = [x.strip() for x in ss if x.strip() > ""]
        sfirst = ss[0]
        if sfirst.startswith("#!"):
            sexe = sfirst.split(" ")[1]
            if sexe == "Rscript":
                s = s.replace("<-", "=")
        else:
            fiddled = []
            fixargs = False
            sexe = 'bash' # assume is a bash script?
            for i, row in enumerate(ss): # replace bogus // with proper /
                if "$args" in row: # this is such a kludge - who knows what the mad fuckers do with $args.
                    fiddled.append('### full disclosure! nf-core $args has been removed by nftoolmaker.py\n')
                    fixargs = True
                elif row.rstrip().endswith(r'\\'):
                    ss[i] = ss[i][:-1]
                elif 'gzip' in row:
                    row = row.replace('| gzip -c ','')
                    ss[i] = row
                    fiddled.append('### full disclosure! | gzip -c removed by nftoolmaker.py\n')
            if fixargs:
                ss = [x for x in ss if not "$args" in x]
            s = '\n'.join(ss)
        s = s.replace('"${task.process}"', '"${task_process}"')
        s = ''.join(fiddled) + s
        scriptf, self.scriptPath = tempfile.mkstemp(
            suffix=".script", prefix="nftoolmaker", dir=None, text=True
        )
        with open(self.scriptPath, "w") as f:
            f.write(s)
            f.write("\n")
        self.tfcl.append("--script_path")
        self.tfcl.append(self.scriptPath)
        return sexe

    def getsection(self, flag):
        insect = False
        inquote = False
        sect = []
        for x in self.nftext:
            if x.lstrip().startswith(flag):
                insect = True
            else:
                if insect:
                    if x.strip() == '"""':
                        if inquote:
                            sect.append(x.strip())
                            inquote = False
                            insect = False
                        else:
                            inquote = True
                    if x.strip() == "":
                        if not inquote:
                            insect = False
                if insect:
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
        a("--galaxy_root", default="/galaxy-central")
        a("--collection", action="append", default=[])
        a("--include_tests", default=False, action="store_true")
        a("--install_flag", action="store_true", default=False)
        a("--admin_only", default=True, action="store_true")
        a("--tested_tool_out", default=None)
        a("--tool_conf_path", default="config/tool_conf.xml")  # relative to $__root_dir__
        a(
            "--xtra_files",
            default=[],
            action="append",
        )  # history data items to add to the tool base directory
        args = anotherparser.parse_args(clist)
        return args


    parser = argparse.ArgumentParser()
    a = parser.add_argument
    a("--nftext", required=True)
    a("--nfyml", required=True)
    a("--collpath", default="toolgen")
    a("--toolgz", required=True)
    a("--toolfactory_dir", required=True, help="Path to the toolfactory directory on the local Galaxy - needed for utility scripts")
    a("--galaxy_root", required=True, help="Path to local Galaxy to run planemo tests")
    nfargs = parser.parse_args()
    nft = open(nfargs.nftext, "r").readlines()
    for i,x in enumerate(nft): # remove bogus comment crap
        row = x.split() # need to find '//' on it's own as the start of a comment - dangerous
        if '//' in row:
            rend = row.index('//')
            fixedrow = row[:rend]
            nft[i] = ' '.join(fixedrow)
            print('####### truncated row from', nfargs.nftext, row, 'to', fixedrow)
    nfy = open(nfargs.nfyml, "r")
    nfym = yaml.safe_load(nfy)
    cl = ["touch", "local_tool_conf.xml"]
    subprocess.run(cl)
    nfmod = ParseNFMod(nft, nfym, nfargs)
    cl = nfmod.tfcl
    print("cl=", "\n".join(cl))
    args = prepargs(cl)
    assert (
        args.tool_name
    ), "## This nf-core module ToolFactory cannot build a tool without a tool name. Please supply one."
    logfilename = "nfmodToolFactory_make_%s_log.txt" % args.tool_name
    if not os.path.exists(nfargs.collpath):
        os.mkdir(nfargs.collpath)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfilename, mode="w")
    fformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(fformatter)
    logger.addHandler(fh)
    tf = Tool_Factory(args)
    tf.makeTool()
    tf.writeShedyml()
    tf.update_toolconf()
    time.sleep(5)
    if tf.condaenv and len(tf.condaenv) > 0:
        tf.install_deps()
        logger.debug("Toolfactory installed deps. Calling fast test")
    time.sleep(2)
    # testret = tf.fast_local_test()
    testret = tf.planemo_local_test()
    logger.debug("Toolfactory finished test")
    if int(testret) > 0:
        logger.error("ToolFactory tool build and test failed. :(")
        logger.info(
            "This is usually because the supplied script or dependency did not run correctly with the test inputs and parameter settings"
        )
        logger.info("when tested with galaxy_tool_test.  Error code:%d" % testret, ".")
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
        logging.shutdown()
        sys.exit(5)
    else:
        tf.makeToolTar(testret)
    logging.shutdown()

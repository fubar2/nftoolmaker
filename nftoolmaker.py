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
FILTERCHARS = "[]{}*.'"


class ParseNFMod:
    """
    failed attmpt to build a parser and Galaxy tool xml generator for nf-core module scripts and metadata.
    Harder than is worth. Easy to deal with templating the script by writing it and then running it at run time.
    Problem is that there are things in the DDL preceding the script and they need to be introspected
    to set the templated variables. I think I give up
    Tackling that - need to substitute our output name for the right ${prefix}.ext so use the extension Luke
    """

    def __init__(self, nft, nfy, args):
        self.scriptPrefixSubs = {}
        self.nftext = nft
        self.nfyaml = nfy
        self.args = args
        self.localTestDir = os.path.join(args.tool_dir, "nfmodtestfiles")
        self.localTestFile = os.path.join(args.tool_dir, "nfgenomicstestdata.txt")
        self.makeCLCoda()
        self.tfcl = ["--parampass", "embednfmod"]
        self.tool_name = nfy["name"]
        self.getTestInfo()
        self.makeMeta()
        stub = self.getsection("stub:")  # not all have these - no idea what they're for
        for i, inpdict in enumerate(nfy["input"]):
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]["type"]
            if ptype == "file":
                self.makeInfile(inpdict, i)
            elif ptype == "string":
                self.makeString(inpdict, i)
            elif ptype in ["number", "integer"]:
                self.makeNum(inpdict, i)
            elif ptype == "map":
                print("Ignoring map specified as input %s" % str(inpdict))
            else:
                print("### unknown input type encountered in %s" % str(inpdict))
        for inpdict in nfy["output"]:
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]["type"]
            if ptype == "file":
                tfdict = self.makeOutfile(inpdict, i)
            elif ptype == "map":
                print("Ignoring map specified as output %s" % str(inpdict))
            else:
                print("### unknown output type encountered in %s" % str(inpdict))
        self.scriptExe = self.makeScript(self.getsection("script:"))
        self.makePackages(self.getlinestart("conda"))
        self.tfcl += self.cl_coda
        self.tfcl = [x for x in self.tfcl if x.strip() > ""]

    def makeCLCoda(self):
        """need a json representation of the tail for the command line
        setting the --nftest flag prevents planemo test and install on the local toolfactory
        """
        coldict = {
            "name": args.collpath,
            "kind": "list",
            "discover": "__name_and_ext__",
            "label": "nfcore module spawn",
        }
        coll = json.dumps(coldict)
        clend = """--collection
%s
--tested_tool_out
%s
--tfcollection
%s
--galaxy_root
"$__root_dir__"
--tool_dir
%s
 """ % (
            coll,
            args.toolgz,
            args.collpath,
            args.tool_dir,
        )
        print("clend", clend)
        self.cl_coda = clend.split("\n")

    def getTestInfo(self):
        """
                Parse the test inputs in https://github.com/nf-core/modules/blob/master/tests/modules/nf-core/ampir/main.nf
                #!/usr/bin/env nextflow
        nextflow.enable.dsl = 2
        include { AMPIR } from '../../../../modules/nf-core/ampir/main.nf'
        workflow test_ampir {
            fasta = [ [ id:'test', single_end:false ], // meta map          file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true),
            ]
            model = "precursor"
            min_length = 10
        min_probability = "0.7"
            AMPIR ( fasta, model, min_length, min_probability )
        }

        now {'tool_name': 'ampir', 'fasta': ["[ [ id:'test', single_end:false ], // meta map", 'https://github.com/nf-core/test-datasets/blob/modules/data/genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/proteome.fasta'], 'model': ['"precursor"'], 'min_length': ['10'], 'min_probability': ['"0.7"']}

             This works!
             wget https://raw.githubusercontent.com/nf-core/test-datasets/updates_names/data/genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/proteome.fasta


        """
        testURLprefix = "https://raw.githubusercontent.com/nf-core/test-datasets/"
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
        if '_' in self.tool_name: # ridiculous hack for multi tool modules
            submod = self.tool_name.replace('_','/') # punt
            testything = "tests/modules/nf-core/%s/main.nf" % submod
        else:
            testything = "tests/modules/nf-core/%s/main.nf" % self.tool_name
        if os.path.exists(testything):
            nftest = open(testything, "r").readlines()
            nftest = [x.strip() for x in nftest]
        else:
            nftest = None
            print(
                "#### bad news - no test data because testything",
                testything,
                "not found",
            )
        foundtest = False
        testbits = []
        for row in nftest:
            if foundtest:
                testbits.append(row)
            if row.startswith(self.tool_name.upper()):
                # this row gives the parameter names in order
                # test input files may not use the internal ones stupidly
                self.testParamIds = row.replace(",", "").split(" ", 1)[1].split(" ")
                print('### testparamids=', self.testParamIds)
                foundtest = False
            if row.startswith("workflow test"):
                foundtest = True
        testthings = {"tool_name": self.tool_name}
        testpaths = {}
        insect = False
        k = None
        v = None
        testU = None
        for row in testbits:
            if row.strip().startswith("]"):
                insect = False  # ugh. let's pray for obsessive formatting stupid.
            if insect:
                if row.startswith(
                    "file("
                ):  #  file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true),
                    testfpath = (
                        row.split("[", 1)[1]
                        .split("],")[0]
                        .replace("']['", "/")
                        .replace("'", "")
                    )  # 'candidatus_portiera_aleyrodidarum/genome/proteome_fasta'
                    tfilename = testfpath.split('/')[-1].replace('_','.') # punt?
                    tstart = '/'.join(testfpath.split('/')[:-1])
                    testfpath = os.path.join(tstart, tfilename)
                    # 'candidatus_portiera_aleyrodidarum/genome/proteome.fasta'
                    localpath = testfpath.replace("/", "_")
                    localpath = os.path.join(self.localTestDir, localpath)
                    foundpaths = file_dict.get(tfilename, None)
                    print('### testfpath', testfpath, 'localpath =', localpath)
                    if len(foundpaths) == 0:
                        print(
                            "test specifier",
                            testfpath,
                            "not found in directory of the test repository. Please run the updater",
                        )
                        sys.exit(3)
                    testU = testURLprefix + foundpaths[0]
                    cl = ["wget", "-O", localpath, testU]
                    p = subprocess.run(cl)
                    if p.returncode:
                        print("Got", p.returncode, "from executing", " ".join(cl))
                        sys.exit(5)
                    testpaths[k] = localpath
                    testthings[k].append(localpath)
            if "=" in row:
                k = row.split("= ")[0].strip()
                v = row.split("= ")[1:]
                testthings[k] = v
            if "[" in row:
                insect = True
        self.testData = testthings
        self.testPaths = testpaths
        print("Test values found = ", testthings)

    def makeInfile(self, inpdict, i):
        """
        {'faa': {'type': 'file', 'description': 'FASTA file containing amino acid sequences', 'pattern': '*.{faa,fasta}'}}

        need --input_files '{"name": "/home/ross/rossgit/galaxytf/database/objects/d/d/4/dataset_dd49e13c-bd4d-4f8b-8eaa-863483d021f6.dat", "CL": "input_tab", "format": "tabular", "label": "Tabular input file to plot", "help": "If 5000+ rows, html output will fail, but png will work.", "required": "required"}'
        Need to add a cp to copy the named file to the template path
        """
        pdict = {}
        pid = list(inpdict.keys())[0]
        ppath = pid
        testid = self.testParamIds[i]
        ppath = self.testPaths.get(testid, None)
        if not ppath:
            ppath = pid
        plabel = inpdict[pid]["description"]
        ppattern = inpdict[pid]["pattern"]
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        if "fasta" in ppattern:
            ppattern = ppattern.replace("faa,", "")
        else:
            ppattern = ppattern.replace("faa", "fasta")
        print("ppattern", ppattern)
        pdict["CL"] = pid
        pdict["name"] = ppath
        pdict["format"] = ppattern
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["required"] = "0"
        self.tfcl.append("--input_files")
        self.tfcl.append(json.dumps(pdict))

    def makeOutfile(self, inpdict, i):
        """
        need  --output_files '{"name": "htmlout", "format": "html", "CL": "", "test": "sim_size:5000", "label": "Plotlytabular $title on $input_tab.element_identifier" , "when": [ "when input=outputimagetype value=small_png format=png" , "when input=outputimagetype value=large_png format=png" ] }'
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"]
        ppattern = inpdict[pname]["pattern"]
        if ppattern == "versions.yml":
            return  # ignore these artifacts
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        if len(ppattern.split(",")) > 0:
            pfmt = ppattern.split(",")[0]
        self.scriptPrefixSubs[pfmt] = "$%s" % pname # will be substituted in configfile
        pfmt = pfmt.replace('faa', 'fasta') # kludge so Galaxy doesn't get confused.
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["format"] = pfmt
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["test"] = "sim_size:1000"  # arbitrary hackery
        self.tfcl.append("--output_files")
        self.tfcl.append(json.dumps(pdict))

    def makeString(self, inpdict, i):
        """
        need something like --additional_parameters '{"name": "xcol", "value": "petal_length", "label": "x axis for plot", "help": "Select the input tabular column for the horizontal plot axis", "type": "datacolumn","CL": "xcol","override": "", "repeat": "0", "multiple": "", "dataref": "input_tab"}'
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"]
        ppattern = inpdict[pname]["pattern"]
        testid = self.testParamIds[i]
        print(self.testData[testid])
        if ppattern.startswith("{") and ppattern.endswith("}"):
            # is a select comma separated list
            self.makeSelect(inpdict, i)
        else:
            pdict["type"] = "text"
            pdict["CL"] = pname
            pdict["name"] = pname
            pdict["value"] = self.testData[testid][0]
            pdict["help"] = ""
            pdict["label"] = plabel
            pdict["repeat"] = "0"
            self.tfcl.append("--additional_parameters")
            self.tfcl.append(json.dumps(pdict))

    def makeNum(self, inpdict, i):
        """
        need something like --additional_parameters '{"name": "xcol", "value": "petal_length", "label": "x axis for plot", "help": "Select the input tabular column for the horizontal plot axis", "type": "datacolumn","CL": "xcol","override": "", "repeat": "0", "multiple": "", "dataref": "input_tab"}'
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        testid = self.testParamIds[i]
        print(self.testData[testid])
        plabel = inpdict[pname]["description"]
        ppattern = inpdict[pname]["pattern"]
        ptype = inpdict[pname]["type"]
        if ptype == "number":
            pdict["type"] = "float"
        else:
            pdict["type"] = "integer"
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["value"] = self.testData[testid][0].replace('"', "")
        pdict["help"] = ""
        pdict["label"] = plabel
        pdict["repeat"] = "0"
        self.tfcl.append("--additional_parameters")
        self.tfcl.append(json.dumps(pdict))

    def makeSelect(self, inpdict, i):
        """--selecttext_parameters '{"name":"outputimagetype", "label":"Select the output format for this plot image. If over 5000 rows of data, HTML breaks browsers, so your job will fail. Use png only if more than 5k rows.", "help":"Small and large png are not interactive but best for many (+10k) points. Stand-alone HTML includes 3MB of javascript. Short form HTML gets it the usual way so can be cut and paste into documents.", "type":"selecttext","CL":"image_type","override":"","value": [ "short_html" , "long_html" , "large_png" , "small_png" ], "texts": [ "Short HTML interactive format" ,  "Long HTML for stand-alone viewing where network access to libraries is not available." ,  "Large (1920x1200) png image - not interactive so hover column ignored" ,  "small (1024x768) png image - not interactive so hover column ignored"  ] }
        "{precursor,mature}" is a ppattern
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]["description"]
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
        self.tfcl.append("'%s'" % self.tool_name)
        self.tfcl.append("--user_email")
        self.tfcl.append("'toolfactory@galaxy.org'")
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
        self.tfcl.append("'%s'" % t["description"])
        self.tfcl.append("--tool_version")
        self.tfcl.append("'0.01'")
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
        """
        sexe = None
        s = scrip.split('"""')[1]
        s = s.replace('"${task.process}"', '"${task_process}"')
        # self.scriptPrefixSubs[pfmt] = pname
        for pfmt in self.scriptPrefixSubs.keys():
            subme = self.scriptPrefixSubs[pfmt]
            s = s.replace('${prefix}.%s' % pfmt, subme)
        ss = s.split("\n")  # first shebang line maybe
        ss = [x for x in ss if x.strip() > ""]
        sfirst = ss[0]
        if sfirst.startswith("#!"):
            sexe = sfirst.split(" ")[1].strip()
            if sexe == "Rscript":
                s = s.replace("<-", "=")
                ss = s.split('\n')
        print("### s=", ss)
        scriptf, self.scriptPath = tempfile.mkstemp(
            suffix=".script", prefix="nftoolmaker", dir=None, text=True
        )
        with open(self.scriptPath, "w") as f:
            f.write('\n'.join(ss))
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


def prepargs(clist):
    parser = argparse.ArgumentParser()
    a = parser.add_argument
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
    a("--tool_dir", default=None)
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
    args = parser.parse_args(clist)
    return args


parser = argparse.ArgumentParser()
a = parser.add_argument
a("--nftext", required=True)
a("--nfyml", required=True)
# tf collection name is always toolgen
a("--collpath", default="toolgen")
a("--toolgz", required=True)
a("--tool_dir", required=True)
args = parser.parse_args()
nft = open(args.nftext, "r").readlines()
nfy = open(args.nfyml, "r")
nfym = yaml.safe_load(nfy)
cl = ["touch", "local_tool_conf.xml"]
subprocess.run(cl)
nfmod = ParseNFMod(nft, nfym, args)
cl = nfmod.tfcl
print("cl=", "\n".join(cl))
args = prepargs(cl)
assert (
    args.tool_name
), "## This ToolFactory cannot build a tool without a tool name. Please supply one."
logfilename = os.path.join(
    args.tfcollection, "ToolFactory_make_%s_log.txt" % args.tool_name
)
if not os.path.exists(args.tfcollection):
    os.mkdir(args.tfcollection)
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

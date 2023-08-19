# nftoolmaker.py
# ross lazarus
# august 2023
# exploring nf-core modules as potential Galaxy tools
# halted: too much work - needs the DSL to be parsed for the script templating.

import argparse
import json
import os
import subprocess
import tempfile
import yaml

"""

"""
FILTERCHARS = "[]{}*.'"
coldict = {"name": "nfcoreout", "kind": "list", "discover": "__name_and_ext__", "label": "nfcore module spawn"}
coll = json.dumps(coldict)
clend = '''--collection
%s
--nftest
--tested_tool_out
'$untested_tool'
--galaxy_root
'$__root_dir__'
--tool_dir
'$__tool_directory__' ''' % coll
CLCODA = clend.split('\n')

class ParseNFMod:
    """
    failed attmpt to build a parser and Galaxy tool xml generator for nf-core module scripts and metadata.
    Harder than is worth. Easy to deal with templating the script by writing it and then running it at run time.
    Problem is that there are things in the DDL preceding the script and they need to be introspected
    to set the templated variables. I think I give up
    """

    def __init__(self, nft, nfy):
        self.nftext = nft
        self.nfyaml = nfy
        self.localTestDir = 'nfmodtestfiles'
        self.tfcl = ["--parampass", "embed"]
        self.tool_name = nfy["name"]
        self.findTestfiles()
        self.getTestInfo()
        self.scriptExe = self.makeScript(self.getsection("script:"))
        self.makePackages(self.getlinestart("conda"))
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

    def findTestfiles(self):
        """
        https://github.com/nf-core/test-datasets/blob/modules/data/genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/proteome.fasta and it cannot be
     inferred easily - need to use os.path.walk to find all the directories etc. Fugly since the entire data repository is ?6GB or so.
     for testing just stub a dict

     svn ls -R https://github.com/nf-core/test-datasets.git
     and
     git clone -b updates_names https://github.com/nf-core/test-datasets.git
     since updates_names seems to have a copy of the generic ones
     or perhaps
     git clone -b updates_names --depth 1 https://github.com/nf-core/test-datasets.git

        """
        self.testfileURLS = {"['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta']":'https://github.com/nf-core/test-datasets/blob/modules/data/genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/proteome.fasta'}


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


     the path needed is https://github.com/nf-core/test-datasets/blob/modules/data/genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome/proteome.fasta and it cannot be
     inferred easily - need to use os.path.walk to find all the directories etc. Fugly since the entire data repository is ?6GB or so.
        """
        testything = "tests/modules/nf-core/%s/main.nf" %  self.tool_name
        if os.path.exists(testything):
            nftest = open(testything, 'r').readlines()
            nftest = [x.strip() for x in nftest]
        else:
            nftest = None
            print('#### bad news - no test data because testything', testything, 'not found')
        foundtest = False
        testbits = []
        for row in nftest:
            if foundtest:
                testbits.append(row)
            if row.startswith(self.tool_name.upper()):
                # this row gives the parameter names in order
                # test input files may not use the internal ones stupidly
                self.testParamIds = row.replace(',','').split(' ', 1)[1].split(' ')
                foundtest = False
            if row.startswith('workflow test'):
                foundtest = True
        testthings = {"tool_name": self.tool_name}
        testpaths = {}
        insect = False
        k = None
        v = None
        testU = None
        for row in testbits:
            if row.strip().startswith(']'):
                insect = False # ugh. let's pray for obsessive formatting stupid.
            if insect:
                if row.startswith('file('):
                    testfpath = '['
                    testfpath += row.split("[", 1)[1].split(",")[0]
                    testU = self.testfileURLS.get(testfpath, None)
                    if testU:
                        kpath = testfpath.translate({ord(i): "_" for i in "[']"})
                        kpath = kpath.replace('__','_')
                        localpath = os.path.join(self.localTestDir, kpath)
                        if not kpath in os.listdir(self.localTestDir):
                            cl = ['wget', "-O", localpath,  testU]
                            subprocess.run(cl)
                        testpaths[kpath] = localpath
                        testthings[k].append(localpath)
                    else:
                        print('test specifier', testfpath, 'not found in database of test file URLs. Please run the updater')
            if '=' in row:
                k = row.split(' = ')[0]
                v = row.split(' = ')[1:]
                testthings[k] = v
            if '[' in row:
                insect = True
        self.testData = testthings
        self.testPaths = testpaths
        print('Test values found = ', testthings)

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
        print(self.testData[testid])
        if self.testData.get(testid, None):
            ppath = [x for x in self.testData[testid] if x.startswith(self.localTestDir)]
            if len(ppath) > 0:
                ppath = ppath[0]
        plabel = inpdict[pid]["description"]
        ppattern = inpdict[pid]["pattern"]
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        ppattern = ppattern.replace('faa','fasta.gz')
        print('ppattern', ppattern)
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
        ppattern = ppattern.replace('faa','fasta')
        pdict["CL"] = pname
        pdict["name"] = pname
        pdict["format"] = ppattern
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
        pdict["value"] = self.testData[testid][0].replace('"','')
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
        t = self.nfyaml["tools"][0]
        if len(t) > 1:
            print(
                "## challenge - meta.yml has a tools entry %s describing more than one tool - not sure if this will end well - using the first only"
                % t
            )
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
        self.tfcl.append(t[self.tool_name]["description"])
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
            if self.scriptExe == "Rscript":
                req.append('r-base')
            else:
                req.append(self.scriptExe)
            self.tfcl.append("--sysexe")
            self.tfcl.append(self.scriptExe.strip())
        creq = ",".join(req)
        self.tfcl.append("--packages")
        self.tfcl.append(creq)

    def makeScript(self, scrip):
        """
        script is delimited by triple "
        """
        sexe = None
        scriptf, self.scriptPath = tempfile.mkstemp(
            suffix=".script", prefix="nftoolmaker", dir=None, text=True
        )
        s = scrip.split('"""')[1]
        s = s.replace('"${task.process}"', '"${task_process}"')
        with open(self.scriptPath, "w") as f:
            f.write(s)
            f.write("\n")
        self.tfcl.append("--script_path")
        self.tfcl.append(self.scriptPath)
        ss = s.split("\n")  # first shebang line maybe
        ss = [x for x in ss if x.strip() > ""]
        sfirst = ss[0]
        if sfirst.startswith("#!"):
            sexe = sfirst.split(" ")[1].strip()
        print("### s=", s.split("\n"))
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
                    sect.append(x.strip())
        return "\n".join(sect)

    def getlinestart(self, flag):
        lstart = [x.lstrip() for x in self.nftext if x.lstrip().startswith(flag)]
        return lstart


parser = argparse.ArgumentParser()
a = parser.add_argument
a("--nftext", required=True)
a("--nfyml", required=True)
args = parser.parse_args()
nft = open(args.nftext, "r").readlines()
nfy = open(args.nfyml, "r")
nfym = yaml.safe_load(nfy)
nfmod = ParseNFMod(nft, nfym)
cl = nfmod.tfcl
cl.insert(0, "toolfactory.py")
cl.insert(0, "/home/ross/rossgit/galaxytf/.venv/bin/python")
cl += CLCODA
print("cl=", "\n".join(cl))
rc = subprocess.run(cl)

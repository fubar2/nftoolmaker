# see https://github.com/fubar2/toolfactory
#
# copyright ross lazarus (ross stop lazarus at gmail stop com) May 2012
#
# all rights reserved
# Licensed under the LGPL
# suggestions for improvement and bug fixes welcome at
# https://github.com/fubar2/toolfactory
#
# February 2023: Refactored to use galaxy-tool-test script in galaxyutil
# planemo not needed if tool is already installed.
# sqlite does not seem to work - switch to postgresql in the installation script
#
# march 2022: Refactored into two tools - generate and test/install
# as part of GTN tutorial development and biocontainer adoption
# The tester runs planemo on a non-tested archive, creates the test outputs
# and returns a new proper tool with test.


import argparse
import copy
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

from bioblend import galaxy
from bioblend import ConnectionError

import galaxyxml.tool as gxt
import galaxyxml.tool.parameters as gxtp

import lxml.etree as ET

import yaml

GALAXY_URL = "http://localhost:8080"
myversion = "V3.0 February 2023"
verbose = True
debug = True
toolFactoryURL = "https://github.com/fubar2/galaxy_tf_overlay"
REP_DIR = "toolgen"
logger = logging.getLogger(__name__)

def timenow():
    """return current time as a string"""
    return time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(time.time()))


cheetah_escape_table = {"$": "\\$", "#": "\\#"}


def cheetah_escape(text):
    """Produce entities within text."""
    return "".join([cheetah_escape_table.get(c, c) for c in text])


def parse_citations(citations_text):
    """"""
    citations = [c for c in citations_text.split("**ENTRY**") if c.strip()]
    citation_tuples = []
    for citation in citations:
        if citation.startswith("doi"):
            citation_tuples.append(("doi", citation[len("doi") :].strip()))
        else:
            citation_tuples.append(("bibtex", citation[len("bibtex") :].strip()))
    return citation_tuples


class Tool_Factory:
    """Wrapper for an arbitrary script
    uses galaxyxml

    """

    def __init__(self, args=None):  # noqa
        """
        prepare command line cl for running the tool here
        and prepare elements needed for galaxyxml tool generation
        """
        assert args.parampass in [
            "0",
            "argparse",
            "positional",
            ], 'args.parampass must be "0","positional" or "argparse"'
        self.script_in_help = False # IUC recommendation
        self.nftest = True
        self.tool_name = re.sub("[^a-zA-Z0-9_]+", "", args.tool_name)
        self.tool_id = self.tool_name
        if self.nftest:
            self.local_tools = "./"
            self.local_tool_conf = os.path.join(self.local_tools, "local_tool_conf.xml")
        else:
            self.local_tools = os.path.join(args.galaxy_root, "local_tools")
            self.local_tool_conf = os.path.join(self.local_tools, "local_tool_conf.xml")
        self.ourcwd = os.getcwd()
        self.collections = []
        if len(args.collection) > 0:
            try:
                self.collections = [json.loads(x) for x in args.collection if len(x.strip()) > 1]
            except Exception:
                logger.error(f"--collections parameter {str(args.collection)} is malformed - should be a dictionary")
        self.infiles = []
        try:
            self.infiles = [json.loads(x) for x in args.input_files if len(x.strip()) > 1]
        except Exception:
            logger.error(f"--input_files parameter {str(args.input_files)} is malformed - should be a dictionary")
        self.extra_files = []
        if len(args.xtra_files) > 0:
            try:
                self.extra_files = [json.loads(x) for x in args.xtra_files if len(x.strip()) > 1]
            except Exception:
                logger.error(f"--xtra_files parameter {str(args.xtra_files)} is malformed - should be a dictionary")
        self.outfiles = []
        try:
            self.outfiles = [json.loads(x) for x in args.output_files if len(x.strip()) > 1]
        except Exception:
            logger.error(f"--output_files parameter {args.output_files} is malformed - should be a dictionary")
        assert (
            len(self.outfiles) + len(self.collections)
        ) > 0, "No outfiles or output collections specified. The Galaxy job runner will fail without an output of some sort"
        self.addpar = []
        try:
            self.addpar = [json.loads(x) for x in args.additional_parameters if len(x.strip()) > 1]
        except Exception:
            logger.error(f"--additional_parameters {args.additional_parameters} is malformed - should be a dictionary")
        self.selpar = []
        try:
            self.selpar = [json.loads(x) for x in args.selecttext_parameters if len(x.strip()) > 1]
        except Exception:
            logger.error(f"--selecttext_parameters {args.selecttext_parameters} is malformed - should be a dictionary")
        self.selfagpar = []
        try:
            self.selflagpar = [json.loads(x) for x in args.selectflag_parameters if len(x.strip()) > 1]
        except Exception:
            logger.error(f"--selectflag_parameters {args.selecttext_parameters} is malformed - should be a dictionary")
        self.args = args
        self.cleanuppar()
        self.lastxclredirect = None
        self.xmlcl = []
        self.is_positional = self.args.parampass == "positional"
        if self.args.sysexe:
            if " " in self.args.sysexe:
                self.executeme = shlex.split(self.args.sysexe)
            else:
                self.executeme = [
                    self.args.sysexe,
                ]
        else:
            if self.args.packages:
                self.executeme = [
                    self.args.packages.split(",")[0].split(":")[0].strip(),
                ]
            else:
                self.executeme = None
        aXCL = self.xmlcl.append
        self.newtool = gxt.Tool(
            self.tool_name,
            self.tool_id,
            self.args.tool_version,
            self.args.tool_desc,
            "",
        )
        self.toold = os.path.join(self.local_tools, self.tool_name)
        self.tooltestd = os.path.join(self.toold, "test-data")
        self.tooloutdir = "tfout"
        self.repdir = REP_DIR
        self.newtarpath = args.tested_tool_out
        self.testdir = os.path.join(self.tooloutdir, "test-data")
        if not os.path.exists(self.tooloutdir):
            os.mkdir(self.tooloutdir)
        if not os.path.exists(self.testdir):
            os.mkdir(self.testdir)
        if not os.path.exists(self.repdir):
            os.mkdir(self.repdir)
        self.tinputs = gxtp.Inputs()
        self.toutputs = gxtp.Outputs()
        self.testparam = []
        if self.args.script_path:
            self.prepScript()
        if self.args.cl_override != None:
            scos = open(self.args.cl_override, "r").readlines()
            self.cl_override = [x.rstrip() for x in scos]
        else:
            self.cl_override = None
        if self.args.test_override != None:
            stos = open(self.args.test_override, "r").readlines()
            self.test_override = [x.rstrip() for x in stos]
        else:
            self.test_override = None
        if self.args.cl_prefix != None:
            scos = open(self.args.cl_prefix, "r").readlines()
            self.cl_prefix = [x.rstrip() for x in scos]
        else:
            self.cl_prefix = None
        if self.args.cl_suffix != None:
            stos = open(self.args.cl_suffix, "r").readlines()
            self.cl_suffix = [x.rstrip() for x in stos]
        else:
            self.cl_suffix = None

        if self.args.script_path:
            for ex in self.executeme:
                aXCL(ex)
            aXCL('$runme')
        else:
            for ex in self.executeme:
                aXCL(ex)

        if self.args.parampass == "0":
            self.clsimple()
        else:
            if self.args.parampass == "positional":
                self.prepclpos()
                self.clpositional()
            else:
                self.prepargp()
                self.clargparse()

    def clsimple(self):
        """no parameters or repeats - uses < and > for i/o"""
        aXCL = self.xmlcl.append
        if len(self.infiles) > 0:
            aXCL('<')
            aXCL('$%s' % self.infiles[0]['infilename'])
        if len(self.outfiles) > 0:
            aXCL('>')
            aXCL('$%s' % self.outfiles[0]["name"])


    def prepargp(self):
        xclsuffix = []
        for i, p in enumerate(self.infiles):
            rep = p["required"] in ['optional1', 'required1']
            req = p["required"] in ['required', 'required1']
            nam = p["infilename"]
            flag = p['CL']
            if p["origCL"].strip().upper() == "STDIN":
                xappendme = [
                    nam,
                    nam,
                    '< $%s' % nam,
                ]
            else:
                over = ""
                if req:
                    if rep:
                        over = f'#for $rep in $R_{nam}:\n--{nam} "$rep.{nam}"\n#end for'
                else:
                    if rep:
                        over = f'#for $rep in $R_{nam}:\n--{nam} "$rep.{nam}"\n#end for'
                    else:
                        over = f"#if ${nam}\n --{nam} ${nam} \n#end if"
                xappendme = [p["CL"], '$%s' % p["CL"], over]
            xclsuffix.append(xappendme)
        for i, p in enumerate(self.outfiles):
            if p["origCL"].strip().upper() == "STDOUT":
                self.lastxclredirect = ['>', '$%s' % p["name"]]
            else:
                xclsuffix.append([p["name"], "$%s" % p["name"], ""])
        for p in self.addpar:
            nam = p["name"]
            val = p["value"]
            flag = p["CL"]
            rep = p.get("repeat",0) == "1"
            if rep:
                over = f'#for $rep in $R_{nam}:\n--{nam} "$rep.{nam}"\n#end for'
            else:
                over = p.get("override",'')
            if p["type"] == 'clflag':
                over = f'#if ${nam} == "set"\n --{flag}\n#end if'
            xclsuffix.append([p["CL"], "'$%s'" % nam, over])
        for p in self.selpar:
            xclsuffix.append([p["CL"], "'$%s'" % p["name"], p.get("override","")])
        for p in self.selflagpar:
            xclsuffix.append(["", "'$%s'" % p["name"], ""])
        for p in self.collections:
            newname = p["name"]
            xclsuffix.append([newname, "'%s'" % newname, ""])
        self.xclsuffix = xclsuffix

    def prepclpos(self):
        xclsuffix = []
        for i, p in enumerate(self.infiles):
            if p["origCL"].strip().upper() == "STDIN":
                xappendme = [
                    '999',
                    p["infilename"],
                    '< $%s' % p["infilename"],
                ]
            else:
                xappendme = [p["CL"], '$%s' % p["infilename"], ""]
            xclsuffix.append(xappendme)
        for i, p in enumerate(self.outfiles):
            if p["origCL"].strip().upper() == "STDOUT":
                self.lastxclredirect = ['>', '$%s' % p["name"]]
            else:
                xclsuffix.append([p["CL"], '$%s' % p["name"], ""])
        for p in self.addpar:
            nam = p["name"]
            rep = p.get("repeat","0") == "1"  # repeats make NO sense
            if rep:
                logger.warning(f"### warning. Repeats for {nam} ignored - not permitted in positional parameter command lines!")
            over = p.get("override","")
            xclsuffix.append([p["CL"], "'$%s'" % nam, over])
        for p in self.selpar:
            xclsuffix.append([p["CL"], "'$%s'" % p["name"], p.get("override", "")])
        for p in self.selflagpar:
            xclsuffix.append(["", "'$%s'" % p["name"], ""])
        for p in self.collections:
            newname = p["name"]
            xclsuffix.append(newname, "'$%s'" % newname, "")
        xclsuffix.sort()
        self.xclsuffix = xclsuffix

    def prepScript(self):
        rx = open(self.args.script_path, "r").readlines()
        rx = [x.rstrip() for x in rx]
        rxcheck = [x.strip() for x in rx if x.strip() > ""]
        assert len(rxcheck) > 0, "Supplied script is empty. Cannot run"
        self.script = "\n".join(rx)
        fhandle, self.sfile = tempfile.mkstemp(prefix=self.tool_name, suffix="_%s" % (self.executeme[0]))
        tscript = open(self.sfile, "w")
        tscript.write(self.script)
        tscript.close()
        self.spacedScript = [f"    {x.replace('${','$ {')}" for x in rx if x.strip() > ""]
        rx.insert(0, '#raw')
        rx.append('#end raw')
        self.escapedScript = rx
        art = '%s.%s' % (self.tool_name, self.executeme[0])
        artifact = open(art, "wb")
        artifact.write(bytes(self.script, "utf8"))
        artifact.close()

    def cleanuppar(self):
        """positional parameters are complicated by their numeric ordinal"""
        if self.args.parampass == "positional":
            for i, p in enumerate(self.infiles):
                assert (
                    p["CL"].isdigit() or p["CL"].strip().upper() == "STDIN"
                ), "Positional parameters must be ordinal integers - got %s for %s" % (
                    p["CL"],
                    p["label"],
                )
            for i, p in enumerate(self.outfiles):
                assert (
                    p["CL"].isdigit() or p["CL"].strip().upper() == "STDOUT"
                ), "Positional parameters must be ordinal integers - got %s for %s" % (
                    p["CL"],
                    p["name"],
                )
            for i, p in enumerate(self.addpar):
                assert p["CL"].isdigit(), "Positional parameters must be ordinal integers - got %s for %s" % (
                    p["CL"],
                    p["name"],
                )
        for i, p in enumerate(self.infiles):
            infp = copy.copy(p)
            print('infp',infp,'\nself.infiles',self.infiles,'\ni',i)
            infp["origCL"] = infp["CL"]
            if self.args.parampass in ["positional", "0"]:
                infp["infilename"] = p["label"].replace(" ", "_")
            else:
                infp["infilename"] = infp["CL"]
            self.infiles[i] = infp
        for i, p in enumerate(self.outfiles):
            outfp = copy.copy(p)
            outfp["origCL"] = outfp["CL"]  # keep copy
            if outfp.get('label',None) == None:
                outfp['label'] = ''
            self.outfiles[i] = outfp
        for i, p in enumerate(self.addpar):
            addp = copy.copy(p)
            addp["origCL"] = addp["CL"]
            self.addpar[i] = addp
        for i, p in enumerate(self.collections):
            addp = copy.copy(p)
            addp["CL"] = addp["name"]
            self.collections[i] = addp

    def clpositional(self):
        # inputs in order then params
        aXCL = self.xmlcl.append
        for (k, v, koverride) in self.xclsuffix:
            aXCL(v)
        if self.lastxclredirect:
            for cl in self.lastxclredirect:
                aXCL(cl)

    def clargparse(self):
        """argparse style"""
        aXCL = self.xmlcl.append
        # inputs then params in argparse named form
        for (k, v, koverride) in self.xclsuffix:
            if koverride > "":
                k = koverride
                aXCL(k)
            else:
                kl = len(k.strip())
                if kl == 0:
                    k = ' '
                elif kl == 1:
                    k = '-%s' % k
                else:
                    k = '--%s' % k
                aXCL(k)
                aXCL(v)
        if self.lastxclredirect:
            for cl in self.lastxclredirect:
                aXCL(cl)

    def getNdash(self, newname):
        if self.is_positional:
            ndash = 0
        else:
            ndash = 2
            if len(newname) < 2:
                ndash = 1
        return ndash

    def doXMLparam(self):  # noqa
        """Add all needed elements to tool"""
        for p in self.outfiles:
            newname = p["name"]
            newfmt = p["format"]
            newcl = p["CL"]
            test = p["test"]
            oldcl = p["origCL"]
            test = test.strip()
            filta = p.get('when',[])
            lab = p.get('label',"")
            if len(lab.strip()) == 0:
                lab = newname
            ndash = self.getNdash(newcl)
            aparm = gxtp.OutputData(name=newname, format=newfmt, num_dashes=ndash, label=lab)
            if len(filta) > 0:
                ofilta = gxtp.ChangeFormat()
                for whens in filta: # when input=|image_type| value=|large_png| format=|png|
                    whenss = whens.replace('|','"').replace('when ','')
                    clauses = whenss.split()
                    for c in clauses:
                        if c.startswith('value'):
                            v = c.split('=')[1]
                        elif c.startswith('format'):
                            f = c.split('=')[1]
                        elif c.startswith('input'):
                            i = c.split('=')[1]
                        else:
                            print('bad when - need value=, format= and input=, got', whens)
                    owhen = gxtp.ChangeFormatWhen(format=f, input=i, value=v)
                    ofilta.append(owhen)
                aparm.append(ofilta)
            aparm.positional = self.is_positional
            if self.is_positional:
                if oldcl.upper() == "STDOUT":
                    aparm.positional = 9999999
                    aparm.command_line_override = "> $%s" % newname
                else:
                    aparm.positional = int(oldcl)
                    aparm.command_line_override = "$%s" % newname
            self.toutputs.append(aparm)
            ld = None
            if test.strip() > "":
                if test.strip().startswith("diff"):
                    c = "diff"
                    ld = 0
                    if test.split(":")[1].isdigit:
                        ld = int(test.split(":")[1])
                    tp = gxtp.TestOutput(
                        name=newname,
                        value="%s_sample" % newname,
                        compare=c,
                        lines_diff=ld,
                    )
                elif test.startswith("sim_size"):
                    c = "sim_size"
                    tn = test.split(":")[1].strip()
                    if tn > "":
                        if "." in tn:
                            delta = None
                            delta_frac = min(1.0, float(tn))
                        else:
                            delta = int(tn)
                            delta_frac = None
                    tp = gxtp.TestOutput(
                        name=newname,
                        value="%s_sample" % newname,
                        compare=c,
                        delta=delta,
                        delta_frac=delta_frac,
                    )
                else:
                    c = test
                    tp = gxtp.TestOutput(
                        name=newname,
                        value="%s_sample" % newname,
                        compare=c,
                    )
                self.testparam.append(tp)
        for p in self.infiles:
            newname = p["infilename"]
            newfmt = p["format"]
            ndash = self.getNdash(newname)
            reps = (p.get("required", "") in ['optional1', 'required1'])
            isoptional = (p.get("required","") in ['optional', 'optional1'])
            if not len(p["label"]) > 0:
                alab = p["CL"]
            else:
                alab = p["label"]
            aninput = gxtp.DataParam(
                newname,
                optional=isoptional,
                label=alab,
                help=p["help"],
                format=newfmt,
                multiple=False,
                num_dashes=ndash,
            )
            aninput.positional = self.is_positional
            if self.is_positional:
                if p["origCL"].upper() == "STDIN":
                    aninput.positional = 9999998
                    aninput.command_line_override = "< $%s" % newname
                else:
                    aninput.positional = int(p["origCL"])
                    aninput.command_line_override = "$%s" % newname
            if reps:
                repe = gxtp.Repeat(name=f"R_{newname}", title=f"Any number of {alab} repeats are allowed")
                repe.append(aninput)
                self.tinputs.append(repe)
                tparm = gxtp.TestRepeat(name=f"R_{newname}")
                tparm2 = gxtp.TestParam(newname, value="%s_sample" % newname)
                tparm.append(tparm2)
                self.testparam.append(tparm)
            else:
                self.tinputs.append(aninput)
                tparm = gxtp.TestParam(newname, value="%s_sample" % newname)
                self.testparam.append(tparm)
        for p in self.addpar:
            newname = p["name"]
            newval = p.get("value","")
            newlabel = p["label"]
            newhelp = p.get("help","")
            newtype = p.get("type","?")
            newcl = p["CL"]
            oldcl = p["origCL"]
            reps = p.get("repeat","0") == "1"
            if not len(newlabel) > 0:
                newlabel = newname
            ndash = self.getNdash(newname)
            if newtype == "text":
                aparm = gxtp.TextParam(
                    newname,
                    label=newlabel,
                    help=newhelp,
                    value=newval,
                    num_dashes=ndash,
                )
            elif newtype == "integer":
                aparm = gxtp.IntegerParam(
                    newname,
                    label=newlabel,
                    help=newhelp,
                    value=newval,
                    num_dashes=ndash,
                )
            elif newtype == "float":
                aparm = gxtp.FloatParam(
                    newname,
                    label=newlabel,
                    help=newhelp,
                    value=newval,
                    num_dashes=ndash,
                )
            elif newtype == "boolean":
                aparm = gxtp.BooleanParam(
                    newname,
                    label=newlabel,
                    help=newhelp,
                    value=newval,
                    num_dashes=ndash,
                )
            elif newtype == "clflag":
                initval = newval
                aparm = gxtp.SelectParam(
                    newname,
                    label=newlabel,
                    help=newhelp,
                    num_dashes=ndash,
                    display='radio'
                )
                anoptt = gxtp.SelectOption(
                    value='set',
                    text='Set this flag',
                )
                anoptf = gxtp.SelectOption(
                    value='notset',
                    text='Do not set this flag',
                )
                if p['value'] == 'set': # make default same as form
                    aparm.append(anoptt)
                    aparm.append(anoptf)
                else:
                    aparm.append(anoptf)
                    aparm.append(anoptt)
            elif newtype == "datacolumn":
                aparm = gxtp.TextParam(
                    newname,
                    type="data_column",
                    data_ref = p['dataref'],
                    multiple = (p['multiple'] == "1"),
                    label=newlabel,
                    help=newhelp,
                    value=newval,
                    num_dashes=ndash,
                )
            else:
                raise ValueError(
                    'Unrecognised parameter type "%s" for \
                 additional parameter %s in makeXML'
                    % (newtype, newname)
                )
            aparm.positional = self.is_positional
            if self.is_positional:
                aparm.positional = int(oldcl)
            if reps:
                repe = gxtp.Repeat(name=f"R_{newname}", title=f"Any number of {newlabel} repeats are allowed")
                repe.append(aparm)
                self.tinputs.append(repe)
                tparm = gxtp.TestRepeat(name=f"R_{newname}")
                tparm2 = gxtp.TestParam(newname, value=newval)
                tparm.append(tparm2)
                self.testparam.append(tparm)
            else:
                self.tinputs.append(aparm)
                tparm = gxtp.TestParam(newname, value=newval)
                self.testparam.append(tparm)
        for p in self.selpar:
            newname = p["name"]
            newval = p.get("value","")
            newlabel = p["label"]
            newhelp = p["help"]
            newtype = p["type"]
            newcl = p["CL"]
            if not len(newlabel) > 0:
                newlabel = newname
            ndash = self.getNdash(newname)
            if newtype == "selecttext":
                newtext = p["texts"]
                aparm = gxtp.SelectParam(
                    newname,
                    label=newlabel,
                    help=newhelp,
                    num_dashes=ndash,
                )
                for i in range(len(newval)):
                    anopt = gxtp.SelectOption(
                        value=newval[i],
                        text=newtext[i],
                    )
                    aparm.append(anopt)
                aparm.positional = self.is_positional
                if self.is_positional:
                    aparm.positional = int(newcl)
                self.tinputs.append(aparm)
                tparm = gxtp.TestParam(newname, value=newval[0])
                self.testparam.append(tparm)
            else:
                raise ValueError(
                    'Unrecognised parameter type "%s" for\
                 selecttext parameter %s in makeXML'
                    % (newtype, newname)
                )
        for p in self.selflagpar:
            newname = p["name"]
            newval = p["value"]
            newlabel = p["label"]
            newhelp = p["help"]
            newtype = p["type"]
            newtext = p["texts"]
            newcl = p["CL"]
            if not len(newlabel) > 0:
                newlabel = newname
            aparm = gxtp.SelectParam(
                newname,
                label=newlabel,
                help=newhelp,
                num_dashes=0,
            )
            for i in range(len(newval)):
                anopt = gxtp.SelectOption(
                    value=newval[i],
                    text=newtext[i],
                )
                aparm.append(anopt)
            aparm.positional = self.is_positional
            if self.is_positional:
                aparm.positional = int(newcl)
            self.tinputs.append(aparm)
            tparm = gxtp.TestParam(newname, value=newval[0])
            self.testparam.append(tparm)


    def doNoXMLparam(self):
        """filter style package - stdin to stdout"""
        if len(self.infiles) > 0:
            alab = self.infiles[0]["label"]
            if len(alab) == 0:
                alab = self.infiles[0]["infilename"]
            max1s = "Maximum one input if parampass is 0 but multiple input files supplied - %s" % str(self.infiles)
            assert len(self.infiles) == 1, max1s
            newname = self.infiles[0]["infilename"]
            aninput = gxtp.DataParam(
                newname,
                optional=False,
                label=alab,
                help=self.infiles[0]["help"],
                format=self.infiles[0]["format"],
                multiple=False,
                num_dashes=0,
            )
            aninput.command_line_override = "< $%s" % newname
            aninput.positional = True
            self.tinputs.append(aninput)
            tp = gxtp.TestParam(name=newname, value="%s_sample" % newname)
            self.testparam.append(tp)
        if len(self.outfiles) > 0:
            newname = self.outfiles[0]["name"]
            newfmt = self.outfiles[0]["format"]
            anout = gxtp.OutputData(newname, format=newfmt, num_dashes=0)
            anout.command_line_override = '> $%s' % newname
            anout.positional = self.is_positional
            self.toutputs.append(anout)
            tp = gxtp.TestOutput(name=newname, value="%s_sample" % newname)
            self.testparam.append(tp)

    def makeXML(self):  # noqa
        """
        Create a Galaxy xml tool wrapper for the new script
        Uses galaxyhtml
        Hmmm. How to get the command line into correct order...
        """
        iXCL = self.xmlcl.insert
        aXCL = self.xmlcl.append
        if self.args.cl_prefix:  # DIY CL start
           self.xmlcl = self.cl_prefix + self.xmlcl
        if self.args.cl_suffix:  # DIY CL end
            self.xmlcl  += self.cl_suffix
        if self.cl_override:
            self.newtool.command_override = self.cl_override  # config file
        else:
            self.newtool.command_override = self.xmlcl
        cite = gxtp.Citations()
        acite = gxtp.Citation(type="doi", value="10.1093/bioinformatics/bts573")
        cite.append(acite)
        self.newtool.citations = cite
        safertext = ""
        if self.args.help_text:
            helptext = open(self.args.help_text, "r").readlines()
            safertext = "\n".join([cheetah_escape(x) for x in helptext])
        if len(safertext.strip()) == 0:
            safertext = "Ask the tool author (%s) to rebuild with help text please\n" % (self.args.user_email)
        if self.script_in_help and self.args.script_path:
            if len(safertext) > 0:
                safertext = safertext + "\n\n------\n"  # transition allowed!
            scr = [x for x in self.spacedScript if x.strip() > ""]
            scr.insert(0, "\n\nScript::\n")
            if len(scr) > 300:
                scr = scr[:100] + ["    >300 lines - stuff deleted", "    ......"] + scr[-100:]
            scr.append("\n")
            safertext = safertext + "\n".join(scr)
        self.newtool.help = safertext
        for p in self.collections:
            newkind = p["kind"]
            newname = p["name"]
            newlabel = p["label"]
            newdisc = p["discover"]
            collect = gxtp.OutputCollection(newname, label=newlabel, type=newkind)
            disc = gxtp.DiscoverDatasets(pattern=newdisc, directory=f"{newname}", visible="false")
            collect.append(disc)
            self.toutputs.append(collect)
            try:
                tparm = gxtp.TestOutputCollection(newname)  # broken until PR merged.
                self.testparam.append(tparm)
            except Exception:
                logging.error(
                    "WARNING: Galaxyxml version does not have the PR merged yet - tests for collections must be over-ridden until then!"
                )
        self.newtool.version_command = f'echo "{self.args.tool_version}"'
        std = gxtp.Stdios()
        std1 = gxtp.Stdio()
        std.append(std1)
        self.newtool.stdios = std
        requirements = gxtp.Requirements()
        self.condaenv = []
        if self.args.packages:
            try:
                for d in self.args.packages.split(","):
                    ver = None
                    packg = None
                    d = d.replace("==", ":")
                    d = d.replace("=", ":")
                    if ":" in d:
                        packg, ver = d.split(":")
                        ver = ver.strip()
                        packg = packg.strip()
                    else:
                        packg = d.strip()
                        ver = None
                    if ver == "":
                        ver = None
                    if packg:
                        requirements.append(gxtp.Requirement("package", packg.strip(), ver))
                        self.condaenv.append(d)
            except Exception:
                logger.error(
                    "### malformed packages string supplied - cannot parse =",
                    self.args.packages,
                )
                sys.exit(2)
        self.newtool.requirements = requirements
        if self.args.parampass == "0":
            self.doNoXMLparam()
        else:
            self.doXMLparam()
        self.newtool.outputs = self.toutputs
        self.newtool.inputs = self.tinputs
        if self.args.script_path:
            configfiles = gxtp.Configfiles()
            configfiles.append(gxtp.Configfile(name="runme", text="\n".join(self.escapedScript)))
            self.newtool.configfiles = configfiles
        tests = gxtp.Tests()
        test_a = gxtp.Test()
        for tp in self.testparam:
            test_a.append(tp)
        tests.append(test_a)
        self.newtool.tests = tests
        self.newtool.add_comment(
            "Created by %s at %s using the Galaxy Tool Factory." % (self.args.user_email, timenow())
        )
        self.newtool.add_comment("Source in git at: %s" % (toolFactoryURL))
        exml = self.newtool.export()
        if self.test_override:  # cannot do this inside galaxyxml as it expects lxml objects for tests
            part1 = exml.split("<tests>")[0]
            part2 = exml.split("</tests>")[1]
            fixed = "%s\n%s\n%s" % (part1, "\n".join(self.test_override), part2)
            exml = fixed
        with open("%s.xml" % self.tool_name, "w") as xf:
            xf.write(exml)
            xf.write("\n")
        # galaxy history item

    def writeShedyml(self):
        """for planemo"""
        yuser = self.args.user_email.split("@")[0]
        yfname = os.path.join(self.toold, ".shed.yml")
        yamlf = open(yfname, "w")
        odict = {
            "name": self.tool_name,
            "owner": yuser,
            "type": "unrestricted",
            "description": self.args.tool_desc,
            "synopsis": self.args.tool_desc,
            "category": "ToolFactory generated Tools",
        }
        yaml.dump(odict, yamlf, allow_unicode=True)
        yamlf.close()

    def makeTool(self):
        """write xmls and input samples into place"""
        os.makedirs(self.tooltestd, exist_ok=True)
        if self.args.parampass == 0:
            self.doNoXMLparam()
        else:
            self.makeXML()
        if self.args.script_path:
            stname = os.path.join(self.toold, self.sfile)
            if not os.path.exists(stname):
                shutil.copyfile(self.sfile, stname)
        xreal = "%s.xml" % self.tool_name
        xout = os.path.join(self.toold, xreal)
        shutil.copyfile(xreal, xout)
        logger.info("Copied %s to %s" % (xreal, xout))
        xrename = "%s_toolxml.xml" % self.tool_name
        xout = os.path.join(self.repdir, xrename)
        shutil.copyfile(xreal, xout)
        logger.info("Copied %s to %s" % (xreal, xout))
        for p in self.infiles:
            pth = p["name"]
            if os.path.exists(pth):
                dest = os.path.join(self.tooltestd, "%s_sample" % p["infilename"])
                shutil.copyfile(pth, dest)
                logger.info("Copied %s to %s" % (pth, dest))
                dest = os.path.join(self.repdir, "%s_sample.%s" % (p["infilename"], p["format"]))
                shutil.copyfile(pth, dest)
                logger.info("Copied %s to %s" % (pth, dest))
            else:
                logger.info("Optional input path %s does not exist - not copied" % pth)
        if self.extra_files and len(self.extra_files) > 0:
            for xtra in self.extra_files:
                fpath = xtra["fpath"]
                dest = os.path.join(self.toold, xtra["fname"])
                shutil.copyfile(fpath,dest)
                logger.info("Copied xtra file %s to %s" % (fpath, dest))

def main():
    """
    This is a Galaxy wrapper.
    It expects to be called by a special purpose tool.xml

    """
    parser = argparse.ArgumentParser()
    a = parser.add_argument
    a("--script_path", default=None)
    a("--history_test", default=None)
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
    a("--tfout", default="./tfout")
    a("--galaxy_root", default="/galaxy-central")
    a("--collection", action="append", default=[])
    a("--include_tests", default=False, action="store_true")
    a("--install_flag", action="store_true", default=False)
    a("--admin_only", default=True, action="store_true")
    a("--tested_tool_out", default=None)
    a("--tool_conf_path", default="config/tool_conf.xml")  # relative to $__root_dir__
    a("--xtra_files", default=[], action="append",) # history data items to add to the tool base directory
    args = parser.parse_args()
    if args.admin_only:
        assert not args.bad_user, (
            'UNAUTHORISED: %s is NOT authorized to use this tool until Galaxy \
admin adds %s to "admin_users" in the galaxy.yml Galaxy configuration file'
            % (args.bad_user, args.bad_user)
        )
    assert args.tool_name, "## This ToolFactory cannot build a tool without a tool name. Please supply one."
    logfilename = os.path.join(REP_DIR, 'ToolFactory_make_%s_log.txt' % args.tool_name)
    if not os.path.exists(REP_DIR):
        os.mkdir(REP_DIR)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logfilename, mode='w')
    fformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fformatter)
    logger.addHandler(fh)
    tf = Tool_Factory(args)
    tf.makeTool()
    tf.writeShedyml()
    logging.shutdown()


if __name__ == "__main__":
    main()

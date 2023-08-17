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

'''

'''
FILTERCHARS =  "[]{}*.'"

class ParseNFMod:
     '''
     failed attmpt to build a parser and Galaxy tool xml generator for nf-core module scripts and metadata.
     Harder than is worth. Easy to deal with templating the script by writing it and then running it at run time.
     Problem is that there are things in the DDL preceding the script and they need to be introspected
     to set the templated variables. I think I give up
     '''


     def __init__(self, nft, nfy):
        self.nftext = nft
        self.nfyaml = nfy
        self.tfcl = ["--parampass", "argparse"]
        self.tool_name = nfy["name"]
        self.scriptExe = self.makeScript(self.getsection('script:'))
        self.makePackages(self.getlinestart('conda'))
        self.makeMeta()
        stub = self.getsection('stub:') # not all have these - no idea what they're for
        for inpdict in nfy['input']:
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]['type']
            print('input pname', pname, 'ptype', ptype)
            if ptype == 'file':
                self.makeInfile(inpdict)
            elif ptype == 'string':
                self.makeString(inpdict)
            elif ptype in ['number', 'integer']:
                self.makeNum(inpdict)
            elif ptype == "map":
                print('Ignoring map specified as input %s' % str(inpdict))
            else:
                print('### unknown input type encountered in %s' % str(inpdict))
        for inpdict in nfy['output']:
            pname = list(inpdict.keys())[0]
            ptype = inpdict[pname]['type']
            print('output pname', pname, 'ptype', ptype)
            if ptype == 'file':
                tfdict = self.makeOutfile(inpdict)
            elif ptype == "map":
                print('Ignoring map specified as output %s' % str(inpdict))
            else:
                print('### unknown output type encountered in %s' % str(inpdict))

     def makeInfile(self, inpdict):
        """
        need --input_files '{"name": "/home/ross/rossgit/galaxytf/database/objects/d/d/4/dataset_dd49e13c-bd4d-4f8b-8eaa-863483d021f6.dat", "CL": "input_tab", "format": "tabular", "label": "Tabular input file to plot", "help": "If 5000+ rows, html output will fail, but png will work.", "required": "required"}'
        Need a path but no samples are available
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]['description']
        ppattern = inpdict[pname]['pattern']
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        pdict['CL'] = pname
        pdict['name'] = pname
        pdict['format'] = ppattern
        pdict['help'] = ""
        pdict['label'] = plabel
        pdict['required'] = "0"
        self.tfcl.append('--input_files')
        self.tfcl.append(json.dumps(pdict))


     def makeOutfile(self, inpdict):
        """
        need  --output_files '{"name": "htmlout", "format": "html", "CL": "", "test": "sim_size:5000", "label": "Plotlytabular $title on $input_tab.element_identifier" , "when": [ "when input=outputimagetype value=small_png format=png" , "when input=outputimagetype value=large_png format=png" ] }'
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]['description']
        ppattern = inpdict[pname]['pattern']
        if ppattern == 'versions.yml':
            return # ignore these artifacts
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS})
        pdict['CL'] = pname
        pdict['name'] = pname
        pdict['format'] = ppattern
        pdict['help'] = ""
        pdict['label'] = plabel
        pdict['test'] = "sim_size:1000" # arbitrary hackery
        self.tfcl.append('--output_files')
        self.tfcl.append(json.dumps(pdict))

     def makeString(self, inpdict):
        """
        need something like --additional_parameters '{"name": "xcol", "value": "petal_length", "label": "x axis for plot", "help": "Select the input tabular column for the horizontal plot axis", "type": "datacolumn","CL": "xcol","override": "", "repeat": "0", "multiple": "", "dataref": "input_tab"}'
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]['description']
        ppattern = inpdict[pname]['pattern']
        if ppattern.startswith('{') and ppattern.endswith('}'):
            # is a select comma separated list
            self.makeSelect(inpdict)
        else:
            pdict['type'] = 'text'
            pdict['CL'] = pname
            pdict['name'] = pname
            pdict['value'] = ""
            pdict['help'] = ""
            pdict['label'] = plabel
            pdict['repeat'] = "0"
            self.tfcl.append('--additional_parameters')
            self.tfcl.append(json.dumps(pdict))


     def makeNum(self, inpdict):
        """
        need something like --additional_parameters '{"name": "xcol", "value": "petal_length", "label": "x axis for plot", "help": "Select the input tabular column for the horizontal plot axis", "type": "datacolumn","CL": "xcol","override": "", "repeat": "0", "multiple": "", "dataref": "input_tab"}'
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]['description']
        ppattern = inpdict[pname]['pattern']
        ptype = inpdict[pname]['type']
        if ptype == "number":
            pdict['type'] = 'float'
        else:
            pdict['type'] = 'integer'
        pdict['CL'] = pname
        pdict['name'] = pname
        pdict['value'] = ""
        pdict['help'] = ""
        pdict['label'] = plabel
        pdict['repeat'] = "0"
        self.tfcl.append('--additional_parameters')
        self.tfcl.append(json.dumps(pdict))



     def makeSelect(self, inpdict):
        """--selecttext_parameters '{"name":"outputimagetype", "label":"Select the output format for this plot image. If over 5000 rows of data, HTML breaks browsers, so your job will fail. Use png only if more than 5k rows.", "help":"Small and large png are not interactive but best for many (+10k) points. Stand-alone HTML includes 3MB of javascript. Short form HTML gets it the usual way so can be cut and paste into documents.", "type":"selecttext","CL":"image_type","override":"","value": [ "short_html" , "long_html" , "large_png" , "small_png" ], "texts": [ "Short HTML interactive format" ,  "Long HTML for stand-alone viewing where network access to libraries is not available." ,  "Large (1920x1200) png image - not interactive so hover column ignored" ,  "small (1024x768) png image - not interactive so hover column ignored"  ] }
        "{precursor,mature}" is a ppattern
        """
        pdict = {}
        pname = list(inpdict.keys())[0]
        plabel = inpdict[pname]['description']
        ppattern = inpdict[pname]['pattern']
        ppattern = ppattern.translate({ord(i): None for i in FILTERCHARS}) # remove {}
        texts = ppattern.split(',')
        ptype = inpdict[pname]['type']
        pdict['type'] = 'selecttext'
        pdict['CL'] = pname
        pdict['name'] = pname
        pdict['help'] = ""
        pdict['override'] = ""
        pdict['label'] = plabel
        pdict['texts'] = texts # should be comma separated values...
        pdict['value'] = pdict['texts']
        self.tfcl.append('--selecttext_parameters')
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
        t = self.nfyaml['tools'][0]
        if len(t) > 1:
            print('## challenge - meta.yml has a tools entry %s describing more than one tool - not sure if this will end well - using the first only' % t)
        helptext = ["%s: %s\n" % (x,t[x]) for x in t.keys()]
        helpf, self.helpPath =  tempfile.mkstemp(suffix='.help', prefix="nftoolmaker", dir=None, text=True)
        with open(self.helpPath, 'w') as f:
            f.write('\n'.join(helptext))
            f.write('\n')
        self.tfcl.append('--help_text')
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
        c = cs[0].replace('"', '').split('::')[1].strip()
        req = [c]
        if self.scriptExe:
            req.append(self.scriptExe)
            self.tfcl.append("--sysexe")
            self.tfcl.append(self.scriptExe.strip())
        creq = ','.join(req)
        self.tfcl.append("--packages")
        self.tfcl.append(creq)

     def makeScript(self, scrip):
        """
        script is delimited by triple "
        """
        sexe = None
        scriptf, self.scriptPath =  tempfile.mkstemp(suffix='.script', prefix="nftoolmaker", dir=None, text=True)
        s = scrip.split('"""')[1]
        with open(self.scriptPath, 'w') as f:
            f.write(s)
            f.write('\n')
        self.tfcl.append("--script_path")
        self.tfcl.append(self.scriptPath)
        ss = s.split('\n') # first shebang line maybe
        ss = [x for x in ss if x.strip() > ""]
        sfirst = ss[0]
        if sfirst.startswith('#!'):
            sexe = sfirst.split(' ')[1].strip()
        print('### s=', s.split('\n'))
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
                    if  x.strip() == '"""':
                        if inquote:
                            sect.append(x.strip())
                            inquote = False
                            insect = False
                        else:
                            inquote = True
                    if x.strip() == '':
                        if not inquote:
                            insect = False
                if insect:
                    sect.append(x.strip())
        return '\n'.join(sect)

     def getlinestart(self,  flag):
        lstart = [x.lstrip() for x in self.nftext if x.lstrip().startswith(flag)]
        return lstart

parser = argparse.ArgumentParser()
a = parser.add_argument
a('--nftext',required=True)
a('--nfyml',required=True)
args = parser.parse_args()
nft = open(args.nftext,'r').readlines()
nfy = open(args.nfyml,'r')
nfym = yaml.safe_load(nfy)
nfmod = ParseNFMod(nft, nfym)
cl = nfmod.tfcl
cl.insert(0,'notest_toolfactory.py')
cl.insert(0,'/home/ross/rossgit/galaxytf/.venv/bin/python')
print('cl=','\n'.join(cl))
rc = subprocess.run(cl)



## nftoolmaker

### Exploring automated conversion of nf-core to Galaxy tools.

A tool that will download and parse a github nf-core module repository, and run the toolfactory.py script by constructing a suitable command line.

The repository https://github.com/nf-core/modules/tree/master/modules/nf-core has lots of modules, described in paired files - meta.yml and main.nf. They could potentially be auto-converted into Galaxy tools by constructing a suitable command line for the ToolFactory script.

## September 1

All modules have been attempted and we now have ~850 ready for
testing of the 950 or so.

Abandoned pyparsing for the tests - too fragile in my
inexperienced hands with all the batshit crazy ways developers have
used the nfcore DDL. Fortunately the test texts are line oriented so
it's much easier for me to just clean up the test sections to extract
the test files and parameter values using row based script hackery.


The collection is huge - 20+GB with all the redundant test data sets!
This will be fixed soon with URI for all test data paths, but can't do that
until the ToolFactory is working in release 23.1 - was broken because
many of the utilities had an incompatible version of galaxy-util or
tool-util - should be fixed once the release is done.

**Please let me know if there are any nf-core modules you need for your
work and I'll try to build a Galaxy tool for you.**


### Jottings and notes from the process so far

August 28
Currently parsing 613 tests but failing 384.
Failed tests texts are collected into a text file so can look for
themes.

Adding a preprocessing step has really helped.
Nesting can be decomposed but it is a hydra so will take some more work
to deal with the remaining 1/3


August 25

~200 of ~1000 modules now parsed


nfParser.py uses pyparsing. parseNfTests.py will try to parse every
found module's test and print "PARSED" if it succeeds:

```
 grep PARSED testres.txt | wc -l
210
(.venv) ross@pn50:~/rossgit/nftoolmaker$ wc -l testres.txt
998 testres.txt
```

Building *should* be possible for all 200 but has not been attempted
yet - will work through some failing test cases to find anything easily
repaired. Sometimes a small change will make a big difference.



August 23

pyparsing is the way forward for properly dealing with the nextflow DDL language in a generalisable way. The yaml is a pushover. Can now parse a test - will build up to parse the entire test.nf now. Will return all test names and their test parameters reliably to replace a lot of fragile and elaborate string hacking.


```
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2
include { HMMER_HMMSEARCH } from '../../../../../modules/nf-core/hmmer/hmmsearch/main.nf'
workflow test_hmmer_hmmsearch {
    input = [
        [ id:'test', single_end:false ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
        false,
        false,
        false
    ]
    HMMER_HMMSEARCH ( input )
}
workflow test_hmmer_hmmsearch_optional {
    input = [
        [ id:'test', single_end:false ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
        true,
        true,
        true
    ]
    HMMER_HMMSEARCH ( input )
}
```
producing a pyparsing internal representation that's easy to break apart
```
>>> nftest = ZeroOrMore(Group(shebang)) + ZeroOrMore(Group(dsl)) + OneOrMore(includeTestname) + Group( OneOrMore(nftestname))
>>> print(nftest.parse_string(nftesttext))
[['#', '!/usr/bin/env', 'nextflow'], ['nextflow', '.enable.dsl', '=', '  2'], 'HMMER_HMMSEARCH', [['test_hmmer_hmmsearch', 'input', ['[', "id:'test',", 'single_end:false', ']'], 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz',  'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'false', 'false', 'false', 'HMMER_HMMSEARCH', 'input', ')'], ['test_hmmer_hmmsearch_optional', 'input', ['[', "id:'test',", 'single_end:false', ']'], 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', 'https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', 'true', 'true', 'true', 'HMMER_HMMSEARCH', 'input', ')']]]
```
Might not look like much, but that's more than we need. There are stubs and other constructions to deal with but so far this only needs ~20 lines of pyparsing!!
Mind you, those 20 lines took some considerable experimentation to get working.


August 21

Using shlex helps tokenise the nfcore scripts - not perfect so lots of fudges with .replace
Someone can do it right once it's working right.
parsing the tests and the other stuff but formats are a real challenge.
nf-core has it's own vocabulary. One solution would be to add them to Galaxy's datatypes.
Another would be to map output parameter names in the script and override with galaxy extensions for each datatype. That needs a mapping.

a grep for the idiom ${prefix} in the entire nf-core module text corpus was converted into the following list of extensions they seem to have.
Some are bogus but the short ones might be genuine. Problem is that formats need to match Galaxy's expectations.

```
nftypes = [ 'BedGraph', 'CollectMultipleMetrics', 'IS', 'IS_compare', 'IS_compare/output', 'R', 'abacas', 'afa', 'agp', 'alignment_summary_metrics', 'all', 'alleleCount', 'aln', 'asm', 'assembly_summary', 'back_chain', 'bai', 'ballgown', 'bam', 'base_distribution_by_cycle_metrics', 'bcf', 'bcf"', 'bed', 'bed"', 'bedGraph', 'bedGraph"', 'bedgraph"', 'bedpe', 'bg', 'bigBed', 'bigWig', 'bin', 'biom', 'bw', 'clustered', 'clw"', 'cnn', 'cns', 'cool', 'coords', 'count', 'coverage_metrics', 'cpn', 'crai', 'cram', 'csi', 'csi"', 'csv', 'csv"', 'cutoffs', 'd4', 'db', 'dbtype', 'delta', 'dict', 'dnd', 'domtbl"', 'embl', 'fa', 'fa;', 'faa', 'fas', 'fasta', 'fastq', 'fastq"', 'ffn', 'flagstat', 'fmask-all"', 'fmask-rf"', 'fna', 'fsa', 'gbff', 'gbk', 'gem', 'genepred', 'gfa', 'gff', 'gff3', 'gmask-all"', 'gmask-rf"', 'gtf', 'gtf"', 'gz', 'gz"', 'gz":', 'gz;', 'hdf5', 'hist', 'hmm', 'html', 'html"', 'ibf', 'idx', 'idxstats', 'igv":', 'index', 'insert_size_metrics', 'interval_list', 'interval_list"', 'intervals', 'json', 'junction', 'lca', 'list', 'loci', 'log', 'lookup', 'maf', 'mappability', 'mash_stats', 'mate1', 'mate2', 'mcool', 'megan"', 'meryldb', 'metrics', 'mpileup', 'mpileup"', 'msf"', 'narrowPeak', 'npz', 'og', 'out', 'paf', 'paf"', 'par', 'pdf', 'ped', 'phyi"', 'phyloFlash', 'phys"', 'pmask-all"', 'pmask-rf"', 'png', 'png"', 'pretext', 'profile', 'pytor', 'quality_by_cycle_metrics', 'quality_distribution_metrics', 'recal', 'recall":', 'refflat', 'refmap', 'report', 'rna_metrics', 'roh', 'sai', 'sam', 'score', 'screen', 'sdf', 'seg', 'simplified', 'sizes', 'snf', 'somalier', 'source', 'stat', 'stats', 'sthlm', 'sto"', 'summary', 'svg', 'tab', 'table', 'table"', 'table":', 'tax', 'tbi', 'tbi"', 'tbl', 'tbl"', 'tif', 'tiff', 'tiling', 'tmap', 'tracking', 'tranches', 'tre', 'tree"', 'tsv', 'tsv"', 'txt', 'txt"', 'txt":', 'unc', 'vcf', 'vcf"', 'version', 'vg', 'vgi"', 'wig', 'wig"', 'xg', 'xml', 'zip', ]

```

Now have a working hmmer_align xml and test data as a result of manual editing.
Need to make the generator use the right parameter names - it's tricky because fiddling the nf-core script text is a bit of a fool's errand - the whole project is really.


August 20

The ToolFactory is now imported as a class and given the command line as an argparse args object so it works just fine.
The hardest part is finding the test data to use for the new tool.
Ampir is working. In the repository. Generated by nftoolmaker.py but it still fails on everything else just about.
Parsing the tests in a reliable and generalisable way is not so easy since it’s a full on DDL Worse, the indirection they use is complicated and stupid. Only part of the path is included - their software takes care of finding it in the midden that is their test data repository.
A lot of progress but plenty to do.


Parsing the yaml and breaking up the DDL into manageable chunks is done. Tool metadata is mostly available and done.

Parsing parameters and generating TF command line components seems to be working with the test case - edge cases will be sought later. Some odd things like maps and stubs don’t make much sense. Input files/strings/numbers/integers and output files are working with the test case.

Harder: Automatic test data.

Test settings now available in a slightly messy format - as:
```
(.venv) ross@pn50:~/rossgit/nftoolmaker$ python nftoolmaker.py --nftext ampir.nfcore --nfyml meta.yml
{'tool_name': 'ampir', 'fasta': ["[ [ id:'test', single_end:false ], // meta map", "file(params.test_data['candidatus_portiera_aleyrodidarum']['genome']['proteome_fasta'], checkIfExists: true),"], 'model': ['"precursor"'], 'min_length': ['10'], 'min_probability': ['"0.7"']}
```
Need to find those shared test files on github and grab them to use with those parameters.
Then ready to change the whole command generator - greatly simplified to echo a string with all the templates into bash or Rscript stdin, then integrate these test parameters into test generation.
Need to find those shared test files on github and grab them to use with those parameters.
Then ready to change the whole command generator - greatly simplified to echo a string with all the templates into bash or Rscript stdin, then integrate these test parameters into test generation.
Then we can start testing 🙂

### Reasons to do this:

We probably can automate some conversions by parsing the paired files and writing a ToolFactory.py command line to generate a tool.
Automated conversions could speed up ingestion of NF workflows
nf-core code that I have seen so far seems to be ugly and unpleasant.


### Reasons not to do this:

The testcase, ampir uses a shared proteome as the test input.

```
https://github.com/nf-core/test-datasets/tree/modules/data/genomics/prokaryotes/candidatus_portiera_aleyrodidarum/genome
```

This is discovered by finding https://github.com/nf-core/modules/blob/master/tests/modules/nf-core/ampir/main.nf which gives the test parameters and the proteome to use. Boy, they make it brittle by this indirection saving some copies of test data. Seems an awkward decision to me.

```
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2
include { AMPIR } from '../../../../modules/nf-core/ampir/main.nf'
workflow test_ampir {
    fasta = [ [ id:'test', single_end:false ], // meta map          file(params.test_data[**'candidatus_portiera_aleyrodidarum'**]['genome']['proteome_fasta'], checkIfExists: true),
    ]
    model = "precursor"
    min_length = 10
min_probability = "0.7"
    AMPIR ( fasta, model, min_length, min_probability )
}
```

Their scripts create output file names like:

```
 -o ${prefix}.bam##idx##${prefix}.bam.bai - shell code copying those named files to the Galaxy history file names before and after script execution will be needed
```

They pass variables, including external ones, into scripts by templating and while we can do that, some of those variables are changed by DDL statements - we would have to reliably parse these - this example wouldn’t be hard to hack but there are more complex examples:

```
script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def args = task.ext.args ?: ''
    def args2 = task.ext.args2 ?: ''
    def args3 = task.ext.args3 ?: ''
    def biscuit_cpus = (int) Math.max(Math.floor(task.cpus*0.95),1)
    def samtools_cpus = task.cpus-biscuit_cpus
    """
    INDEX=`find -L ./ -name "*.bis.amb" | sed 's/\\.bis.amb\$//'`

    biscuit align \\
        -@ $biscuit_cpus \\
        $args \\
        \$INDEX \\
        $reads | \\
    samblaster \\
        $args2 | \\
    samtools sort \\
        -@ $samtools_cpus \\
        $args3 \\
        --write-index \\
        -o ${prefix}.bam##idx##${prefix}.bam.bai

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        biscuit: \$( biscuit version |& sed '1!d; s/^.*BISCUIT Version: //' )
        samtools: \$( samtools --version |& sed '1!d; s/^.*samtools //' )
        samblaster: \$( samblaster --version |& sed 's/^.*samblaster: Version //' )
    END_VERSIONS
    """
}
```
An example updates from https://github.com/nf-core/funcscan/blob/1.1.3/modules/nf-core/antismash/antismashlitedownloaddatabases/main.nf that seems to
poke things from the local python3.8 with a big stick. This is scary.

```
cp_cmd = ( session.config.conda && session.config.conda.enabled ) ? "cp -r \$(python -c 'import antismash;print(antismash.__file__.split(\"/__\")[0])') antismash_dir;" :
"cp -r /usr/local/lib/python3.8/site-packages/antismash antismash_dir;"
```

Some scripts have elaborate DSL preambles that will be tricky to translate.
Inputs often have regexp patterns - need to parse to create useful Galaxy forms such as:

```
- faa:
    type: file
    description: FASTA file containing amino acid sequences
    pattern: "*.{faa,fasta}"
```

Test data is a twisty maze of packages, all trainwrecks.
Some “modules” have tests that rely on the live output from another module. That is not very modular and tricky to fix.

Some “modules” have more than one test so that’s not happening for now - will just take the first one

```
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2
include { SURVIVOR_FILTER  as SURVIVOR_FILTER_NO_BED} from '../../../../../modules/nf-core/survivor/filter/main.nf'
include { SURVIVOR_FILTER  as SURVIVOR_FILTER_BED} from '../../../../../modules/nf-core/survivor/filter/main.nf'
workflow test_survivor_filter_no_bed {
        input_no_bed = [
        [ id:'test'], // meta map
            file(params.test_data['homo_sapiens']['illumina']['test_genome_vcf'], checkIfExists: true),
            []
    ]
    SURVIVOR_FILTER_NO_BED (
        input_no_bed,
        51,
        10001,
        0.01,
        10
    )

}
workflow test_survivor_filter {
    input_bed = [
        [ id:'test'], // meta map
            file(params.test_data['homo_sapiens']['illumina']['test_genome_vcf'], checkIfExists: true),
            file(params.test_data['homo_sapiens']['genome']['genome_bed'], checkIfExists: true)
        ]

    SURVIVOR_FILTER_BED (
        input_bed,
        51,
        10001,
        0.01,
        10
    )
}
```
keywords are "include", "workflow" and the testnames
includes contain the workflow test names
workflow { to } has the test file and test name to match up
with test alias parameter names in order inside parentheses.

All of the bash scripts seem to use \\ as a continuation. Bash does not like that so they all need to be fiddled into submission.

Need to dump each test file into the new tool folder test directory with the correct name.

The use of the idiom ${prefix}.bazbar to name output files is painful. These need to be replaced in entirety with the correct output parameter name using the extension as the clue to finding the corresponding output - but not using any extension in the script

test parameter names are often bogus. Must use the metadata parameter names but rely on their ordering 😡

Interesting pattern in survivor_merge:

```
    SURVIVOR merge \\
        <(ls *.vcf) \\
        ${max_distance_breakpoints} \\
        ${min_supporting_callers} \\
        ${account_for_type} \\
        ${account_for_sv_strands} \\
        ${estimate_distanced_by_sv_size} \\
        ${min_sv_size} \\
        ${prefix}.vcf

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        survivor: \$(echo \$(SURVIVOR 2>&1 | grep "Version" | sed 's/^Version: //'))
    END_VERSIONS
```

This makes some sense because the input pattern in yaml is "*.vcf" so need another special case to allow multiple input files that also fiddles the script to link all the input files with a .vcf extension to the working directory. On it goes.

Chained tests are a thing.
```
workflow test_hmmer_eslreformat_afa {
    input = [
        [ id:'test' ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz')      // Change to params.test_data syntax after the data is included in ./tests/config/test_data.config
    ]
    hmm   = file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz'
    HMMER_HMMALIGN ( input, hmm )
    HMMER_ESLREFORMAT_AFA ( HMMER_HMMALIGN.out.sthlm )
}
```

So these need a dictionary of test names and outputs.

How to decompose HMMER_HMMALIGN.out.sthlm into a specific testfiel path? the extension here happens to be the name of the output so maybe possible,

Wotiff there’s more than one output file? Ah well. Let’s leave this one for the moment - first figure out if this is going to be worth the bother by recording these modules and coming back later.

Names given in tests are useless or missing. It’s just the ordering that’s used.
In general, params can be specified as named lists in at least two seemingly equivalent ways:
This specifies them and passes them into the test as a list of values:
```
workflow test_hmmer_hmmsearch {

    input = [
        [ id:'test', single_end:false ], // meta map
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/bac.16S_rRNA.hmm.gz', checkIfExists: true),
        file('https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/delete_me/hmmer/e_coli_k12_16s.fna.gz', checkIfExists: true),
        false,
        false,
        false
    ]

    HMMER_HMMSEARCH ( input )
}

```

vs the above where test params are named

so the main.nf must be used to get the type and name of the parameters expected for the test - in this case the input param values are files and boolean flags.

Comments in nfcore text files are a pain. They should be removed before parsing

Fortunately, pyparsing!

# nftoolmaker

## Exploring automated conversion of nf-core to Galaxy tools.

Trying to make a tool that will download and parse a github nf-core module repository, and run the toolfactory.py script by constructing a suitable command line.

The repository https://github.com/nf-core/modules/tree/master/modules/nf-core has lots of modules, described in paired files - meta.yml and main.nf. They could potentially be auto-converted into Galaxy tools by constructing a suitable command line for the ToolFactory script.

### Progress to date.
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
``` script:
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
### Reproducibility issues

The executable for nf-core R scripts is specified by a shebang (like this for ampir: #!/usr/bin/env Rscript) so R is always the latest installed version - convenient but not reproducible - nothing in metadata about the script executable version. Unless as Bjoern points out, they always pin a container from Galaxy :) but not sure that’s universal in all modules? Does nf-core always run modules in singularity?
Bash scripts call a binary - presumably the one installed as a dependency from the “conda” entry in the main.nf file such as https://github.com/nf-core/modules/blob/master/modules/nf-core/abacas/main.nf

The architecture is so fussy and complicated that reproducibility seems at risk in places.
The version is recorded at the end of each run, but really not ideal. Examples of “updaters” include:
amrfinderplus includes an updater module, that grabs whatever the latest binary happens to be for this tool - they do record the version at least I guess - https://github.com/nf-core/funcscan/blob/1.1.3/modules/nf-core/amrfinderplus/update/main.nf
A gem of an example of how tools are updated from https://github.com/nf-core/funcscan/blob/1.1.3/modules/nf-core/antismash/antismashlitedownloaddatabases/main.nf that seems to
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

Some “modules” have more than one test so that’s not happening for now - will just take the first one.
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
Why aliases?
Seems we like the flexibility to make things more tricky and intertwined than necessary where we can.
The tool has metadata, but the tests can use different metadata names sometimes, because, well, that seems to be what
nextflow developers seem to like - freedom! freedom! freedom!.
Freedom to fill the test repository with duplicate files! Wonderful.

# nftoolmaker

Failed attempt to autogenerate Galaxy tools from nf-core modules
Exploring automated conversion of nf-core to Galaxy tools.
The repository https://github.com/nf-core/modules/tree/master/modules/nf-core has lots of modules, described in paired files - meta.yml and main.nf. They could potentially be auto-converted into Galaxy tools by constructing a suitable command line for the ToolFactory script.

### Progress to date.

Trying to make a tool that will download and parse a github nf-core module repository, and run the toolfactory.py script by constructing a suitable command line.

Easy: Parsing the yaml and breaking up the DDL into manageable chunks is done. Tool metadata is mostly available and done.

More tricky: Made a good start on parsing parameters and generating TF command line components. Some odd things like maps and stubs don’t make much sense. Input files/strings/numbers/integers and output files are well underway.

Impossible: Automatic test data - so cannot generate a real tool - will need an expert to do that manually at present.


### Reasons to do this:

We probably can automate some conversions by parsing the paired files and writing a ToolFactory.py command line to generate a tool.
Automated conversions could speed up ingestion of NF workflows
nf-core code that I have seen so far seems to be ugly and unpleasant.

### Reasons not to do this:
No test sample data in meta.yml or anywhere obvious. Without that, cannot automate the tool test at generation. Someone skilled would need to take an untested, autogenerated tool, regenerate it with suitable test data and adjust as necessary until it works.

Their scripts create output file names like:
 -o ${prefix}.bam##idx##${prefix}.bam.bai - shell code copying those named files to the Galaxy history file names before and after script execution will be needed
They pass variables, including external ones, into scripts by templating and while we can do that, some of those variables are changed by DDL statements - we would have to reliably parse these - this example wouldn’t be hard to hack but there are more complex examples:
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

### Reproducibility issues
Bash scripts call a binary - presumably the one installed as a dependency from the “conda” entry in the main.nf file such as https://github.com/nf-core/modules/blob/master/modules/nf-core/abacas/main.nf

The architecture seems terribly bad for reproducibility IMHO in places - the version is recorded at the end of each run, but really not ideal.

Examples of “updaters” include:
amrfinderplus includes an updater module, that grabs whatever the latest binary happens to be for this tool - they do record the version at least I guess - https://github.com/nf-core/funcscan/blob/1.1.3/modules/nf-core/amrfinderplus/update/main.nf
A gem of an example of how tools are updated from https://github.com/nf-core/funcscan/blob/1.1.3/modules/nf-core/antismash/antismashlitedownloaddatabases/main.nf that seems to poke things from the local python3.8 with a big stick. This is scary. cp_cmd = ( session.config.conda && session.config.conda.enabled ) ? "cp -r \$(python -c 'import antismash;print(antismash.__file__.split(\"/__\")[0])') antismash_dir;" : "cp -r /usr/local/lib/python3.8/site-packages/antismash antismash_dir;"

Some scripts have elaborate DSL preambles that will be tricky to translate.

Inputs often have regexp patterns - need to parse to create useful Galaxy forms such as:
- faa:
    type: file
    description: FASTA file containing amino acid sequences
    pattern: "*.{faa,fasta}"


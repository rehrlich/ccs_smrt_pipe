ccs_smrt_pipe uses PacBio .bax.h5 files to create fastq input files for MCSMRT.


##Required software:
Smrtanalysis version 2.3


##Installation:
Modify the line:
SMRT_ROOT="/opt/smrtanalysis"
in the file ccs_job_maker.sh so instead of /opt/smrtanalysis it has the location of smrtanalysis on your computer.  If you type ls and this location you should see something like:
admin  common  current  install  smrtcmds  tmpdir  userdata
If you can't find it, ask the person who installed smrtanalysis where it is.
Optional:  Modify the header on ccs_job_maker.sh so you can submit it to sge.


##Creating the barcode fasta file:
The set of barcodes you purchased should have a fasta file with their sequences.  Several can be found here:  https://github.com/PacificBiosciences/Bioinformatics-Training/tree/master/barcoding
The order of the barcodes in this file doesn't matter.  Extra barcodes are also fine.


##Single sample mode:
This is intended to be used for debugging and testing parameters in a bash loop.  You should generally use the multi sample mode because it is more efficient when you have multiple samples per cell.
This takes several command line inputs (described below) and runs a SMRT pipe circular consensus sequencing (ccs) job to create a consensus fastq file.


##Multi sample mode:
This runs many SMRT pipe ccs jobs.  Jobs are defined by a tab separated file.  The first line of the file must include the following column headings in any order:  job_name	barcode_file	video_path	barcode1	barcode2	outdir	name	full_passes	pred_accuracy	barcode_mode
Each line in the file is one sample and each column is a parameter for a ccs job.  All of the parameters work the same as the single sample parameters except for job name.  When multiple samples from the same SMRT cell can be demultiplexed using the same parameters, they should be given the same job name.  Otherwise, they must be given different names.  Lines with the same job name must contain the same values for all parameters except for name, barcode1 and barcode2.
All barcodes for a single job name should be unique.  For example, if job1 has sample A with barcode b1=x1 and b2=x2 then sample B from job1 cannot have x1 for either of its barcodes.  A different job can have a sample with barcode b1=x1 and b2=x2.
All jobs must have the same outidr.
All sample names must be unique.


##Single sample mode:

Usage: ccs_job_maker.sh single [-h] [-o OUTDIR] [-n NAME] [-fp FULL_PASSES]
                               [-pa PRED_ACCURACY]
                               [-bcm {asymmetric,symmetric}] -bcf BARCODE_FILE
                               -v VIDEO_PATH -b1 BARCODE1 -b2 BARCODE2

Optional arguments:
  -h, --help            show this help message and exit
  -o OUTDIR, --outdir OUTDIR
                        output directory (default: smrt_pipe_ccs)
  -n NAME, --name NAME  A name for the fastq output file (default: Sample1)
  -fp FULL_PASSES, --full_passes FULL_PASSES
                        The minimum number of full passes which must be an
                        integer between zero and ten (default: 3)
  -pa PRED_ACCURACY, --pred_accuracy PRED_ACCURACY
                        Minimum prediction accuracy which must be an integer
                        between 70 and 100 (default: 90)
  -bcm {asymmetric,symmetric}, --barcode_mode {asymmetric,symmetric}
                        must be either "asymmetric" or "symmetric" (default:
                        asymmetric)

Required arguments:
  -bcf BARCODE_FILE, --barcode_file BARCODE_FILE
                        The path to the fasta file with the barcodes (default:
                        None)
  -v VIDEO_PATH, --video_path VIDEO_PATH
                        The directory containing the *.bax.h5 files (default:
                        None)
  -b1 BARCODE1, --barcode1 BARCODE1
                        The forward barcode name (default: None)
  -b2 BARCODE2, --barcode2 BARCODE2
                        The reverse barcode name (default: None)


##Multi sample mode:
Usage: ccs_job_maker.sh batch [-h] -i INPUT_FILE

Optional arguments:
  -h, --help            show this help message and exit

Required arguments:
  -i INPUT_FILE, --input_file INPUT_FILE
                        batch input file


##Detailed explanation of arguments:
OUTDIR - This is a path to a directory that does not currently exist.  The default option is to create a directory called smrt_pipe_ccs in your current directory.
FULL_PASSES - PacBio describes this as "The minimum number of full-length passes over the insert DNA for the read to be included."  It must be a whole number between zero and ten, inclusive.
PRED_ACCURACY - PacBio describes this as "The minimum predicted accuracy (in %) of the Reads of Insert emitted."  It must be a whole number between 70 and 100, inclusive.
BARCODE_MODE - This specifies the type of barcoding used so that barcodes can be scored correctly.  The argument is symmetric if the barcode sequences are the same on both sides of the insert and asymmetric if they are different.
BARCODE_FILE - This is the path to a fasta file with the barcodes used for the experiment.
VIDEO_PATH - A directory containing the *.bax.h5 data files.  In the directory with the raw data from a pacbio cell, this the Analysis_Results folder.  All *.bax.h5 files in the directory will be used.  On my computer this path would be something like /data/pacbio/rawdata/run_name/A01_1/Analysis_Results
BARCODE - b1 and b2 must be valid fasta headers from the barcode fasta file.


##Detailed explanation of output directory:
OUTDIR/fastq - This has the fastq output file(s).  The header lines are the headers created by smrtpipe with ';ccs=X;' appended to the end.  X is the number of ccs passes that were used to generate that entry in the file.
OUTDIR/job_name - Thiese directories have all of the files created by smrt pipe.


All code is under a GPL license except the function _get_ccs_passes from the file count_passes.py which was modified from https://github.com/PacificBiosciences/Bioinformatics-Training/raw/master/scripts/ccs_passes.py and the settings_template.xml which was modified from a settings.xml file created using PacBio's SMRT portal.

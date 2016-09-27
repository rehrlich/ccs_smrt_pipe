#!/usr/bin/env bash
#$ -j y
#$ -cwd
#$ -pe smp 16
#$ -R y
#
#python3.5 ccs_job_maker.py -bcf /opt/smrtanalysis/install/smrtanalysis_2.3.0.140936/common/userdata/references/barcodes_nasal \
#-s /opt/smrtanalysis -v /data/pacbio/rawdata/20160128Jason_143/E01_1/Analysis_Results \
#-b1 0001_Forward -b2 0002_Forward


# failed 127512
#python3.5 ccs_job_maker.py -bcf barcodes.fasta \
#-s /opt/smrtanalysis \
#-v /data/pacbio/rawdata/20160128Jason_143/E01_1/Analysis_Results \
#-b1 0001_Forward -b2 0002_Forward

# barcodes is an uploaded ref dir
python3.5 ccs_job_maker.py -bcf /data/shared/homes/rachel/ccs_smrt_pipe/barcodes \
-s /opt/smrtanalysis \
-v /data/pacbio/rawdata/20160128Jason_143/E01_1/Analysis_Results \
-b1 0001_Forward -b2 0002_Forward
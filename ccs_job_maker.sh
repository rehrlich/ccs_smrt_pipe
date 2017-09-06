#!/usr/bin/env bash
#$ -N ccs_jobs
#$ -j y
#$ -cwd
#$ -pe smp 16
#$ -R y

# Author:  Rachel Ehrlich

SMRT_ROOT="/opt/smrtanalysis"

if [ -e $SMRT_ROOT"/current/etc/setup.sh" ]; then
    source $SMRT_ROOT"/current/etc/setup.sh"
    dir=`dirname "$(readlink -f "$0")"`
    python $dir/ccs_job_maker.py "$@"
else
    echo "Error:  smrtanalysis not found."
fi
#!/usr/bin/env bash
#$ -j y
#$ -cwd
#$ -pe smp 16
#$ -R y

SMRT_ROOT=$1
out_dir=$2
settings=$3
inputs=$4
counter_script=$5
pass_counts=$6

source $SMRT_ROOT/current/etc/setup.sh

smrtpipe.py --output=$out_dir --params=$settings xml:$inputs
barcode_archive=$out_dir'/data/barcoded-fastqs.tgz'
data_dir=$(dirname $barcode_archive)
tar -xzf $barcode_archive -C $data_dir

python $counter_script $data_dir > $pass_counts



#!/usr/bin/env bash
#$ -j y
#$ -cwd
#$ -pe smp 16
#$ -R y

out_dir=$1
settings=$2
inputs=$3


smrtpipe.py --output=$out_dir --params=$settings xml:$inputs
barcode_archive=$out_dir'/data/barcoded-fastqs.tgz'
data_dir=$(dirname $barcode_archive)
tar -xzf $barcode_archive -C $data_dir




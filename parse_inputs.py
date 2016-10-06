import argparse
import os
import sys
from itertools import groupby


def make_args():
    parser = argparse.ArgumentParser(description='Create SMRT pipe ccs jobs',
                                     add_help=True,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(help='sub-command help')

    batch_parser = subparsers.add_parser('batch', help='batch input help')
    required_flags_batch = batch_parser.add_argument_group('Required arguments')
    required_flags_batch.add_argument('-i', '--input_file',
                                      help='batch input file',
                                      required=True)

    single_parser = subparsers.add_parser('single', help='single input help',
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    single_parser.add_argument('-o', '--outdir',
                               help='output directory',
                               default=os.getcwd() + '/smrt_pipe_ccs')
    single_parser.add_argument('-n', '--name',
                               help='A name for the fastq output file',
                               default='Sample1')
    single_parser.add_argument('-fp', '--full_passes',
                               help='The minimum number of full passes which must be an integer between zero and ten',
                               type=int,
                               default=3)
    single_parser.add_argument('-pa', '--pred_accuracy',
                               help='Minimum prediction accuracy which must be an integer between 70 and 100',
                               type=int,
                               default=90)
    single_parser.add_argument('-bcm', '--barcode_mode',
                               help='must be either "asymmetric" or "symmetric"',
                               choices=['asymmetric', 'symmetric'],
                               default='asymmetric')

    required_flags = single_parser.add_argument_group('Required arguments')

    required_flags.add_argument('-bcf', '--barcode_file',
                                help='The path to the fasta file with the barcodes',
                                required=True)
    required_flags.add_argument('-v', '--video_path',
                                help='The directory containing the *.bax.h5 files',
                                required=True)
    required_flags.add_argument('-b1', '--barcode1',
                                help='The forward barcode name',
                                required=True)
    required_flags.add_argument('-b2', '--barcode2',
                                help='The reverse barcode name',
                                required=True)

    return parser.parse_args()


def group_by(unsorted_iterable, key_func):
    sorted_iterable = sorted(unsorted_iterable, key=key_func)
    return groupby(sorted_iterable, key_func)


def group_by_job(input_file):
    """This would be so much easier with pandas...
    Check that everything gets the same outdir - can't exist yet
    group rows by job_id
    each job_id has one dicttionary of parameters plus a list of
    name, b1, b2 named tuples

    :param input_file:
    :return: list of dicts, dicts have sample specific parameters and job parameters
    """
    with open(input_file, 'r') as f:
        col_numbers = {x: i for i, x in enumerate(f.readline().rstrip('\n').split('\t'))}

        data = [line.rstrip('\n').split('\t') for line in f.readlines()]

    project_names = set()
    project_outdir = data[0][col_numbers['outdir']]

    sample_specific_parameters = {'name', 'barcode1', 'barcode2'}

    jobs = list()

    for job_name, job_data in group_by(data, key_func=lambda x: x[col_numbers['job_name']]):
        job_barcodes = set()
        parameters = dict()
        samples = list()
        for sample in job_data:

            if len(sample) != len(col_numbers):
                sys.exit('Error:  The row: \n' + '\t'.join(sample) + '\nhas'
                         ' the wrong number of columns.  Please remove any'
                         ' empty rows.')

            sample_name = sample[col_numbers['name']]
            if sample_name in project_names:
                sys.exit('Error:  The sample named ' + sample_name +
                         ' is not unique in the input file.')
            project_names.add(sample_name)

            sample_outdir = sample[col_numbers['outdir']]
            if sample_outdir != project_outdir:
                sys.exit('Error:  All samples must have the same outdir.')

            bc1, bc2 = sample[col_numbers['barcode1']], sample[col_numbers['barcode2']]
            if bc1 == bc2:
                sys.exit('Error:  The barcodes for sample ' + sample_name +
                         ' are the same.')
            if bc1 in job_barcodes or bc2 in job_barcodes:
                sys.exit('Error:  One of the barcodes for sample ' +
                         sample_name + ' has already been used in job ' +
                         job_name)
            job_barcodes.update({bc1, bc2})

            if parameters:
                for param_name, col_num in col_numbers.items():
                    if param_name not in sample_specific_parameters:
                        sample_value = sample[col_num]
                        if sample_value != parameters[param_name]:
                            sys.exit("Error:  The value for " + param_name +
                                     " for sample " + sample_name +
                                     " doesn't match other values in the job.")
            else:
                for param_name, col_num in col_numbers.items():
                    if param_name not in sample_specific_parameters:
                        parameters[param_name] = sample[col_num]
            samples.append({param_name: sample[col_numbers[param_name]] for param_name in sample_specific_parameters})

        jobs.append({'samples': samples, 'parameters': parameters})

    return jobs

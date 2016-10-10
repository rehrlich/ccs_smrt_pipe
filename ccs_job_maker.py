import os
import sys
from subprocess import call
from glob import glob

import parse_inputs
import make_barcode_ref
import make_xml_inputs

script_dir = os.path.dirname(os.path.abspath(__file__))


class CCSJob:
    counter_script = script_dir + '/count_ccs_passes.py'
    smrt_script = script_dir + '/smrt_pipe_job.sh'

    def __init__(self, parameters, samples):
        self.job_dir = parameters['outdir'] + '/' + parameters['job_name']

        self.barcode_ref = make_barcode_ref.BarcodeRef(sample_data=samples,
                                                       job_dir=self.job_dir,
                                                       barcode_file=parameters[
                                                           'barcode_file'])

        self.ccs_settings = make_xml_inputs.CCSSettings(
            full_passes=parameters['full_passes'],
            pred_accuracy=parameters['pred_accuracy'],
            barcode_file=self.barcode_ref.barcode_dir + '/barcode_ref',
            job_dir=self.job_dir)

        self.ccs_inputs = make_xml_inputs.CCSInputs(
            video_dir=parameters['video_path'],
            job_dir=self.job_dir)

        self.ccs_h5_files = []

    def run(self):
        call(['bash', 'smrt_pipe_job.sh', self.job_dir,
              self.ccs_settings.settings_output,
              self.ccs_inputs.inputs_file])

        self.ccs_h5_files = glob(self.job_dir + '/data/*.ccs.h5')

    def get_name_to_fq(self):
        no_paths = self.barcode_ref.get_name_fastq_pairs()
        pairs = list()
        for name, fq in no_paths:
            pairs.append({'name': name, 'fastq': self.job_dir + '/data/' + fq})
        return pairs


def main():
    args = parse_inputs.make_args()
    if 'input_file' in args:
        print('batch mode')
        jobs = parse_inputs.group_by_job(args.input_file)
    else:
        print('single mode')
        args.job_name = args.name
        jobs = parse_inputs.organize_single_job_inputs(args)
    jobs = [CCSJob(job['parameters'], job['samples']) for job in jobs]

    for job in jobs:
        job.run()

    #
    # pass_counts_path = cL_job.outdir + '/data/pass_counts.txt'
    # poly_passes = PolymerasePasses(pass_counts_path)
    #
    # fq_outdir = args.outdir + '/fq/'
    # os.makedirs(fq_outdir, exist_ok=True)
    #
    # for sample in cL_job.barcoded_samples:
    #     sample.counted_path = fq_outdir + sample.nickname + '.fastq'
    #     poly_passes.add_counts_to_fq(sample.uncounted_path, sample.counted_path)
    #

if __name__ == '__main__':
    main()

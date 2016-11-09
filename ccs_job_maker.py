# Author:  Rachel Ehrlich


import os
import traceback
from subprocess import call
from glob import glob

import parse_inputs
import make_barcode_ref
import make_xml_inputs
import count_passes

script_dir = os.path.dirname(os.path.abspath(__file__))


class CCSJob:
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

        self.ccs_h5_files = glob(self.job_dir + '/data/*.ccs.h5')

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


def concat_fastqs(fq_dir):
    cmd = [x for x in glob(fq_dir + '/*.fastq') if
           not x.endswith('_no_ccs_count.fastq')]
    cmd.insert(0, 'cat')
    with open(fq_dir + '/all_samples.fastq', 'w') as f:
        call(cmd, stdout=f)


def main():
    args = parse_inputs.make_args()
    if 'input_file' in args:
        print('batch mode')
        jobs = parse_inputs.group_by_job(args.input_file)
    else:
        print('command_line mode')
        jobs = parse_inputs.organize_single_job_inputs(args)

    project_dir = jobs[0]['parameters']['outdir']
    fq_dir = project_dir + '/fastq'

    jobs = [CCSJob(job['parameters'], job['samples']) for job in jobs]

    # for job in jobs:
    #     job.run()

    call(['mkdir', fq_dir])

    for job in jobs:
        try:
            polymerase_pass_counts = count_passes.PolymerasePasses(job.ccs_h5_files)
        except:
            traceback.print_exc()
            print('There was a problem counting ccs passes in the files:\n' +
                  '\n'.join(job.ccs_h5_files) + '\nAttempting to count ccs ' +
                  'passes for the remaining job(s).')
            for sample in job.get_name_to_fq():
                fq_in = sample['fastq']
                if os.path.isfile(fq_in):
                    fq_out = fq_dir + '/' + sample['name'] + '_no_ccs_count.fastq'
                    call(['cp', fq_in, fq_out])
                else:
                    fq_out = fq_dir + '/' + sample['name'] + '.fastq'
                    print('Something went wrong with the demultiplexing and ' +
                          'the file\n' + fq_out + '\ncould not be created.  ' +
                          'Did you use the correct barcodes and barcode file?')

        else:

            for sample in job.get_name_to_fq():
                fq_out = fq_dir + '/' + sample['name'] + '.fastq'
                fq_in = sample['fastq']

                if os.path.isfile(fq_in):
                    header_suffix = 'barcodelabel=' + sample['name'] + ';'
                    polymerase_pass_counts.add_counts_to_fq(fq_in, fq_out,
                                                            header_suffix)
                else:
                    print('Something went wrong with the demultiplexing and ' +
                          'the file\n' + fq_out + '\ncould not be created.  ' +
                          'Did you use the correct barcodes and barcode file?')

    concat_fastqs(fq_dir)


if __name__ == '__main__':
    main()

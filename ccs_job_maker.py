import os
import sys
from subprocess import call

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
            barcode_file=self.barcode_ref.barcode_dir,
            job_dir=self.job_dir)

        self.ccs_inputs = make_xml_inputs.CCSInputs(
            video_dir=parameters['video_path'],
            job_dir=self.job_dir)


        # self.outdir = outdir
        # os.makedirs(self.outdir, exist_ok=True)
        #
        # self.barcoded_samples = list()
        # self.barcode_file = barcode_file
        # self.pass_counts = None

    def run(self, smrt_root):
        self.pass_counts = self.outdir + '/data/pass_counts.txt'
        call(['bash', self.smrt_script, smrt_root, self.outdir,
              self.settings, self.inputs, self.counter_script,
              self.pass_counts])

    def add_sample(self, sample):
        sample.uncounted_path = self.outdir + '/data/' + sample.barcode1 + \
                                '--' + sample.barcode2 + '.fastq'
        assert os.path.isfile(sample.uncounted_path)
        self.barcoded_samples.append(sample)


class PolymerasePasses:
    def __init__(self, pass_counts_path):
        self.pass_counts = dict()
        with open(pass_counts_path, 'r') as f:
            for line in f:
                split_line = line.split()
                self.pass_counts[split_line[0]] = split_line[1]

    def add_counts_to_fq(self, in_fq, out_fq):
        counted_fq = list()
        with open(in_fq, 'r') as in_file:
            for i, line in enumerate(in_file):
                if i % 4 == 0:
                    name = line[1:].split()[0]
                    try:
                        count = self.pass_counts[name]
                    except KeyError:
                        print('ERROR:  There is a header in the fastq file: ' +
                              in_fq + ' which was not found in the pass counts' +
                              ' file.  This is a known issue with older ' +
                              'installations of smrtanalysis.  Please make ' +
                              'sure your copy has been correctly patched and ' +
                              'updated.')
                        sys.exit()
                    counted_fq.append(name + ';ccs=' + count + ';\n')
                else:
                    counted_fq.append(line)

        with open(out_fq, 'w') as out_file:
            out_file.write(''.join(counted_fq))


def main():
    args = parse_inputs.make_args()
    if 'input_file' in args:
        print('batch mode')
        jobs = parse_inputs.group_by_job(args.input_file)
    else:
        print('single mode')
        args.job_name = args.name
        jobs = parse_inputs.organize_single_job_inputs(args)
    for job in jobs:
        CCSJob(job['parameters'], job['samples'])
    return

    cL_job = CcsJob(args.outdir + '/job1', str(args.full_passes),
                    str(args.pred_accuracy),
                    args.barcode_file, args.video_path)
    cL_job.run(args.smrt_root)

    sample = BarcodedSample(args.barcode1, args.barcode2, args.name)
    cL_job.add_sample(sample)

    pass_counts_path = cL_job.outdir + '/data/pass_counts.txt'
    poly_passes = PolymerasePasses(pass_counts_path)

    fq_outdir = args.outdir + '/fq/'
    os.makedirs(fq_outdir, exist_ok=True)

    for sample in cL_job.barcoded_samples:
        sample.counted_path = fq_outdir + sample.nickname + '.fastq'
        poly_passes.add_counts_to_fq(sample.uncounted_path, sample.counted_path)


if __name__ == '__main__':
    main()

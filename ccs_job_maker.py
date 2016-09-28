import argparse
import os
import sys
from glob import iglob
from subprocess import call


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


def verify_args(args):
    if os.path.isfile(args.outdir + '/fq/' + args.name + '.fastq'):
        print('Error:  A sample with the name ' + args.name +
              ' already exists.  Please change either the name or the '
              'output directory and try again.')
    else:
        return
    sys.exit()


class CCSSettings:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _settings_template = _script_dir + '/settings_template.xml'

    def __init__(self, full_passes, pred_accuracy, barcode_file,
                 settings_output):

        self._full_passes = full_passes
        self._pred_accuracy = pred_accuracy
        self._barcode_file = barcode_file
        self.settings_output = settings_output

    def _check_parameters(self):
        if not 0 <= self._full_passes <= 10:
            print('Full passes must be an integer between zero and 10.')
        if not 70 <= self._pred_accuracy <= 100:
            print('Prediction accuracy must be an integer between 70 and 100.')

    def _make_output(self):
        with open(self._settings_template, 'r') as f:
            txt = f.read()

        pairs = [('NUM_FULL_PASSES', self._full_passes),
                 ('PERCENT_PRED_ACCURACY', self._pred_accuracy),
                 ('BARCODE_FASTA_DIR', self._barcode_file)]

        for old, new in pairs:
            txt = txt.replace(old, new)

        with open(self.settings_output, 'w') as f:
            f.write(txt)


class CcsJob:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inputs_template = script_dir + '/inputs_template.xml'
    counter_script = script_dir + '/count_ccs_passes.py'
    smrt_script = script_dir + '/smrt_pipe_job.sh'

    def __init__(self, outdir, full_passes, pred_acc, barcode_file, video_path):
        self.outdir = outdir
        os.makedirs(self.outdir, exist_ok=True)

        self.barcoded_samples = list()
        self.full_passes = full_passes
        self.pred_accuracy = pred_acc
        self.barcode_file = barcode_file
        self.settings = self.outdir + '/settings.xml'
        self.video_path = video_path
        self.inputs = self.outdir + '/inputs.xml'
        self.pass_counts = None

    def make_inputs_file(self):
        with open(self.inputs_template, 'r') as f:
            txt = f.read()

        for full_path in iglob(self.video_path + '/*.bax.h5'):
            video_num = full_path[-8]
            txt = txt.replace('VIDEO' + video_num, full_path)

        with open(self.inputs, 'w') as f:
            f.write(txt)

    def run(self, smrt_root):
        if not os.path.isfile(self.settings):
            self.make_settings_file()
        if not os.path.isfile(self.inputs):
            self.make_inputs_file()

        self.pass_counts = self.outdir + '/data/pass_counts.txt'
        call(['bash', self.smrt_script, smrt_root, self.outdir,
              self.settings, self.inputs, self.counter_script,
              self.pass_counts])

    def add_sample(self, sample):
        sample.uncounted_path = self.outdir + '/data/' + sample.barcode1 + \
                                '--' + sample.barcode2 + '.fastq'
        assert os.path.isfile(sample.uncounted_path)
        self.barcoded_samples.append(sample)


class BarcodedSample:
    def __init__(self, barcode1, barcode2, nickname):
        self.barcode1 = barcode1
        self.barcode2 = barcode2
        self.nickname = nickname
        self.counted_path = None
        self.uncounted_path = None


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
    args = make_args()
    print(args)
    return

    verify_args(args)

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

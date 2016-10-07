import sys
from glob import glob
import os
from subprocess import call

script_dir = os.path.dirname(os.path.abspath(__file__))


def validate_template(template_path):
    if not os.path.isfile(template_path):
        sys.exit('Error:  The template file ' + template_path + ' was not ' +
                 'found.  Did you download the xml files from github?')


class CCSSettings:
    _settings_template = script_dir + '/settings_template.xml'

    def __init__(self, full_passes, pred_accuracy, barcode_file, job_dir):
        self._full_passes = int(full_passes)
        self._pred_accuracy = int(pred_accuracy)
        self._barcode_file = barcode_file
        self.settings_output = job_dir + '/ccs_settings.xml'
        call(['mkdir', '-p', job_dir])
        self._check_parameters()
        self._make_file()

    def _check_parameters(self):
        if not 0 <= self._full_passes <= 10:
            sys.exit('Full passes must be an integer between zero and 10.')
        if not 70 <= self._pred_accuracy <= 100:
            sys.exit('Prediction accuracy must be an integer between 70 and 100.')
        validate_template(self._settings_template)

    def _make_file(self):
        with open(self._settings_template, 'r') as f:
            txt = f.read()

        pairs = [('NUM_FULL_PASSES', self._full_passes),
                 ('PERCENT_PRED_ACCURACY', self._pred_accuracy),
                 ('BARCODE_FASTA_DIR', self._barcode_file)]

        for old, new in pairs:
            txt = txt.replace(old, str(new))

        with open(self.settings_output, 'w') as f:
            f.write(txt)


class CCSInputs:
    _inputs_template = script_dir + '/inputs_template.xml'

    def __init__(self, video_dir, job_dir):
        self._video_dir = video_dir
        self._video_paths = glob(self._video_dir + '/*.bax.h5')
        self._job_dir = job_dir
        self.inputs_file = self._job_dir + '/inputs.xml'
        call(['mkdir', '-p', self._job_dir])
        self._check_parameters()
        self._make_file()

    def _check_parameters(self):
        if len(self._video_paths) == 0:
            print('Error:  No bax.h5 files found in ' + self._video_dir)
            if len(glob(self._video_dir + '/*.bam')) > 0:
                print('The video directory has bam files.  This script only ' +
                      'works for bax.h5 files.')
            sys.exit()

        safe_suffixes = {'.1.bax.h5', '.2.bax.h5', '.3.bax.h5'}
        for video_path in self._video_paths:
            if video_path[-9:] not in safe_suffixes:
                sys.exit('Error:  The .bax.h5 file names have been modified.' +
                         '  Video files must end with one of the following ' +
                         'suffixes:  ' + ' '.join(safe_suffixes))

        validate_template(self._inputs_template)

    def _make_file(self):
        fofn = self._job_dir + '/videos.fofn'
        with open(fofn, 'w') as f:
            f.write('\n'.join(x for x in self._video_paths))

        with open(self.inputs_file, 'w') as f:
            call(['fofnToSmrtpipeInput.py', fofn], stdout=f)

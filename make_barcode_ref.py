# Author:  Rachel Ehrlich


import os
import shutil
from subprocess import PIPE, Popen, call
import sys
from itertools import chain


class BarcodeRef:
    def __init__(self, sample_data, job_dir, barcode_file):
        self._sample_data = sample_data
        self._ordered_barcode_file = job_dir + '/ordered_barcodes.fasta'
        self.barcode_dir = job_dir + '/barcode_ref'
        call(['mkdir', '-p', self.barcode_dir])
        self._ordered_barcodes = list(chain.from_iterable([(x['barcode1'], x['barcode2']) for x in sample_data]))
        self._barcode_file = barcode_file
        self._check_parameters()
        self._make_ordered_fasta()
        self._upload_ref(self._ordered_barcode_file)

    @staticmethod
    def _get_sample_fasta():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sample_fasta = script_dir + '/example.fasta'
        if not os.path.isfile(sample_fasta):
            sys.exit('Error:  The example.fasta file, which is used for error '
                     'checking, was not found.  Did you download it?')
        return sample_fasta

    def _check_parameters(self):
        if not os.path.isfile(self._barcode_file):
            sys.exit('Error:  The barcode file ' + self._barcode_file +
                     ' does not exist.')

        expected_output = self._upload_ref(self._get_sample_fasta())
        output = self._upload_ref(self._barcode_file)

        if output != expected_output:
            print(output)
            sys.exit('Error:  Could not create barcode reference from the ' +
                     'fasta file ' + self._barcode_file)

        with open(self._barcode_file, 'r') as f:
            fasta = f.read()
        for barcode in self._ordered_barcodes:
            if '>' + barcode + '\n' not in fasta:
                sys.exit('Error:  The barcode ' + barcode + ' was not found ' +
                         'in the file ' + self._barcode_file)

    def _make_ordered_fasta(self):
        with open(self._barcode_file, 'r') as f:
            fasta_lookup = dict()
            barcode = ''
            for line in f:
                if line.startswith('>'):
                    if barcode != '':
                        fasta_lookup[barcode] = ''.join(entry)
                    barcode = line[1:].rstrip()
                    entry = list()
                entry.append(line)

            fasta_lookup[barcode] = ''.join(entry)

        with open(self._ordered_barcode_file, 'w') as f:
            for barcode in self._ordered_barcodes:
                entry = fasta_lookup[barcode]
                if not entry.endswith('\n'):
                    entry += '\n'
                f.write(entry)

    def _upload_ref(self, fasta_path):
        shutil.rmtree(self.barcode_dir)
        cmd = ['referenceUploader',
               '-c', '-p', self.barcode_dir,
               '-n', 'barcode_ref',
               '-f', fasta_path]

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        output = p.communicate()[1].decode(encoding='UTF-8')
        call(['samtools', 'faidx',
              self.barcode_dir + '/barcode_ref/sequence/barcode_ref.fasta'])
        return output

    def get_name_fastq_pairs(self):
        """
        :return: list of (name, fastq name NOT path)
        """
        pairs = list()
        for sample in self._sample_data:
            pairs.append((sample['name'],
                          sample['barcode1'] + '--' + sample['barcode2'] +
                          '.fastq'))
        return pairs


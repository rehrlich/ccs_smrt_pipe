import os
from subprocess import PIPE, Popen, call
import sys
from itertools import chain


class BarcodeRef:
    def __init__(self, sample_data, job_dir, barcode_file):
        self._ordered_barcode_file = job_dir + '/ordered_barcodes.fasta'
        self._barcode_dir = job_dir + '/barcode_ref'
        self._ordered_barcodes = list(chain.from_iterable([(x['barcode1'], x['barcode2']) for x in sample_data]))
        self._barcode_file = barcode_file
        self._check_parameters()
        self._make_ordered_fasta()
        self._upload_ref()

    @staticmethod
    def popen(cmd):
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        output = p.communicate()[1].decode(encoding='UTF-8')
        return output

    def _check_parameters(self):
        if not os.path.isfile(self._barcode_file):
            sys.exit('Error:  The barcode file ' + self._barcode_file +
                     ' does not exist.')

        # Not using this reference but this checks that the fasta is valid
        cmd = ['referenceUploader',
               '-c', '-p', self._barcode_dir,
               '-n', 'barcode_ref',
               '-f', self._barcode_file]
        expected_output = ('SLF4J: Failed to load class "org.slf4j.impl.StaticLoggerBinder".\n' +
                            'SLF4J: Defaulting to no-operation (NOP) logger implementation\n' +
                            'SLF4J: See http://www.slf4j.org/codes.html#StaticLoggerBinder for further details.\n')

        output = self.popen(cmd)

        if output != expected_output:
            print(output)
            sys.exit('Error:  Could not create barcode reference from the ' +
                     'fasta file ' + self._barcode_file)
        call(['rm', '-r', self._barcode_dir])

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

    def _upload_ref(self):
        cmd = ['referenceUploader',
               '-c', '-p', self._barcode_dir,
               '-n', 'barcode_ref',
               '-f', self._ordered_barcode_file]
        self.popen(cmd)

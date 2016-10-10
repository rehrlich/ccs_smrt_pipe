# Author:  Rachel Ehrlich


import sys
import os

import h5py


class PolymerasePasses:
    def __init__(self, ccs_h5_files):
        self._ccs_h5_files = ccs_h5_files
        self._pass_counts = dict()
        self._get_ccs_passes()

    def _get_ccs_passes(self):
        for ccs_h5_file in self._ccs_h5_files:

            hf = h5py.File(ccs_h5_file)
            basename = os.path.basename(ccs_h5_file)[:-9]

            # should be unnecessary
            suffix = ccs_h5_file[-9:]
            assert suffix in ('.1.ccs.h5', '.2.ccs.h5', '.3.ccs.h5')

            for hole_num, num_passes in zip(hf['/PulseData/ConsensusBaseCalls/ZMW/HoleNumber'].value, hf['/PulseData/ConsensusBaseCalls/Passes/NumPasses'].value):
                if num_passes > 0:
                    self._pass_counts['%s/%d/ccs' % (basename, hole_num)] = str(num_passes)

    def add_counts_to_fq(self, in_fq, out_fq):
        counted_fq = list()
        with open(in_fq, 'r') as in_file:
            for i, line in enumerate(in_file):
                if i % 4 == 0:
                    name = line[1:].split()[0]
                    try:
                        count = self._pass_counts[name]
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
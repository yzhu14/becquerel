"""Base class for spectrum file parsers."""

from __future__ import print_function
import os
import numpy as np
from scipy.interpolate import interp1d


class SpectrumFileParsingError(Exception):
    """Failed while parsing a spectrum file."""

    pass


class SpectrumFile(object):
    """Spectrum file parser base class.

    Just instantiate a class with a filename:
        spec = SpectrumFile(filename)

    Then the data are in
        spec.data [counts]
        spec.channels
        spec.energies
        spec.energy_bin_widths

    """

    def __init__(self, filename):
        """Initialize the spectrum."""
        self.filename = filename
        assert os.path.exists(self.filename)
        # fields to read from file
        self.spectrum_id = ''
        self.sample_description = ''
        self.detector_description = ''
        self.location_description = ''
        self.hardware_status = ''
        self.collection_start = None
        self.collection_stop = None
        self.realtime = 0.0
        self.livetime = 0.0
        self.num_channels = 0
        # arrays to be read from file
        self.channels = np.array([], dtype=np.float)
        self.data = np.array([], dtype=np.float)
        self.cal_coeff = []
        # arrays to be calculated using calibration
        self.energies = np.array([], dtype=np.float)
        self.energy_bin_widths = np.array([], dtype=np.float)

    def __str__(self):
        """String form of the spectrum."""

        print_channels = False

        s = ''
        s += 'Filename:              {:s}\n'.format(self.filename)
        s += 'Spectrum ID:           {:s}\n'.format(self.spectrum_id)
        s += 'Sample description:    {:s}\n'.format(self.sample_description)
        s += 'Detector description:  {:s}\n'.format(self.detector_description)
        s += 'Location Description:  {:s}\n'.format(self.location_description)
        s += 'Hardware Status:       {:s}\n'.format(self.hardware_status)
        if self.collection_start is not None:
            s += 'Collection Start:      {:%Y-%m-%d %H:%M:%S}\n'.format(
                self.collection_start)
        else:
            s += 'Collection Start:      None\n'
        if self.collection_stop is not None:
            s += 'Collection Stop:       {:%Y-%m-%d %H:%M:%S}\n'.format(
                self.collection_stop)
        else:
            s += 'Collection Stop:       None\n'
        s += 'Livetime:              {:.2f} sec\n'.format(self.livetime)
        s += 'Realtime:              {:.2f} sec\n'.format(self.realtime)
        s += 'Number of channels:    {:d}\n'.format(self.num_channels)
        if len(self.cal_coeff) > 0:
            s += 'Calibration coeffs:    '
            s += ' '.join(['{:E}'.format(x) for x in self.cal_coeff])
            s += '\n'
        s += 'Data:                  \n'
        if print_channels:
            for ch, dt in zip(self.channels, self.data):
                s += '    {:5.0f}    {:5.0f}\n'.format(ch, dt)
        else:
            s += '    [length {}]\n'.format(len(self.data))
        return s

    def read(self, verbose=False):
        """Read in the file."""
        raise NotImplementedError('read method not implemented')

    def write(self, filename):
        """Write back to a file."""
        raise NotImplementedError('write method not implemented')

    def apply_calibration(self):
        """Calculate energies corresponding to channels."""
        self.energies = self.channel_to_energy(self.channels)
        self.energy_bin_widths = self.bin_width(self.channels)

    def channel_to_energy(self, channel):
        """Apply energy calibration to the given channel(s)."""
        chan = np.array(channel, dtype=float)
        en = np.zeros_like(chan)
        for j in range(len(self.cal_coeff)):
            en += self.cal_coeff[j] * pow(chan, j)
        return en

    def energy_to_channel(self, energy):
        """Invert the energy calibration to find the channel(s)."""
        energy = np.array(energy, dtype=float)
        return interp1d(self.energies, self.channels)(energy)

    def bin_width(self, channel):
        """Calculate the width of the bin in keV at the channel(s)."""
        en0 = self.channel_to_energy(channel - 0.5)
        en1 = self.channel_to_energy(channel + 0.5)
        return en1 - en0
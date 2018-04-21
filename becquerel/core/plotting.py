"""Tools for plotting spectra."""

from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
from uncertainties import unumpy


class PlottingError(Exception):
    """General exception for plotting.py"""

    pass


class SpectrumPlotter(object):
    """Class for handling spectrum plotting."""

    def __init__(self, spec, *fmt, xmode=None, ymode=None, xlim=None,
                 ylim=None, ax=None, yscale=None, title=None, xlabel=None,
                 ylabel=None, **kwargs):
        """
        Args:
          spec:   Spectrum instance to plot
          fmt:    matplotlib like plot format string
          xmode:  define what is plotted on x axis ('energy' or 'channel')
          ymode:  define what is plotted on y axis ('counts', 'cps', 'cpskev'
                  or 'eval_over')
          xlim:   set x axes limits, if set to 'default' use special scales
          ylim:   set y axes limits, if set to 'default' use special scales
          ax:     matplotlib axes object, if not provided one is created using
                  the 'figsize' argument once the plot command is called
          yscale: matplotlib scale: 'linear', 'log', 'logit', 'symlog'
          title:  costum plot title, default is filename if available
          xlabel: costum xlabel value
          ylabel: costum ylabel value
          kwargs: arguments that are directly passed to matplotlib plot commands
        """

        #TODO Marco: maybe we should use tuplets for all the x/y stuff in order
        #to reduce the number of attributes (pylint ask for 7 we have 23)!
        self._xedges = None
        self._ydata = None
        self._xmode = None
        self._ymode = None
        self._xlabel = None
        self._ylabel = None
        self._ax = None
        self._xlim = None
        self._ylim = None

        self.spec = spec
        fmtlen = len(fmt)
        if fmtlen == 0:
            self.fmt = ''
        elif fmtlen == 1:
            self.fmt = fmt[0]
        else:
            raise PlottingError('Wrong number of positional parameters')

        if 'figsize' in kwargs:
            self._figsize = kwargs.pop('figsize')
        else:
            self._figsize = None
        if 'eval_over' in kwargs:
            self._eval_time = kwargs.pop('eval_over')
        else:
            self._eval_time = None

        self.xlim = xlim
        self.ylim = ylim

        self.yscale = yscale
        self.ax = ax
        self.title = title
        self.kwargs = kwargs

        self.xmode = xmode
        self.ymode = ymode

        self.xlabel = xlabel
        self.ylabel = ylabel


    @property
    def xmode(self):
        """
        Returns the current x axis plotting mode
        """

        return self._xmode


    @xmode.setter
    def xmode(self, mode):
        """
        Define x data mode, handles all data errors, requires spec.
        Defines also xedges and xlabel.

        Args:
          mode: energy (or kev), channel (or channels, chn, chns)
        """

        if mode is None:
            if self.spec.is_calibrated:
                self._xmode = 'energy'
            else:
                self._xmode = 'channel'
        else:
            if mode.lower() in ('kev', 'energy'):
                if not self.spec.is_calibrated:
                    raise PlottingError('Spectrum is not calibrated, however'
                                        ' x axis was requested as energy')
                self._xmode = 'energy'
            elif mode.lower() in ('channel', 'channels', 'chn', 'chns'):
                self._xmode = 'channel'
            else:
                raise PlottingError('Unknown x data mode: {}'.format(mode))

        if self._xmode == 'energy':
            self._xedges = self.spec.bin_edges_kev
            self._xlabel = 'Energy [keV]'
        elif self._xmode == 'channel':
            self._xedges = self.get_channel_edges(self.spec.channels)
            self._xlabel = 'Channel'


    @property
    def ymode(self):
        """
        Returns the current y axis plotting mode.
        """
        return self._ymode


    @ymode.setter
    def ymode(self, mode):
        """
        Define y data mode, handles all data errors, requires spec.
        Defines also ydata and ylabel.

        Args:
          mode: counts, cps, cpskev, eval_over
        """

        if self._eval_time is not None:
            self._ymode = 'eval_over'
        elif mode is None:
            if self.spec.counts is not None:
                self._ymode = 'counts'
            elif self.spec.cps is not None:
                self._ymode = 'cps'
            elif self.spec.cpskev is not None:
                self._ymode = 'cpskev'
            else:
                raise PlottingError('Cannot evaluate y data from spectrum')
        elif mode.lower() in ('count', 'counts', 'cnt', 'cnts'):
            if self.spec.counts is None:
                raise PlottingError('Spectrum has counts not defined')
            self._ymode = 'counts'
        elif mode.lower() == 'cps':
            if self.spec.cps is None:
                raise PlottingError('Spectrum has cps not defined')
            self._ymode = 'cps'
        elif mode.lower() == 'cpskev':
            if self.spec.cps is None:
                raise PlottingError('Spectrum has cps not defined')
            self._ymode = 'cpskev'
        else:
            raise PlottingError('Unknown y data mode: {}'.format(mode))

        if self._ymode == 'counts':
            self._ydata = self.spec.counts_vals
            self._ylabel = 'Counts'
        elif self._ymode == 'cps':
            self._ydata = self.spec.cps_vals
            self._ylabel = 'Countrate [1/s]'
        elif self._ymode == 'cpskev':
            self._ydata = self.spec.cpskev_vals
            self._ylabel = 'Countrate [1/s/keV]'
        elif self._ymode == 'eval_over':
            self._ydata = self.spec.counts_vals_over(self._eval_time)
            self._ylabel = 'Countrate [1/s]'


    @property
    def ax(self):
        """
        Returns the current matplotlib axes object used for plotting.
        If no axes object is defined yet it will create one.
        """

        if self._ax is None:
            if self._figsize is None:
                _, self._ax = plt.subplots()
            else:
                _, self._ax = plt.subplots(self._figsize)
        return self._ax


    @ax.setter
    def ax(self, ax):
        """
        Defines the current matplotlib axes object used for plotting.
        Is affected by the figsize member variable, if set.

        Args:
          ax: Axes to be set
        """

        self._ax = ax
        if ax is not None and self.yscale is None:
            self.yscale = ax.get_yscale()


    @property
    def xlabel(self):
        """
        Returns the current x label
        """
        return self._xlabel


    @xlabel.setter
    def xlabel(self, label):
        """
        Sets the xlabel to a costum value.
        """
        if label is not None:
            self._xlabel = label


    @property
    def ylabel(self):
        """
        Returns the current y label
        """
        return self._ylabel


    @ylabel.setter
    def ylabel(self, label):
        """
        Sets the ylabel to a costum value.
        """
        if label is not None:
            self._ylabel = label


    def get_corners(self):
        """
        Creates a stepped version of the current spectrum data.

        Return:
          xcorner, ycorner: x and y values that can be used directly in
                            matplotlib's plotting function
        """

        return self.bin_edges_and_heights_to_steps(
            self._xedges, unumpy.nominal_values(self._ydata))


    def _prepare_plot(self, **kwargs):
        """Prepare for the plotting."""

        self.kwargs.update(**kwargs)
        if not self.ax.get_xlabel():
            self.ax.set_xlabel(self._xlabel)
        if not self.ax.get_ylabel():
            self.ax.set_ylabel(self._ylabel)
        if self.yscale is not None:
            self.ax.set_yscale(self.yscale)
        if self.title is not None:
            self.ax.set_title(self.title)
        elif self.spec.infilename is not None:
            self.ax.set_title(self.spec.infilename)
        if self._xlim is not None:
            self.ax.set_xlim(self.xlim)
        if self._ylim is not None:
            self.ax.set_ylim(self.ylim)
            if self.yscale == 'symlog':
                self.ax.set_yscale(self.yscale, linthreshy=self.linthreshy)
        return self.get_corners()


    def plot(self, *fmt, **kwargs):
        """
        Create actual plot with matplotlib's plot method.

        Args:
          fmt:    Matplotlib plot like format string
          kwargs: Any matplotlib plot() keyword argument, overwrites
                  previously defined keywords
        """

        fmtlen = len(fmt)
        if fmtlen == 1:
            self.fmt = fmt[0]
        elif fmtlen > 1:
            raise PlottingError('Wrong number of positional parameters')

        xcorners, ycorners = self._prepare_plot(**kwargs)
        self.ax.plot(xcorners, ycorners, self.fmt, **self.kwargs)
        return self.ax


    def fill_between(self, **kwargs):
        """
        Create actual plot with matplotlib's fill_between method.

        Args:
          kwargs: Any matplotlib fill_between() keyword argument, overwrites
                  previously defined keywords
        """

        xcorners, ycorners = self._prepare_plot(**kwargs)
        self.ax.fill_between(xcorners, ycorners, **self.kwargs)
        return self.ax


    @staticmethod
    def get_channel_edges(channels):
        """Get a vector of xedges for uncalibrated channels."""

        n_edges = len(channels) + 1
        return np.linspace(-0.5, channels[-1] + 0.5, num=n_edges)


    @staticmethod
    def bin_edges_and_heights_to_steps(bin_edges, heights):
        """A robust alternative to matplotlib's drawstyle='steps-*'"""

        assert len(bin_edges) == len(heights) + 1
        x = np.zeros(len(bin_edges) * 2)
        y = np.zeros_like(x)
        x[::2] = bin_edges.astype(float)
        x[1::2] = bin_edges.astype(float)
        y[1:-1:2] = heights.astype(float)
        y[2:-1:2] = heights.astype(float)
        return x, y


    @staticmethod
    def dynamic_min(data_min, min_delta_y):
        """Get an axes lower limit (for y) based on data value.

        The lower limit is the next power of 10, or 3 * power of 10, below the min.

        Args:
          data_min: the minimum of the data (could be integers or floats)
          min_delta_y: the minimum step in y
        """

        if data_min > 0:
            ceil10 = 10**(np.ceil(np.log10(data_min)))
            sig_fig = np.floor(10 * data_min / ceil10)
            if sig_fig <= 3:
                ymin = ceil10 / 10
            else:
                ymin = ceil10 / 10 * 3
        elif data_min == 0:
            ymin = min_delta_y / 10.0
        else:
            # negative
            floor10 = 10**(np.floor(np.log10(-data_min)))
            sig_fig = np.floor(-data_min / floor10)
            if sig_fig < 3:
                ymin = -floor10 * 3
            else:
                ymin = -floor10 * 10

        return ymin


    @staticmethod
    def dynamic_max(data_max, yscale):
        """Get an axes upper limit (for y) based on data value.

        The upper limit is the next power of 10, or 3 * power of 10, above
        the max (For linear, the next N * power of 10.).

        Args:
          data_max: the maximum of the data (could be integers or floats)
        """

        floor10 = 10**(np.floor(np.log10(data_max)))
        sig_fig = np.ceil(data_max / floor10)
        if yscale == 'linear':
            sig_fig = np.floor(data_max / floor10)
            ymax = floor10 * (sig_fig + 1)
        elif sig_fig < 3:
            ymax = floor10 * 3
        else:
            ymax = floor10 * 10

        return np.maximum(ymax, 0)


    @property
    def xlim(self):
        """Returns the xlim, requires xedges."""

        if self._xlim is None or self._xlim == 'default':
            return np.min(self._xedges), np.max(self._xedges)

        return self._xlim

    @xlim.setter
    def xlim(self, limits):
        """Sets xlim."""

        if limits is not None and limits != 'default' and len(limits) != 2:
            raise PlottingError('xlim should be length 2: {}'.format(limits))
        self._xlim = limits


    @property
    def ylim(self):
        """Returns ylim, requires yscale, ydata."""

        if self._ylim is None or self._ylim == 'default':
            if self.yscale is None:
                raise PlottingError('No y scale and no axes defined,'
                                    ' requires at least one of them')

            min_ind = np.argmin(np.abs(self._ydata[self._ydata != 0]))
            delta_y = np.abs(self._ydata - self._ydata[min_ind])
            min_delta_y = np.min(delta_y[delta_y > 0])

            data_min = np.min(self._ydata)
            if self.yscale == 'linear':
                ymin = 0
            elif self.yscale == 'log' and data_min < 0:
                raise PlottingError('Cannot plot negative values on a log ' +
                                    'scale; use symlog scale')
            elif self.yscale == 'symlog' and data_min >= 0:
                ymin = 0
            else:
                ymin = self.dynamic_min(data_min, min_delta_y)

            data_max = np.max(self._ydata)
            ymax = self.dynamic_max(data_max, self.yscale)
            return ymin, ymax

        return self._ylim


    @ylim.setter
    def ylim(self, limits):
        """Sets ylim."""

        if limits is not None and limits != 'default' and len(limits) != 2:
            raise PlottingError('ylim should be length 2: {}'.format(limits))
        self._ylim = limits


    @property
    def linthreshy(self):
        """Returns linthreshy, requires ydata."""

        min_ind = np.argmin(np.abs(self._ydata[self._ydata != 0]))
        delta_y = np.abs(self._ydata - self._ydata[min_ind])
        return np.min(delta_y[delta_y > 0])
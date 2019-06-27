# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 15:38:11 2017

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from scipy.signal import firwin, cheby1, filtfilt, lfilter

def decimate(x, q, n=None, ftype='iir', axis=-1, zero_phase=False):
    """
    Slightly improved version of scipy.signal.decimate to allow for zero-phase filtering.
    
    Downsample the signal by using a filter.

    By default, an order 8 Chebyshev type I filter is used.  A 30 point FIR
    filter with hamming window is used if `ftype` is 'fir'.

    Parameters
    ----------
    x : ndarray
        The signal to be downsampled, as an N-dimensional array.
    q : int
        The downsampling factor.
    n : int, optional
        The order of the filter (1 less than the length for 'fir').
    ftype : str {'iir', 'fir'}, optional
        The type of the lowpass filter.
    axis : int, optional
        The axis along which to decimate.
    zero_phase : bool
        If True, filtfilt is used instead of lfilter to perform non-causal filtering, eliminating the phase shift.

    Returns
    -------
    y : ndarray
        The down-sampled signal.

    See also
    --------
    resample

    """

    if not isinstance(q, int):
        raise TypeError("q must be an integer")

    if n is None:
        if ftype == 'fir':
            n = 30
        else:
            n = 8

    if ftype == 'fir':
        b = firwin(n + 1, 1. / q, window='hamming')
        a = [1.]
    else:
        b, a = cheby1(n, 0.05, 0.8 / q)

    if zero_phase:
        y = filtfilt(b, a, x, axis=axis) ## Added code
    else:
        y = lfilter(b, a, x, axis=axis)

    sl = [slice(None)] * y.ndim
    sl[axis] = slice(None, None, q)
    return y[sl]

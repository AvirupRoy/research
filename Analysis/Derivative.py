# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 14:23:45 2017

@author: wisp10
"""

import numpy as np
from scipy.signal import savgol_filter

def savgolDerivative(x,y, window_length, polyorder, derivative=1):
    '''Compute nth derivative from irregularly spaced x,y data, using a
    Savitzky Golay filter of order *polyorder* with length *window_length*.
    '''
    i = len(x)
    s = np.argsort(x)
    xu = np.linspace(np.min(x), np.max(x), i)
    yu = np.interp(xu, x[s], y[s])
    du = savgol_filter(yu, window_length, polyorder, deriv=derivative, delta=xu[1]-xu[0])
    deriv = np.interp(x, xu, du)
    return deriv

def savgolDerivativeRegular(x,y, window_length, polyorder, derivative=1):
    '''Compute nth derivative from regular spaced y(x) data.'''
    delta = x[1]-x[0]    
    s = np.argsort(x) # Sorted to ensure ascending
    yu = y[s]
    du = savgol_filter(yu, window_length, polyorder, deriv=derivative, delta=delta)
    deriv = np.empty_like(du)
    deriv[s] = du
    return du

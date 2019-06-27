# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 11:40:34 2016

@author: wisp10
"""

import h5py as hdf
import matplotlib.pyplot as mpl
import numpy as np
fileName = 'test.h5'
hdfFile = hdf.File(fileName, mode='r')
d = hdfFile['rawData']
print "Shape:", d.shape
print "Size: {:,}".format(d.size), 'samples'
print "Compression:", d.compression
print "Options:", d.compression_opts
print "Chunk size:", d.chunks


channel = 0

y = d[channel,-1500000:].astype(np.float32)/10000.


def fitFunction(t, A, f, phase, O):
    y = A*np.sin(2*np.pi*f*t+phase)+O
    return y

from scipy.optimize import curve_fit
nSamples = len(y)
dt = 1./200000.
x = np.arange(0, nSamples) * dt
guess = [0.5*(np.max(y)-np.min(y)), 4E3, np.deg2rad(300.), np.mean(y)]
fit,pcov = curve_fit(fitFunction, x[:10000], y[:10000], p0=guess)
mpl.figure()
mpl.subplot(2,1,1)
mpl.plot(x,y,'-', label='data')
yfit =fitFunction(x,*fit)
mpl.plot(x, yfit, '-', label='fit')
#mpl.plot(x,fitFunction(x,*guess), '-', label='guess')
mpl.legend()
mpl.subplot(2,1,2)
mpl.plot(x,y-yfit, '.')
mpl.show()

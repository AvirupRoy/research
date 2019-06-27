# -*- coding: utf-8 -*-
"""
Created on Thu Oct 05 23:10:14 2017

@author: wisp10
"""

import numpy as np
import h5py as hdf
import matplotlib.pyplot as mpl

class Spectrum(object):
    def __init__(self, hdfRoot):
        self.f = hdfRoot[u'Frequency'].value
        self.psd = hdfRoot[u'PSD'].value
        self.psdStd = hdfRoot[u'PSD_std'].value
        try:
            self.psdSkew = hdfRoot[u'PSD_skew'].value
            self.psdKurtosis = hdfRoot[u'PSD_kurtosis'].value
        except KeyError:
            self.psdSkew = None
            self.psdKurtosis = None
        self.Times = hdfRoot[u'Times'].value
        self.Vmax = hdfRoot[u'Vmax'].value
        self.Vmean = hdfRoot[u'Vmean'].value
        self.Vmin = hdfRoot[u'Vmin'].value
        self.Vstd = hdfRoot[u'Vstd'].value
        self.device = hdfRoot.attrs['device']
        self.channel = hdfRoot.attrs['channel']
        self.range = hdfRoot.attrs['range']
        
    def plot(self, **kwargs):
        mpl.loglog(self.f, 1E12*np.sqrt(self.psd)/100E3, **kwargs)
        

class NoiseSpectraReader(object):
    def __init__(self, fileName):
        hdfFile = hdf.File(fileName, mode='r')
        self.nSpectra = len(hdfFile.keys())
        self.hdfFile = hdfFile
        
    def spectrum(self, i):
        return Spectrum(self.hdfFile['/Data%06d' % i])
        
    def __len__(self):
        return self.nSpectra
        
    def __getitem__(self, key):
        if isinstance(key, slice):
           (start, step, stop) = key.indices(self.nSpectra)
           return [self[i] for i in xrange(start, step, stop)]
        else:
            if key < 0 : #Handle negative indices
                key += len( self )
            if key < 0 or key >= self.nSpectra:
                raise IndexError
        return self.spectrum(key)

    def __iter__(self):
        for i in range(0, self.nSpectra):
          yield self.spectrum(i)
        

if __name__ == '__main__':
#    import matplotlib.pyplot as mpl
    path = 'D:\\Users\\Runs\\G4C\\Noise\\'
    fileName = 'TES1_Noise_71.168mK_Bias1.5180V_Coil0.0000V_20171028_113055.h5'
    
    spectra = NoiseSpectraReader(path+fileName)
    for spectrum in spectra:
        spectrum.plot()
    mpl.xlabel('f (Hz)')
    mpl.ylabel(u'$V_n$ (nV/$\\sqrt{Hz}$)')
    mpl.show()
    
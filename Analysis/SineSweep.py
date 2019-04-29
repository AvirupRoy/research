# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 18:09:05 2017

@author: wisp10
"""

import h5py as hdf
import matplotlib.pyplot as mpl
import numpy as np
import warnings
from Analysis.HkImport import HkImporter

class SineSweep(object):
    def __init__(self, fileName):
        f = hdf.File(fileName, 'r')
        attrs = f.attrs
        self.program = attrs['Program']
        self.version = attrs['Version']
        self.sample = attrs['Sample']
        self.deviceName = attrs['deviceName']
        self.comment = attrs['Comment']
        self.sampleRate = attrs['sampleRate']
        self.offset = attrs['offset']
        self.amplitude = attrs['amplitude']
        self.fStart = attrs['fStart']
        self.fStop = attrs['fStop']
        self.fSteps = attrs['fSteps']
        self.settlePeriods = attrs['settlePeriods']
        self.measurePeriods = attrs['measurePeriods']
        self.minSettleTime = attrs['minSettleTime']
        self.minMeasureTime = attrs['minMeasureTime']
        self.aoChannel = attrs['aoChannel']
        self.aoRangeMin = attrs['aoRangeMin']
        self.aoRangeMax = attrs['aoRangeMax']
        self.aiChannel = attrs['aiChannel']
        self.aiRangeMin = attrs['aiRangeMin']
        self.aiRangeMax = attrs['aiRangeMax']
        self.aiTerminalConfig = attrs['aiTerminalConfig']
        self.startTimeLocal = attrs['StartTimeLocal']
        self.stopTimeLocal = attrs['StopTimeLocal']
        self.startTimeUTC = attrs['StartTimeUTC']
        self.stopTimeUTC = attrs['StopTimeUTC']
        
        sweep = f['Sweep']
        self.Vmin = sweep['Vmin'].value
        self.Vmax = sweep['Vmax'].value
        if np.any(self.Vmin > self.Vmax):
            warnings.warn('Vmin and Vmax were swapped in the file.')
            self.Vmin, self.Vmax = self.Vmax, self.Vmin
        self.f = sweep['f'].value
        self.X = sweep['X'].value
        self.Y = sweep['Y'].value
        self.t = sweep['t'].value
        self.Vdc = sweep['dc'].value
        self.TF = (self.X + 1j * self.Y)/self.amplitude
        if np.any(self.overload()):
            warnings.warn('There are AI overloads in this file.')
        self.label = None
        
        if 'HK' in f.keys():
            self.hk = HkImporter(f['HK'])
        else:
            self.hk = None
        
        
        self.adrR = f['AdrResistance'].value
        self.adrTime = f['AdrResistance_TimeStamps'].value
        
    def plotPolar(self, **kwargs):
        return mpl.plot(np.real(self.TF), np.imag(self.TF), '.-', **kwargs)
        
    def overload(self):
        return (self.Vmin <= self.aiRangeMin) | (self.Vmax >= self.aiRangeMax)
        
    def plotRPhi(self, axes=None, **kwargs):
        if axes is None:
            fig, axes = mpl.subplots(2,1, sharex=True)
        if self.label is not None and not 'label' in kwargs.keys():
            kwargs['label'] = self.label
        
        axes[0].loglog(self.f, np.abs(self.TF), **kwargs)
        axes[0].set_ylabel(u'$R$')
        phi = np.rad2deg(np.unwrap(np.angle(self.TF, deg=False)))
        axes[1].semilogx(self.f, phi, **kwargs)
        axes[1].set_ylabel(u'$\\Phi$ (deg)')
        return axes
        
    def plotXY(self, axes=None, **kwargs):
        if axes is None:
            fig, axes = mpl.subplots(2,1, sharex=True)

        if self.label is not None and not 'label' in kwargs.keys():
            kwargs['label'] = self.label
        
        axes[0].semilogx(self.f, np.real(self.TF), **kwargs)
        axes[0].set_ylabel(u'$X$')
        axes[1].semilogx(self.f, np.imag(self.TF), **kwargs)
        axes[1].set_ylabel(u'$Y$')
        return axes
        
    def normalizeWith(self, ssRef):
        assert np.all(ssRef.f == self.f)
        self.TF /= ssRef.TF
       

if __name__ == '__main__':
#    f = hdf.File(fileName, 'r')
#    from Utility import generateHdfImportCode
#    generateHdfImportCode(f)
#    generateHdfImportCode(f['Sweep'])
    path = 'D:\\Users\\Runs\\G4C\\TF\\'
    fileName = path+'TES1_20171024_230500.h5'
    fileNames = ['TES1_20171027_154619.h5', 'TES1_20171027_155517.h5', 'TES1_20171027_163631.h5', 'TES1_20171027_163943.h5', 'TES1_20171027_164330.h5', 'TES1_20171027_164759.h5', 'TES1_20171027_165930.h5']
    fileNames = ['TES1_20171027_200112.h5', 'TES1_20171027_200429.h5', 'TES1_20171027_200247.h5']

    path = 'D:\\Users\\Runs\\G5C\\TF\\'
    fileNames = ['TES1_20180326_214310.h5', 'TES1_20180326_213552.h5']
    
    axes = None
    for fileName in fileNames:
        ss = SineSweep(path+fileName)  
        #mpl.figure()
        ss.plotPolar()
        #axes = ss.plotRPhi(axes)
        print('Amplitude:', ss.amplitude)
        #mpl.semilogx(ss.t-ss.t[0], ss.Vdc)
        
    mpl.show()
    
    #mpl.plot(ss.f, ss.X)
    


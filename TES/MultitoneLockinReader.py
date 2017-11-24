# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 10:44:24 2017

@author: wisp10
"""
import h5py as hdf
import numpy as np
import matplotlib.pyplot as mpl
import warnings

class LockinTrace(object):
    def __init__(self, hdfRoot, sampleRate, excitationPhase, filterBandwidth, filterOrder):
        a = hdfRoot.attrs
        self.fRef = a['fRef']
        self.sampleRate = sampleRate
        self.dt = 1./sampleRate
        self.thetaRef = excitationPhase
        self.filterBw = filterBandwidth
        self.filterOrder = filterOrder
        self.chunkSize = a['chunkSize']
        self.numberOfDatasets = a['numberOfDataSets']
        self.amplitudes = hdfRoot['A'].value
        self.data = hdfRoot['data_%06d' % 0]
        self.tGenerated0 = hdfRoot['tGenerated'][0]
        self.tGenerated = hdfRoot['tGenerated'].value
        self.tAcquired = hdfRoot['tAcquired'].value

    @property
    def t(self):
        ts = self.tGenerated0 + np.arange(0, len(self.data)) * self.dt
        return ts
        
    def plot(self):
        t = self.t
        mpl.plot(t, np.real(self.data),label='real')
        mpl.plot(t, np.imag(self.data),label='imag')
    
class MultitoneLockinReader(object):
    def __init__(self, fileName):
        f = hdf.File(fileName, 'r')
        a = f.attrs
        program = a['Program']
        if program != 'MultitoneLockin':
            warnings.warn('Unrecognized program:%s', program )
        self.version = a['Version']
        self.sample = a['Sample']
        self.comment = a['Comment']
        self.startTimeLocal = a['StartTimeLocal']
        self.startTimeUTC = a['StartTimeUTC']
        self.stopTimeLocal = a['StopTimeLocal']
        self.stopTimeUTC = a['StopTimeUTC']
        self.sampleRate = a['sampleRate']
        self.inputDecimation = a['inputDecimation']
        self.offset = a['offset']
        self.deviceName = a['deviceName']
        self.aoChannel = a['aoChannel']
        self.aoRangeMin = a['aoRangeMin']
        self.aoRangeMax = a['aoRangeMax']
        self.aiChannel = a['aiChannel']
        self.aiRangeMin = a['aiRangeMin']
        self.aiRangeMax = a['aiRangeMax']
        self.rawCount = a['rawCount']
        self.aiTerminalConfig = a['aiTerminalConfig']
        self.excitationFrequencies = a['excitationFrequencies']
        self.excitationAmplitudesStart = a['excitationAmplitudes']
        self.excitationPhases = a['excitationPhases']
        self.liaFilterBws = a['lockinFilterBandwidths']
        self.liaFilterOrders = a['lockinFilterOrders']
        self.outputSampleRates = a['outputSampleRates']
        self.rampRate = a['rampRate']
        n = len(self.excitationFrequencies)
        assert n == len(self.excitationAmplitudesStart)
        assert n == len(self.excitationPhases)
        assert n == len(self.liaFilterBws)
        assert n == len(self.liaFilterOrders)
        self.nFrequencies = n
        self.tGenerated = f['tGenerated'].value
        self.tAcquired = f['tAcquired'].value
        self.Vdc = f['Vdc'].value
        self.Vmax = f['Vmax'].value
        self.Vmin = f['Vmin'].value
        self.Vrms = f['Vrms'].value
        self.offset = f['offset'].value
        self._hdfRoot = f
        
    def trace(self, i):
        '''
        Return the time trace for the ith frequency.
        '''
        if i < 0 or i >= self.nFrequencies:
            return IndexError
        root = self._hdfRoot['F_%02d' % i]
        return LockinTrace(root, 
                           sampleRate=self.outputSampleRates[i],
                           excitationPhase=self.excitationPhases[i],
                           filterBandwidth=self.liaFilterBws[i],
                           filterOrder=self.liaFilterOrders[i])

    def __len__(self):
        return self.nFrequencies
        
    def __getitem__(self, key):
        if isinstance(key, slice):
           (start, step, stop) = key.indices(self.nFrequencies)
           return [self[i] for i in xrange(start, step, stop)]
        else:
            if key < 0 : #Handle negative indices
                key += len( self )
            if key < 0 or key >= self.nFrequencies:
                raise IndexError
        return self.trace(key)

    def __iter__(self):
        for i in range(0, self.nFrequencies):
            try:
                s = self.trace(i)
            except IOError as e:
                print('Unable to load trace:', e)
                s = None
            yield s
                           

if __name__ == '__main__':
    fileName = 'None_20171122_145434.h5'
    mtl = MultitoneLockinReader(fileName)
    mpl.figure()
    for i in range(10):
        t = mtl.trace(i)
        t.plot()
    
    mpl.figure()
    mpl.plot(mtl.tGenerated, mtl.Vmax, '-')
    mpl.plot(mtl.tGenerated, mtl.Vmin, '-')
    mpl.plot(mtl.tGenerated, mtl.Vdc, '-')
    mpl.show()
    f = hdf.File(fileName, 'r')
    
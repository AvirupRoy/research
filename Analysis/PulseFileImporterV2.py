# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 15:33:12 2018

@author: wisp10
"""
from __future__ import print_function, division

import h5py as hdf
import numpy as np
from Analysis.HkImport import HkImporter
import warnings

class TesInfo(object):
    def __init__(self, hdfRoot):
        a = hdfRoot.attrs
        self.tesId = a['tes']
        self.fbC = a['fbC']
        self.fbR = a['fbR']
        self.bias = a['bias']
        self.normalBias = a['normalBias']
        self.ivFbC = a['ivFbC']
        self.ivFbR = a['ivFbR']
        self.recordIv = a['recordIv']
        self.resetEveryPulseCombo = a['resetEveryPulseCombo']
    def __str__(self):
        s = '{0} Vb={1} V (driven normal @ {2} V)'.format(self.tesId, self.bias, self.normalBias)
        return s
        
class AcquistionInfo(object):
    def __init__(self, hdfRoot):
        a = hdfRoot.attrs
        self.aiTerminalConfig = a['aiTerminalConfig']
        self.recordLength = 1E-3*a['recordLength']
        self.decimation = int(a['decimation'])
        self.device = a['device']
        self.aiChannel = a['aiChannel']
        self.triggerTerminal = a['triggerTerminal']
        self.sampleRate = 1E3*a['sampleRate']
        self.preTriggerFraction = 1E-2*a['preTrigger']
        self.preTriggerSamples = int(self.preTriggerFraction*self.sampleRate*self.recordLength)
    def __str__(self):
        s = 'Input channel {0}/{1} ({2}) @ fs={3} kS/s'.format(self.device, self.aiChannel, self.aiTerminalConfig, 1E-3*self.sampleRate)
        return s
        
class LaserDiodePulserInfo(object):
    def __init__(self, hdfRoot):
        a = hdfRoot.attrs
        self.fgVisa = a['fgVisa']
        '''VISA ID of function generator'''        
        
        self.lowLevel = a['lowLevel']
        '''Laser diode low drive-level (V)'''
        
        self.burstPeriod = a['burstPeriod']
        '''Burst period (in seconds)'''
        
        self.templatePulsePeriod = a['templatePulsePeriod']
        '''Period (in seconds) of template pulses. Usually constant throughout file, but might change in the future.'''
        
        self.templatePulseWidth = a['templatePulseWidth']
        '''Width (in seconds) of template pulses. Usually constant throughout file, but might change in the future.'''
        
        self.templateHighLevel = a['templateHighLevel']
        '''Laser diode drive high level for template pulses.  Usually constant throughout file, but might change in the future'''
        
        self.baselineLength = a['baselineLength']
        '''Length (in seconds) of the baseline (i.e. no pulses) record in each trace.'''
        
class IvCurve(object):
    def __init__(self, hdfRoot):
        a = hdfRoot.attrs
        self.nHold0 = a['nHold0']
        self.nHold1 = a['nHold1']
        self.nHold2 = a['nHold2']
        self.nRamp1 = a['nRamp1']
        self.nRamp2 = a['nRamp2']
        self.sampleRate = a['sampleRate']
        self.slewRate = a['slewRate']
        self.VbiasNormal = a['VbiasNormal']
        self.VbiasFinal = a['Vbias']
        self.tStart = a['tStart']
        self.tStop = a['tStop']
        self.Vsquid = hdfRoot['Vsquid'].value
        
    def analyze(self, Rsq, Rb, Rs):
        Vsq = self.Vsquid
        offset = np.mean(Vsq[int(0.5*self.nHold0):self.nHold0-5])
        Vsq -= offset
        #Ites = Vsq/Rsq

        self.VsquidFinal = np.mean(Vsq[-self.nHold2+1:])
        self.ItesFinal = self.VsquidFinal / Rsq
        self.IbiasFinal = self.VbiasFinal / Rb
        IshuntFinal = self.IbiasFinal - self.ItesFinal
        self.VtesFinal = Rs * IshuntFinal
        self.RtesFinal = self.VtesFinal/self.ItesFinal
        self.PtesFinal = self.ItesFinal * self.VtesFinal
        return self.RtesFinal, self.ItesFinal

class PulseImporter(object):
    '''Importer for (laser) pulse record files.'''
    def __init__(self, fileName):
        '''Import HDF5 (laser) pulse record file.'''
        f = hdf.File(fileName, 'r')
        self._hdfFile = f
        a = f.attrs
        self.program = a['Program']
        if not self.program in ['PulseCollector']:
            warnings.warn('This file may not have been produced by the PulseCollector program')
        self.programVersion = a['Version']
        if not self.programVersion in ['0.2']:
            warnings.warn('This class reads file from program version 0.2 onward.')
        self.decimationMode = a['Decimation']
        self.sample = a['Sample']
        self.startTime = a['StartTime']
        self.startTimeLocal = a['StartTimeLocal']
        self.startTimeUTC = a['StartTimeUTC']
        self.stopTime = a['StopTime']
        self.stopTimeLocal = a['StopTimeLocal']
        self.stopTimeUTC = a['StopTimeUTC']
        
        self.ldPulseChangeTimes = f['pulseChangeTimes'].value
        
        self.ldPulseHighLevels = f['pulseHighLevels'].value
        '''Laser diode high level for each trace'''

        self.ldPulsePeriods = f['pulsePeriods'].value
        '''Laser diode pulse periods for each trace'''
        
        self.ldPulseWidths = f['pulseWidths'].value
        '''Laser diode pulse width for each trace'''
        
        self.pulseCounts = f['pulseCounts'].value
        '''Pulse counts for each trace'''
        
        self.pulseTypes = f['pulseTypes'].value
        '''Pulse types for each trace.'''
        
        self.traceCount = len(self.pulseTypes)
        '''Number of traces in file.'''
        
        # Check that all groups are actually there
        iOk = np.asarray(['Sequence%06d' % i in f.keys() for i in range(self.traceCount)])
        nBad = np.count_nonzero(~iOk)
        if nBad > 0:
            warnings.warn('Missing group(s) for %d of %d traces: %s' % (nBad, self.traceCount, str(np.where(~iOk)[0])))
            self.ldPulseChangeTimes = self.ldPulseChangeTimes[iOk]
            self.ldPulseHighLevels = self.ldPulseHighLevels[iOk]
            self.ldPulseWidths = self.ldPulseWidths[iOk]
            self.pulseCounts = self.pulseCounts[iOk]
            self.pulseTypes = self.pulseTypes[iOk]
            self.traceCount = np.count_nonzero(iOk)
            
        self._mapping = np.where(iOk)[0]
        '''Map to support look-up of traces when there are missing traces'''
        
        self.tes = TesInfo(f['TES'])
        '''Details on the TES and SQUID feeback loop.'''        
        
        self.acquisition = AcquistionInfo(f['Acquisition'])
        '''Details on the data acquistion'''
        
        self.ldPulser = LaserDiodePulserInfo(f['LaserDiodePulser'])
        self.iv = IvCurve(f['IV'])
        self.hk = HkImporter(f['HK'])
        '''Housekeeping data recorded during this dataset'''
        
        self.sampleRate = self.acquisition.sampleRate / self.acquisition.decimation
        '''Sample rate of the data (after decimation) - identical for each trace'''
        
        self.dt = 1./self.sampleRate
        '''Time step of the trace data  (after decimation)'''
        #self.pretriggerSamples = int(self.acquisition.preTriggerSamples / self.acquisition.decimation)
        
        self.traceLength = self.ldPulser.burstPeriod
        '''Length of each trace (s)'''
        
        self.pulseDelay = 0.1
        '''Time of first pulse in traces'''
        
        self.iTemplate = np.where(self.pulseTypes == 0)[0]
        '''Indices of all the template pulse traces'''
        
        self.iBaseline = np.where(self.pulseTypes == 1)[0]
        '''Indices of all baseline traces'''
        
        self.iTest     = np.where(self.pulseTypes == 2)[0]
        '''Indices of all test pulse traces'''
        
        try:
            self.sampleDelay = self._hdfFile.attrs['sampleDelay']
            '''Delay due to the FIR decimation filter'''
        except KeyError: # Sample delay not stored in data file. Using numbers for DecimateFast FIR half-band filter.
            self.sampleDelay = {1: 0, 2: 43, 4:129, 8: 301, 16: 645, 32: 1333}[self.acquisition.decimation]
        self._traceStartTimes = None
        self._prePulseMeans = None
        self._prePulseRmss = None
        
    def __len__(self):
        '''Return the number of traces in this file.'''
        return self.traceCount
        
    def trace(self, n):
        '''Return the nth trace from the file.'''
        print('n=',n)
        return Trace(self._hdfFile['Sequence%06d' % self._mapping[n]], self.sampleRate, self.pulseDelay, self.sampleDelay, pp = self.ldPulsePeriods[n], pw = self.ldPulseWidths[n], pc = self.pulseCounts[n], hl = self.ldPulseHighLevels[n])
        
    def __getitem__(self, key):
        '''Return a trace or set of traces from the file. Supports fancy indexing.'''
        if isinstance(key, slice):
           (start, step, stop) = key.indices(self.traceCount)
           return [self[i] for i in xrange(start, step, stop)]
        else:
            if key < 0 : #Handle negative indices
                key += len( self )
            if key < 0 or key >= self.traceCount:
                raise IndexError
        return self.trace(key)

    def __iter__(self):
        for i in range(self.traceCount):
            try:
                s = self.trace(i)
            except IOError as e:
                print('Unable to load sweep:', e)
                s = None
            yield s
            
    @property
    def traceStartTimes(self):
        if self._traceStartTimes is None:
            self._traceStartTimes = np.asarray([trace.startTime for trace in self])
        return self._traceStartTimes
        
    def _calcPrePulseBaselines(self):
        means = []; rmss = []
        for trace in self:
            mean, rms = trace.prePulseBaseline()
            means.append(mean); rmss.append(rms)
        self._prePulseMeans = np.asarray(means)
        self._prePulseRmss = np.asarray(rmss)
        
    @property
    def prePulseMeans(self):
        if self._prePulseMeans is None:
            self._calcPrePulseBaselines()
        return self._prePulseMeans

    @property
    def prePulseRmss(self):
        if self._prePulseRmss is None:
            self._calcPrePulseBaselines()
        return self._prePulseRmss
    
    def __str__(self):
        s = ''
        return s
        
        
class Trace(object):
    def __init__(self, hdfGroup, sampleRate, pulseDelay, sampleDelay, pp, pw, pc, hl):
        self.nSamples = hdfGroup['Vsquid'].shape[0]
        try:
            self.chunkTimes = hdfGroup['chunkTimes'].value
        except KeyError:
            warnings.warn('Trace has no chunkTimes:%s' % str(hdfGroup.name))
            self.chunkTimes = np.asarray([np.nan])
        self.sampleRate  = sampleRate
        self.dt = 1./sampleRate
        self.pulseDelay = pulseDelay
        self.sampleDelay = sampleDelay
        self.ldPulseWidth = pw
        self.ldPulsePeriod = pp
        self.ldPulseCount = pc
        self.ldHighLevel = hl
        self.length = self.nSamples / self.sampleRate
        self.startTime = self.chunkTimes[-1] - self.length
        self._hdfGroup = hdfGroup
        self._Vsquid = None
        self.firstPulsePosition = int(self.sampleDelay + self.pulseDelay*self.sampleRate)
        self.lastPulsePosition = int(self.firstPulsePosition + (self.ldPulseCount-1) * self.ldPulsePeriod * self.sampleRate)
        self.samplesPerPeriod = int(self.ldPulsePeriod*self.sampleRate)
        
    @property
    def Vsquid(self):
        '''The actual data. Using lazy-evaluation here so other operations
        are possible without reading in all the datasets.'''
        if self._Vsquid is None:
            self._Vsquid = self._hdfGroup['Vsquid'].value
        return self._Vsquid

    @property        
    def pulsePositions(self):
        '''Return the positions of all pulses (in samples)'''
        return self.sampleDelay + (self.pulseDelay + np.arange(self.ldPulseCount) * self.ldPulsePeriod) * self.sampleRate
       
    def prePulseBaseline(self):
        '''Return mean and rms of pre-pulse baseline'''
        V = self.Vsquid[self.sampleDelay:self.firstPulsePosition]
        return np.mean(V), np.std(V)
        
    def postPulseBaseline(self):
        '''Return mean and rms of post-pulse baseline'''
        V = self.Vsquid[self.lastPulsePosition+self.samplesPerPeriod:]
        return np.mean(V), np.std(V)
        
    @property
    def t(self):
        return np.arange(self.nSamples)*self.dt
        
    def plot(self, maxPoints=5E5):
        skip = max(1, int(self.nSamples / maxPoints))
        mpl.plot(self.t[::skip], self.Vsquid[::skip])
        
    def __str__(self):
        s = 'Trace with {0} laser pulses (pw={1} s, {2} V) at {3} s intervals'.format(self.ldPulseCount, self.ldPulseWidth, self.ldHighLevel, self.ldPulsePeriod)
        return s
        
        
if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    cooldown = 'G5C'
    path = 'D:\\Users\\Runs\\{0}\\Pulses\\'.format(cooldown)
    fileName = path+'TES1_Pulses_20180301_121547.h5'
    #fileName = path+'TES1_Pulses_20180301_133923.h5'
    pulses = PulseImporter(fileName)
    print(pulses.tes)
    print(pulses.acquisition)
    print('Number of traces:', len(pulses))
    print('Sample rate (decimated): {0} kS/s'.format(1E-3*pulses.sampleRate) )
    print('Decimation: {0}'.format(pulses.acquisition.decimation))
    tesId = pulses.tes.tesId
    from Analysis.G4C.MeasurementDatabase import obtainTes
    tes = obtainTes(cooldown, tesId)
    Rfb = 10E3 # This should be in the file, but currently isn't
    Rsq = tes.Rsquid(Rfb)
    pulses.iv.analyze(Rsq=Rsq, Rb = tes.Rbias, Rs = tes.Rshunt)
    print('TES bias point: Rtes=%.3f mOhm, Ites=%.3f uA, Ptes=%.3f pW' % (pulses.iv.RtesFinal*1E3, pulses.iv.ItesFinal*1E6, pulses.iv.PtesFinal*1E12))

    if False:    
        fig, ax = mpl.subplots(3,1,sharex=True)
        titles = ['Baseline', 'Template pulses', 'Test pulses']
        for i, pulseSet in enumerate([pulses.iBaseline, pulses.iTemplate, pulses.iTest]):
            for j in pulseSet[0:1]:
                trace = pulses[j]
                ax[i].plot(trace.t, trace.Vsquid, '-', label=str(trace))
                ax[i].set_ylabel('Vsquid (V)')
                ax[i].set_title(titles[i])
                ax[i].legend()
    
        ax[-1].set_xlabel('t (s)')
        mpl.show()
        
    t0s = pulses.traceStartTimes
    means = pulses.prePulseMeans

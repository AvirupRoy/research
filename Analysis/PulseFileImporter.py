# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 15:33:12 2018

@author: wisp10
"""
from __future__ import print_function, division

import h5py as hdf
import numpy as np
from Analysis.HkImport import HkImporter
from Utility.RunningStats import RunningStats

def halfCosWindow(length, halfCosFraction):
    window = np.ones(length)
    halfCosLength = int(halfCosFraction*length)
    xSeries = np.arange(2*halfCosLength)/float(2*halfCosLength-1)
    cosFunction = 0.5*(1 - np.cos(2*np.pi*xSeries))
    window[:halfCosLength] = cosFunction[:halfCosLength]
    window[-1*halfCosLength:] = cosFunction[-1*halfCosLength:]
    return window
    

eV = 1.602176620898E-19

class TesInfo(object):
    def __init__(self, hdfRoot):
        a = hdfRoot.attrs
        self.fbC = a['fbC']
        self.fbR = a['fbR']
        self.bias = a['bias']
        self.normalBias = a['normalBias']
        self.ivFbC = a['ivFbC']
        self.ivFbR = a['ivFbR']
        self.recordIv = a['recordIv']
        self.tesId = a['tes']
        self.resetEveryPulseCombo = a['resetEveryPulseCombo']
        
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
        
class LaserDiodePulserInfo(object):
    def __init__(self, hdfRoot):
        a = hdfRoot.attrs
        try:
            self.pulsePeriod = 1E3* a['pulsePeriod']
        except KeyError:
            self.templatePulsePeriod = 1E-3*a['templatePulsePeriod']
            self.testPulsePeriod = 1E-3*a['testPulsePeriod']
            if self.templatePulsePeriod == self.testPulsePeriod:
                self.pulsePeriod = self.templatePulsePeriod
        self.testHighLevel = a['testHighLevel']
        self.fgVisa = a['fgVisa']
        self.templateHighLevel = a['templateHighLevel']
        self.lowLevel = a['lowLevel']
        self.testPulseWidth = 1E-6*a['testPulseWidth']
        self.templatePulseWidth = 1E-6*a['templatePulseWidth']
        
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
    def __init__(self, fileName):
        f = hdf.File(fileName, 'r')
        self._hdfFile = f
        a = f.attrs
        self.program = a['Program']
        self.version = a['Version']
        self.decimationMode = a['Decimation']
        self.sample = a['Sample']
        self.startTime = a['StartTime']
        self.startTimeLocal = a['StartTimeLocal']
        self.startTimeUTC = a['StartTimeUTC']
        self.pulseCount = a['pulseCount']
        self.stopTime = a['StopTime']
        self.stopTimeLocal = a['StopTimeLocal']
        self.stopTimeUTC = a['StopTimeUTC']
        
        self.pulseEndTimes = f['pulseEndTimes'].value
        self.ldPulseHighLevels = f['ldPulseHighLevels'].value
        self.ldPulseWidths = f['ldPulseWidths'].value
        self.pulseTypes = f['pulseTypes'].value
        
        self.tes = TesInfo(f['TES'])
        self.acquisition = AcquistionInfo(f['Acquisition'])
        self.ldPulser = LaserDiodePulserInfo(f['LaserDiodePulser'])
        self.iv = IvCurve(f['IV'])     
        self.hk = HkImporter(f['HK'])
        
        self.sampleRate = self.acquisition.sampleRate / self.acquisition.decimation
        self.dt = 1./self.sampleRate
        self.recordLength = int(self.sampleRate*self.acquisition.recordLength)
        self.df = self.sampleRate/self.recordLength
        self.pretriggerSamples = int(self.acquisition.preTriggerSamples / self.acquisition.decimation)
        
        self.templatePulseEnergy = 1.
        self._baselines = None
        self._preTriggerNoise = None
        self._window = None
        self._waf = 1.
        
        self.iTemplate = np.where(self.pulseTypes == 0)[0]
        self.iBaseline = np.where(self.pulseTypes == 1)[0]
        self.iTest     = np.where(self.pulseTypes == 2)[0]
        
    def __len__(self):
        return self.pulseCount
        
    def pulse(self, i):
        return Pulse(self._hdfFile['Pulse%06d' % i], self.sampleRate, self.pretriggerSamples)
        
    def __getitem__(self, key):
        if isinstance(key, slice):
           (start, step, stop) = key.indices(self.pulseCount)
           return [self[i] for i in xrange(start, step, stop)]
        else:
            if key < 0 : #Handle negative indices
                key += len( self )
            if key < 0 or key >= self.pulseCount:
                raise IndexError
        return self.pulse(key)

    def __iter__(self):
        for i in range(0, self.pulseCount):
            try:
                s = self.pulse(i)
            except IOError as e:
                print('Unable to load sweep:', e)
                s = None
            yield s

    @property            
    def baselines(self):
        if self._baselines is None:
            self._baselines = np.asarray([pulse.preTriggerBaseline() for pulse in self])
        return self._baselines

    @property
    def preTriggerNoise(self):
        if self._preTriggerNoise is None:
            self._preTriggerNoise = np.asarray([pulse.preTriggerNoise() for pulse in self])
        return self._preTriggerNoise
        
    def templatePulseAverage(self, individualBaseline = False, iGood = None, iBad = None):
        if iGood is None:
            iGood = self.iTemplate
        if iBad is not None:
            iGood = [i for i in iGood if not i in iBad]

        stats = RunningStats()
        if not individualBaseline:
            offset = np.mean(self.baselines[iGood])
        for i in iGood:
            p = self.pulse(i)
            if individualBaseline:
                offset = p.preTriggerBaseline()
            stats.push(p.Vsquid - offset)
            
        self.templatePulse = stats.mean()
        self.templatePulseStd = stats.std()
        self.windowedSignal = self.window*self.waf*self.templatePulse
        return self.templatePulse
        
    def makeWindow(self, halfCosineFraction=0.1):
        self._window = halfCosWindow(self.recordLength, halfCosineFraction) 
        self._waf = np.sqrt(1./np.mean(np.square(self._window)))
        
    def applyCalibration(self, templatePulseEnergy):
        '''Apply calibration: templatePulseEnergy in units of eV'''
        self.templatePulseEnergy = templatePulseEnergy

    @property        
    def window(self):
        if self._window is None:
            self.makeWindow()
        return self._window
            
    @property
    def waf(self):
        return self._waf
        
    def avgerageNoise(self, iGood = None, iBad = None):
        if iGood is None:
            iGood = self.iBaseline
        if iBad is not None:
            iGood = [i for i in iGood if not i in iBad]

        stats = RunningStats()
        for i in iGood:
            p = self.pulse(i)
            offset = p.preTriggerBaseline()
            windowedNoise = self.window*(p.Vsquid-offset)
            noiseFFT = np.sqrt(2)*self.waf*np.fft.rfft(windowedNoise)*self.dt # Vrms/Hz
            powerSpectrum = np.square(np.abs(noiseFFT))*self.df # Vrms^2/Hz
            stats.push(powerSpectrum)
        self.noisePowerSpectrum = stats.mean()
        return self.noisePowerSpectrum
        

    def frequencies(self):
        filLen_f = 0.5*self.recordLength + 1
        return np.arange(filLen_f)*self.df

    def s_f(self):
        s_f = 2*np.fft.rfft(self.windowedSignal)*self.dt/self.templatePulseEnergy # Vpk/Hz
        return s_f

    def NEP(self):
        '''Return noise-equivalent power in eV'''
        n_f = self.n_f()
        responsivity = self.s_f() / eV # convert from per eV to per Joule
        nep = n_f / responsivity
        return np.abs(nep)

    def n_f(self):
        return np.sqrt(self.noisePowerSpectrum)

    def baselineResolution(self):
        '''Return theoretical baseline resolution'''
        nep = self.NEP()
        deltaErms = (1./np.sqrt(np.sum(self.df/np.square(nep)))) / eV
        return 2.35482*deltaErms
        
class Pulse(object):
    def __init__(self, hdfDataset, sampleRate, preTriggerSamples):
        self.Vsquid = hdfDataset.value
        #self.signal = a['signal']
        a = hdfDataset.attrs
        self.units = a['units']
        self.endTime = a['endTime']
        self.pulseType = a['pulseType']
        self.ldPulseWidth = a['ldPulseWidth']
        self.ldPulseHighLevel = a['ldPulseHighLevel']
        self.preTriggerSamples = preTriggerSamples
        self.sampleRate = sampleRate
        self.dt = 1./self.sampleRate
        
    def preTriggerBaseline(self):
        return np.mean(self.Vsquid[3:self.preTriggerSamples])
        
    def preTriggerNoise(self):
        return np.std(self.Vsquid[3:self.preTriggerSamples])
        
    def roughPh(self):
        i = self.preTriggerSamples + np.argmin(self.Vsquid[self.preTriggerSamples:self.preTriggerSamples+20])
        return np.mean(self.Vsquid[i-1:i+1]) - self.preTriggerBaseline()
        
        
if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    cooldown = 'G5C'
    path = 'D:\\Users\\Runs\\{0}\\Pulses\\'.format(cooldown)
    fileName = path+'TES1_20180227_003009.h5' # I think I can get out to n=65 or maybe higher. Drift corrections might be necessary. Several populations of test pulses.
    pulses = PulseImporter(fileName)
   
    
    print('Number of pulses:', len(pulses))
    tesId = pulses.tes.tesId
    tesId = 'TES1' # Not correct for the first few files
    from Analysis.G4C.MeasurementDatabase import obtainTes
    tes = obtainTes(cooldown, tesId)
    Rfb = 10E3 # This should be in the file, but currently isn't
    Rsq = tes.Rsquid(Rfb)
    pulses.iv.analyze(Rsq=Rsq, Rb = tes.Rbias, Rs = tes.Rshunt)
    print('TES bias point: Rtes=%.3f mOhm, Ites=%.3f uA, Ptes=%.3f pW' % (pulses.iv.RtesFinal*1E3, pulses.iv.ItesFinal*1E6, pulses.iv.PtesFinal*1E12))


    t0 = pulses.startTime
    fig, ax = mpl.subplots(2,1,sharex=True)    
    ax[0].plot(pulses.pulseEndTimes-t0, pulses.baselines)
    thermo = pulses.hk.thermometers['RuOx2005Thermometer']
    ax[1].plot(thermo.t-t0,thermo.T)
    ax[1].set_xlabel('t (s)')

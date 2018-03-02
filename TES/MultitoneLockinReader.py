# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 10:44:24 2017

@author: wisp10
"""
import h5py as hdf
import numpy as np
import matplotlib.pyplot as mpl
import warnings

class DcTrace(object):
    def __init__(self, hdfRoot):
        a = hdfRoot.attrs
        self.sampleRate = a['sampleRate']
        self.filterBandwidth = a['lpfBw']
        self.filterOrder = a['lpfOrder']
        self.dt = 1./self.sampleRate
        self.dc = hdfRoot['DC']
        self.tGenerated0 = hdfRoot['tGenerated'][0]
        self.tGenerated = hdfRoot['tGenerated'].value
        self.tAcquired = hdfRoot['tAcquired'].value
        self.hdfRoot = hdfRoot

    def loadDecimated(self):
        self.dcDec = self.hdfRoot['DCdec']
        
    def filterDecimated(self, bw=1, order=8):
        from DAQ.SignalProcessing import IIRFilter
        lpf = IIRFilter.lowpass(order=order, fc=bw, fs=self.sampleRate)
        self.dcSym = lpf.filterSymmetric(self.dcDec)

    @property
    def t(self):
        ts = self.tGenerated0 + np.arange(0, len(self.dc)) * self.dt
        return ts

    def plot(self, axes=None):
        t = self.t
        mpl.plot(t, self.dc, '-')

class PseudoSineSweep(object):
    '''A stand-in for the SineSweep class'''
    def __init__(self, f, amplitudes, X, Y):
        self.amplitude = amplitudes
        #self.X = X
        #self.Y = Y
        self.f = f
        self.TF = (X + 1j * Y)/self.amplitude

    def plotPolar(self, **kwargs):
        return mpl.plot(np.real(self.TF), np.imag(self.TF), '.-', **kwargs)
        
    def plotRPhi(self, axes=None):
        if axes is None:
            fig, axes = mpl.subplots(2,1, sharex=True)
        
        axes[0].loglog(self.f, np.abs(self.TF), '.-')
        axes[0].set_ylabel(u'$R$')
        phi = np.rad2deg(np.unwrap(np.angle(self.TF, deg=False)))
        axes[1].semilogx(self.f, phi, '.-')
        axes[1].set_ylabel(u'$\\Phi$ (deg)')
        return axes


class LockinTrace(object):
    def __init__(self, hdfRoot, sampleRate, excitationPhase, filterBandwidth, filterOrder):
        a = hdfRoot.attrs
        self.fRef = a['fRef']
        self.sampleRate = sampleRate
        self.dt = 1./sampleRate
        self.thetaRef = excitationPhase
        self.filterBw = filterBandwidth
        self.filterOrder = filterOrder
        self.amplitudes = hdfRoot['A'].value
        self.Z = hdfRoot['Z'].value
        self.tGenerated0 = hdfRoot['tGenerated'][0]
        self.tGenerated = hdfRoot['tGenerated'].value
        self.tAcquired = hdfRoot['tAcquired'].value
        self.hdfRoot = hdfRoot
        
    def loadDecimated(self):
        self.Xdec = self.hdfRoot['Xdec']
        self.Ydec = self.hdfRoot['Ydec']
        
    def filterDecimated(self, bw=1, order=8, notchQ=1):
        '''Apply non-causal IIR filter ot the decimated (but unfiltered) data. You need to load
        the data first using loadDecimated()'''
        from DAQ.SignalProcessing import IIRFilter
        x = self.Xdec
        y = self.Ydec
        if notchQ > 0 and self.fRef < 0.5*self.sampleRate:
            for f in [self.fRef]: #, 2*self.fRef]:
                if f >= 0.25*self.sampleRate:
                    continue
                print('Applying notch filter at f=', f)
                notchFilterX = IIRFilter.notch(notchQ, f, self.sampleRate)
                notchFilterY = IIRFilter.notch(notchQ, f, self.sampleRate)
                x = notchFilterX.filterSymmetric(x)
                y = notchFilterY.filterSymmetric(y)
            
        lpfX = IIRFilter.lowpass(order=order, fc=bw, fs=self.sampleRate)
        lpfY = IIRFilter.lowpass(order=order, fc=bw, fs=self.sampleRate)
        x = lpfX.filterSymmetric(x)
        y = lpfY.filterSymmetric(y)
        self.Zsym = 2*(x+1j*y)

    @property
    def t(self):
        ts = self.tGenerated0 + np.arange(0, len(self.Z)) * self.dt
        return ts
        
    def plot(self, axes=None):
        t = self.t
        if axes is None:
            fig,axes = mpl.subplots(2,1, sharex=True)
        axes[0].plot(t, np.real(self.Z),label='%.1f Hz' % self.fRef)
        axes[1].plot(t, np.imag(self.Z),label='%.1f Hz' % self.fRef)
        return axes
    
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
        self.loadHousekeeping()

        self.traces = []        
        for i in range(self.nFrequencies):
            root = f['F_%02d' % i]
            trace = LockinTrace(root, 
                               sampleRate=self.outputSampleRates[i],
                               excitationPhase=self.excitationPhases[i],
                               filterBandwidth=self.liaFilterBws[i],
                               filterOrder=self.liaFilterOrders[i])
            self.traces.append(trace)

        
    def loadHousekeeping(self):
        if 'HK' in self._hdfRoot.keys():
            from Analysis.HkImport import HkImporter
            self.hk = HkImporter(self._hdfRoot['HK'])
        else:
            self.hk = None
        
    def dc(self):
        root = self._hdfRoot['DC']
        return DcTrace(root)
        
    def filterSymmetric(self, bw, order):
        '''Filter all trace in this sweep with a symmetric (non-causal) filter
        of specified *order* and bandwidth *bw*.
        The result is contained in the Z variable of each trace.
        '''
        for trace in self.traces:
            trace.loadDecimated()
            trace.filterDecimated(bw=1, order=8)
            trace.Z = trace.Zsym
        
    def extractSineSweep(self, interval):
        fRefs = self.excitationFrequencies
        Zs = np.zeros_like(fRefs, dtype=np.complex128)
        amplitudes = np.zeros_like(fRefs, dtype=np.float)
        for traceNr, trace in enumerate(self):
            i = (trace.t > interval[0]) & (trace.t <= interval[1])
            amplitude = np.unique(trace.amplitudes) # Ideally, we would figure out which chunk we are looking for and then pull the amplitude for that chunk
            if len(amplitude) > 1:
                import warnings
                warnings.warn('Amplitude was changed')
            amplitude = amplitude[0]
            #mpl.plot(trace.t[i], trace.Xdec[i])
            #X = np.mean(trace.Xdec[i])
            #Y = np.mean(trace.Ydec[i])
            #Z = 2*X+2j*Y
            Z = np.mean(trace.Z[i])

            Zs[traceNr] = Z
            amplitudes[traceNr] = amplitude
        ss = PseudoSineSweep(fRefs, amplitudes, X=np.real(Zs), Y=np.imag(Zs))
        return ss
        
        
    def trace(self, i):
        '''
        Return the time trace for the ith frequency.
        '''
        return self.traces[i]

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
    fileName = 'TES1_20171122_200532.h5'
    fileName = 'TestWithOffsetSubtract_20171124_165704.h5'
    fileName = 'TestNoOffsetSubtract_20171124_170654.h5'
    fileName = 'Test_20171124_174955.h5'
    fileName = 'Test_20171127_192415.h5'
    fileName = 'TES1_20171128_200308.h5'
    fileName = 'TES1_20171128_203131.h5'
    fileName = 'TES1_20171129_174037.h5'
    fileName = 'TES1_20171129_174946.h5'
    fileName = 'TES1_20171129_183733.h5'
    fileName = 'TES1_20171129_222719.h5'
    fileName = 'TES1_20171130_092055.h5'
    fileName = 'TES1_20171130_092852.h5'
    fileName = 'test_20171130_115906.h5'
    fileName = 'TES1_Test_20171130_215325.h5'
    fileName = 'TES1_20171201_002346.h5'
    fileName = 'TES1_20171201_004343.h5' # Playing with log bias
    fileName = 'TES1_20171203_024539.h5'
    fileName = 'TES1_20171203_024801.h5'
    fileName = 'TES1_MTL_20171203_030331.h5'
    fileName = 'TES1_MTL_20171204_125919.h5'
    fileName = 'TES1_MTL_20171206_081716.h5'
    fileName = 'TES1_MTL_20171206_070841.h5'
    fileName = 'TES2_MTL_20171207_130406.h5'
    fileName = 'TES2_MTL_20171208_180739.h5'
    
    mtl = MultitoneLockinReader(fileName)
    axes = None
    for trace in mtl:
        trace.loadDecimated()
        trace.filterDecimated(bw=1, order=8)
        #axes = trace.plot(axes)
        trace.Z = trace.Zsym
        axes = trace.plot(axes)
    axes[0].legend(loc='best')
    
    #mpl.figure()
    #mpl.plot(mtl.tGenerated, mtl.offset, '-')
    mpl.figure()
    #mpl.plot(mtl.tGenerated, mtl.Vmax, '-')
    #mpl.plot(mtl.tGenerated, mtl.Vmin, '-')
    mpl.plot(mtl.tGenerated, mtl.Vdc, '-', label='Chunk DC')
    dcTrace = mtl.dc()
    dcTrace.loadDecimated()
    dcTrace.filterDecimated(bw=1, order=6)
    mpl.plot(dcTrace.t, dcTrace.dc, '-', label='Filtered DC')
    mpl.plot(dcTrace.t, dcTrace.dcSym, '-', label='Symmetric DC')

    mpl.legend()
    mpl.show()
    f = hdf.File(fileName, 'r')
    
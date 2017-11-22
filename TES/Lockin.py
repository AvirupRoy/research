# -*- coding: utf-8 -*-
"""
A lock-in with proper decimation and filtering
Available in pure Numpy (*LockInNumpy*) and Intel MKL (*LockInMkl*) accelerated versions.
Created on Wed Dec 21 15:04:44 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>

"""
from __future__ import division

import logging
import numpy as np
TwoPi = 2.*np.pi

from DecimateFast import DecimatorCascade
from DAQ.SignalProcessing import IIRFilter

class LockInBase(object):
    '''Base class for the dual-phase lock-in detection'''
    __logger = logging.getLogger(__name__ + '.LockInBase')
    def __init__(self, sampleRate, fRef, phase, decimation, lpfBw, lpfOrder, chunkSize, dtype=np.float64):
        '''Initialize a Lock-in with the following parameters:
        *sampleRate*: Sample rate of the incoming data (in S/s)
        *fRef*: Detection frequency (in Hz)
        *phase*: Phase of the signal (in rad)
        *decimation*: Decimation to perform after lock-in detection (must be power of 2)
        *lpfBw*: Bandwidth of the final low-pass filter (in Hz)
        *lpfOrder*: Order of the final low-pass filter
        *chunkSize*: Size of the data-chunks to expect (must be an integer multiple of the decimation)
        *dtype*: np.float32 or np.float64
        The output sample rate will be input sampleRate/decimation
        '''
        self.dtype = dtype
        assert sampleRate >= 2*fRef, "Reference frequency outside of Nyquist limit"
        assert chunkSize % decimation == 0, "chunkSize must be an integer multiple of decimation"
        assert sampleRate > 2*lpfBw*decimation, "bandwidth outside of Nyquist limit"
        self.phase = phase
        self.phaseStep = fRef/sampleRate*TwoPi
        self.phaseSteps = np.asarray(np.mod(np.arange(0, chunkSize, 1, dtype=np.float64)*self.phaseStep, TwoPi), dtype)
        self.decimation = decimation
        self.decX = DecimatorCascade(decimation, chunkSize, dtype=dtype)
        self.decY = DecimatorCascade(decimation, chunkSize, dtype=dtype)
        self.__logger.info("Filter order:", self.decX.filterOrder)
        self.lpfX = IIRFilter.lowpass(order=lpfOrder, fc=lpfBw, fs=sampleRate/decimation)
        self.lpfY = IIRFilter.lowpass(order=lpfOrder, fc=lpfBw, fs=sampleRate/decimation)
        self.reset()

    def R(self):
        return np.abs(self.Z)

    def Theta(self):
        return np.arctan2(np.imag(self.Z), np.real(self.Z))

    def reset(self):
        self.decX.reset()
        self.decY.reset()
        self.lpfX.initializeFilterFlatHistory(yout=0)
        self.lpfY.initializeFilterFlatHistory(yout=0)
        self.Z = 0
        self.nSamples = 0
        
class LockInNumpy(LockInBase):
    '''Numpy implementation of the lock-in'''
    def integrateData(self, data):
        '''Run a chunk of samples through the lock-in amplifier. 
        Length of data must match chunkSize specified during construction of
        the Lock-in (for performance reasons).'''
        nNew = len(data)
        assert nNew % self.decimation == 0
        phases = self.phase + self.phaseSteps
        s, c = np.sin(phases), np.cos(phases)
        x,y=s*data,c*data
        xdec = self.decX.decimate(x)
        ydec = self.decY.decimate(y)
        X = 2.*self.lpfX.filterCausal(xdec)
        Y = 2.*self.lpfY.filterCausal(ydec)
        Z = X+1j*Y
        self.phase = (self.phase + nNew*self.phaseStep) % TwoPi
        self.nSamples += nNew
        return Z

try:
    import IntelMkl as mkl
except Exception as e:
    print e
    pass

    
class LockInMkl(LockInBase):
    '''Higher performance implementation of the Lock-in using Intel MKL.'''
    def __init__(self, *args, **kwargs):
        LockInBase.__init__(self, *args, **kwargs)
        if self.dtype == np.float32:
            self.sinCos = mkl.sinCosFloat
            self.mul = mkl.mulFloat
            #self.axpy = mkl.axpyFloat
        elif self.dtype == np.float64:
            self.sinCos = mkl.sinCosDouble
            self.mul = mkl.mulDouble
        self.sinPhi, self.cosPhi = np.empty_like(self.phaseSteps), np.empty_like(self.phaseSteps) # This could probably be pre-allocated
        self.x, self.y = np.empty_like(self.phaseSteps), np.empty_like(self.phaseSteps) # This could probably be pre-allocated

    def integrateData(self, data):
        '''Run a chunk of samples through the lock-in amplifier. '''
        nNew = len(data)
        assert nNew % self.decimation == 0
        phases = self.phase + self.phaseSteps 
        self.sinCos(nNew, phases, self.sinPhi, self.cosPhi)
        self.mul(nNew, data, self.sinPhi, self.x)
        self.mul(nNew, data, self.cosPhi, self.y)
        xdec = self.decX.decimate(self.x)
        ydec = self.decY.decimate(self.y)
        X = 2.*self.lpfX.filterCausal(xdec)
        Y = 2.*self.lpfY.filterCausal(ydec)
        Z = X+1j*Y
        self.phase = (self.phase + nNew*self.phaseStep) % TwoPi
        self.nSamples += nNew
        return Z

if __name__ == '__main__':
    mkl.mklSetNumThreads(1)
    
    import matplotlib.pyplot as mpl
    import time
    sampleRate = 2000000
    fRef = 1058
    phase = 0

    bw = 5
    decimation = 2**(int(np.log2(sampleRate/(40*bw))))
    print "Decimation:", decimation
    n = int(sampleRate/decimation)
    chunkSize = decimation*n
    print "Sample rate after decimation:", sampleRate/decimation

    dtype = np.float32
    order = 8
    lia = LockInNumpy(sampleRate, fRef, phase, decimation, bw, order, chunkSize, dtype=dtype)
    #lia = LockInMkl(sampleRate, fRef, phase, decimation, bw, order, chunkSize, dtype=dtype)
    
    from MultitoneGenerator import MultitoneGenerator    
    g = MultitoneGenerator(sampleRate, chunkSize, dtype)
    g.setOffset(0.1)
    fs = [fRef, 29350.]; As = [1.0, 0.1]; phases = [0, 180.]
    for f, A, p in zip(fs,As,phases):
        g.addSineWave(f, A, p)

    for i in range(20):
        samples = g.generateSamples()
        t1 = time.time()
        Z = lia.integrateData(samples)
        dt = time.time()-t1
        print "dt=", dt, 's', len(samples)/dt*1E-6, 'MS/s'
        print "Samples generated:",g.samplesGenerated
        print "Samples lock-ined:", lia.nSamples
    mpl.figure()
    mpl.plot(np.real(Z))
    mpl.plot(np.real(Z))
    mpl.show()

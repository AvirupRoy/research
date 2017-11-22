# -*- coding: utf-8 -*-
"""
Multitone (sine-wave) generator
Created on Wed Dec 21 12:33:18 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
from __future__ import division, print_function
import numpy as np
TwoPi = 2.*np.pi

try:
    import IntelMkl as mkl
    
except Exception as e:
    print("Unable to import Intel MKL, using numpy instead:", e)
    mkl = None


class MultitoneGeneratorBase(object):
    '''Generate a continuous waveform as a sum of sine waves of specified
    frequency, amplitude and phase, with an overall offset.'''
    def __init__(self, sampleRate, chunkSize, dtype=np.float32):
        '''Initialize for a specified sample rate fs.'''
        assert sampleRate > 0
        self.dtype= dtype
        self.sampleRate = sampleRate
        self.chunkSize = chunkSize
        self.deltaPhases = None
        self.offset = 0
        self.amplitudes = []
        self.phases = []
        self.phaseSteps = []
        self.rampRate = 0
        self.ramping = False
        self.samplesGenerated = 0
        self.dcLast = 0
        
    def setRampRate(self, rate):
        self.rampRate = rate
        
    def setAmplitude(self, i, A):
        self.amplitudes[i] = A
        
    def setChunkSize(self, chunkSize):
        self.chunkSize = chunkSize
        self.deltaPhases = None
        
    def _regenPhaseSteps(self):
        t = np.arange(0, self.chunkSize, 1, dtype=self.dtype)
        self.deltaPhases = []
        for i in range(len(self.phaseSteps)):
            ph = np.mod(t*self.phaseSteps[i], TwoPi) # This is improved from the other version
            self.deltaPhases.append(ph)
        
    def addSineWave(self, frequency, amplitude, phase=0):
        assert frequency < 0.5*self.sampleRate
        phaseStep = TwoPi*frequency/self.sampleRate
        self.amplitudes.append(amplitude)
        self.phases.append(phase)
        self.phaseSteps.append(phaseStep)
        self.deltaPhases = None
        
    def setOffset(self, offset):
        if self.rampRate > 0:
            self.ramping = True
            self.offset = offset
        
class MultitoneGeneratorNp(MultitoneGeneratorBase):
    def generateSamples(self):
        '''Generate a chunk of samples.
        Returns waveform data and an array of amplitudes  for each frequency'''
        if self.deltaPhases is None:
            self._regenPhaseSteps()
        wave = np.full((self.chunkSize,), self.offset, dtype=self.dtype) 
        n = self.chunkSize # Number of samples to generate
        if self.ramping:
            nSteps = abs(self.offset-self.dcLast) // self.rampRate
            if nSteps < n:
                self.ramping = False
            else:
                nSteps = n
            if (self.offset-self.dcLast) > 0:
                final = min(self.dcLast+nSteps*self.rampRate, self.offset)
            else:
                final = max(self.dcLast-nSteps*self.rampRate, self.offset)
            wave[0:nSteps] = np.linspace(self.dcLast, final, nSteps)
        self.dcLast = wave[-1]
            
        for i in range(len(self.amplitudes)):
            #print("self.phases[i]:", i, self.phases[i])
            phases = self.phases[i]+self.deltaPhases[i]
            phases %= TwoPi
            wave += self.amplitudes[i]*np.sin(phases)
            self.phases[i] = (self.phases[i] + self.chunkSize*self.phaseSteps[i]) % TwoPi
        self.samplesGenerated += len(wave)
        return self.offset, np.asarray(self.amplitudes), wave

if mkl is not None:
    class MultitoneGeneratorMkl(MultitoneGeneratorBase):
        def __init__(self, sampleRate, chunkSize, dtype=np.float32):
            MultitoneGeneratorBase.__init__(self, sampleRate, chunkSize, dtype)
            if dtype==np.float32:
                self.sin = mkl.sinFloat
                #self.mul = mkl.mulFloat
                self.axpy = mkl.axpyFloat
            else:
                self.sin = mkl.sinDouble
                self.axpy = mkl.axpyDouble
            self.sinPhi = np.empty((chunkSize,), dtype=dtype) # temporary to hold sin(phi) for each frequency

        def generateSamples(self):
            '''Generate a chunk of samples.
            Returns waveform data and an array of amplitudes for each frequency'''
            if self.deltaPhases is None:
                self._regenPhaseSteps()
            n = self.chunkSize # Number of samples to generate
            wave = np.full((n,), self.offset, dtype=self.dtype) 
            if self.ramping:
                nSteps = abs(self.offset-self.dcLast) / self.rampRate
                if nSteps < n:
                    self.ramping = False
                else:
                    nSteps = n
                if (self.offset-self.dcLast) > 0:
                    final = min(self.dcLast+nSteps*self.rampRate, self.offset)
                else:
                    final = max(self.dcLast-nSteps*self.rampRate, self.offset)
                wave[0:nSteps] = np.linspace(self.dcLast, final, nSteps)
            self.dcLast = wave[-1]
            for i in range(len(self.amplitudes)):
                phases = self.phases[i]+self.deltaPhases[i]
                self.sin(n, phases, self.sinPhi) # sinPhi = sin(phases)
                self.axpy(n, self.amplitudes[i], self.sinPhi, 1, wave, 1) # wave=self.amplitudes[i]*sinPhi
                self.phases[i] = (self.phases[i] + n*self.phaseSteps[i]) % TwoPi # This could be vectorized (not that it matters)
            self.samplesGenerated += len(wave)
            return self.offset, np.asarray(self.amplitudes), wave
    
    MultitoneGenerator = MultitoneGeneratorMkl
else:
    MultitoneGenerator = MultitoneGeneratorNp


def testRamping():
    import matplotlib.pyplot as mpl
    chunkSize = 1000
    g = MultitoneGeneratorNp(1E5, 1000)
    g.setRampRate(0.01)
    t = np.linspace(0, 1, chunkSize, dtype=np.float32)
    dt = t[1]-t[0]
    for i in range(10):
        if i%4 == 0:
            g.setOffset(22)
        if i%6 == 0:
            g.setOffset(-10)
        x = g.generateSamples()
        mpl.plot(t, x, '.')
        t = t+1+dt
    mpl.show()
    
if __name__ == '__main__':
    if mkl is not None:
        mkl.mklSetNumThreads(1)

    testRamping()
    
    chunkSize = 100000
    repeats = 50

    dtype = np.float32
    gMkl = MultitoneGeneratorMkl(1E6, chunkSize, dtype=dtype)
    gNp = MultitoneGeneratorNp(1E6, chunkSize)
    fs = [5000, 29350]; As = [1.0, 0.1]; phases = [0, 180.]
    for f, A, p in zip(fs,As,phases):
        gNp.addSineWave(f, A, p)
        gMkl.addSineWave(f, A, p)

    gMkl.generateSamples()

    t1 = mkl.mklSecondsFloat()
    for i in range(repeats):
        gMkl.generateSamples()
    dtMkl = mkl.mklSecondsFloat() - t1
    print("MKL:", dtMkl, 's', repeats*chunkSize/dtMkl*1E-6, 'MS/s')

    gNp.generateSamples()
    t1 = mkl.mklSecondsFloat()
    for i in range(repeats):
        gNp.generateSamples()
    dtNp = mkl.mklSecondsFloat() - t1
    print("numpy:", dtNp, 's', repeats*chunkSize/dtNp*1E-6, 'MS/s')
    
    print("t_Numpy/t_MKL:", dtNp/dtMkl)

    sNp = gMkl.generateSamples()
    sMkl = gNp.generateSamples()
    
    print("Max error:", np.max(np.abs(sNp-sMkl)))
    import matplotlib.pyplot as mpl
    mpl.figure()
    mpl.subplot(3,1,1)
    mpl.plot(sNp)
    mpl.ylabel('numpy')
    mpl.subplot(3,1,2)
    mpl.plot(sMkl)
    mpl.ylabel('mkl')
    mpl.subplot(3,1,3)
    mpl.plot(sNp-sMkl)
    mpl.ylabel('np-mkl')
    mpl.show()

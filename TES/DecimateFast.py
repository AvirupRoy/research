# -*- coding: utf-8 -*-
"""
A faster version of Decimate.py
Created on Thu Dec 15 10:12:10 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from __future__ import print_function, division

import numpy as np
from scipy.signal import kaiserord, firwin
import pyximport
pyximport.install(setup_args={#"script_args":["--compiler=mingw32"],
                              "include_dirs":np.get_include()},
                  reload_support=True)
import FilterFIR

class Decimator(object):
    '''Half-band decimator with FIR filter.'''
    def __init__(self, chunkSize, stopBandRipple=100, width=0.15, dtype=np.float64):
        '''
        *chunkSize*: Size of the input data chunks to be decimated (must be a multiple of the decimation factor)
        *stopBandRipple*: Maximum ripple in the stop-band of the FIR filter (default: 100)
        *width*: Transition width of the filter (default 0.15)
        *dtype*: np.float32 or float64
        '''
        self.dtype = dtype
        numTaps, beta = kaiserord(stopBandRipple, width)
        if numTaps % 2 == 0:         # We need an odd number of taps
            numTaps += 1
        self.numberOfTaps = numTaps
        self.filterOrder = numTaps-1
        self.b = np.asarray(firwin(numTaps, 0.5, window=('kaiser', beta)), dtype=dtype)
        if dtype==np.float32:
            self.filter = FilterFIR.FirHalfbandDecimateFloat(chunkSize, self.b)
        elif dtype==np.float64:
            self.filter = FilterFIR.FirHalfbandDecimateDouble(chunkSize, self.b)

    def decimate(self, data):
        '''Decimate the data and return the decimated samples.
        The length of data has to be an even number.
        The returned data will be half the length of the input.
        Uses the Cython implementation to do the decimation/filtering'''
        n = len(data)
        assert n % 2 == 0
        yout = np.empty((len(y)//2,), dtype=self.dtype)
        self.filter.lfilter(y, yout)
        return yout
        

class DecimatorCascade(object):
    '''Cascade of half-band decimators with FIR low-pass filters.'''
    def __init__(self, factor, chunkSize, stopBandRipple=100, width=0.15, dtype=np.float64):
        '''Construct the decimator cascade.
        *factor*: Desired decimation factor (must be power of 2)
        *chunkSize*: Size of the input data chunks to be decimated (must be a multiple of the decimation factor)
        *stopBandRipple*: Maximum ripple in the stop-band of the FIR filter (default: 100)
        *width*: Transition width of the filter (default 0.15)
        *dtype*: np.float32 or float64
        '''
        self.dtype = dtype
        self.nStages = int(np.log2(factor))
        self.factor = 2**self.nStages
        assert self.factor == factor, "Decimation factor must be a power of 2"
        numTaps, beta = kaiserord(stopBandRipple, width) # Calculate FIR filter coefficients
        if numTaps % 2 == 0:         # We need an odd number of taps
            numTaps += 1
        self.numberOfTaps = numTaps
        self.filterOrder = numTaps-1
        b = np.asarray(firwin(numTaps, 0.5, window=('kaiser', beta)), dtype=dtype)
        self.b = b
        self.filters = []        
        for i in range(self.nStages):
            if dtype==np.float32:
                self.filters.append(FilterFIR.FirHalfbandDecimateFloat(chunkSize, b))
            elif dtype==np.float64:
                self.filters.append(FilterFIR.FirHalfbandDecimateDouble(chunkSize, b))
                
    def sampleDelay(self):
        '''Returns the delay introduced by the FIR filter in (fractional) number of samples.'''
        return 0.5*(2**self.nStages - 1) * (self.numberOfTaps-1)
            
    def reset(self, value=0):
        '''Not implemented'''
        pass
        
    def decimate(self, data):
        '''Decimate the data and return the decimated samples.
        The length of data has to be an integer multiple in length of the decimation factor.'''
        n = len(data)
        assert n % self.factor == 0
        y = data
        for f in self.filters:
            yout = np.empty((len(y)//2,), dtype=self.dtype)
            f.lfilter(y, yout)
            y = yout
        return y
        
def performanceTest2():
    dtype=np.float32
    fs = 2E6
    tMax = 5.
    t = np.linspace(0, 2., fs*tMax, dtype=dtype)
    
    noise = 0.1*np.asarray(np.random.rand(len(t)), dtype=dtype)
    y=noise

    fFinal = 1.0
    decGoal = fs/(fFinal*20)
    decFactor = 2**int(np.log2(decGoal))
    chunkSize = decFactor*16
    d = DecimatorCascade(decFactor, chunkSize, dtype=dtype)
    print("Decimation:", d.factor)
    print("Decimator filter order:", d.filterOrder)
    print("Chunk size", chunkSize)
    
    decimatedSampleRate = fs/decFactor
    print("Decimated sample rate:", decimatedSampleRate)
    finalFilter = IIRFilter.lowpass(order=8, fc=fFinal, fs=decimatedSampleRate)
    finalFilter.initializeFilterFlatHistory(0)
    for i in range(int(len(y)/chunkSize)):
        sl = slice(i*chunkSize,(i+1)*chunkSize, None)
        chunk = y[sl]
        t1 = time.time()
        dec = d.decimate(chunk)
        filtered = finalFilter.filterCausal(dec)
        dt = time.time()-t1
        print('Decimation time:', dt)
        print('Decimation throughput:', chunkSize/dt*1E-6, 'MS/s')

def performanceTest():
    from DAQ.SignalProcessing import IIRFilter
    
    dtype=np.float32
    fs = 1E6
    fref = 1000
    f1 = 1000
    offset = 1
    f2 = 1500
    TwoPi = 2.*np.pi
    tMax = 2.
    t = np.linspace(0, 2., fs*tMax, dtype=dtype)
    
    noise = 0.1*np.asarray(np.random.rand(len(t)), dtype=dtype)
    
    s = 0.1*np.sin(TwoPi*f1*t) + 0.1*np.sin(TwoPi*f2*t) + offset + noise
    y = s*np.sin(TwoPi*fref*t)
    x = s*np.cos(TwoPi*fref*t)
    y=x

    fFinal = 20
    decGoal = fs/(fFinal*40)
    decFactor = 2**int(np.log2(decGoal))
    chunkSize = decFactor*50
    d = DecimatorCascade(decFactor, chunkSize, dtype=dtype)
    print("Decimation:", d.factor)
    print("Decimator filter order:", d.filterOrder)
    
    decimatedSampleRate = fs/decFactor
    print("Decimated sample rate:", decimatedSampleRate)
    finalFilter = IIRFilter.lowpass(order=8, fc=fFinal, fs=decimatedSampleRate)
    finalFilter.initializeFilterFlatHistory(0)
    for i in range(int(len(y)/chunkSize)):
        sl = slice(i*chunkSize,(i+1)*chunkSize, None)
        chunk = y[sl]
        dec = d.decimate(chunk)
        filtered = finalFilter.filterCausal(dec)

if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    import time
    from DAQ.SignalProcessing import IIRFilter
    
    performanceTest2()
    
    #import profile
    #profile.run("performanceTest()")

    dtype = np.float64
    
    fs = 1E6
    fref = 1000
    f1 = 1000
    offset = 1.
    f2 = 1500
    TwoPi = 2.*np.pi
    t = np.linspace(0, 1, fs, dtype=dtype)
    
    #noise = 0.1*np.asarray(np.random.rand(len(t)), dtype=dtype)
    
    s = 0.1*np.sin(TwoPi*f1*t) + 0.1*np.sin(TwoPi*f2*t) + offset #+ noise
    y = s*np.sin(TwoPi*fref*t)
    x = s*np.cos(TwoPi*fref*t)
    #y=y

    fFinal = 20
    decGoal = fs/(fFinal*50)
    decFactor = 2**int(np.log2(decGoal))
    chunkSize = decFactor*50
    d = DecimatorCascade(decFactor, chunkSize, dtype=dtype)
    #d.reset(0.05)
    print("Decimation:", d.factor)
    print("Decimator filter order:", d.filterOrder)
    
    mpl.figure()
    t1 = time.time()
    
    decimatedSampleRate = fs/decFactor
    print("Decimated sample rate:", decimatedSampleRate)
    print("Cut-off rate:", fFinal)
    finalFilter = IIRFilter.lowpass(order=8, fc=fFinal, fs=decimatedSampleRate)
    finalFilter.initializeFilterFlatHistory(0.05)
    for i in range(int(len(y)/chunkSize)):
        sl = slice(i*chunkSize,(i+1)*chunkSize, None)
        chunk = y[sl]
        dec = d.decimate(chunk)
        filtered = finalFilter.filterCausal(dec)
        sl_dec = slice(i*chunkSize,(i+1)*chunkSize, decFactor)
        t_dec = t[sl_dec]
        mpl.plot(t_dec, dec, 'b-', label='decimated')
        mpl.plot(t_dec, filtered, 'r-', label='lp filtered')
    t2 = time.time()
    #mpl.plot(t_dec, dec, 'b-', label='decimated')
    print("Time:", t2-t1)
    print("Total samples:", len(y))
    print("Final sample rate:", decimatedSampleRate)
    mpl.show()
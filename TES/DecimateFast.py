# -*- coding: utf-8 -*-
"""
A faster version of Decimate.py

Created on Thu Dec 15 10:12:10 2016

@author: calorim
"""
from __future__ import print_function, division

import numpy as np
from scipy.signal import kaiserord, firwin
import profile
import pyximport
pyximport.install(setup_args={#"script_args":["--compiler=mingw32"],
                              "include_dirs":np.get_include()},
                  reload_support=True)
import FilterFIR

class Decimator(object):
    def __init__(self, factor, chunkSize, dtype=np.float64):
        self.dtype = dtype
        self.nStages = int(np.log2(factor))
        self.factor = 2**self.nStages
        assert self.factor == factor, "Decimation factor must be a power of 2"
        stopBandRipple=100 # dB stop band attenuation/ripple
        width=0.2
        N, beta = kaiserord(stopBandRipple, width)
        self.filterOrder = N
        b = np.asarray(firwin(N+1, 0.5, window=('kaiser', beta)), dtype=dtype)
        self.filters = []        
        for i in range(self.nStages):
            if dtype==np.float32:
                self.filters.append(FilterFIR.FirHalfbandDecimateFloat(chunkSize, b))
            elif dtype==np.float64:
                self.filters.append(FilterFIR.FirHalfbandDecimateDouble(chunkSize, b))
            
    def reset(self, value=0):
        pass
        
    def decimate(self, data):
        '''Decimate the data and return the decimated samples.
        The lenght of data has to be an integer multiple in length of the decimation factor.'''
        n = len(data)
        assert n % self.factor == 0
        y = data
        for f in self.filters:
            yout = np.empty((len(y)/2,), dtype=self.dtype)
            f.lfilter(y, yout)
            y = yout
        return y

def performanceTest():
    from DAQ.SignalProcessing import IIRFilter
    
    dtype=np.float64
    fs = 1E6
    fref = 1000
    f1 = 1000
    offset = 1
    f2 = 1500
    TwoPi = 2.*np.pi
    t = np.linspace(0, 1, fs, dtype=dtype)
    
    noise = 0.1*np.asarray(np.random.rand(len(t)), dtype=dtype)
    
    s = 0.1*np.sin(TwoPi*f1*t) + 0.1*np.sin(TwoPi*f2*t) + offset + noise
    y = s*np.sin(TwoPi*fref*t)
    x = s*np.cos(TwoPi*fref*t)
    y=x

    fFinal = 20
    decGoal = fs/(fFinal*40)
    decFactor = 2**int(np.log2(decGoal))
    chunkSize = decFactor*50
    d = Decimator(decFactor, chunkSize, dtype=dtype)
    print("Decimation:", d.factor)
    print("Filter order:", d.filterOrder)
    
    decimatedSampleRate = fs/decFactor
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
    
    profile.run("performanceTest()")

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
    decGoal = fs/(fFinal*40)
    decFactor = 2**int(np.log2(decGoal))
    chunkSize = decFactor*50
    d = Decimator(decFactor, chunkSize, dtype=dtype)
    #d.reset(0.05)
    print("Decimation:", d.factor)
    print("Filter order:", d.filterOrder)
    
    mpl.figure()
    t1 = time.time()
    decimatedSampleRate = fs/decFactor
    finalFilter = IIRFilter.lowpass(order=8, fc=fFinal, fs=decimatedSampleRate)
    finalFilter.initializeFilterFlatHistory(0.05)
    for i in range(int(len(y)/chunkSize)):
        sl = slice(i*chunkSize,(i+1)*chunkSize, None)
        chunk = y[sl]
        dec = d.decimate(chunk)
        filtered = finalFilter.filterCausal(dec)
        sl_dec = slice(i*chunkSize,(i+1)*chunkSize, decFactor)
        t_dec = t[sl_dec]
        mpl.plot(t_dec, filtered, 'r-', label='lp filtered')
    t2 = time.time()
    #mpl.plot(t_dec, dec, 'b-', label='decimated')
    print("Time:", t2-t1)
    print("Total samples:", len(y))
    print("Final sample rate:", decimatedSampleRate)
    mpl.show()
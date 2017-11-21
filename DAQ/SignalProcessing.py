# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 13:07:09 2016

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
import numpy as np
import scipy.signal as scs

class IIRFilter(object):
    def __init__(self, filterType, order, fcs, fs = 2.):
        self.b, self.a = scs.iirfilter(N = order, Wn = fcs / (0.5*fs), rp = None, rs = None, btype=filterType, ftype='butter', output='ba')
        self.order = order
        self.fcs = fcs
        self.filterType = filterType
        self.zi = None
        
    @classmethod
    def lowpass(cls, order, fc, fs=1):
        '''Generate a butterworth low-pass filter of specified order with cut-off frequency fc and sample rate fs.'''
        return cls(filterType='lowpass', order=order, fcs=fc, fs=fs)

    @classmethod
    def highpass(cls, order, fc, fs=1):
        '''Generate a butterworth high-pass filter of specified order with cut-off frequency fc and sample rate fs.'''
        return cls(filterType='highpass', order=order, fcs=fc, fs=fs)
        
    @classmethod
    def bandpass(cls, order, fc_low, fc_high, fs=2.):
        '''Generate a butterworth band-pass filter with specified cut-off frequencies fc_low and fc_high and sample rate fs.'''
        return cls(filterType='bandpass', order=order, fcs=np.array([fc_low, fc_high]), fs=fs)

    @classmethod
    def bandstop(cls, order, fc_low, fc_high, fs=2.):
        return cls(filterType='bandstop', order=order, fcs=np.array([fc_low, fc_high]), fs=fs)
        
    def filterCausal(self, y):
        '''Performs causal filtering of the data, keeping track of the filter state for repeated calls.'''
        yout, self.zi = scs.lfilter(self.b, self.a, x=y, zi = self.zi)
        return yout
        
    def filterSymmetric(self, y):
        '''Perform forward/backward filtering of the data to obtain an acausal signal.'''
        yout = scs.filtfilt(self.b, self.a, y)   # would like to use method="gust" here
        return yout
        
    def initializeFilterFlatHistory(self, yout, yin = None):
        '''Initialize filter assuming the history has been a constant signal with output yout
        and, input yin (if None, assumed to be equal to yout)'''
        yout = np.ones(self.order)*yout
        if yin is None:
            yin = yout
        else:
            yin = np.ones(self.order)*yin
        self.zi = scs.lfiltic(self.b, self.a, y = yout, x = yin)

if __name__ == '__main__':
    import numpy as np
    import matplotlib.pyplot as mpl
    import time
    
    
    A = 1
    f = 100
    fs = 10000
    
    dt = 1./fs
    t = np.arange(0, 5*fs) * dt
    y = A*np.sin(2.*np.pi*f*t+0.25)+0.6 + 0.1*A*np.sin(2.*np.pi*20*f*t)+0.3*A*np.sin(2*np.pi*0.2*t)
    y = y.astype(dtype=np.float32)
    print "len(t)", len(t)

    lpf = IIRFilter.lowpass(order=10, fc=1000, fs=fs)    
    hpf = IIRFilter.highpass(order=2, fc=1, fs=fs)
    
    bpf = IIRFilter.bandpass(order=2, fc_low = 1, fc_high=300, fs=fs)    

    lpf.initializeFilterFlatHistory(y[0])
    hpf.initializeFilterFlatHistory(0, y[0])
    bpf.initializeFilterFlatHistory(0, y[0])
    t1 = time.time()
    for i in range(4):
        yf = hpf.filterCausal(lpf.filterCausal(y))
    t2 = time.time()
    print "lowpass+highpass time:", t2-t1
    t1 = time.time()
    for i in range(4):
        ybpf = bpf.filterCausal(y)
    t2 = time.time()
    print "Band pass time:", t2-t1
    
    t1 = time.time()
    yf2 = hpf.filterSymmetric(lpf.filterSymmetric(y))
    t2 = time.time()
    print "Symmetric HP+LP time:", t2-t1
    
    mpl.plot(t,y, label='signal')
    mpl.plot(t,yf, label='causal low and high pass')
    mpl.plot(t,ybpf, label='causal band-pass')
    mpl.plot(t,yf2, label='symmetric')
    mpl.legend()
    mpl.xlabel('t [s]')
    mpl.show()

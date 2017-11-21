# -*- coding: utf-8 -*-
"""
Created on Mon Aug  8 14:59:32 2016

@author: jaeckel
"""

import numpy as np

class Avs47():
    '''Load data from AVS 47B logging files'''
    def __init__(self, path, files):
        '''Specify a file path and some number of piezo files to be loaded. If piezoFiles is a str, it is assumed that the data is available in a single .npz file.
        If piezoFiles is a list of file names for text files, they will all be concatenated in memory. You can then use saveToNpz() to speed up loading for next time.'''
        if type(files) == str:
            d = np.load(path+files)
            self.t = d['t']
            self.R = d['R']
            self.channel = d['channel']
            self.range = d['range']
            self.excitation = d['excitation']
        else:
            t = None
            for fileName in files:
                d = np.genfromtxt(path+fileName, skip_header=5, names=True, delimiter='\t')
                if t is None:
                    t = d['time']
                    ch = d['channel'].astype(np.int)
                    ex = d['excitation'].astype(np.int)
                    rang = d['range'].astype(np.int)
                    R = d['R']
                else:
                    t = np.hstack([t, d['time']])
                    ch = np.hstack([ch, d['channel'].astype(np.int)])
                    ex = np.hstack([ex, d['excitation'].astype(np.int)])
                    rang = np.hstack([rang, d['range'].astype(np.int)])
                    R = np.hstack([R, d['R']])
            self.t = t
            self.channel = ch
            self.R = R
            self.excitation = ex
            self.range = rang

    def select(self, good):
        '''Only retain those data where good is True'''
        self.t = self.t[good]
        self.R = self.I[good]
        self.channel = self.channel[good]
        self.excitation = self.excitation[good]
        self.range = self.range[good]

    def selectTime(self, tStart, tStop):
        '''Only retain those data in the specified time frame'''
        good = (self.t >= tStart) & (self.t <= tStop)
        self.select(good)

    def saveToNpz(self, fileName):
        '''Save the data to an npz file for faster loading.'''
        np.savez(fileName, t = self.t, R = self.R, channel = self.channel, range=self.range, excitation=self.excitation)

    def plot(self):
        import matplotlib.pyplot as mpl
        import matplotlib.dates as mpldates
        mpl.rcParams['timezone'] = 'US/Central'
        mpl.figure()
        t = mpldates.epoch2num(self.t)
        channels = np.unique(self.channel)

        print "Len channels:", len(channels)
        for i, channel in enumerate(channels):
            mpl.subplot(len(channels),1,i+1)
            select = self.channel == channel
            mpl.plot_date(t[select], self.R[select], '-')
            mpl.ylabel('Channel %i R (Ohm)' % channel)
        mpl.xlabel('Time')

if __name__ == '__main__':
    import time
    t1 = time.time()
    path = '../ADR3_Data/data/F4C/'

    if False:
        import glob
        files = glob.glob(path+'AVSBridge_*.dat')

        bridge = Avs47('', files)

        t2 = time.time()
        print "Loading raw text took ", t2-t1, "s"
        bridge.saveToNpz('AVS47.npz')

    t1 = time.time()
    bridge = Avs47('', 'AVS47.npz')
    t2 = time.time()
    print "Loading npz file took ", t2-t1, "s"
    bridge.plot()

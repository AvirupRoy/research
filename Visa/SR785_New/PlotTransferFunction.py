# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:51:11 2015

@author: wisp10
"""

fileName = 'Test Files/15E7C0004.swp'

import numpy as np

class TransferFunction:
    pass

def loadData(fileName):
    with open(fileName, 'r') as f:
        ds = {}
        i = 0
        while True:
            line = f.readline();
            i += 1
            if 'Frequency (Hz)	Magnitude' in line:
                break
            s = line.split(':')
            if len(s) == 2:
                key = s[0][0:]
                value = s[1][:-1]
                ds[key]=value
    print i
    print ds
    d = np.genfromtxt(fileName, names = True, delimiter='\t', skip_header=i-1)
    r = TransferFunction
    r.f = d['Frequency_Hz']
    r.R = d['Magnitude']
    r.phase = d['Phase_deg']
    r.meta = ds
    return r


import matplotlib.pyplot as mpl

#files = ['Test Files/15E7C0004.swp', 'Test Files/15E7C0005.swp', 'Test Files/15E7C0006.swp', 'Test Files/15E7C0007.swp']
#files = ['Test Files/Amplitude010mV.swp', 'Test Files/Amplitude020mV.swp', 'Test Files/Amplitude040mV.swp', 'Test Files/Amplitude060mV.swp',  'Test Files/Amplitude080mV.swp']
#files = ['Test Files/Attenuator200x_010mV.swp', 'Test Files/Attenuator200x_040mV.swp']
#files = ['Test Files/DirectCoupled_020mV.swp']
files = ['Test Files/TES1_020mV.swp', 'Test Files/TES1_040mV.swp']

for fileName in files:
    d = loadData(fileName)
    mpl.subplot(2,1,1)
    mpl.loglog(d.f, d.R, '-')
    mpl.ylabel('Magnitude')
    mpl.subplot(2,1,2)
    mpl.semilogx(d.f, d.phase, '-')
    mpl.ylabel('Phase [deg]')
    mpl.xlabel('f [Hz]')
    
mpl.show()

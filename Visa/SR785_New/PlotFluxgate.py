# -*- coding: utf-8 -*-
"""
Created on Tue Jan 05 21:08:21 2016

@author: wisp10
"""

fileName = 'D:\Users\FJ\ADR3\Visa\Fluxgate_20160106.dat'

import numpy as np
import matplotlib.pyplot as mpl

d = np.genfromtxt(fileName, skip_header=2, names=True)

t = d['t']
V1 = d['V1V']
V2 = d['V2V']

mpl.figure()
mpl.plot(t,V1,label='Fluxgate')
mpl.plot(t,V2,label='Reference')
mpl.ylabel('Voltage [V]')
mpl.xlabel('Time')
#mpl.show()

Gain = 4
R = 100
S = 12.2 # mA/mT = A/T
Vref = 2.5

B = -(V1-V2)/(Gain*S*R)
#mpl.figure()
#mpl.plot(t,V1-V2)
#mpl.ylabel('Vflux-Vref [V]')
#mpl.xlabel('Time')
##mpl.show()

mpl.figure()
mpl.plot(t,B/1E-6)
mpl.ylabel(u'B [$\mu$T]')
mpl.xlabel('Time')
mpl.show()

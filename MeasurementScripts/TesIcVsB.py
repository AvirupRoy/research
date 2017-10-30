# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 11:08:29 2017

@author: wisp10
"""

from __future__ import print_function
import time
import numpy as np

from TES import IvCurveDaqRemote

ivRemote = IvCurveDaqRemote.IvCurveDaqRemote('TesIcVsB')

print(ivRemote.auxAoVoltage())

#Vcoils = np.hstack([np.arange(-7, -2, 0.05), np.arange(-2,2, 0.01), np.arange(2, 7, 0.05)])
stepSize=0.02
Vcoils = np.arange(-4.5,4.5+stepSize, stepSize)
#Vcoils = np.arange(-2, +2+stepSize, stepSize)
#Vcoils = Vcoils[::-1]
#Vcoils = np.hstack([Vcoils, Vcoils[::-1]])


print('Number of points:', len(Vcoils))

ivRemote.setAuxAoVoltage(Vcoils[0])
time.sleep(0.5)
ivRemote.start()
while ivRemote.sweepCount() > 2:
    time.sleep(0.5)

for Vcoil in Vcoils:
    print('Vcoil=%.3f V' % Vcoil)
    ivRemote.setAuxAoVoltage(Vcoil)
    time.sleep(0.1)
    count = ivRemote.sweepCount()     # Wait for another sweep to be collected
    
    while True:
        time.sleep(0.25)
        newCount = ivRemote.sweepCount()
        print('.', end='')
        if newCount > count:
            print('Done')
            break
    time.sleep(0.1)

ivRemote.stop()

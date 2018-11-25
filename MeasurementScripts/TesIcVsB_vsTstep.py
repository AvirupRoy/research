# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 11:08:29 2017

@author: wisp10
"""

from __future__ import print_function
import time
import numpy as np

from PyQt4.QtCore import QCoreApplication
from TES.IvCurveDaqRemote import IvCurveDaqRemote
from Adr import Adr
import logging
logging.basicConfig(level=logging.WARN)

app = QCoreApplication([])
adr = Adr(app)

ivRemote = IvCurveDaqRemote('TesIcVsB')
print(ivRemote.auxAoVoltage())

#Vcoils = np.hstack([np.arange(-5, -1, 0.05), np.arange(-1,1, 0.01), np.arange(1, 5, 0.05)])
#stepSize=0.01
#Vcoils = np.arange(-2, +2+stepSize, stepSize)
#stepSize=0.1
#Vcoils = np.arange(-2,7+stepSize, stepSize)

center = 3.5
centerSpan = 2.
centerStep = 0.02
fullStep = 0.1  
fullSpan = 5.
#fullSpan = 0.

Vcoils = np.hstack([np.arange(center-0.5*fullSpan, center-0.5*centerSpan, fullStep), np.arange(center-0.5*centerSpan, center+0.5*centerSpan, centerStep), np.arange(center+0.5*centerSpan, center+0.5*fullSpan+fullStep, fullStep)])
#Vcoils = np.hstack([Vcoils, Vcoils[::-1]])

#Vcoils = Vcoils[::-1]
#Vcoils = np.hstack([Vcoils, Vcoils[::-1]])
print('Coil range:', np.min(Vcoils), np.max(Vcoils))
print('Number of points:', len(Vcoils))

Ts = np.asarray([0.070, 0.0725, 0.075, 0.076, 0.077, 0.078, 0.079, 0.080, 0.081, 0.082])
Ts = np.asarray([0.076, 0.078, 0.080, 0.082, 0.083])
#Ts = np.asarray([0.075])
Ts = np.asarray([0.0835, 0.084, 0.0845])


for T in Ts:
    print('Ramping to ', T)
    adr.rampTo(T)
    ivRemote.setAuxAoVoltage(Vcoils[0])
    adr.stabilizeTemperature(T)
    time.sleep(60)
    
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
            time.sleep(0.5)
            newCount = ivRemote.sweepCount()
            print('.', end='')
            if newCount > count:
                print('Done')
                break
        time.sleep(0.1)
    ivRemote.stop()
    time.sleep(10)
    
ivRemote.setAuxAoVoltage(0)
adr.rampTo(0.0835)

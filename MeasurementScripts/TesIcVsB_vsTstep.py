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
stepSize=0.02
Vcoils = np.arange(-5,5+stepSize, stepSize)

#Vcoils = Vcoils[::-1]
#Vcoils = np.hstack([Vcoils, Vcoils[::-1]])
print('Number of points:', len(Vcoils))

#Ts = np.asarray([0.070, 0.075, 0.0775, 0.080, 0.082, 0.083, 0.84, 0.085])
#Ts = np.asarray([0.076, 0.077, 0.078])
Ts = np.asarray([0.086, 0.087])

for T in Ts:
    print('Ramping to ', T)
    adr.rampTo(T)
    adr.stabilizeTemperature(T)
    time.sleep(30)
    
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
adr.rampTo(0.120)

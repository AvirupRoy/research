# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 11:08:29 2017

@author: wisp10
"""

from __future__ import print_function
import time
import numpy as np
from PyQt4.QtCore import QCoreApplication
from TES import IvCurveDaqRemote
from Adr import Adr

Thigh = 0.085
Tlow = 0.060    

#Vcoils = np.asarray([-0.4,-0.3,-0.2,-0.1,0.1])
#Vcoils = np.asarray([-1.0, -0.9, -0.8, -0.7, -0.6, -0.5])
Vstep = 0.05
Vcoils = np.arange(3.35, 4.+Vstep, Vstep)
rampRateDown = -0.5 # Slow
rampRateUp   = +4.0 # Fast
app = QCoreApplication([])
adr = Adr(app)
ivRemote = IvCurveDaqRemote.IvCurveDaqRemote('TesIvVsTramp_Bstep')
print(ivRemote.auxAoVoltage())

for Vcoil in Vcoils:
    print('Now going for Vcoil=', Vcoil)
    adr.setRampRate(rampRateUp)
    adr.rampTo(Thigh)
    print('Ramping up...')
    adr.stabilizeTemperature(Thigh)
    print('Stable.')
    time.sleep(30)
    adr.setRampRate(rampRateDown)
    ivRemote.setAuxAoVoltage(Vcoil)
    print('Starting measurement.')
    ivRemote.start()
    time.sleep(30)
    print('Ramping down.')
    adr.rampTo(Tlow)    
    adr.stabilizeTemperature(Tlow, timeOut=60*60)
    print('Stopping measurement')
    ivRemote.stop()    
    time.sleep(30)
    
adr.setRampRate(rampRateUp)
adr.rampTo(0.150)

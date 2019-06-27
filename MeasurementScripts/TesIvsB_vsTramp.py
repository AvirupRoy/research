# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 11:08:29 2017

@author: wisp10
"""

from __future__ import print_function
import time
import numpy as np
from PyQt4.QtCore import QCoreApplication
from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote
from TES import IvCurveDaqRemote
from Adr import Adr


device = 'TES2'
Rb =  6.8735E3
Ibiases = np.asarray([150E-6, -150E-6, 200E-6, -200E-6])
#Ibiases = np.asarray([-400E-6])
Vbiases = Ibiases*Rb

Thigh = 0.085
Tlow = 0.065

app = QCoreApplication([])
adr = Adr(app)
ivRemote = IvCurveDaqRemote.IvCurveDaqRemote('TesIcVsB')
print(ivRemote.auxAoVoltage())
osr = OpenSquidRemote(port = 7894)
pfl = Pfl102Remote(osr, device)

def waitForSweeps(remote, n=1):
    count = ivRemote.sweepCount()
    newCount = 0
    while newCount < count+n:
        time.sleep(1)
        app.processEvents()
        newCount = ivRemote.sweepCount()

for Vbias in Vbiases:
    print('Now going for Vbias=', Vbias)
    adr.setRampRate(8)
    adr.rampTo(Thigh)
    print('Ramping up...')
    adr.stabilizeTemperature(Thigh)
    print('Stable.')
    time.sleep(10)
    pfl.resetPfl()
    adr.setRampRate(0.5)
    ivRemote.setAuxAoVoltage(0)
    print('Starting measurement.')
    ivRemote.start()
    time.sleep(5)
    waitForSweeps(ivRemote,2)
    print('Setting bias.')
    ivRemote.setAuxAoVoltage(Vbias)
    waitForSweeps(ivRemote,2)
    print('Ramping down.')
    adr.rampTo(Tlow)    
    adr.stabilizeTemperature(Tlow, timeOut=45*60)
    ivRemote.setAuxAoVoltage(0)
    print('Turning off bias')
    waitForSweeps(ivRemote,2)
    print('Stopping measurement')
    ivRemote.stop()    
    time.sleep(15)
    
adr.setRampRate(8)
adr.rampTo(0.084)

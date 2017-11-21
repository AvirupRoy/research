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
#from Adr import Adr


device = 'TES2'
#Rb =  6.8735E3
#Ibiases = np.asarray([150E-6, -150E-6, 200E-6, -200E-6])
#Ibiases = np.asarray([-400E-6])
#Vbiases = Ibiases*Rb
step = 0.1
Vbiases = np.hstack([np.arange(5, 2, -0.1),np.arange(2, 0.8, -0.010)])

app = QCoreApplication([])
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

ivRemote.setAuxAoVoltage(Vbiases[0])
time.sleep(2)

pfl.resetPfl()
ivRemote.start()
time.sleep(15) # Need to wait for sweep count to reset...

for Vbias in Vbiases:
    print('Setting bias:', Vbias)
    ivRemote.setAuxAoVoltage(Vbias)
    waitForSweeps(ivRemote,2)

ivRemote.stop()    
time.sleep(15)
ivRemote.setAuxAoVoltage(0)

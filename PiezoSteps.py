# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 12:53:55 2016

@author: wisp10
"""

from PiezoControlRemote import PiezoControlRemote

origin = 'PiezoSteps'
piezo = PiezoControlRemote(origin = origin)

print "Testing communications:"
piezoRampTarget = piezo.rampTarget()
if piezoRampTarget is None:
    raise Exception('Cannot communicate with piezo')
print "Piezo target:", piezoRampTarget

import time

holdTime = 4*60

#Vpiezos = [0, +140, 0, -140, 0] #, +120, 0, -120, 0, +160, 0, -160, 0]
Vpiezos = [+120,0,-120,0,+160, 0, -160, 0]
import numpy as np
#Vpiezos = np.arange(120, 160, 10)
#Vpiezos = np.hstack([Vpiezos, np.arange(160, -160, -40)])
#Vpiezos = np.hstack([Vpiezos, np.arange(-160, 5, 40)])
#Vpiezos = [120, 130, 140, 150, 160, 150, 140, 130, 120, 0, -120, -130, -140, -150, -160, -150, -140, -130, -120, 0]
#Vpiezos = [+40, 0, +80, 0, 120, 0, -40, 0, -80, 0, +120, 0, -125, 0]
#Vpiezos = [+40, 0, +80, 0, +20, 0]
#Vpiezos = [+125, 0, -125, 0]
print Vpiezos

while True:
    for Vp in Vpiezos:
        print "New piezo voltage:", Vp
        piezo.setRampTarget(Vp)
        piezo.startRamp()
        print "Holding..."
        time.sleep(holdTime)

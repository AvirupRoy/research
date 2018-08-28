# -*- coding: utf-8 -*-
"""
Just some quick code to help me catalogue and compare the various transfer functions taken with the pulses
Created on Tue Mar 27 13:04:33 2018

@author: wisp10
"""
from __future__ import print_function, division
import ast
import matplotlib.pyplot as mpl
from Analysis.SineSweep import SineSweep
from Analysis.G4C.MeasurementDatabase import obtainTes
from Calibration.RuOx import getCalibration
cooldown = 'G5C'; deviceId = 'TES1'
path = 'D:\\Users\\Runs\\%s\\TF\\' % cooldown

cal = getCalibration('RuOx2005')
tes = obtainTes(cooldown, deviceId)

#fileNames = ['TES1_20180326_214310.h5', 'TES1_20180326_213552.h5']; # 120mK, 10kOhm, 100kOhm, normal
#fileNames = ['TES1_20180326_204354.h5', 'TES1_20180326_203444.h5'] # just above 60mK, 100kOhm, 10kOhm, superconducting
fileNames = ['TES1_20180326_195940.h5', 'TES1_20180326_194736.h5'] # 60mK, 10KOhm, 100kOhm, Vbias=1.92
fileNames = ['TES1_20180326_155444.h5', 'TES1_20180326_155140.h5'] # 55mK, 100kOhm, 10kOhm, superconducting
fileNames = ['TES1_20180326_154605.h5', 'TES1_20180326_154258.h5'] # 55mK, 10kOhm, 100kOhm, Vbias=2.00

fileNames = ['TES1_20180323_153128.h5', 'TES1_20180323_152543.h5'] # 120mK, 10kOhm, 100kOhm, normal
fileNames = ['TES1_20180323_152115.h5'] # 100kOhm with 15nF, normal
fileNames = ['TES1_20180323_043927.h5'] # 60mK, SC, 100kOhm, 15nF
fileNames = ['TES1_20180323_042352.h5'] # 60mK, Vbias=2.15, 100kOhm, 1.5nF

# Compare all the superconducting 100kOhm, 1.5nF -> They are right on top of each other, good!
fileNames = ['TES1_20180326_204354.h5', 'TES1_20180326_155444.h5'] # 60mK, 55mK 

# Compare all the normal 100kOhm, 1.5nF -> also right on top each other, good!
fileNames = ['TES1_20180326_213552.h5', 'TES1_20180323_152543.h5'] 


ivFileNames = ['TES1_IV_20180326_213434.h5', 'TES1_IV_20180326_213211.h5']


ax = None
for fileName in fileNames:
    ss = SineSweep(path+fileName)
    metaData = ast.literal_eval(ss.comment)
    Rfb = metaData['Rfb']
    Cfb = metaData['Cfb']
    Vbias = metaData['Vbias']
    Vcoil = metaData['Vcoil']
    Rsq = tes.Rsquid(Rfb)

    Rmean = ss.adrR.mean()
    Tsensor = cal.calculateTemperature(Rmean)
    
    print('Filename:', fileName)
    print('Rfb:', Rfb)
    print('Cfb:', Cfb)
    print('Vbias:', Vbias)
    print('Sensor temperature:', Tsensor)

    ss.TF /= Rsq # convert to I(f)
    
    #ss.comment
    label = 'Rfb=%.0fk$\\Omega$, Vbias=%.3f V' % (1E-3*Rfb, Vbias)
    ss.plotPolar(label=label)
    #ax = ss.plotXY(ax, label=label)
    
    #axes = ss.plotRPhi(axes)
    print('Amplitude:', ss.amplitude)
    #mpl.semilogx(ss.t-ss.t[0], ss.Vdc)
 
mpl.legend()       
mpl.show()

# -*- coding: utf-8 -*-
"""
Created on Mon Nov 06 17:02:45 2017

@author: wisp10
"""
from Analysis.TesIvSweepReader import IvSweepCollection
from Analysis.G4C.MeasurementDatabase import obtainTes
import matplotlib.pyplot as mpl
import numpy as np
cooldown = 'G4C'
deviceId = 'TES2'
path = 'D:\\Users\\Runs\\%s\\IV\\' % cooldown
fileName = 'TES2_IV_20171104_041421.h5'


Rgoal = 1.2E-3
Pgoal = 1.5E-12

tes = obtainTes(cooldown, deviceId)
sweeps = IvSweepCollection(path+fileName)
Rfb = sweeps.info.pflRfb


Vteses = []
Iteses = []
Vbiases = []

for sweep in sweeps:
    #sweep.plotRaw()
    MiOverMfb = tes.MiOverMfb(Rfb)
    shift =  sweep.checkForOffsetShift()
    print(shift)
    sweep.subtractSquidOffset()
    sweep.applyCircuitParameters(Rb=tes.Rbias, Rfb=Rfb, Rs=tes.Rshunt, Mfb=1.0, Mi=MiOverMfb)
    Vbias, Ites, Vtes = sweep.findBiasPoint('R', Rgoal)
    #Vbias, Ites, Vtes = sweep.findBiasPoint('P', Pgoal)
#    iSelect = sweep.iRampDo1 & (sweep.Vtes>2E-10)
#    i = np.argmin(np.abs(sweep.Ites[iSelect] - ItesGoal))
#    Ites = sweep.Ites[iSelect][i]
#    Vb = sweep.Vbias[iSelect][i]
#    Vtes = sweep.Vtes[iSelect][i]
    
    Iteses.append(Ites)
    Vbiases.append(Vbias)
    Vteses.append(Vtes)

    print ('Bias:,', Vbias)
#    sweep.plot()
#    mpl.scatter(Vtes, Ites)

    sweep.plotRaw()
    mpl.scatter(Vbias, Ites*Rfb)

fit = np.polyfit(Iteses, Vbiases, 1)    
#Vbias = np.polyval(fit, ItesGoal)


mpl.show()

# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 14:21:54 2018

@author: wisp10
"""






import h5py as hdf
from Analysis.TesIvSweepReader import IvSweepCollection
from Analysis.G4C.MeasurementDatabase import obtainTes
import matplotlib.pyplot as mpl
#import numpy as np

cooldown = 'G5C'
device = 'TES1'

tes = obtainTes(cooldown, device)
path = 'D:/Users/Runs/%s/IV/' % cooldown


#fileNames = ['TES1_IV_20180326_213434.h5', 'TES1_IV_20180326_213211.h5'] # 120mK, Rfb=100k:Rn=6.6675 mOhm, Rfb=10k:Rn=6.6676mOhm
fileNames = ['TES1_IV_20180326_154913.h5']; Vbias = 2.0 # For 55mK, Vbias=2.0, get R = 0.8744mOhm, Ttes=84.933mK
#fileNames = ['TES1_IV_20180326_000118.h5']; Vbias = 2.15 # For 55mK, Vbias=2.15, get R= 1.0856mOhm, Ttes=85.245mK
#fileNames = ['TES1_IV_20180326_154913.h5']; Vbias = 2.15 # For 55mK, Vbias=2.0, get R = 1.0844mOhm, Ttes=85.256mK

for fileName in fileNames:
    sweeps = IvSweepCollection(path+fileName)
    print('Comment:', sweeps.info.comment)
    Rfb = sweeps.info.pflRfb
    print('Rfb=', Rfb)
    Rsq = tes.Rsquid(Rfb)
    MiOverMfb = tes.MiOverMfb(Rfb)
    
    Rn = 0.00625
    for i in range(0, len(sweeps), 1):
        sweep = sweeps[i]
        print('Tbase=', sweep.Tadr)
        sweep.subtractSquidOffset()
        sweep.findTesBias(tes.Rbias, tes.Rshunt, Rsq)
        #R0, dRdVbias = sweep.fitRtesCloseTo('Vbias', Vbias, n=3, order=1)
        Tbase = sweep.Tadr
        
        sweep.applyThermalModel(tes.temperature, Tbase)
        I0, R0, T0, alpha_IV = sweep.findAlphaIvCloseTo('Vbias', Vbias, n=10, order=1)
        print('I0, R0, T0, alphaIV=', I0, R0, T0, alpha_IV)
        
        Rn = sweep.fitRn(1E-10)
        print('Rn=', Rn)
        sweep.plot()
        
        
mpl.show()

# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 13:53:44 2017

@author: wisp10
"""

import h5py as hdf
import numpy as np
from Analysis.TesIvSweepReader import IvSweepCollection
from MeasurementDatabase import obtainTes

path = '..\\..\\MeasurementScripts\\'
fileName = path+'TES2_Shapiro_20171215_003919.h5'

class ShapiroImporter(object):
    def __init__(self, fileName):
        with hdf.File(fileName, 'r') as f:
            sweepCount = f.attrs['sweepCount']
            self.VcoilDcs = np.empty((sweepCount,), dtype=float)
            self.VcoilAcs = np.zeros_like(self.VcoilDcs)
            self.VcoilAcFs = np.zeros_like(self.VcoilDcs)
            self.Tbases = np.zeros_like(self.VcoilDcs)
            self.fileNames = []
            
            for i in range(sweepCount):
                g = f['Shapiro%05d' % i]
                a = g.attrs
                self.VcoilDcs[i] = a['VcoilDc']
                self.VcoilAcs[i] = a['VcoilAc']
                self.VcoilAcFs[i] = a['VcoilAcF']
                self.Tbases[i] = a['Tbase']
                self.fileNames.append(a['IvSweepFileName'])
    def ivSweeps(self, i):
        sweeps = IvSweepCollection(self.fileNames[i])
        return sweeps
        

cooldown = 'G4C'
deviceId = 'TES2'
tes = obtainTes(cooldown, deviceId)

shapiro =  ShapiroImporter(fileName)

np.unique(shapiro.VcoilAcs)

select = np.where(shapiro.VcoilAcs==0.1)[0]

import matplotlib.pyplot as mpl
Rfb = 10E3

fAc = np.unique(shapiro.VcoilAcFs)

h = 6.62607004E-34
q_e = 1.60217662E-19

Vshapiro = h*fAc/(2*q_e)
Voffset = +0.015E-9
for i in select:
    sweeps = shapiro.ivSweeps(i)
    sweep = sweeps[0]
    sweep.subtractSquidOffset(zeros=[0,2])
    sweep.findTesBias(tes.Rbias, tes.Rshunt, tes.Rsquid(Rfb))
    i = sweep.iRampDo1
    mpl.plot(1E9*(sweep.Vtes[i]+Voffset), 1E6*sweep.Ites[i])
    #sweep.plotDetails()
    #sweep.plot()
mpl.vlines(np.arange(1, 40)*Vshapiro*1E9, 0, 100)

mpl.show()

# -*- coding: utf-8 -*-
"""
Created on Wed Dec 09 18:20:47 2015

@author: wisp10
"""
import matplotlib.pyplot as mpl
import h5py as hdf
import numpy as np
from TES_IVSweepsDaq import determineCriticalCurrent
   
#name = 'D:\\Users\\FJ\\ADR3\\TES\\RealDeal_20151209-181904_IV.h5'
#name = 'D:\Users\FJ\ADR3\TES\RealDeal_20151209-190132_IV.h5'
#name = 'D:\Users\FJ\ADR3\TES\RealDeal_20151210-004328_IV.h5'
#name = 'D:\Users\FJ\ADR3\TES\RealDeal_20151209-230251_IV.h5'
#name = 'D:\Users\FJ\ADR3\TES\RealDeal_20151210-133921_IV.h5'
#name = 'D:\Users\FJ\ADR3\TES\RealDeal_20151210-173458_IV.h5'
#name = 'RealDeal_20151211-171207_IV.h5'
#name = 'RealDeal_20151212-032847_IV.h5'
#name = 'RealDeal_20151211-180611_IV.h5'
name = 'RealDeal_20151211-180611_IV.h5'
print "File:", name
f = hdf.File(name, mode='r')
sweeps = f['Sweeps']
Vcs = []
Ics = []
Vcoils = []
nSweeps = len(sweeps.keys())
print "Number of sweeps:", nSweeps
Rthermos = []
for i in range(0, nSweeps):
    try:
        sweep = sweeps['%d' % i]
    except:
        print "Missing sweep", i
        continue
    try:
        Vc = sweep.attrs['VcritDrive']
        Ic = sweep.attrs['VcritMeas']
    except:
        print "Sweep", i
        Vc, Ic = determineCriticalCurrent(Vdrives, Vmeas)
        mpl.plot(Vc, Ic, 'o')
    try:
        R = sweep.attrs['Rthermometer']
    except:
        R = np.nan
    Rthermos.append(R)
    Vdrives = np.asarray(sweep['Vdrive'])
    Vmeas = np.asarray(sweep['Vmeasured'])
    mpl.plot(Vdrives, Vmeas,'-')
    Vcoil = sweep.attrs['Vcoil']
    Vcs.append(Vc)
    Ics.append(Ic)
    Vcoils.append(Vcoil)
mpl.show()

Ics = np.asarray(Ics)
Vcs = np.asarray(Vcs)
Vcoils = np.asarray(Vcoils)
Rthermos = np.asarray(Rthermos)
plus = Vcs >= 0
minus = Vcs < 0
mpl.figure()
mpl.plot(Rthermos[plus], Vcs[plus], '.-b')
mpl.plot(Rthermos[minus], Vcs[minus], '.-b')
mpl.xlabel('$R_{thermo}$ [$\\Omega$]')
mpl.ylabel('$V_{bias}^{crit}$')
mpl.figure()
mpl.plot(Vcoils[plus], Vcs[plus], '.-b')
mpl.plot(Vcoils[minus], Vcs[minus], '.-r')
mpl.xlabel('$I_{coil}$ [mA]')
mpl.ylabel('$V_{bias}^{crit}$')
mpl.show()
mpl.figure()
mpl.plot(Vcoils[plus], Ics[plus], '.-b')
mpl.plot(Vcoils[minus], Ics[minus], '.-r')
mpl.xlabel('$I_{coil}$ [mA]')
mpl.ylabel('$I_{TES}^{crit}$')
mpl.show()

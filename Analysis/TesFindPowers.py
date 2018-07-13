# -*- coding: utf-8 -*-
"""
Extract TES power for constant resistance from IV sweeps
This is then used in a second step to extract thermal conductance G(T)
Created on Tue Oct 17 16:52:57 2017
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from Analysis.TesIvSweepReader import IvSweepCollection
import matplotlib.pyplot as mpl
import numpy as np
import h5py as hdf
import time

cooldown = 'G5C'
deviceId = 'TES2'
path = 'D:/Users/Runs/%s/IV/' % cooldown
from G4C.MeasurementDatabase import obtainTes

if cooldown == 'G4C':

    if deviceId == 'TES1':
        fileName = 'TES1_IV_20171016_192024.h5'
        #fileName = 'TES1_IV_20171020_211121.h5' # vs field
        #fileName = 'TES1_IV_20171021_002721.h5' # vs filed
        #fileName = 'TES1_IV_20171023_085630.h5'
        #fileName = 'TES1_IV_20171023_070138.h5'
        fileName = 'TES1_IvsB_20171110_192055.h5'
    elif deviceId == 'TES2':
        fileName = 'TES2_IV_20171017_203505.h5'
elif cooldown == 'G5C':
    #from G5C.MeasurementDatabase import obtainTes
    if deviceId == 'TES1':
        fileName = 'TES1_IV_20180217_212544.h5' # Pre-coil fix
        fileName = 'TES1_IV_20180227_033138.h5'
        fileName = 'TES1_20180227_021040.h5'
    elif deviceId == 'TES2':
        fileName = 'TES2_20180306_153815.h5'
        #fileName = 'TES2_IV_20180402_150627.h5' # This file has sharp features in IV curve that make analysis difficult

tes = obtainTes(cooldown, deviceId)


#percentOfRn = np.arange(0.4, 1, 0.02) #np.asarray([0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
percentOfRn = np.asarray([0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.825, 0.85, 0.85, 0.86, 0.87, 0.88, 0.89, 0.9, 0.91, 0.92, 0.93])
sweeps = IvSweepCollection(path+fileName)

Rfb = sweeps.info.pflRfb
print('Rfb=%.3fkOhm' % (Rfb/1E3))
MiOverMfb = tes.MiOverMfb(Rfb)
Rn = tes.Rnormal
iRamp = sweeps.iRampDo1

fig, axes = mpl.subplots(3,1, sharex=True)

Ps = np.zeros((len(sweeps), len(percentOfRn)))
Tbases = np.zeros((len(sweeps),))
plotSweeps = range(0, len(sweeps), 20)

hk = sweeps.hk
if hk is not None:
    thermoId = 'RuOx2005Thermometer'
    thermo = hk.thermometers[thermoId]
else:
    thermo = None

for sweepNumber, sweep in enumerate(sweeps[::1]):
    sweep.correctSampleDelay()
    sweep.subtractSquidOffset()
    
#    mpl.figure()
#    sweep.plotRaw()
    #sweep.plot(np.polyval([slope,offset], ))
    sweep.applyCircuitParameters(tes.Rbias, Rfb, tes.Rshunt, Mfb=1.0, Mi=MiOverMfb)
#    mpl.figure()    
#    sweep.plot()
#    mpl.xlabel('Vtes')
#    mpl.ylabel('Ites')
    
#    mpl.figure()
    iSelect = iRamp & (sweep.Vtes > 1E-11) & (sweep.Ites > 1E-6)

    for i, relRn in enumerate(percentOfRn):
        try:
            k = np.where(sweep.Rtes[iSelect]>=relRn*Rn)[0][-1]  # The last index matters!
            P = sweep.Ptes[iSelect][k]
            Ps[sweepNumber,i] = P
        except IndexError:
            pass
    
    if thermo is None:
        Tbases[sweepNumber] = sweep.Tadr
    else:
        t0 = sweep.time
        i = (t0-20 <= thermo.t) & (thermo.t < t0+20)
        fit = np.polyfit(thermo.t[i] - t0, thermo.Tbase[i], 1)
        Tb = fit[1]; print('rate=%.3f mK/s'% (1E3*fit[0]))
        Tbases[sweepNumber] = Tb
    
    if sweepNumber in plotSweeps:
        x = sweep.Vtes[iSelect]*1E9
        x = sweep.Ibias[iSelect]*1E6
        axes[0].plot(x, sweep.Ites[iSelect]*1E6)
        axes[1].plot(x, sweep.Rtes[iSelect]*1E3)
        axes[2].plot(x, sweep.Ptes[iSelect]*1E12)

with hdf.File(path+deviceId+'_FindG.h5', 'w') as f:
    f.attrs['sourceFile'] = fileName
    f.attrs['deviceId'] = deviceId
    f.attrs['program'] = 'TesFindG.py'
    f.attrs['time'] = time.time()
    f.attrs['deviceName'] = tes.DeviceName
    f.attrs['Rbias'] = tes.Rbias
    f.attrs['Rshunt'] = tes.Rshunt
    f.attrs['Rnormal'] = tes.Rnormal
    f.attrs['MiOverMfb'] = MiOverMfb
    f.create_dataset('Tbase', data=Tbases)
    f.create_dataset('Ps', data=Ps)
    f.create_dataset('percentOfRn', data=percentOfRn)

axes[0].set_ylabel(u'$I_{TES}$ ($\\mu$A)')
axes[0].set_ylim(-50, +200) # Not sure yet
axes[1].hlines(percentOfRn*Rn*1E3, np.min(x), np.max(x))
axes[1].set_ylim(-0.05*Rn*1E3, +1.05*Rn*1E3)
axes[1].set_ylabel(u'$R_{TES}$ (m$\\Omega$)')
axes[2].set_ylabel(u'$P_{TES}$ (pW)')
#axes[2].set_xlabel(u'$V_{TES}$ (nV)')
axes[2].set_xlabel(u'$I_{bias}$ ($\\mu$A)')
mpl.suptitle('%s' % tes.DeviceName)

mpl.figure()
for i,relRn in enumerate(percentOfRn):
    mpl.plot(Tbases*1E3, Ps[:,i]*1E12, '.', label='%.1f' % (relRn*100))

mpl.xlabel(u'$T_{base}$ (mK)')    
mpl.ylabel(u'$P_{TES}$ @ $R_n$ (pW)')
mpl.legend()
mpl.show()

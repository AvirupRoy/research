# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 13:43:19 2017

@author: wisp10
"""
import h5py as hdf
from Analysis.TesIvSweepReader import IvSweepCollection
import matplotlib.pyplot as mpl
import numpy as np
from G4C.MeasurementDatabase import obtainTes
#from Analysis.FileTimeStamps import filesInDateRange
import time
from scipy.optimize import curve_fit
cooldown = 'G8C'
deviceId = 'TES3'

tes = obtainTes(cooldown, deviceId)

#path = '/Volumes/Gray Matter/Work/TES_Data/%s/IV/' % cooldown
path = '/Users/calorim/Documents/ADR3/%s/IV/TES3/' % cooldown
fileNames = []
if cooldown == 'G4C':
    Rcoil = 1152.7
    suffix = ''
    if deviceId == 'TES1':
        
        #fileName = 'TES1_IcVsB_80mK_20171017_140138.h5' #Bad file
        #fileName = 'TES1_IcVsB_80mK_20171017_141936.h5' # Up
        #fileName = 'TES1_IcVsB_80mK_20171017_144653.h5' # Down
        #fileName = 'TES1_IcVsB_82mK_20171017_151934.h5' # Up
        #fileName = 'TES1_IcVsB_82mK_20171017_155641.h5' # Down
        #fileName = 'TES1_IcVsB_84mK_20171017_164324.h5' # Down
        #fileName = 'TES1_IcVsB_84mK_20171017_171906.h5' # Up
        #fileName = 'TES1_IcVsB_85mK_20171017_180133.h5' # Up
        #fileName = 'TES1_IcVsB_86mK_20171017_185450.h5' # Up
        #fileName = 'TES1_IcVsB_86mK_20171017_191242.h5' # Down
        #fileName = 'TES1_IcVsB_87mK_20171017_193048.h5' # Up
        #fileName = 'TES1_IcVsB_87mK_20171017_194506.h5' # Down
        fileName = 'TES1_IV_20171016_192024.h5'
        #fileName = 'TES1_IcVsB_20171020_153007.h5' # After ADR recycle, 80mK
        #fileName = 'TES1_IcVsB_20171020_155949.h5' # 81mK
        #fileName = 'TES1_IcVsB_20171020_162933.h5' # 82mK
        #fileName = 'TES1_IcVsB_20171020_165938.h5' # 83mK
        #fileName = 'TES1_IcVsB_20171020_172927.h5' # 84mK
        #fileName = 'TES1_IcVsB_20171020_175910.h5' # 85mK
        #fileName = 'TES1_IcVsB_20171020_185019.h5' # 86mK
        #fileName = 'TES1_IcVsB_20171020_192009.h5' # 87mK
        
    elif deviceId == 'TES2':
        pass
        # These are now up & down
        #fileName = 'TES2_IcVsB_20171019_065347.h5' # This seems to be pretty much normal
        #fileName = 'TES2_IcVsB_20171019_050558.h5' # 83mK
        #fileName = 'TES2_IcVsB_20171019_042105.h5' # 82mK
        #fileName = 'TES2_IcVsB_20171019_033557.h5'  # 80mK
        #fileName = 'TES2_IcVsB_20171019_025049.h5' # 77.5mK
        #fileName = 'TES2_IcVsB_20171019_020537.h5' # 75mK
        #fileName = 'TES2_IcVsB_20171019_011955.h5' # 70mK
        #fileName = 'TES2_IcVsB_20171019_134625.h5' # 81 mK
        #fileName = 'TES2_IcVsB_20171019_143310.h5' # 79 mK, +-2V
        #fileName = 'TES2_IcVsB_20171019_160508.h5' # 74 mK, +-10, up only
        #fileName = 'TES2_IcVsB_20171019_165817.h5' # 76 mK, +-5V, up only
        #fileName = 'TES2_IcVsB_20171019_173639.h5' # 77 mK, +-5V, up only
        #fileName = 'TES2_IcVsB_20171019_180550.h5' # 77 mK, +-5V, down only
        #fileName = 'TES2_IcVsB_20171019_184301.h5' # 75 mK, +-5V, up only
        #fileName = 'TES2_IcVsB_20171019_191901.h5' # 78 mK, +-4.5V, up only
        #fileName = 'TES2_IcVsB_20171019_203451.h5' # 79 mK
        #fileName = 'TES2_IcVsB_20171019_210456.h5' # 80 mK
        #fileName = 'TES2_IcVsB_20171019_213426.h5' # 81 mK
        #fileName = 'TES2_IcVsB_20171019_220422.h5' # 82 mK Not working? Division by zero
        
        #fileName = 'TES2_IcVsB_20171020_140250.h5' # 76 After ADR recycle
        #fileName = 'TES2_IcVsB_20171020_143235.h5' # 77
        #fileName = 'TES2_IV_20180116_051423.h5' # 80
        #fileName = 'TES2_IV_20180116_035921.h5' # 77
        #fileName = 'TES2_IV_20180116_024418.h5' # 75
        #fileName = 'TES2_IV_20180116_012826.h5' # 73
        #fileName = 'TES2_IV_20180116_001316.h5' # 71
        #fileName = 'TES2_IV_20180115_225750.h5' # 69 mK
        #fileName = 'TES2_IV_20180115_214219.h5' # 67mK
        #fileName = 'TES2_IV_20180115_202641.h5'
        #fileName = 'TES2_IV_20180115_191024.h5' # 63mK
    fileName = path+fileName
    
if cooldown == 'G5C':
    if deviceId == 'TES1':
        if False:
            suffix = ''
            Rcoil = 1152. # pre ADR deflux
            #fileNames = filesInDateRange(path+'TES1_IcVsB_*.h5', '20180217_002313', '20180218_103957')
            #fileNames = filesInDateRange(path+'TES1_IcVsB_*.h5', '20180218_170840', '20180219_062019')
            #ileNames = filesInDateRange(path+'TES1_IcVsB_*.h5', '20180219_195524', '20180220_110725') # Now with isolated drive
            #fileName = fileNames[9]
            #fileName = 'TES1_IcVsB_20180218_002313.h5'
            #fileName = path+'TES1_IcVsB_20180220_112517.h5' # Quick test run
            fileNames = filesInDateRange(path+'TES1_IcVsB_*.h5', '20180220_122034', '20180220_232216') # Covering wider Vcoil span
        
        if False:
            suffix = '_Detrap'
            Rcoil = 1128.8 # After 2018-02-22 14:03 (doubled up on coil wiring)
            #fileName = path+'TES1_IcVsB_20180222_150538.h5'
            #fileName = path+'TES1_IcVsB_20180222_152936.h5'
            fileNames = filesInDateRange(path+'TES1_IcVsB_*.h5', '20180222_184415', '20180223_232204')
            print('Number of files:', len(fileNames))
        
    if deviceId == 'TES2':
        if False:
            suffix = ''
            Rcoil = 1152. # pre ADR deflux
            #fileName = path+'TES2_IcVsB_20180220_221036.h5'
            fileNames = filesInDateRange(path+'TES2_IcVsB_*.h5', '20180221_001957', '20180221_084049')
            #fileName = fileNames[9]
            #fileName = path+'TES2_IcVsB_20180221_095138.h5' # Hysteresis test
            #fileName = path+'TES2_IcVsB_20180221_103855.h5' # Hysteresis test
            #fileName = path+'TES2_IcVsB_20180221_105455.h5' # Hysteresis test
            #fileName = path+'TES2_IcVsB_20180221_120341.h5' # Hysteresis without crossing the kink

        if False:
            # Post ADR deflux at 20K
            suffix = '_Detrap'
            Rcoil = 1128.8 # After 2018-02-22 14:03 (doubled up on coil wiring)
            fileNames = filesInDateRange(path+'TES2_IcVsB_*.h5', '20180306_210250', '20180307_101750')
            #fileName = path+'TES2_IcVsB_20180306_210250.h5'
            #fileName = path+'TES2_IcVsB_20180306_223048.h5'
            #fileName = path+'TES2_IcVsB_20180306_233739.h5'

if cooldown == 'G8C':
    if deviceId == 'TES3':
        Rcoil = 1024.
        fileNames = ['TES3_IcvsBvsT_20190411_145326.h5','TES3_IcvsBvsT_20190411_151656.h5',
                 'TES3_IcvsBvsT_20190411_154026.h5','TES3_IcvsBvsT_20190411_162154.h5',
                 'TES3_IcvsBvsT_20190411_164210.h5','TES3_IcvsBvsT_20190411_170325.h5',
                 'TES3_IcvsBvsT_20190411_172639.h5']
            


if len(fileNames) >= 1:
    i = int(input('Which one do you want to process? (0-%d)' % (len(fileNames)-1)))
    fileName = fileNames[i]

fileName =path+fileName
doSave = True    
sweeps = IvSweepCollection(fileName)

VcritsPos = []
VcritsNeg = []
Vcoils = []

hk = sweeps.hk
if hk is None:
    Tadrs = np.asarray([sw.Tadr for sw in sweeps])
else:
    Tadrs = hk.thermometers['RuOx2005Thermometer'].Tbase

TadrMean = np.nanmean(Tadrs)
TadrStd  = np.nanstd(Tadrs)

print('File name:', fileName)
print('Tadr=%.3f +- %.3f mK' % (1E3*TadrMean, 1E3*TadrStd))

Rfb = sweeps.info.pflRfb
MiOverMfb = tes.MiOverMfb(Rfb)

IcritsPos = np.ones((len(sweeps),), dtype=float)*np.nan
IcritsNeg = IcritsPos.copy()
Vcoils = IcritsPos.copy()

iUp = sweeps.iRampUp1
iDo = sweeps.iRampDo2

Vthreshold = 2.0
Tcguess = 78E-3

for sweepNumber, sweep in enumerate(sweeps):
    sweep.subtractSquidOffset()
    shift = np.any(sweep.checkForOffsetShift())
    sweep.applyCircuitParameters(tes.Rbias, Rfb, tes.Rshunt, Mfb=1.0, Mi=MiOverMfb)
    
    iCritPos = np.where(iUp & (sweep.Vtes > Vthreshold) & Tadrs<Tcguess)[0][0]
    IcritPos = sweep.Ibias[iCritPos]
    IcritsPos[sweepNumber] = IcritPos
    
    iCritNeg = np.where(iDo & (sweep.Vtes < -Vthreshold) & Tadrs<Tcguess)[0][0]
    IcritNeg = sweep.Ibias[iCritNeg]
    IcritsNeg[sweepNumber] = IcritNeg
    
#    if shift:
#        print('Found offset shift in sweep #', sweepNumber)
#        IcritsPos[sweepNumber] = np.nan
#        IcritsNeg[sweepNumber] = np.nan
        

    Vcoils[sweepNumber] = sweep.auxAoValue
    
def fitCriticalCurrent(Tadr,Ic0,Tc,beta):
        Ic = Ic0*np.power((1-Tadr/Tc),beta)
        return Ic


fitNeeded = False

if fitNeeded:
    fitGuess = [200*1E6,Tcguess,1]
    fit, pcov = curve_fit(fitCriticalCurrent, Tadrs, IcritsPos, fitGuess)
    Ic0 = fit[0]
    Tc = fit[1]
    beta = fit[2]
    fitx = np.linspace(0,150)
    print('Ic0 =%.2fmA\n' % Ic0,'Tc=%.2fmK\n' % Tc, 'beta=%.2f\n' % beta)

import os

doSave = True
if doSave:
    with hdf.File(path+deviceId+'_Analysis_IcVsB%s.h5' % suffix, 'a') as f:
        name = os.path.basename(fileName)        
        key = '.'.join(name.split('.')[:-1])
        if key in f.keys():
            del f[key]
        g = f.create_group(key)
        g.attrs['sourceFile'] = fileName
        g.attrs['cooldown'] = cooldown
        g.attrs['deviceId'] = deviceId
        g.attrs['program'] = 'TesIvSweep_IcVsB.py'
        g.attrs['time'] = time.time()
        g.attrs['TadrMean'] = TadrMean
        g.attrs['TadrStd'] = TadrStd
        g.attrs['Rcoil'] = Rcoil
        #g.attrs['deviceName'] = tes.deviceName
        g.attrs['Rb'] = tes.Rbias
        g.create_dataset('Vcoil', data=Vcoils)
        g.create_dataset('IcritPos', data=IcritsPos)
        g.create_dataset('IcritNeg', data=IcritsNeg)

mpl.plot(Vcoils, 1E6*IcritsPos, '.-r', label='+', ms=1)
mpl.plot(Vcoils, 1E6*IcritsNeg, '.-b', label='-', ms=1)
mpl.xlabel('Coil drive (V)')
mpl.ylabel('Critical current (uA)')
mpl.legend(loc='best', title='Bias polarity')
mpl.suptitle('Critical current vs. B')
mpl.show()
mpl.figure()
mpl.plot(Tadrs*1E3,IcritsPos*1E6,'r.',label='pos')
mpl.plot(Tadrs*1E3,np.negative(IcritsNeg)*1E6,'b.',label='neg')
if fitNeeded:
    mpl.plot(fitx,fitCriticalCurrent(fitx,*fit), label=' fit')
mpl.xlabel('Adr temperature(mK)')
mpl.ylabel('Critical current ($\mu$A)')
mpl.yscale('log')
mpl.legend(loc='best',title='Bias polarity')
mpl.suptitle('Temp dependence of critical current')

#mpl.subplot(2,1,1)
#mpl.plot(sweep.Vbias[iUp], sweep.Vsquid[iUp])
#mpl.vlines(Vcrit, 0, 1 )
#mpl.subplot(2,1,2)
#mpl.plot(sweep.Vbias[iUp], grad[iUp])
#mpl.show()

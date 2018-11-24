#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 13:35:11 2018

@author: avirup
"""

'''Analysis of Shake test data'''

import numpy as np
import matplotlib.pyplot as plt
import h5py as hdf
import pandas as pd

path = '/home/avirup/adr3/ShakeTestData/'

HKI = hdf.File(path+'HK_ShakeTestIncreasing_201811212004_Mainfile.h5', 'r')
HKD = hdf.File(path+'HK_ShakeTestDecreasing_201811212208_Mainfile.h5', 'r')
LocI = pd.read_csv(path+'ShakeTestIncreasing_201811212004_Mainfile.csv')
LocD = pd.read_csv(path+'ShakeTestDecreasing_201811212208_Mainfile.csv')
tempFAAI = HKI['/HK/FAA/T']
tempFAAD = HKD['/HK/FAA/T']
tFAAI = HKI['/HK/FAA/t']
tFAAD = HKD['/HK/FAA/t']

vMagI = HKI['/HK/Magnet/Vmagnet']

fI = LocI['freq']
stLocI = LocI['startTime']
enLocI = LocI['endTime']
XI = LocI['X']
YI = LocI['Y']
VoutI = np.sqrt(XI**2+YI**2) 
aI = VoutI*1000./109.524


 
fD = LocD['freq']
stLocD = LocD['startTime']
enLocD = LocD['endTime']
XD = LocD['X']
YD = LocD['Y']
VoutD = np.sqrt(XD**2+YD**2) 
aD = VoutD*1000./109.524 
 






     #''' Calibration of charge amp '''

meanTI=[]
meantLocI=np.zeros_like(stLocI)
shakeTimeI = enLocI-HKI['/HK/FAA/t'][0]#LocI['startTime'][0] 
for  i in range(len(stLocI)):
    in1 = np.argmin(np.abs(tFAAI-stLocI[i])) 
    in2 = np.argmin(np.abs(tFAAI-enLocI[i]))
    meanTI = np.append(meanTI,np.mean(tempFAAI[in1:in2]))
    meantLocI[i] = 0.5*(enLocI[i]+stLocI[i])

meanTD=[]
meantLocD=np.zeros_like(stLocD)
shakeTimeD = enLocD-HKD['/HK/FAA/t'][0]#LocI['startTime'][0] 
for  i in range(len(stLocD)):
    in1 = np.argmin(np.abs(tFAAD-stLocD[i])) 
    in2 = np.argmin(np.abs(tFAAD-enLocD[i]))
    meanTD = np.append(meanTD,np.mean(tempFAAD[in1:in2]))
    meantLocD[i] = 0.5*(enLocD[i]+stLocD[i])
    
plt.title('Frequency dependence of vibration')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Acceleration ( peak g)')
plt.plot(fI,aI,label='forward sweep')
plt.plot(fD,aD,label='reverse sweep')
plt.legend(loc='best')

plt.figure()
plt.title('Effect of averaging FAA temperatures over lockin sampling time - forward sweep')
plt.plot(meantLocI-tFAAI[0],meanTI,'b-', label='avg')
plt.plot(tFAAI-tFAAI[0],tempFAAI,'r-',label='raw')
plt.xlabel('time (s)')
plt.ylabel('Base temperature (K)')
plt.legend()

fig,ax1 = plt.subplots()
plt.title('Vibration and temperature change for forward sweep')
ax1.plot(fI, meanTI,'k-',label='base temp')
ax1.set_xlabel('Frequency (Hz)')
ax1.set_ylabel('FAA temp (K)',color='r')
ax1.tick_params('y', colors='r')
ax1.legend(loc='best')
ax2=ax1.twinx()
ax2.plot(fI, aI,'g-',label='acceleration')
ax2.set_ylabel('Acceleration ( peak g)',color='g')
ax2.tick_params('y', colors='g')
ax2.legend(loc='best')
fig.tight_layout()

#####################################################################################################

plt.figure()
plt.title('Effect of averaging FAA temperatures over lockin sampling time - reverse sweep')
plt.plot(meantLocD-tFAAD[0],meanTD,'b-', label='avg')
plt.plot(tFAAD-tFAAD[0],tempFAAD,'r-',label='raw')
plt.xlabel('time (s)')
plt.ylabel('Base temperature (K)')
plt.legend()

fig,ax1 = plt.subplots()
plt.title('Vibration and temperature change for reverse sweep')
ax1.plot(fD, meanTD,'r-',label='base temp')
ax1.set_xlabel('Frequency (Hz)')
ax1.set_ylabel('FAA temp (K)',color='r')
ax1.tick_params('y', colors='r')
ax1.legend(loc='best')
ax2=ax1.twinx()
ax2.plot(fD, aD,'g-',label='acceleration')
ax2.set_ylabel('Acceleration ( peak g)',color='g')
ax2.tick_params('y', colors='g')
ax2.legend(loc='best')
fig.tight_layout()


plt.figure()
plt.title('Temp variation with frequency')
plt.plot(fD,meanTD,'b-', label='reverse')
plt.plot(fI,meanTI,'r-',label='forward')
plt.xlabel('Frequency (Hz)')
plt.ylabel('$\Delta$T (K)')
plt.legend()

#plt.figure()
#plt.plot(meanLoctI-meanLoctI[0], tFAAI-tFAAI[0])
plt.show()




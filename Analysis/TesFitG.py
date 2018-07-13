# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 19:13:15 2017

@author: wisp10
"""

import h5py as hdf
import matplotlib.pyplot as mpl
import matplotlib.cm as cm
import numpy as np
from scipy.optimize import curve_fit

cmap = cm.coolwarm

cooldown = 'G5C'
deviceId = 'TES2'

path = 'D:/Users/Runs/%s/IV/' % cooldown
fileName = '%s_FindG.h5' % deviceId
outputPath = '%s/Plots/' % cooldown

if cooldown == 'G4C':
    if deviceId=='TES1':
        Tmin = 70E-3; Tmax = 110E-3; Pmin = 0.1E-12  # TES 1
    elif deviceId == 'TES2':
        Tmin = 66E-3; Tmax = 110E-3; Pmin = 0.1E-12  # TES 2
elif cooldown ==  'G5C':
    if deviceId=='TES1':
        Tmin = 70E-3; Tmax = 110E-3; Pmin = 0.1E-12  # TES 1
    if deviceId=='TES2':
        Tmin = 61E-3; Tmax = 85E-3; Pmin = 0.1E-12  # TES 2

with hdf.File(path+fileName, 'r') as f:
    a = f.attrs
    deviceName = a['deviceName']
    sourceFile = a['sourceFile']
    Rn = a['Rnormal']
    Tbases = f['Tbase'].value
    Ps = f['Ps'].value
    percentOfRn = f['percentOfRn'].value

mpl.figure()


def powerModel(Tbase, K, Tc, beta):
    P = K * (np.power(Tc, beta+1) - np.power(Tbase, beta+1))
    return P

TcFix = 88.4E-3
betas = np.ones_like(percentOfRn)*np.nan
Tcs = np.ones_like(percentOfRn)*np.nan
Ks = np.ones_like(percentOfRn)*np.nan
for i,relRn in enumerate(percentOfRn):
    color = cmap(relRn)
    label = '%.1f' % (relRn*100) if i%2==0 else None
    iSelect = (Tbases >= Tmin) & (Tbases <= Tmax) & (Ps[:,i] > Pmin)
    mpl.plot(Tbases*1E3, Ps[:,i]*1E12, 'k+', ms=5)
    
    guess = [2.5E-8, 88.4E-3, 2.5]
    try:
        fit,pcov = curve_fit(powerModel, Tbases[iSelect], Ps[iSelect, i], guess)
        print(relRn, fit)
        K = fit[0]
        Tc = fit[1]
        beta = fit[2]
        Tcs[i] = Tc
        betas[i] = beta
        Ks[i] = K
        fitX = np.linspace(Tmin, Tc)
        mpl.plot(fitX*1E3, powerModel(fitX, *fit)*1E12, '-', label=label, color=color, lw=1.5)
    except Exception as e:
        print(e)
        pass

mpl.xlim(1E3*Tmin, 1E3*np.nanmax(Tcs)+5)
mpl.ylim(-0.05E-12, np.max(Ps)*1E12)
mpl.xlabel(u'$T_{base}$ (mK)')    
mpl.ylabel(u'$P_{TES}$ @ $R_n$ (pW)')
mpl.suptitle(u'%s: %s G fits vs. Rn (%.2f m$\\Omega$)' % (deviceId, deviceName, 1E3*Rn) )
mpl.legend(loc='best', title=u'% of $R_n$', ncol=1)
mpl.savefig(outputPath+'%s_G_fits.pdf' % deviceId)
mpl.savefig(outputPath+'%s_G_fits.png' % deviceId)

fig, axes = mpl.subplots(3,1,sharex=True)
fig.suptitle('%s: %s - G fits' % (deviceId, deviceName))
axes[0].plot(percentOfRn, betas, 'o')
axes[0].set_ylabel(u'$\\beta$')
axes[0].set_ylim(2, 3)
axes[0].grid()
axes[1].plot(percentOfRn, Tcs*1E3, 'o')
axes[1].set_ylabel(u'$T_c$ (mK)')
axes[1].grid()
Tfix = TcFix
GatT = (betas+1)*Ks*np.power(Tfix, betas)
axes[2].plot(percentOfRn, GatT*1E9, 'o')
axes[2].set_ylabel(u'$G$(T=%.1f mK) (nW/K)' % (Tfix*1E3))
axes[2].grid()
mpl.xlabel('Percent of $R_n$')
mpl.savefig(outputPath+'%s_G_params.pdf' % deviceId)
mpl.savefig(outputPath+'%s_G_params.png' % deviceId)

favoriteRn = 0.8
i = np.argmin(np.abs(percentOfRn-favoriteRn))
fit = [Ks[i], Tcs[i], betas[i]]
fig, axes = mpl.subplots(2,1, sharex=True)
fitDetails = 'At %.0f %% $R_n$: $\\beta$=%.2f, $T_c$=%.2f mK, G(%.2fmK)=%.3f nW/K' % (favoriteRn*100, betas[i], 1E3*Tcs[i], 1E3*Tfix, 1E9*GatT[i])
fig.suptitle('%s: %s - G fit\n%s' % (deviceId, deviceName, fitDetails))
axes[0].plot(Tbases*1E3, Ps[:,i]*1E12, 'k+', label='%.1f' % (relRn*100))
fitX = np.linspace(Tmin, 110E-3)
residuals = Ps[:,i] - powerModel(Tbases, *fit)
axes[0].plot(fitX*1E3, powerModel(fitX, *fit)*1E12, 'r-')
axes[0].set_ylabel(u'$P_{TES}$ @ $R_n$ (pW)')
axes[0].set_ylim(-0.1, powerModel(Tmin, *fit)*1E12)
axes[0].grid()
axes[1].plot(Tbases*1E3, residuals*1E12, '.')
axes[1].set_ylabel(u'Residuals $P$-$P_{fit}$ (pW)')
axes[1].set_xlabel(u'$T_{base}$ (mK)')
axes[1].set_xlim(1E3*Tmin,1E3*Tcs[i]+1)
axes[1].set_ylim(-0.05, +0.05)
axes[1].grid()
mpl.savefig(outputPath+'%s_G_final.pdf' % deviceId)
mpl.savefig(outputPath+'%s_G_final.png' % deviceId)

mpl.show()

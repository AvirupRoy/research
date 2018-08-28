# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 16:42:41 2018

@author: wisp10
"""

from Analysis.PulseFileImporter import PulseImporter
from Analysis.FileTimeStamps import filesInDateRange
import matplotlib.pyplot as mpl

device = 'TES2'
cooldown = 'G5C'
path = 'G:/Runs/%s/Pulses/'  % cooldown
fileNames = filesInDateRange(path+'TES2_Pulses_*.h5', '20180608_193438', '20180608_205923')


#fileName = filesNames[0]

import lmfit
import numpy as np

def singleDecay(t, A0, tau):
    return A0*np.exp(-t/tau)

import pandas as pd

df = pd.DataFrame()
for fileName in fileNames:
    print('File name:', fileName)
    pulses = PulseImporter(fileName)
    iTemplate = np.sort(np.hstack([pulses.iTest,pulses.iTemplate]))
    pulses.templatePulseAverage(individualBaseline=True, iGood=iTemplate)
    pulses.avgerageNoise()
    res = pulses.baselineResolution()
    tpl = -pulses.templatePulse
    Vb = pulses.tes.bias
    iMax = np.argmax(tpl)
    Vmax = tpl[iMax]
    iLast = iMax+np.where(tpl[iMax:]<1E-3*Vmax)[0][0]
    
    model = lmfit.Model(singleDecay, independent_vars='t')
    params = model.make_params()
    params['A0'].value = Vmax
    params['tau'].value = 1E-3
    
    y = tpl[iMax:iLast]
    t = np.arange(iLast-iMax) / pulses.sampleRate
    
    result = model.fit(data=y, params=params, t=t)
    print(result.fit_report())
    tau = result.params['tau']
    label = '%.3f V, %.3f$\\pm$%.3f ms' % (Vb, 1E3*tau.value, 1E3*tau.stderr)
    mpl.semilogy(t, y, label=label)
    mpl.semilogy(t, result.best_fit, '-')
    df = df.append({'Vbias': Vb, 'tauDecay':tau.value, 'tauDecayStd':tau.stderr, 'Amplitude':Vmax, 'baselineRes':res}, ignore_index=True)
    
mpl.legend()

fig, axes = mpl.subplots(3,1,sharex=True)
x = df.Vbias
axes[0].plot(x, df.Amplitude, 'o-')
axes[0].set_ylabel('Pulse height (V)')
axes[1].plot(x, 1E3*df.tauDecay, 'o-')
axes[1].set_ylabel('Pulse decay time (ms)')
axes[1].set_xlabel('Bias voltage (V)')
axes[2].plot(x, df.baselineRes, 'o-')
mpl.show()

# -*- coding: utf-8 -*-
"""
Created on Fri Jul 13 15:07:35 2018

@author: wisp10
"""

from Analysis.PulseFileImporter import PulseImporter
from Analysis.FileTimeStamps import filesInDateRange
import matplotlib.pyplot as mpl

device = 'TES2'
cooldown = 'G5C'
path = 'G:/Runs/%s/Pulses/'  % cooldown
startDate = '20180608_193438'
#startDate = '20180608_200457'
fileNames = filesInDateRange(path+'TES2_Pulses_*.h5', startDate, '20180608_205923')


fileNames = fileNames[0:5]

#import lmfit
import numpy as np

def singleDecay(t, A0, tau):
    return A0*np.exp(-t/tau)

import pandas as pd

df = pd.DataFrame()
for fileName in fileNames:
    print('File name:', fileName)
    pulses = PulseImporter(fileName)
    #iTemplate = np.sort(np.hstack([pulses.iTest,pulses.iTemplate]))
    #pulses.templatePulseAverage(individualBaseline=True, iGood=iTemplate)
    noise = pulses.avgerageNoise()
    f = pulses.frequencies()
    Vb = pulses.iv.VbiasFinal
    mpl.loglog(f, np.sqrt(noise), label='%.3f V' % Vb)
mpl.legend()
mpl.show()

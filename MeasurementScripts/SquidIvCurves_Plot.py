# -*- coding: utf-8 -*-
"""
Created on Tue Oct 03 19:24:31 2017

@author: wisp10
"""

import matplotlib.pyplot as mpl
import numpy as np
import h5py as hdf
#fileName = 'SQUID_TES2_20171003_222133.h5'
#fileName = 'SQUID_TES1_20171003_224842.h5'
#fileName = 'SQUID_TES1_125mK_20171003_232839.h5'
fileName = 'SQUID_TES2_125mK_20171003_235034.h5'
fileName = 'SQUID_TES2_080mK_20171004_001145.h5'
fileName = 'SQUID_TES1_080mK_20171004_002353.h5'
#fileName = 'SQUID_TES2_075mK_20180103_181020.h5' # When checking for Shapiro fun
fileName = 'SQUID_TES2_075mK_Vac50mV_fac321kHz_20180103_182011.h5' # Now, FG is ON
#with hdf.File(fileName, 'r') as f:
f = hdf.File(fileName, 'r')
g = f['IV_Test']

x = g['FgMean'].value

iMax = np.argmax(x)

x = x[:iMax]
iOff = np.argmin(np.abs(x))


for key in g.keys():
    if not 'Offset' in key:
        continue
    sg = g[key]
    y = sg['PflMean'].value
    y = y[:iMax]
    offset = np.mean(y[iOff-5:iOff+5])
    y -= offset
    mpl.plot(x, y, '-', label=key)

mpl.legend(loc='best')       
figName = fileName.split('.h5')[0]+'IV.png'
mpl.savefig(figName) 
mpl.show()
        
    
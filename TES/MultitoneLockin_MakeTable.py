# -*- coding: utf-8 -*-
"""
Created on Fri Nov 24 18:06:15 2017

@author: wisp10
"""

import pandas as pd

import numpy as np

#fmin = 6.32; fmax = 87.123E3; n = 16
#fmin = 12.32; fmax = 87.123E3; n = 18
fmin = 12.32; fmax = 87.123E3; n = 20

A = 0.04
bw = 2.
filterOrder = 8

fRefs = np.round(np.logspace(np.log10(fmin),np.log10(fmax), n), 2)
fRefs[-4] = 0
fRefs[-2] = 0
fRefs = fRefs[fRefs!=0]

active = np.ones_like(fRefs, dtype=np.bool)
As = A*np.ones_like(fRefs)
phases = np.rad2deg(np.random.rand(len(fRefs)) * np.pi)
bws = bw*np.ones_like(fRefs)
orders = filterOrder*np.ones_like(fRefs, dtype=np.int)
df = pd.DataFrame({'active':active, 'fRef':fRefs, 'amplitude':As,
                   'phase':phases, 'lpBw':bws, 'lpOrder':orders})
print(df)
df.to_csv('FrequencyTableFast.csv')

import matplotlib.pyplot as mpl

mpl.semilogx(fRefs,np.ones_like(fRefs), 'o')
mpl.show()

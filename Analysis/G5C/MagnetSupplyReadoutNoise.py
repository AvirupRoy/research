# -*- coding: utf-8 -*-
"""
Created on Fri May 11 17:20:00 2018

@author: wisp10
"""

fileName = 'D:\\Users\\Runs\\G5C\\MagnetControlRawCurves.csv'

import matplotlib.pyplot as mpl
import numpy as np
import pandas as pd

df = pd.read_csv(fileName)

Vm = df['Magnet voltage_x']
Vf = df['FET output_x']
Icoarse = df['Current coarse_x']
Ifine = df['Current fine_x']

fs = 50E3

t = np.arange(len(Vm))/fs

mpl.plot(t[200:], Ifine[200:])
mpl.grid()
mpl.show()

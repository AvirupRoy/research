# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 15:31:09 2018

@author: wisp10
"""
import numpy as np
import matplotlib.pyplot as mpl

fileName = '../../DAQ/Thermistors_2018015.txt'

d = np.genfromtxt(fileName, names=True)

items = ['WaterIn', 'WaterOut', 'OilIn', 'OilOut', 'HeCold']
labels = ['water in', 'water out', 'oil in', 'oil out', 'He cold']
lineStyles = ['-b', '-r', '--b', '--r', '-g']
t = d['Time']

def Kelvin(K):
    return K
    
def Celsius(K):
    return K-273.15

def Fahrenheit(K):
    return 1.8*Celsius(K) + 32

conversion = Celsius; units = '$^{\\circ}$C'
conversion = Fahrenheit; units = '$^{\\circ}$F'
#conversion = Kelvin; units = 'K'
t0 = 1.518728210E9

for item,label, ls in zip(items, labels, lineStyles):
    y = conversion(d['%sT' % item])
    mpl.plot((t-t0)/3600, y, ls, label=label)

mpl.ylabel('Temperature (%s)' % units)
mpl.xlabel('Time since compressor start (h)')
mpl.legend(loc='best')
mpl.grid()
mpl.show()


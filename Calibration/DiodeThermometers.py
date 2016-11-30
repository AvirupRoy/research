# -*- coding: utf-8 -*-
"""
A collection of all diode calibrations
Created on Wed Nov 23 14:22:24 2016

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

import numpy as np

calibrationDirectory = 'D:\Users\FJ\ADR3\Calibration/'

class DT470Thermometer(object):
    def __init__(self):
        super(DT470Thermometer, self).__init__()
        self.loadCalibrationData()
        i = np.argsort(self.V) # Make sure they are sorted in order of increasing V
        self.V = self.V[i]
        self.T = self.T[i]
        
    def loadCalibrationData(self):
        fileName = calibrationDirectory+'Lakeshore_Curve10.dat'
        d = np.genfromtxt(fileName, skip_header=1, names=True)
        self.T = d['TK']
        self.V = d['V']
        
    @property
    def name(self):
        return 'Lakeshore DT470 Curve 10'

    @property        
    def Vmin(self):
        return self.V[0]

    @property        
    def Vmax(self):
        return self.V[-1]

    @property
    def Tmin(self):
        return np.min(self.T)
        
    @property
    def Tmax(self):
        return np.max(self.T)
        
    def calculateTemperature(self, V):
        return np.interp(V, self.V, self.T, left=self.Tmax, right=self.Tmin)

class DT670Thermometer(DT470Thermometer):
    def loadCalibrationData(self):
        fileName = calibrationDirectory+'Lakeshore_DT670.dat'
        d = np.genfromtxt(fileName, skip_header=1, names=True)
        self.T = d['TK']
        self.V = d['V']

    @property
    def name(self):
        return 'Lakeshore DT670'

class Si70Thermometer(DT470Thermometer) :
    def loadCalibrationData(self):
        fileName = calibrationDirectory+'Si70.dat'
        d = np.genfromtxt(fileName, skip_header=2, names=True, delimiter='\t')
        self.T = d['TK']
        self.V = d['V']
        
    @property
    def name(self):
        return 'Si 70'
        
DiodeCalibrationCurves = ['DT470', 'DT670', 'Si70']
'''A list of all available diode calibrations'''
    
def diodeCalibration(name):
    '''Factory function to obtain a specified diode calibration class'''
    if name == 'DT470':
        return DT470Thermometer()
    elif name == 'DT670':
        return DT670Thermometer()
    elif name == 'Si70':
        return Si70Thermometer()
    else:
        raise KeyError


if __name__ == '__main__':
    import matplotlib.pyplot as mpl

    mpl.figure()
    for name in DiodeCalibrationCurves:
        cal = diodeCalibration(name)
        V = np.linspace(cal.Vmin, cal.Vmax, 200) 
        T = cal.calculateTemperature(V)
        mpl.plot(V, T, '-', label='%s (%.2f to %.2f K)' % (cal.name, cal.Tmin, cal.Tmax))
    mpl.legend(loc='best')
    mpl.xlabel('V (V)')
    mpl.ylabel('T (K)')
    mpl.show()

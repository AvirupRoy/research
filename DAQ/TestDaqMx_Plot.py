# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 11:44:15 2015
Plot data collected uisng TestDAQmx
@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

import numpy as np
import matplotlib.pyplot as mpl


deviceName = 'USB6002'
aoChannel = 'ao0'
aiChannel = 'ai0'
date = '20150824-170201'


fileName = '%s_%s_%s_%s.dat' % (deviceName, aoChannel, aiChannel, date)
print "Loading data from:", fileName
d = np.genfromtxt(fileName, delimiter='\t', skip_header=2, names=True)

Vcommand = d['Vcommand']
Vdmm = d['Vdmm']
Vai = d['Vai']
VaiStd = d['VaiStd']

fit = np.polyfit(Vcommand, Vdmm, 1)

gain = fit[0]
offset = fit[1]

nPoints = len(Vcommand)
xFit = [-10,10]
mpl.figure()
mpl.subplot(2,1,1)
mpl.plot(Vcommand, Vdmm, '.', label='data')
mpl.plot(xFit, np.polyval(fit, xFit), '-', label='fit (gain=%.7g, offset=%.4gV' % (gain, offset))
mpl.ylabel('Measured with DMM [V]')
mpl.legend(loc='best')
mpl.subplot(2,1,2)
mpl.plot(Vcommand, Vdmm-np.polyval(fit, Vcommand), '.b', label='fit')
mpl.plot(Vcommand, Vdmm-Vcommand, '.r', label='$V_{meas}-V_{cmd}$')
mpl.legend(loc='best')
mpl.ylabel('Residual [V]')
mpl.xlabel('Commanded voltage [V]')
mpl.suptitle('Verfication of %s, AO channel %s with DMM\n%s (%d points)' % (deviceName, aoChannel, date, nPoints))
mpl.show()

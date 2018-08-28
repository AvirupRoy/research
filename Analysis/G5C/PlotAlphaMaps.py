# -*- coding: utf-8 -*-
"""
Created on Wed Nov 01 17:36:06 2017

@author: wisp10
"""
import h5py as hdf
import matplotlib.pyplot as mpl
from Analysis.Tes_IVMaps import AlphaMap
from Analysis.G4C.MeasurementDatabase import obtainTes
import numpy as np


if __name__ == '__main__':
    deviceId = 'TES1'
    tes = obtainTes('G5C', deviceId)
    Rn = tes.Rnormal
    Rs = np.asarray([0.05, 0.15]) * Rn
    Ps = np.asarray([1E-12, 2E-12, 3E-12, 3.5E-12])
    
    
    fileName = '%s_AlphaMapsVsB.h5' % deviceId
    #fileName = 'TES2_AlphaMapVcoil-0.450_2.h5'
    
    with hdf.File(fileName, 'r') as f:
        for key in f.keys():
            g = f[key]
            Vcoil = g.attrs['Vcoil']
            coilString = 'Vcoil=%+6.4f V' % Vcoil
            print(coilString)
            alphaMap = AlphaMap.fromHdf(g)
            figure =  mpl.figure()
            alphaMap.showMap()
            for R in Rs:
                V = alphaMap.Is * R
                good = V < alphaMap.Vmax
                mpl.plot(1E6*alphaMap.Is[good], 1E9*V[good], 'k--')
                
            for P in Ps:
                V = P/alphaMap.Is
                good = V < alphaMap.Vmax
                mpl.plot(1E6*alphaMap.Is[good], 1E9*V[good], 'k-')
                
            mpl.suptitle('%s - %s' % (deviceId, coilString))
            mpl.savefig('Plots\\%s_Alpha_%s.png' % (deviceId, coilString))
            #mpl.savefig('Plots\\%s_Alpha_%s.png' % (deviceId, coilString))
            #mpl.close(figure)

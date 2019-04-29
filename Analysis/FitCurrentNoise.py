#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 16:04:28 2019

@author: Avirup Roy <aroy22@wisc.edu>
"""

from Analysis.TesModel_Maasilta import HangingModel
from Analysis.TransferFunction import TesAdmittance, TheveninEquivalentCircuit
import h5py as hdf
import time
import matplotlib.pyplot as plt
import numpy as np
import lmfit

Rshunt = 250E-6


        
class NoiseSpectrum(object):
    class Info:
        def __init__(self,attrs):
            self.name = attrs['name']
            self.program = attrs['program']
            
            
    def __init__(self,fileName):
        f = hdf.File(fileName,'r')
        self.info = NoiseSpectrum.Info(f.attrs)
        self.f = f['Data000000']['Frequency']
        self.psd = f['Data000000']['PSD']
        self.iNoise = np.sqrt(self.psd)
        self.psdKurtosis = f['Data000000']['PSD_kurtosis']
        self.psdSkew = f['Data000000']['PSD_skew']
        self.psdStd = f['Data000000']['PSD_std']
        self.t = f['Data000000']['Times']
        self.vMax = f['Data000000']['Vmax']
        self.vMean = f['Data000000']['Vmean']
        self.vMin = f['Data000000']['Vmin']
        self.vStd = f['Data000000']['Vstd']
        
    def plotPSD(self):
        plt.rc('text', usetex=True)
        plt.rc('font', family='serif')
        plt.loglog(self.f,self.iNoise*1E6)
        plt.grid()
        plt.xlabel('Frequency(Hz)')
        plt.ylabel('Current noise ($\mu$A/$\sqrt {Hz}$)')
        plt.show()
        
    def fitCurrentNoise(self, *args, **kwargs):
        fMax = 1E5
        noises = tesModel.noiseComponents(*args, **kwargs)
        noiseTotal = np.sum(noises[component] for component in noises.keys())
        betaI, tau, L = TesAdmittance.guessBetaTauL(R0, fmin=10E3, fmax=fMax)
        C = tau*G
        f = TesAdmittance.f
        iFit = f < fMax
        model = lmfit.Model(noiseTotal, independent_vars='f')
        params = model.make_params()
        params['alphaI'].vary = True;  params['alphaI'].value = alphaI;
        params['betaI'].vary  = True;  params['betaI'].value = betaI;
        params['P'].vary      = False; params['P'].value = P0
        params['g_tesb'].vary = True;  params['g_tesb'].value = 0.9*G; params['g_tesb'].min = 0
        params['g_tes1'].vary = True;  params['g_tes1'].value = 0.1*G; params['g_tes1'].min = 0   # Wild guess
        params['Ctes'].vary   = True;  params['Ctes'].value = 0.8*C;  # params['Ctes'].min   = 0
        params['C1'].vary     = True;  params['C1'].value   = 0.2*C;  # params['C1'].min     = 0   # Wild guess
        params['T'].vary      = False; params['T'].value = T0
        params['R'].vary      = False; params['R'].value = R0
        
        result = model.fit(data=noiseTotal[iFit].view(dtype=np.float),
                       f=np.hstack([f[iFit], f[iFit]]),
                       params=params )
        print(result.fit_report())
            
            
       

if __name__ == '__main__':
    T0 = 85E-3
    alphaI = 100
    betaI = 1
    betaThermal = 2.256
    I0 = 10E-6
    R0 = 10E-3
    P0= I0**2*R0
    G = 56.76E-12
    tesModel = HangingModel(Rshunt=Rshunt)
    path = '/Users/calorim/Documents/ADR3/G8C/Noise/'
    fileNames = ['TES2_Noise_20190409_1340.h5']
    for fileName in fileNames:
        noise =NoiseSpectrum(path+fileName)
        noise.plotPSD()
            
    
    
    
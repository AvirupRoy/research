# -*- coding: utf-8 -*-
"""
Code to read the housekeeping data from HDF5 files as produced by Utility/HkLogger.py
Created on Thu Nov 30 16:50:12 2017

@author: wisp10
"""

import warnings

class HkThermometer(object):
    def __init__(self, hdfRoot):
        try:
            self.sensorName = hdfRoot.attrs['SensorName']
        except KeyError:
            self.sensorName = None
        self.t = hdfRoot['t'].value
        try:
            self.P = hdfRoot['P'].value
        except KeyError:
            self.P = None
        self.R = hdfRoot['R'].value
        self.T = hdfRoot['T'].value
        try:
            self.Tbase = hdfRoot['Tbase'].value
        except KeyError:
            warnings.warn('Tbase not available for %s. Recalculating...' % self.sensorName)
            from Calibration.RuOx import getCalibration
            try:
                cal = getCalibration(self.sensorName)
                self.Tbase = cal.correctForReadoutPower(self.T, self.P)
            except KeyError:
                warnings.warn('No read-out power correction for thermometer %s' % self.sensorName)
                self.Tbase = self.T
        
    def plotT(self):
        import matplotlib.pyplot as mpl
        mpl.plot(self.t, self.T, '-')
        
class HkTesBias(object):
    def __init__(self, hdfRoot):
        self.t = hdfRoot['t'].value
        self.Vbias = hdfRoot['Vbias'].value

class HkFieldCoil(object):
    def __init__(self, hdfRoot):
        self.t = hdfRoot['t'].value
        self.Vcoil = hdfRoot['Vcoil'].value
        
class HkMagnet(object):
    def __init__(self, hdfRoot):
        self.t = hdfRoot['t']
        self.Icoarse = hdfRoot['ImagnetCoarse'].value
        self.Ifine = hdfRoot['ImagnetFine'].value
        self.Vmagnet = hdfRoot['Vmagnet'].value

class HkImporter(object):
    def __init__(self, hdfRoot):
        '''Load HK data from hdfRoot.
        hdfRoot:  h5py file object or file name
        '''
        if type(hdfRoot) == str:
            import h5py
            f = h5py.File(hdfRoot, 'r')
            hdfRoot = f['HK']
            
        thermometers = {}
        for key in hdfRoot.keys():
            if 'Thermometer' in key or key in ['GGG', 'FAA']:
                thermometers[key] = HkThermometer(hdfRoot[key])
        self.thermometers = thermometers
        self.magnet = HkMagnet(hdfRoot['Magnet'])
        self.tesBias = HkTesBias(hdfRoot['TESBias'])
        self.fieldCoil = HkFieldCoil(hdfRoot['FieldCoilBias'])
        
    def plotMagnetAndAdrThermometers(self):
        hk = self
        import matplotlib.pyplot as mpl
        fig, axes = mpl.subplots(3,1, sharex=True)
        for i,thermoId in enumerate(['RuOx2005Thermometer', 'BusThermometer', 'BoxThermometer']):
            try:
                thermo = self.thermometers[thermoId]
            except KeyError:
                continue
            axes[0].plot(thermo.t, thermo.T, label=thermoId)
        axes[0].set_ylabel('Temperature')
        axes[1].plot(hk.magnet.t, hk.magnet.Ifine, label='magnet current')
        axes[1].plot(hk.magnet.t, hk.magnet.Icoarse, label='magnet current (coarse)')
        axes[1].set_ylabel('Magnet current')
        axes[2].plot(hk.magnet.t, hk.magnet.Vmagnet)
        axes[2].set_ylabel('Magnet voltage')
        axes[-1].set_xlabel('Time')
        axes[0].legend()
if __name__ == '__main__':
    import h5py as hdf
    path = '/media/avirup/Data/ADR3/G8C/TF/' 
    fileName = 'TES3_20190416_031220.h5'
    file = path+fileName
    hdfRoot = hdf.File(file,'r')
    print(HkThermometer(hdfRoot['HK']['GGG']).R)

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
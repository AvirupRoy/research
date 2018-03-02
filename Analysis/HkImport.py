# -*- coding: utf-8 -*-
"""
Code to read the housekeeping data from HDF5 files as produced by Utility/HkLogger.py
Created on Thu Nov 30 16:50:12 2017

@author: wisp10
"""

class HkThermometer(object):
    def __init__(self, hdfRoot):
        self.sensorName = hdfRoot.attrs['SensorName']
        self.t = hdfRoot['t'].value
        self.P = hdfRoot['P'].value
        self.R = hdfRoot['R'].value
        self.T = hdfRoot['T'].value
        
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

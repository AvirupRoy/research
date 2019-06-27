
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 01 11:31:02 2017

@author: wisp10
"""
from __future__ import print_function, division
import glob

def timeStampFromPath(filePath):
    '''Return the Unix epoch time from a filename (with full path) of the form x_YYYYMMDD_HHMMSS.y'''
    import os
    baseName = os.path.basename(filePath).split('.')[0]
    pieces = baseName.split('_')
    dateStr = '_'.join(pieces[-2:])
    return timeStampFromString(dateStr)
    
def timeStampFromString(dateStr):
    '''Return the Unix epoch time from a string of the form YYYYMMDD_HHMMSS'''
    import time
    t = time.mktime(time.strptime(dateStr, '%Y%m%d_%H%M%S'))
    return t


        
if __name__ == '__main__':
    from Analysis.G4C.MeasurementDatabase import obtainTes
    from Analysis.TesIvSweepReader import IvSweepCollection
    from Analysis.Tes_IVMaps import TIVMap
    import numpy as np
    import h5py as hdf
    cooldown = 'G5C'
    deviceId = 'TES1'
    dataPath = 'D:\\Users\\Runs\\%s\\IV\\' % cooldown
    if deviceId == 'TES1':
        tFirst = timeStampFromString('20180224_003557')
        tLast = timeStampFromString('20180224_100638')
        tFirst = timeStampFromString('20180225_215627')
        tLast = timeStampFromString('20180226_115013')
        #Tmin = 0.062
        tFirst = timeStampFromString('20180228_232115')
        tLast = timeStampFromString('20180228_232125')
        #fileName = 'TES1_IV_20180228_232117.h5'
        Tmin = 0.058
    elif deviceId == 'TES2':
        tFirst = timeStampFromString('20171031_184923')
        tLast = timeStampFromString('20171101_095334')
        Tmin = 0.078
        
        

    outputFile = '%s_AlphaMapsVsB.h5' % deviceId
#    fileNames = glob.glob(dataPath+'%s_IVvsT_*.h5' % deviceId)
    fileNames = glob.glob(dataPath+'%s_IV_*.h5' % deviceId)

    tes = obtainTes(cooldown, deviceId)
    deltaTmin = 3E-3

    Istep = 0.5E-6; Vstep = 0.5E-9
    Imin = 5E-6; Imax = 110E-6; nI = 1+int((Imax-Imin)/Istep)
    Vmin = 1E-9; Vmax=125E-9; nV = 1+int((Vmax-Vmin)/Vstep)
    
    Vcoils = []
    for fileName in fileNames:
        t = timeStampFromPath(fileName)
        if t < tFirst or t > tLast:
            print('Skipping:', fileName)
            continue
            pass

        print('Working on:', fileName)
        sweeps = IvSweepCollection(fileName)
        print('Number of sweeps:', len(sweeps))
        if len(sweeps)==0:
            continue
        sweep = sweeps[0]
        print('ADR resistance:', np.min(sweeps.adrR), np.max(sweeps.adrR))
        Vcoil = sweep.auxAoValue
        print('Coil voltage:', Vcoil)
        Vcoils.append(Vcoil)
        Rfb = sweeps.info.pflRfb
        MiOverMfb = tes.MiOverMfb(Rfb)
        print('Rfb=%.3fkOhm' % (Rfb/1E3))
        mapT = TIVMap(Imin, Imax, nI, Vmin, Vmax, nV)    
        mapT.fillFromSweeps(sweeps, tes, Rfb, polarity='+', deltaTmin = deltaTmin)
        mapAlpha = mapT.computeAlphaMap(Tmin = Tmin)
        with hdf.File(outputFile, 'a') as f:
            g = f.require_group('Pos_Vcoil_%+6.4f' % Vcoil)
            g.attrs['Vcoil'] = Vcoil
            g.attrs['sourceFile'] = fileName
            g.attrs['Rfb'] = Rfb
            g.attrs['deltaTmin'] = deltaTmin
            mapT.toHdf(g)
            mapAlpha.toHdf(g)

        with hdf.File(outputFile, 'a') as f:
            f.attrs['Vcoils'] = np.asarray(Vcoils)

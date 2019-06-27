# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 16:18:05 2018

@author: wisp10
"""

from __future__ import print_function

path = 'D:\\Users\\Runs\\G5C\\Pulses\\'
import glob
import h5py as hdf
import os
fileNames = glob.glob(path+'TES2_2018*.h5')

for fileName in fileNames:
    try:
        with hdf.File(fileName, 'r') as f:
            programName = f.attrs['Program']
        print(fileName, programName)
        if programName == 'PulseCollector':
            parts = fileName.split('_')
            parts.insert(1, 'Pulses')
            newName = '_'.join(parts)
            print(newName)
            os.rename(fileName, newName)    
    except IOError:
        print(fileName, 'BROKEN')

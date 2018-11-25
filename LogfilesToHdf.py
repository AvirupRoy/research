# -*- coding: utf-8 -*-
"""
Repackage multiple log files to HDF5 format
Created on Mon Feb 08 17:44:11 2016

@author: wisp10
"""

import h5py
import numpy as np

import datetime as dt



basePath = 'D:\\Users\\Runs\\E8C'
startDate = dt.date(2016, 01, 24)
endDate = dt.date(2016, 02, 07)

basePath = 'D:\\Users\\Runs\\E6C'
startDate = dt.date(2015, 11, 02)
endDate = dt.date(2015, 11, 17)

basePath = 'D:\\Users\\Runs\\F9C'
startDate = dt.date(2017, 01, 02)
endDate = dt.date(2017, 02, 07)

basePath = 'D:\\Users\\Runs\\F8C'
startDate = dt.date(2016, 10, 21)
endDate = dt.date(2017, 01, 02)


#fileType = 'AVSBridge'
#fileType = 'DiodeThermometer'
#fileType = 'DiodeThermometer3K'
#fileType = 'DiodeThermometerMagnet'
#fileType = 'DiodeThermometer60K'
fileType = 'MagnetControl2'

fileTemplate = '%s_%%s.dat' % fileType
fileNames = []
date = startDate
while date <= endDate:
    dateStr = '%d%02d%02d' % (date.year, date.month, date.day)
    fileNames.append(fileTemplate % dateStr)
    date += dt.timedelta(days=1)

import os

def readTextFile(filePath):
    with open(filePath, 'r') as f:
        metaData = {}
        lineCount = 0
        while True:
            l = f.readline()
            lineCount += 1
            if l[0] != '#':
                break
            else:
                x = l[1:].strip().split('=')
                if len(x) < 2:
                    continue
                key = x[0]
                try:
                    v = float(x[1])
                except ValueError:
                    v = x[1]
                metaData[key] = v
    if 'DiodeThermometer' in filePath:
        d = np.genfromtxt(filePath, delimiter='\t', skiprows=lineCount-1, names=['t', 'V', 'T', 'I'], dtype=None)
    else:
        d = np.genfromtxt(filePath, delimiter='\t', skiprows=lineCount-2, names=True, dtype=None)
    return metaData, d

import time
outputFilePath = os.path.join(basePath, '%s.h5' % fileType)
hdfFile = h5py.File(outputFilePath, mode='w')
hdfFile.attrs['creator'] = __file__
hdfFile.attrs['created'] = time.time()
import socket
hdfFile.attrs['hostname'] = socket.getfqdn()
hdfFile.attrs['basepath'] = basePath
hdfFile.attrs['sourceFiles'] = fileNames
first = True
for fileName in fileNames:
    print "File name:", fileName,
    filePath = os.path.join(basePath, fileName)
    if not os.path.exists(filePath):
        print "\tNot found."
        continue
    metadata, d = readTextFile(filePath)
    dataLength = len(d)
    print "\tNumber of data points:", dataLength
    if first:
        for key in metadata.keys():
            hdfFile.attrs[key] = metadata[key]
    for name in d.dtype.names:
        if first:
            ds = hdfFile.create_dataset(name=name, shape=(0,), maxshape=(None,), dtype=d.dtype[name], shuffle=True, fletcher32=True, compression='lzf')
        else:
            ds = hdfFile[name]
        oldLength = ds.shape[0]
        ds.resize(oldLength+dataLength, axis=0)
        ds[-dataLength:] = d[name]
    first = False
print "Total number of datapoints:", len(ds)
hdfFile.close()

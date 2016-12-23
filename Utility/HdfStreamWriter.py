# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 15:05:06 2016

@author: calorim
"""

from numpy import float64

MAX_SIZE = 2**31 # 2GS

from PyQt4.QtCore import QObject
class HdfStreamWriter(QObject):
    def __init__(self, grp, dtype, metaData = {}, parent=None):
        QObject.__init__(self, parent)
        self.metaData = metaData
        self.dtype = dtype
        self._sequence = 0
        self.grp = grp
        dsetTimeStamps = self.grp.create_dataset('timeStamps', (2,0), maxshape=(2,None), chunks=(2,500), dtype=float64)
        dsetTimeStamps.attrs['col1'] = 'Sample'
        dsetTimeStamps.attrs['col2'] = 'timeStamp'
        self.dsetTimeStamps = dsetTimeStamps
        self.dset = None
        self.totalSamples = 0
        
    def startNewDataset(self, t, metaData=None):
        if metaData is not None:
            self.metaData = metaData
        dset = self.grp.create_dataset("data_%06d" % self._sequence, (0,), maxshape=(None,), chunks=(8192,), dtype=self.dtype, compression='lzf', shuffle=True, fletcher32=True)
        self._sequence += 1
        self.grp.attrs['numberOfDataSets'] = self._sequence
        for k in self.metaData:
            dset.attrs[str(k)] = self.metaData[k]
        dset.attrs['startsWithTimeStamp'] = t
        self.dset = dset
        
    def writeData(self, t, data):
        nSamples = len(data)
        if self.dset is None:
            self.startNewDataset(t)
        if self.dset.shape[0] >= (MAX_SIZE - nSamples):       # Start a new dataset if we reach or exceed 2 GSamples
            self.dset.attrs['ContinuedInNextDataSet'] = True
            self.startNewDataset(t)
            self.dset.attrs['ContinuesFromPreviousDataSet'] = True
            self.dset.attrs['startsWithTimeStamp'] = t
        dset = self.dset
        oldLength = dset.shape[0]
        dset.resize((oldLength+nSamples,))
        self.dset[-nSamples:] = data         # Append the data
        self.dsetTimeStamps.resize((2,self.dsetTimeStamps.shape[1]+1))
        self.dsetTimeStamps[:,-1] = (self.totalSamples, t)
        self.totalSamples += nSamples

if __name__ == '__main__':
    import h5py as hdf
    import numpy as np
    import time
    hdfFile = hdf.File('testWriter.h5', mode='w')
    
    dtype=np.complex64
    
    metaData = {}
    metaData['Program'] = 'HDF stream writer'
    metaData['Speed'] = 1256.165
    metaData['Gains'] = [1.2,35.,46.,437.]
    metaData['Random'] = np.random.rand(20)
    grp = hdfFile.create_group('Blabla')
    writer = HdfStreamWriter(grp, dtype=dtype, metaData=metaData)
    for i in range(50):
        print i
        t = time.time()
        data = np.arange(10+i*100000, dtype=dtype)
        writer.writeData(t, data)

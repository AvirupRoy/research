# -*- coding: utf-8 -*-
"""
A class to write long data-streams to hdf files
Used by MultitoneLockin.py
Created on Thu Dec 22 15:05:06 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from __future__ import print_function, division
from numpy import int64

MAX_SIZE = 2**31 # 2GS

from PyQt4.QtCore import QObject
class HdfStreamWriter(QObject):
    '''*HdfStreamWriter* writes multiple datasets to hdf files, automatically expanding
    the hdf dataset as needed.
    To deal with the 2**31=2Gs limitation of the file format, the data are 
    automatically broken into groups as needed.
    '''
    def __init__(self, grp, dtype, scalarFields = [], metaData = {}, parent=None):
        '''Construct a HdfStreamWriter object.
        *grp*:          the hdfRoot where the datasets will be created
        *dtype*       : the data-type of the data to be stored
        *scalarFields*: list of tuples specifying name and datatypes of any additional scalar data to be stored for each writeData call.
        *metaData*    : a dictionary of key/value pairs to be stored as attributes in the hdf chunks
        *parent*      : a optional QObject parent
        Returns: None
        '''
        QObject.__init__(self, parent)
        self.metaData = metaData
        self.dtype = dtype
        self._sequence = 0
        self.grp = grp
        self.scalarDatasets = []
        for name,dtype in scalarFields:
            ds = grp.create_dataset(name, (0,), maxshape=(None,), chunks=(500,), dtype=dtype)
            self.scalarDatasets.append(ds)
        self.sampleIndex = grp.create_dataset('sampleIndex', (0,), maxshape=(None,), chunks=(500,), dtype=int64)
        self.dset = None
        self.totalSamples = 0
        self.chunkSize = 0
        
    def startNewDataset(self, metaData=None):
        '''Begin a new data set
        *metaData* : optional meta-data to store with all subsequent datasets (default: None)
        Returns: None
        '''
        if metaData is not None:
            self.metaData = metaData
        dset = self.grp.create_dataset("data_%06d" % self._sequence, (0,), maxshape=(None,), chunks=(8192,), dtype=self.dtype) #, compression='lzf', shuffle=True, fletcher32=True)
        self._sequence += 1
        self.grp.attrs['numberOfDataSets'] = self._sequence
        for k in self.metaData:
            dset.attrs[str(k)] = self.metaData[k]
        self.dset = dset
        
    def writeData(self, data, scalarData=None):
        '''Write more data to the current dataset.
        *data*     : numpy array of data
        scalarData : list of scalar datapoints to go in the scalarField specified
        in constructor.
        Returns: None
        '''
        nSamples = len(data)
        if self.chunkSize == 0:
            self.chunkSize = nSamples
            self.grp.attrs['chunkSize'] = nSamples
        elif self.chunkSize is not None and nSamples != self.chunkSize:
            del self.grp.attrs['chunkSize']
            self.chunkSize = None
        if self.dset is None:
            self.startNewDataset()
        if self.dset.shape[0] >= (MAX_SIZE - nSamples):       # Start a new dataset if we reach or exceed 2 GSamples
            self.dset.attrs['ContinuedInNextDataSet'] = True
            self.startNewDataset()
            self.dset.attrs['ContinuesFromPreviousDataSet'] = True
        dset = self.dset
        oldLength = dset.shape[0]
        dset.resize((oldLength+nSamples,))
        self.dset[-nSamples:] = data         # Append the data
        for i,ds in enumerate(self.scalarDatasets):
            ds.resize((ds.shape[0]+1,))
            ds[-1] = scalarData[i] 
        self.sampleIndex.resize((self.sampleIndex.shape[0]+1,))
        self.sampleIndex[-1] = self.totalSamples
        self.totalSamples += nSamples

if __name__ == '__main__':
    import h5py as hdf
    import numpy as np
    import time
    hdfFile = hdf.File('testWriter.h5', mode='w')
    
    dtype=np.float64
    
    metaData = {}
    metaData['Program'] = 'HDF stream writer'
    metaData['Speed'] = 1256.165
    metaData['Gains'] = [1.2,35.,46.,437.]
    metaData['Random'] = np.random.rand(20)
    grp = hdfFile.create_group('Blabla')
    writer = HdfStreamWriter(grp, dtype=dtype, scalarFields=[('t', np.float64), ('mean', np.float64), ('overload', np.bool)], metaData=metaData)
    for i in range(50):
        print('Chunk ',i)
        t = time.time()
        data = np.arange(10+1000, dtype=dtype)
        mean = np.mean(data)
        overload = np.any(data>0.1)
        writer.writeData(data, [t, mean, overload])

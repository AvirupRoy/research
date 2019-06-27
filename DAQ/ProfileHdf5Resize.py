# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 10:06:54 2016

@author: wisp10
"""

import h5py as hdf
import numpy as np
import time

nChannels = 3
compression = 'gzip'
compression = 'lzf'  # About 5x faster than gzip 
#compression =  None  # 
#compression = 'szip'
chunkSize = 10000
hdfFile = hdf.File('test2.h5', mode='w')
dset = hdfFile.create_dataset("rawData", (nChannels,0), maxshape=(nChannels, None), chunks=(nChannels, chunkSize), dtype=np.int16, compression=compression, shuffle=True, fletcher32=True)
print "Compression:", dset.compression, dset.compression_opts

data = np.random.rand(nChannels, 100000)*65536
data = data.astype(dtype=np.int16, order='F')

t1 = time.time()
for i in range(100):
    nChannels = data.shape[0]
    nSamples  = data.shape[-1]
    oldShape = dset.shape
    dset.resize(oldShape[1]+nSamples, axis=1)
    dset[:, -nSamples:] = data

t2 = time.time()
print "Elapsed time:", t2-t1
hdfFile.close()

hdfFile = hdf.File('test3.h5', mode='w')
dset = hdfFile.create_dataset("rawData", (0,nChannels), maxshape=(None,nChannels), chunks=(chunkSize, nChannels), dtype=np.int16, compression=compression, shuffle=True, fletcher32=True)

data = np.random.rand(100000, nChannels)*65536
data = data.astype(dtype=np.int16, order='F')

t1 = time.time()
for i in range(100):
    nChannels = data.shape[-1]
    nSamples  = data.shape[0]
    oldShape = dset.shape
    dset.resize(oldShape[0]+nSamples, axis=0)
    dset[-nSamples:,:] = data

t2 = time.time()
print "Elapsed time:", t2-t1
hdfFile.close()

# Conclusions:
# *It makes hardly any difference which dimension we keep expanding. In fact, the first case (expanding the second dimension seems to be slightly faster).
# *Whether data are in C or F order doesn't seem to make any difference.
# **This is mostly because we are compression/chunking dominated. It does make a difference when compression is off and chunks are small.
# What makes a big difference is the chunk size. Smaller is better. 100000 seems to be fine, but above that things get real slow.
# Oddly, having some uneven chunk size does not seem to make things worse
# A chunk size of 10000 might be a good compromise (even though small is still faster)

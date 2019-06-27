# -*- coding: utf-8 -*-
"""
Fast FIR Filter in cython
Created on Fri Dec 16 10:33:20 2016

@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

#from __future__ import division
import numpy as np
cimport numpy as np
cimport cython
DTYPE = np.float32
ctypedef np.float32_t CTYPE

from libc.math cimport sin, cos, fmod

## Unfortunately only works on GCC
#cdef extern from "<math.h>" nogil:
#    void sincos(double x, double* sinx, double* cosx)
#    void sincosf(float x, float* sinx, float* cosx)
    
cdef CTYPE TwoPi = 2.*np.pi

cdef class Lockin(object):
    '''Cython optimized lock-in. Not as fast as the MKL version.'''
    cdef CTYPE dPhi
    cdef CTYPE phi
    def __init__(self, CTYPE sampleRate, CTYPE f, CTYPE phi):
        self.dPhi = f/sampleRate*TwoPi
        self.phi = phi

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.initializedcheck(False)
    def integrateSamples(self, CTYPE [::1] data, CTYPE [::1] X, CTYPE [::1] Y):
        cdef Py_ssize_t L = data.shape[0] # number of new data points
        cdef CTYPE phi = self.phi
        cdef Py_ssize_t i
        cdef CTYPE sinPhi
        cdef CTYPE cosPhi
        with nogil:
            for i in range(0, L):
                #sincos(phi, &sinPhi, &cosPhi)
                #X[i] = data[i]*sinPhi
                #Y[i] = data[i]*cosPhi
                X[i] = data[i]*sin(phi)
                Y[i] = data[i]*cos(phi)
                phi += self.dPhi
                if i % 128 == 0:
                    phi = fmod(phi,TwoPi)
            self.phi = phi

cdef class FirFilter(object):
    cdef CTYPE [:] b
    cdef int chunkSize
    cdef CTYPE [:] buffer
    def __init__(self, int chunkSize, np.ndarray b):
        self.b = b
        self.chunkSize = chunkSize
        assert self.chunkSize >= self.b.shape[0]
        cdef Py_ssize_t L = chunkSize + self.b.shape[0] - 1
        self.buffer = np.zeros((L,), dtype=DTYPE)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.initializedcheck(False)
    def lfilter(self, CTYPE [:] data, CTYPE [:] output):
        cdef Py_ssize_t i,j
        cdef Py_ssize_t L = data.shape[0] # number of new data points
        cdef Py_ssize_t N = self.b.shape[0] - 1 # number of taps
        cdef CTYPE [:] buffer = self.buffer # View on buffer
        cdef CTYPE [:] b = self.b # View on coefficients
#        if output is None:
#            output = np.empty_like(data)
        cdef CTYPE [:] output_v = output

        cdef CTYPE s

        with nogil:
            # Copy the new samples in at end of buffer  (this is not optimal, but the performance pentalty is small)
            for j in range(0, L):
                self.buffer[j+N] = data[j]

            # Do the convolution
            for j in range(0, L):
                s = 0
                for i in range(0, N+1):
                    s += b[i]*self.buffer[N+j-i]
                output_v[j] = s

            # Now move the last N samples we need to keep to the beginning of buffer
            for i in range(0, N):
                self.buffer[i] = self.buffer[L+i]


cdef class FirHalfbandDecimateFloat(object):
    cdef np.float32_t [::1] b
    cdef int chunkSize
    cdef np.float32_t [::1] buffer
    def __init__(self, int chunkSize, np.ndarray b):
        '''Cython optimized FIR half-band decimator for single precision data.
        *chunkSize* Length of the data chunks to be filtered (used to preallocate buffers)
        *b* FIR filter coefficients.'''
        self.b = b
        assert b.shape[0] % 2 == 1
        self.chunkSize = chunkSize
        assert chunkSize >= b.shape[0]
        assert chunkSize % 2 == 0
        cdef Py_ssize_t L = chunkSize + self.b.shape[0] - 1
        self.buffer = np.zeros((L,), dtype=np.float32)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    @cython.initializedcheck(False)
    def lfilter(self, np.float32_t [::1] data, np.float32_t [::1] output):
        '''Apply the filter to data and place result in output (half length of data)'''
        cdef Py_ssize_t i,j
        cdef Py_ssize_t L = data.shape[0] # number of new data points
        cdef Py_ssize_t N = self.b.shape[0] - 1 # number of taps
        cdef np.float32_t [::1] buffer = self.buffer # View on buffer
        cdef np.float32_t [::1] b = self.b # View on coefficients
        assert output.shape[0] == L/2
#        if output is None:
#            output = np.empty_like(data)
        cdef np.float32_t [::1] output_v = output

        cdef double s
        cdef Py_ssize_t center = N / 2
        with nogil:
            # Copy the new samples in at end of buffer (this is not optimal, but the performance pentalty is small (~2ms/2MS))
            for j in range(0, L):
                self.buffer[j+N] = data[j]

            # Do the convolution (only every other point required due to decimation)
            for j in range(0, L, 2):
                s = 0
                for i in range(0, N+1, 2): # Only every other coefficient due to Halfband filter
                    s += b[i]*self.buffer[N+j-i]
                s += b[center]*self.buffer[N+j-center] # Plus the center, of course
                output_v[j/2] = s

            # Now move the last N samples we need to keep to the beginning of buffer
            for i in range(0, N):
                self.buffer[i] = self.buffer[L+i]

cdef class FirHalfbandDecimateDouble(object):
    cdef np.float64_t [::1] b
    cdef int chunkSize
    cdef np.float64_t [::1] buffer
    def __init__(self, int chunkSize, np.ndarray b):
        '''Cython optimized FIR half-band decimator for double precision data.
        *chunkSize* Length of the data chunks to be filtered (used to preallocate buffers)
        *b* FIR filter coefficients.'''
        self.b = b
        assert b.shape[0] % 2 == 1
        self.chunkSize = chunkSize
        assert chunkSize >= b.shape[0]
        assert chunkSize % 2 == 0
        cdef Py_ssize_t L = chunkSize + self.b.shape[0] - 1
        self.buffer = np.zeros((L,), dtype=np.float64)

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    @cython.initializedcheck(False)
    def lfilter(self, np.float64_t [::1] data, np.float64_t [::1] output):
        '''Apply the filter to data and place result in output (half length of data)'''
        cdef Py_ssize_t i,j
        cdef Py_ssize_t L = data.shape[0] # number of new data points
        cdef Py_ssize_t N = self.b.shape[0] - 1 # number of taps
        cdef np.float64_t [::1] buffer = self.buffer # View on buffer
        cdef np.float64_t [::1] b = self.b # View on coefficients
        assert output.shape[0] == L/2
#        if output is None:
#            output = np.empty_like(data)
        cdef np.float64_t [::1] output_v = output

        cdef double s
        cdef Py_ssize_t center = N / 2
        with nogil:
            # Copy the new samples in at end of buffer (this is not optimal, but the performance pentalty is small (~2ms/2MS))
            for j in range(0, L):
                self.buffer[j+N] = data[j]

            # Do the convolution (only every other point required due to decimation)
            for j in range(0, L, 2):
                s = 0
                for i in range(0, N+1, 2): # Only every other coefficient due to Halfband filter
                    s += b[i]*self.buffer[N+j-i]
                s += b[center]*self.buffer[N+j-center] # Plus the center, of course
                output_v[j/2] = s

            # Now move the last N samples we need to keep to the beginning of buffer
            for i in range(0, N):
                self.buffer[i] = self.buffer[L+i]

def test():
    print "Hello World"


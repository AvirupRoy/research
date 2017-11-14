#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Class for running/online statistics calculation of mean, std deviation, skewness, and kurtosis
Created on 2017-07-05
Expanded on 2017-09-26
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""


from __future__ import print_function
import numpy as np
#class RunningStats:
#    """A class to calculate the mean, variance (and standard deviation) in an
#    iterative fashion. Works for vectors as well as scalars.
#    Implementation of Welford algorithm after https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance"""
#    
#    def __init__(self):
#        self.n = 0
#        self.old_m = 0
#        self.new_m = 0
#        self.old_s = 0
#        self.new_s = 0
#
#    def clear(self):
#        self.n = 0
#
#    def push(self, x):
#        """Add another data-set. x can be scalar or a vector (or maybe a matrix as well?). 
#        Uses Welford's algorithm to update variance/std deviation."""
#        
#        self.n += 1
#
#        if self.n == 1:
#            self.old_m = self.new_m = x
#            self.old_s = np.zeros_like(x)
#        else:
#            delta = x - self.old_m
#            self.new_m = self.old_m + delta / self.n
#            delta2 = x - self.new_m
#            self.new_s = self.old_s + delta * delta2
#
#            self.old_m = self.new_m
#            self.old_s = self.new_s
#
#    def mean(self):
#        """Return the running mean."""
#        return self.new_m if self.n else 0.0
#
#    def variance(self, ddof=0):
#        """Return the running variance. 
#        In standard statistical practice, ddof=1 provides an unbiased estimator of the variance of a hypothetical infinite population. ddof=0 provides a maximum likelihood estimate of the variance for normally distributed variables."""
#        return self.new_s / (self.n-ddof) if self.n > 1 else 0.0
#
#    def std(self, ddof=0):
#        """return the running standard deviation."""
#        return np.sqrt(self.variance(ddof))

class RunningStats(object):
    """A class to calculate the mean, variance (and standard deviation) in an
    iterative fashion. Works for vectors as well as scalars.
    Implementation of Welford algorithm after https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance"""
    
    def __init__(self):
        self.n = 0
        self.M1 = 0 # 1st order moment (mean)
        self.M2 = 0 # 2nd order moment (for variance)

    def clear(self):
        self.n = 0

    def push(self, x):
        """Add another data-set. x can be scalar or a vector (or maybe a matrix as well?). 
        Uses Welford's algorithm to update variance/std deviation."""
        
        self.n += 1
        n = self.n

        if n == 1:
            self.M1 = x
            self.M2 = np.zeros_like(x)
        else:
            delta = x - self.M1
            self.M1 = self.M1 + delta / n
            delta2 = x - self.M1
            self.M2 = self.M2 + delta * delta2

    def mean(self):
        """Return the running mean."""
        return self.M1 if self.n else np.nan

    def variance(self, ddof=0):
        """Return the running variance. 
        In standard statistical practice, ddof=1 provides an unbiased estimator of the variance of a hypothetical infinite population. ddof=0 provides a maximum likelihood estimate of the variance for normally distributed variables."""
        return self.M2 / (self.n-ddof) if self.n > 1 else np.nan

    def std(self, ddof=0):
        """return the running standard deviation."""
        return np.sqrt(self.variance(ddof))
    
    
class RunningStatsWithKurtosis(RunningStats):
    """An extension of RunningStats that adds skew and kurtosis calculation.
    More time consuming."""
    def __init__(self):
        self.n = 0
        self.M1 = 0 # 1st order moment (mean)
        self.M2 = 0 # 2nd order moment (for variance)
        self.M3 = 0 # 3nd order moment (for skew)
        self.M4 = 0 # 4th order moment (for kurtosis)
        
    def push(self, x):
        """Add another data-set. x can be scalar or a vector."""

        n1 = self.n        
        self.n += 1
        n = self.n

        if n == 1:
            self.M1 = x
            self.M2 = np.zeros_like(x)
        else:
            delta = x - self.M1
            delta_n = delta / n
            delta_n2 = delta_n * delta_n
            term1 = delta * delta_n * n1
            self.M1 = self.M1 + delta_n
            self.M4 = self.M4 + term1 * delta_n2 * (n*n - 3*n + 3) + 6 * delta_n2 * self.M2 - 4 * delta_n * self.M3
            self.M3 = self.M3 + term1 * delta_n * (n - 2) - 3 * delta_n * self.M2
            self.M2 = self.M2 + term1
        
    def skew(self):
        """Return the skew (should be zero for a symmetric distribution)."""
        return np.sqrt(self.n)*self.M3 / np.power(self.M2, 1.5) if self.n > 1 else np.nan
    
    def kurtosis(self, fisher=True):
        """Return the kurtosis. 
        If fisher is True (default), Fisher’s definition is used (a normal distribution has 0.0 kurtosis).
        If fisher is False, Pearson’s definition is used (normal distribution gives kurtosis of 3.0)."""
        off = 3 if fisher else 0
        return self.n*self.M4 / (self.M2*self.M2) - off if self.n > 1 else np.nan

if __name__ == '__main__':
    print('Test for scalars')
    xs = np.random.normal(size=10)
    rs = RunningStats()
    for x in xs:
        rs.push(x)
        print('Class: mean=', rs.mean(), 'var=', rs.variance(), 'std=', rs.std())
    print('Numpy: mean=', xs.mean(), 'var=', xs.var(), 'std=', xs.std())

    print('Test for vectors')
    rs = RunningStats()
    nSamples = 1000; nVector = 5
    npxs = np.empty((nSamples, nVector))
    for i in range(nSamples):
        x = np.random.normal(size=nVector)
        rs.push(x)
        npxs[i,:] = x
    print('Class: mean=', rs.mean())
    print('Numpy: mean=', npxs.mean(axis=0))
    print('Class: var =', rs.variance())
    print('Numpy: var =', npxs.var(axis=0))
    print('Class: std =', rs.std())
    print('Numpy: std =', npxs.std(axis=0))


    print('Test for scalars')
    from scipy import stats
    xs = np.random.normal(size=10)
    rs = RunningStatsWithKurtosis()
    for x in xs:
        rs.push(x)
        print('Class: mean=', rs.mean(), 'var=', rs.variance(), 'std=', rs.std(), 'skew=', rs.skew(), 'kurt=', rs.kurtosis())
    print('Numpy: mean=',xs.mean(), 'var=', xs.var(), 'std=', xs.std(), 'skew=', stats.skew(xs), 'kurt=', stats.kurtosis(xs))
    print('Test for vectors')
    rs = RunningStatsWithKurtosis()
    nSamples = 100; nVector = 5
    npxs = np.empty((nSamples, nVector))
    for i in range(nSamples):
        x = np.random.normal(size=nVector)
        rs.push(x)
        npxs[i,:] = x
    print('Class: mean=', rs.mean())
    print('Numpy: mean=', npxs.mean(axis=0))
    print('Class: var =', rs.variance())
    print('Numpy: var =', npxs.var(axis=0))
    print('Class: std =', rs.std())
    print('Numpy: std =', npxs.std(axis=0))
    print('Class: skew =', rs.skew())
    print('Scipy: skew =', stats.skew(npxs, axis=0))
    print('Class: kurt =', rs.kurtosis())
    print('Scipy: kurt =', stats.kurtosis(npxs, axis=0))
                
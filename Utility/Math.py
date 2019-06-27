# -*- coding: utf-8 -*-
"""
Created on Fri Mar 04 10:14:17 2016

@author: wisp10
"""

import time

class Integrator():
    def __init__(self, T=1, dtMax = 0):
        self.T = T
        assert dtMax >= 0
        self.dtMax = dtMax
        self.reset()

    def reset(self):
        self.data = 0
        self.tOld = 0
        
    def lastTime(self):
        return self.tOld
        
    def append(self, t, y):
        '''Add a new point at time t with value y.
        Returns the value of the integral.'''
        if self.tOld == 0:
            self.tOld = t
            return 0
        else:
            dt = min(t-self.tOld, self.dtMax)
            self.data += y*dt
            self.tOld = t
        return self.value()
        
    def value(self):
        return self.data/self.T
        
import numpy as np        
class History():
    def __init__(self, maxAge=5):
        self._maxAge = maxAge
        self.t = []
        self.y = []

    def append(self, t, y):
        self.y = np.append(self.y, y)
        self.t = np.append(self.t, t)
        tNewest = np.max(t)
        iRecent = self.t >= tNewest-self._maxAge
        self.y = self.y[iRecent]
        self.t = self.t[iRecent]
        return self.mean()
        
    def mean(self):
        return np.mean(self.y)

    def __str__(self):
        return "t=%s y=%s" % (self.t, self.y)

    def dydt(self, t=None):
        if t == None:
            t = time.time()
        nPoints = len(self.t)
        if nPoints < 2:
            return 0
        elif nPoints < 5:
            order = 1
        elif nPoints < 10:
            order = 2
        else:
            order = 3

        tCenter = np.mean(self.t)
        fit = np.polyfit(self.t-tCenter, self.y, order)
        der = np.polyder(fit)
        dydt = np.polyval(der, t-tCenter)
        return dydt

def pruneData(y, maxLength=20000, fraction=0.3): # This is copied from AVS47
    if len(y) < maxLength:
        return y
    start = int(fraction*maxLength)
    firstSection = 0.5*(np.asarray(y[0:start:2])+np.asarray(y[1:start+1:2]))
    return np.hstack( (firstSection, y[start+1:]) ).tolist()
      

if __name__ == '__main__':
    import numpy as np
    import matplotlib.pyplot as mpl
    
    #t = np.linspace(100,1000, 1000)
    t = np.random.rand(1000)*900+100
    t = np.sort(t)
    y = np.sin(2.*np.pi*t*0.05)+0.001*t+1
    r = np.zeros_like(y)
    integrator = Integrator(T=100)
    for i in range(len(t)):
        r[i] = integrator.addPoint(t[i], y[i])
        
    mpl.plot(t, y, '-b')
    mpl.plot(t, r, '-r')
    mpl.show()

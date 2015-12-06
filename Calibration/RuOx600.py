# -*- coding: utf-8 -*-
"""
Created on Tue May 19 10:22:44 2015

@author: jaeckel
"""

import numpy as np

class RuOx600_Nonsense:
    def __init__(self):
        pass

    def calculateTemperature(self, R):
        raise Exception("Not implemented")

    def calculateResistance(self, T):
        # This makes no sense!
        logT = np.log(T)
        logR = 9.631-4.37697*logT+1.00025*logT**2-0.07915*logT**3
        #R = np.power(10, logR)
        R = np.exp(logR)
        return R

class RuOx600:
    def __init__(self):
        d=np.genfromtxt('Calibration\RO600BPT.dat', names=True, skip_header=2)
        bptT = d['TK']
        bptR = d['ROhm']
        si = np.argsort(bptR) # Make sure to sort in increasing order of R for interpolation to work.
        self.bptT = bptT[si]
        self.bptR = bptR[si]

    def calculateTemperature(self, R):
        R = np.asarray(R)
        T = np.zeros_like(R)
        i = R >=1725.82
        lnR = np.log(R)
        A = -0.771272244
        B = 0.00010067892
        C = -1.071888E-9
        OneOverT = A + B*R[i]*lnR[i] + C*R[i]**2*lnR[i]
        T[i] = 1./OneOverT

        i = (R >= 1178.49) & (R <= 1725.82)
        A = -0.3199412263
        B = 5.7488447E-8
        C = -8.840903E-11
        OneOverT = A + B*R[i]**2.*lnR[i] + C*R[i]**3
        #OneOverT = A + B*R[i]*lnR[i] + C*R[i]**2*lnR[i]
        T[i] = 1./OneOverT

        i = (R<1178.49) & (R>1100.75)
        T[i] = np.interp(R[i], self.bptR, self.bptT)
        return T

    def calculateResistance(self, T):
        raise Exception("Not implemented")

if __name__=='__main__':
    import matplotlib.pyplot as mpl

    #T = np.logspace(np.log10(0.04), np.log10(4.2))
    #cal = RuOx600_Nonsense()
    #R = cal.calculateResistance(T)
    #mpl.loglog(T,R,'-', label='RuOx600 from some silly paper')

    cal = RuOx600()
    R = np.logspace(np.log10(1179), np.log10(29072.86))
    T = cal.calculateTemperature(R)
    mpl.loglog(T,R,'-', label='RO600')
    print cal.calculateTemperature([3081.68]), "should be 0.61K"
    print cal.calculateTemperature([1265.78]), "should be 6.30K"
    print cal.calculateTemperature([1127.06]), "should be 15.00K"
    mpl.legend()
    mpl.xlabel('T [K]')
    mpl.ylabel('R [Ohm]')
    mpl.show()


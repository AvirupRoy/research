# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 11:15:11 2015

@author: jaeckel
"""
import numpy as np

def SteinhartHart(R, a, b, c):
    lnR = np.log(R)
    T = 1./(a+b*lnR+c*lnR**3)
    return T

def SteinhartHartB(R, T0, B, R0):
    T = 1./(1./T0+np.log(R/R0)/B)
    return T

if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    from scipy.optimize import curve_fit

    d = np.loadtxt('NTCAFEKX05103HH.dat', delimiter='\t')
    T = d[:,0]+273.15
    R = d[:,1]*1E3

    T0 = 298.15; B = 3960; R0 = 10E3
    guess = [T0, B, R0]
    popt, pcov = curve_fit(SteinhartHartB, R, T, guess)
    T0 = popt[0]; B = popt[1]; R0 = popt[2]
    print "Steinhart-Hart B fit:"
    print 'T0 = ', T0, 'K'
    print 'B  = ', B
    print 'R0 = ', R0, 'Ohm'

    a = 1.6E-3; b = 2.5E-4; c = 7.1E-8
    guess = [a, b, c]
    popt, pcov = curve_fit(SteinhartHart, R, T, guess)
    a = popt[0]; b = popt[1]; c = popt[2]
    print "Full Steinhart-Hart fit:"
    print "a = ", a
    print "b = ", b
    print "c = ", c

    mpl.subplot(2,1,1)
    mpl.semilogy(T,R,'+',label='data')
    T_SHB = SteinhartHartB(R, T0, B, R0)
    T_SH  = SteinhartHart(R, a, b, c)
    mpl.semilogy(T_SHB,R, '-', label='Steinhart-Hart B')
    mpl.semilogy(T_SH,R, '-', label='full Steinhart-Hart')
    mpl.ylabel('R [Ohm]')
    mpl.legend()
    mpl.subplot(2,1,2)
    mpl.plot(T, T-T_SHB, 'o', label='Steinhart-Hart B')
    mpl.plot(T, T-T_SH, 's', label='full Steinhart-Hart')
    mpl.ylabel('T error [K]')
    mpl.xlabel('T [K]')
    mpl.legend()
    mpl.show()

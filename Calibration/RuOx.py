# -*- coding: utf-8 -*-
"""
Various RuOx thermometer calibrations
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
    '''This is the nominal calibration from the documentation that came for ADR3.
    It's not an actual calibration for the particular sensors in our system, but rather
    some nominal curves. However, it seems to be relatively accurate from ~45 to 3K.'''
    name = 'RuOx 600'
    
    def __init__(self):
        d=np.genfromtxt(r"D:\Research\ADR3 Codebase\adr3\Calibration\RO600BPT.dat", names=True, skip_header=2)
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

# -*- coding: utf-8 -
class RuOx2005():
    """RuOx2005 calibration (where from?)"""
    name = 'RuOx2005'
    A = 0.26832207756
    B = -0.320557039
    C = -0.0445353463
    D = 0.02544895043
    E = 0.00202967465
    def calculateTemperature(self, R):
        lnR = np.log(R)
        lnRSq = lnR**2
        T = (self.A + self.C*lnR + self.E*lnRSq) / (1+self.B*lnR+self.D*lnRSq)
        return T
        
class RuOxBus():
    """Cross calibration between ADR3 bus thermometer (RuOx600)
    read-out using AVS-47 resistance bridge (excitation level ????)
    through DMM and RuOx2005 (excitation level ????) read-out through lock-in.
    Provided by Shuo.
    Calibration data files:
    Calibration date:
    """
    name = 'RuOx bus'
    coefficients = [+2.53204782685596E+2,
                    +8.41717864826237E-1,
                    +2.24534685438334E-5,
                    -2.88735965350513E-9,
                    +1.74315053423948E-13,
                    -6.01752584503444E-18,
                    +1.25716217285131E-22,
                    -1.57224250852703E-27,
                    +1.08383221820494E-32,
                    -3.16671482123809E-38][::-1]
    def __init__(self):
        self.RuOx2005 = RuOx2005()

    def busToRuOx2005(self, Rbus):
        """convert RuOx(bus) resistance to equivalent RuOx2005 resistance"""
        return np.polyval(self.coefficients, Rbus)
        
    def calculateTemperature(self, R):
        """Convert ADR bus thermometer resistance readings to temperature using the cross-calibration between
        bus RuOx 600 and RuOx2005."""
        rRuOx2005 = self.busToRuOx2005(R)
        T = self.RuOx2005.calculateTemperature(rRuOx2005)
        return T
    
class RuOxBox():
    name = 'RuOx box'
    '''This calibration is from Yu, for the 1kOhm RuOx resistor
    inside the TES testing box. It's not known over which range it's good,
    probably only around 40 to 150mK or so.'''
    def __init__(self):
        self.a = 5.45088256
        self.b = 2.09708549
        
    def calculateTemperature(self, R):
        T = ((np.log(R) - self.a) / self.b)**(-4.)
        return T
    
if __name__=='__main__':
    import matplotlib.pyplot as mpl


    rBus = np.logspace(np.log10(1.5E3), np.log10(80E3), 1000)
    rRuOx2005 = RuOxBus().busToRuOx2005(rBus)
    mpl.figure()
    mpl.plot(rBus, rRuOx2005, '-')
    mpl.xlabel('R(bus thermometer) [Ohms]')
    mpl.ylabel('R(RuOx2005) [Ohms]')

    T_newCal = RuOxBus().calculateTemperature(rBus)
    mpl.figure()
    mpl.loglog(rBus, T_newCal, '.-')
    mpl.xlabel('R(bus thermometer) [Ohms]')
    mpl.ylabel('T [K]')
    
    T_oldCal = RuOx600().calculateTemperature(rBus)
    mpl.figure()
    mpl.plot(T_newCal, T_newCal-T_oldCal, '-')    
    mpl.xlabel('T (new calibration) [K]')
    mpl.ylabel('T (new-old) [K]')
    mpl.show()

    #T = np.logspace(np.log10(0.04), np.log10(4.2))
    #cal = RuOx600_Nonsense()
    #R = cal.calculateResistance(T)
    #mpl.loglog(T,R,'-', label='RuOx600 from some silly paper')

    cal = RuOx600()
    R = np.logspace(np.log10(1179), np.log10(29072.86))
    T = cal.calculateTemperature(R)
    mpl.loglog(T,R,'-', label='RO600')
    print(cal.calculateTemperature([3081.68]), "should be 0.61K")
    print(cal.calculateTemperature([1265.78]), "should be 6.30K")
    print(cal.calculateTemperature([1127.06]), "should be 15.00K")
    mpl.legend()
    mpl.xlabel('T [K]')
    mpl.ylabel('R [Ohm]')
    mpl.show()


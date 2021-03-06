# -*- coding: utf-8 -*-
"""
Various RuOx thermometer calibrations
Created on Tue May 19 10:22:44 2015

@author: jaeckel
"""

import numpy as np

class ResistiveThermometer(object):
    n = None
    def correctForReadoutPower(self, Th, P):
        '''Correct the sensor temperature reading for Joule heating (power P).'''
        if self.n is None:
            return Th
            
        np1 = self.n+1.0
        Tcold = np.power(np.power(Th, np1)-P/self.K, 1./np1)
        return Tcold

class RuOx600_Nonsense(ResistiveThermometer):
    info = 'Bad calibration equation from some Scientific Instruments datasheet'
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

class RuOx600(ResistiveThermometer):
    '''This is the nominal calibration from the documentation that came for ADR3.
    It's not an actual calibration for the particular sensors in our system, but rather
    some nominal curves. However, it seems to be relatively accurate from ~45mK to 3K.'''
    name = 'RuOx 600'
    info = 'Nominal sensor calibration for Scientific Instruments RuOx 600 series'
    
    def __init__(self):
        d=np.genfromtxt(r"D:\Users\FJ\ADR3\Calibration\RO600BPT.dat", names=True, skip_header=2)
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

class RuOx2005(ResistiveThermometer):
    """Calibration for RuOx 2005 sensor
    This is based on the Scientific Instruments calibration report dated
    October 25th, 2000, sent to Noran Instruments.
    Calibration was performed 2000-10-11 (SI Job No. 714000)
    The sensor is a model RO600A, S/N 2005.
    Excitation was 0.03uA ac (rms?) from 50 to 80mK and 0.3uA AC from 80mK to 3.2K.
    They only provided calibration equation and interpolation tables, no raw data.
    This calibration superseded an earlier one (2000-02-28, same job #) that apparently was in error.
    """
    name = 'RuOx2005'
    info = 'Calibration for RuOx model RO600A sensor serial #2005'
    A = 0.26832207756
    B = -0.320557039
    C = -0.0445353463
    D = 0.02544895043
    E = 0.00202967465
    
    K = 1.1992E-6 # W/K thermal stand-off, from G4C run.
    n = 2.541     # thermal power law index, from G4C run
    
    def calculateTemperature(self, R):
        '''Calculate sensor temperature from resistance reading.
        You can correct for readout power using the *correctForReadoutPower* method.
        '''
        lnR = np.log(R)
        lnRSq = lnR**2
        T = (self.A + self.C*lnR + self.E*lnRSq) / (1+self.B*lnR+self.D*lnRSq)
        return T
        
        
class RuOxBus(ResistiveThermometer):
    """Cross calibration between ADR3 bus thermometer ("RuOx600")
    read-out using AVS-47 resistance bridge (excitation level ????)
    through DMM and RuOx2005 (excitation level ????) read-out through lock-in.
    Provided by Shuo.
    Calibration data files:
    Calibration date:
    """
    name = 'RuOx bus'
    info = 'RuOx bus RO600A cross-calibrated against RuOx #2005 by Shuo (not so good above ~300mK)'
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

    K = 1.6819E-6 # W/K thermal stand-off, from G4C run.
    n = 2.691     # thermal power law index, from G4C run
                    
    def __init__(self):
        self.RuOx2005 = RuOx2005()

    def _busToRuOx2005(self, Rbus):
        """convert RuOx(bus) resistance to equivalent RuOx2005 resistance"""
        return np.polyval(self.coefficients, Rbus)
        
    def calculateTemperature(self, R):
        """Convert ADR bus thermometer resistance readings to temperature using the cross-calibration between
        bus RuOx 600 and RuOx2005."""
        rRuOx2005 = self._busToRuOx2005(R)
        T = self.RuOx2005.calculateTemperature(rRuOx2005)
        return T
    
class RuOxBox(ResistiveThermometer):
    name = 'RuOx box'
    '''This calibration is from Yu, for the 1kOhm RuOx resistor
    inside the TES testing box. It's not known over which range it's good,
    probably only around 40 to 150mK or so.
    For run G4C it is clear that this is not a very good calibration since it
    disagrees with bus thermometer and RuOx2005.
    '''
    info = 'Chip resistor used in box cross-calibrated against RuOx #2005 by Yu. Not particularly trustworthy.'
    
    K = 0.7320E-6 # W/K thermal stand-off, from G4C run, not a very good fit!
    n = 2.124     # thermal power law index, from G4C run, not a very good fit!
    
    def __init__(self):
        self.a = 5.45088256
        self.b = 2.09708549
        
    def calculateTemperature(self, R):
        T = ((np.log(R) - self.a) / self.b)**(-4.)
        return T
        
def getCalibration(thermometerId):
    if 'RuOx2005' in thermometerId:
        return RuOx2005()
    elif 'Bus' in thermometerId:
        return RuOxBus()
    else:
        raise KeyError('No calibration for this thermometer')
    
if __name__=='__main__':
    import matplotlib.pyplot as mpl


    rBus = np.logspace(np.log10(1.5E3), np.log10(80E3), 1000)
    rRuOx2005 = RuOxBus()._busToRuOx2005(rBus)
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

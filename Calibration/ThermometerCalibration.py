# -*- coding: utf-8 -*-
"""
Created on Wed Jul 03 16:20:57 2013
# Vectorize me!
@author: jaeckel
"""

#from math import acos, cos, log10
import numpy as np

class BreakpointCalibration(object):
    def __init__(self):
        self.Rmin = 0
        self.Rmax = 0
        self.log10Rs = []
        self.Ts = []

    def setBreakpoints(self, log10Rs, Ts):
        diff = np.diff(log10Rs)
        if np.all(diff > 0):
            self.log10Rs = log10Rs
            self.Ts = Ts
        else: # Need to sort datapoints in order for interpolation to work
            si = np.argsort(log10Rs)
            self.log10Rs = log10Rs[si]
            self.Ts = Ts[si]

        self.Rmin = 10**min(log10Rs)
        self.Rmax = 10**max(log10Rs)

    def isValid(self):
        return self.Rmin < self.Rmax

    def inRange(self, R):
        '''Is this resistance included in the calibration range?'''
        return (R >= self.Rmin-1E-3) & (R  <= self.Rmax+1E-3)

    def calculateTemperature(self, R):
        r = np.asarray(R)
        good = np.asarray(self.inRange(r))
        T = np.zeros_like(r)
        T[good] = np.interp(np.log10(r[good]), self.log10Rs, self.Ts)
        if isinstance(R, np.ndarray):
            return T
        else:
            return type(R)(T)


class ChebychevCalibration(object):
    '''Hold all the information contained  in a single Lakeshore Chebychev temperature calibration fit.'''
    def __init__(self):
        self.ZL = 0
        self.ZU = 0
        self.Rmin = 0
        self.Rmax = 0
        self.Chebychev = []

    def writeCofCalibrationFile(self, f, fitRange=1):
        f.write('FIT RANGE:                              %d\n' % fitRange)
        f.write('Fit type for range %d:                   LOG\n' % fitRange)
        f.write('Order of fit range %d:                   %d\n' % (fitRange, self.order))
        f.write('Zlower for fit range %d:                 %.9g\n' % (fitRange, self.ZL))
        f.write('Zupper for fit range %d:                 %.9g\n' % (fitRange, self.ZU))
        f.write('Lower Resist. limit for fit range %d:    %.6f\n' % (fitRange, self.Rmin))
        f.write('Upper Resist. limit for fit range %d:    %.6f\n' % (fitRange, self.Rmax))
        for i,cheb in enumerate(self.Chebychev):
            f.write('C(%d) Equation  %d:                       %.8e\n' % (i, fitRange, cheb))

    @property
    def order(self):
        return len(self.Chebychev)-1

    def isValid(self):
        '''A simple sanity check on the calibration coefficients.'''
        if self.ZU <= self.ZL:
            return False
        if self.Rmax <= self.Rmin:
            return False
        if len(self.Chebychev) < 2:
            return False
        return True

    def inRange(self, R):
        '''Is this resistance included in the calibration range?'''
        return (R >= self.Rmin-1E-3) & (R  <= self.Rmax+1E-3)

    def calculateTemperature(self, R):
        '''Convert the resistance into a temperature reading if possible. Returns 0 if not in range.'''
        r = np.asarray(R)
        good = np.asarray(self.inRange(r))
        T = np.zeros_like(r)

        Z = np.log10(r[good])
        X = ((Z-self.ZL)-(self.ZU-Z))/(self.ZU-self.ZL)
        #T=float(0)
        #if X < -1 or X > +1:
        #    return T
        acosX = np.arccos(X)
        for i in range(len(self.Chebychev)):
            T[good] += self.Chebychev[i] * np.cos(float(i) * acosX)

        if isinstance(R, np.ndarray):
            return T
        else:
            return type(R)(T)


class CalibrationSet(object):
    def __init__(self, sensorSerial):
        self._sensorSerial = sensorSerial
        self._calibrations = []
        self.n = None

    def sensorSerial(self):
        return self._sensorSerial

    def clearCalibrations(self):
        self._calibrations = []

    def loadCalibrationFile(self, filename):
        a = filename.split('.')
        if len(a) < 1:
            raise Exception('Cannot determine file type from filename extension.')
        extension = a[-1].upper()
        if 'COF' in extension:
            self.loadCofCalibrationFile(filename)
        elif 'BPT' in extension:
            self.loadBptCalibrationFile(filename)
        elif '340' in extension:
            self.load340CalibrationFile(filename)
        else:
            raise Exception('Unrecognized filename extension:%s' % extension)

    def load340CalibrationFile(self, filename):
        pass

    def loadBptCalibrationFile(self, filename):
        '''Load simple breakpoint table (*.bpt). First column=log10(R), second column=T'''
        with open(filename, 'r') as f:
            log10Rs = []
            Ts = []
            for line in f:
                a = line.split()
                if len(a) != 2:
                    raise Exception('Invalid line in BPT calibration file.')
                log10Rs.append(float(a[0]))
                Ts.append(float(a[1]))
            cal = BreakpointCalibration()
            cal.setBreakpoints(log10Rs, Ts)
            if cal.isValid():
                self._calibrations.append(cal)
            else:
                raise Exception('Calibration invalid!')

    def loadTable(self, filename, **kwargs):
        '''Load data from a T, R table. kwargs will be passed on to np.genfromtxt()'''
        d = np.genfromtxt(filename, **kwargs)
        Ts = d[:,0]
        Rs = d[:,1]
        cal = BreakpointCalibration()
        cal.setBreakpoints(np.log10(Rs), Ts)
        if cal.isValid():
            self._calibrations.append(cal)
        else:
            raise Exception('Calibration invalid!')

    def loadCofCalibrationFile(self, filename):
        '''Load Chebychev polynomial calibrations from Lakeshore COF files.'''
        with open(filename, 'r') as f:
            n = self._readlineCof(f, 'Number of fit ranges', int)
            for i in range(1,n+1):
                index = self._readlineCof(f, 'FIT RANGE', int)
                if index != i:
                    raise Exception('Incorrect numbering of fit ranges.')
                fitType = self._readlineCof(f, 'Fit type for range', str)
                if fitType.upper() == 'LOG':
                    pass
                else:
                    raise Exception('Unsupported fit type:"%s"' % fitType)
                fitOrder = self._readlineCof(f, 'Order of fit range', int)
                if fitOrder<2 or fitOrder>20:
                    raise Exception('Fit order out of range')
                cal = ChebychevCalibration()
                cal.ZL = self._readlineCof(f, 'Zlower for fit range', float)
                cal.ZU = self._readlineCof(f, 'Zupper for fit range', float)
                cal.Rmin = self._readlineCof(f, 'Lower Resist. limit for fit range', float)
                cal.Rmax = self._readlineCof(f, 'Upper Resist. limit for fit range', float)
                chebychev = []
                for k in range(fitOrder+1):
                    chebychev.append(self._readlineCof(f, 'C(%d) Equation' % (k), float))
                cal.Chebychev = chebychev
                if not cal.isValid():
                    raise Exception('Calibration appears invalid')
                self._calibrations.append(cal)

    def writeCofCalibrationFile(self, filename):
        with open(filename, 'w') as f:
            f.write('Number of fit ranges:                   %d\n' % len(self._calibrations))
            for i,cal in enumerate(self._calibrations):
                cal.writeCofCalibrationFile(f, i+1)

    def _readlineCof(self, f, token, dtype=float):
        '''Helper function for parsing of COF files. Performs sanity checks for correct formatting.'''
        l = f.readline()
        a = l.split(':')
        #print("Line: ", l)
        if len(a) < 2:
            message = "Incomplete entry in COF file (line: %s)" % l
            raise Exception(message)
        if not token.upper() in a[0].upper():
            raise Exception('Invalid entry in COF file. Expected "%s", found "%s".' % (token, a[0]))
        if dtype == float:
            return float(a[1])
        elif dtype == int:
            return int(a[1])
        elif dtype == str:
            return str(a[1]).strip()
        else:
            raise Exception('Unknown data type')

    def calculateTemperature(self, R):
        '''Convert a resistance reading into a temperature based on the Chebychev fits.'''
        r = np.asarray(R)
        T = np.zeros_like(r)
        for cal in self._calibrations:
            Ti = cal.calculateTemperature(r)
            good = np.asarray(Ti > 0)
            T[good] = Ti[good]

        if isinstance(R, np.ndarray):
            return T
        else:
            return type(R)(T)
            
    def correctForReadoutPower(self, Th, P):
        '''Correct the sensor temperature reading for Joule heating (power P).'''
        if self.n is None:
            return Th
            
        np1 = self.n+1.0
        Tcold = np.power(np.power(Th, np1)-P/self.K, 1./np1)
        return Tcold


if __name__ == '__main__':
#   serial = '23851'
    serial = '21692'
    fileName = '%s.cof' % serial
    cal = CalibrationSet(serial)
    cal.loadCalibrationFile(fileName)
    import matplotlib.pyplot as mpl
#    import numpy as np
    #Rs = np.logspace(np.log(50), np.log(8E3))
    Rs = np.linspace(20, 8E3, 2000)
    Ts = cal.calculateTemperature(Rs)
    mpl.figure()
    mpl.loglog(Ts, Rs, '-', label='Chebychev fit from %s' % fileName)

    d = np.genfromtxt('%s_TestData.dat' % serial, names=True)
    test_T = d['TK']
    test_R = d['ROhm']
    mpl.plot(test_T, test_R, 'o', label='cal. data')

    mpl.xlabel('T [K]')
    mpl.ylabel('R [Ohm]')
    mpl.xlim(45E-3,3)
    mpl.suptitle('Thermometer calibration %s' % serial)
    mpl.legend(loc='best')
    mpl.show()

#    cal = CalibrationSet('RO600')
#    cal.loadTable('RO600BPT.dat', skip_header=3)
#    c = cal._calibrations[0]

    #filename2 = 'Calibrations/C19239.bpt'
    #filename3 = 'Calibrations/C19239.cof'
    #cal = CalibrationSet('C19239')
    #cal.loadBptCalibrationFile(filename2)
    #cal.loadCofCalibrationFile(filename3)
    #print cal.calculateTemperature(R)


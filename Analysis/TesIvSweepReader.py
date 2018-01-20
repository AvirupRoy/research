# -*- coding: utf-8 -*-
"""
Created on Thu Oct 05 14:30:44 2017

@author: wisp10
"""
from __future__ import print_function, division
import h5py as hdf
import numpy as np            
import matplotlib.pyplot as mpl
from Analysis.HkImport import HkImporter
import warnings

#f = hdf.File(fileName, 'r')

def generateImportCode(hdfRoot):
    for key in hdfRoot.attrs.keys():
        print("self.%s = attrs['%s']" % (key,key))

class HdfGenericImporter(object):
    def __init__(self, fileName):
        f = hdf.File(fileName, 'r')
        for key in f.attrs.keys():
            self.__setattr__(key, f.attrs[key])
        f.close()

class IvSweepCollection(object):
    class Info:
        def __init__(self, attrs):
            self.program = attrs['Program']
            self.version = attrs['Version']
            self.sample = attrs['Sample']
            self.comment = attrs['Comment']
            self.startTime = attrs['StartTime']
            self.startTimeLocal = attrs['StartTimeLocal']
            self.startTimeUTC = attrs['StartTimeUTC']
            self.Vmax = attrs['Vmax']
            self.sampleRate = attrs['sampleRate']
            self.decimation = attrs['decimation']
            self.deviceName = attrs['deviceName']
            self.aoChannel = attrs['aoChannel']
            self.aoRangeMin = attrs['aoRangeMin']
            self.aoRangeMax = attrs['aoRangeMax']
            self.aiChannel = attrs['aiChannel']
            self.aiRangeMin = attrs['aiRangeMin']
            self.aiRangeMax = attrs['aiRangeMax']
            self.zeroHoldTime = attrs['zeroHoldTime']
            self.aiTerminalConfig = attrs['aiTerminalConfig']
            self.peakHoldTime = attrs['peakHoldTime']
            self.betweenHoldTime = attrs['betweenHoldTime']
            self.slewRate = attrs['slewRate']
            self.pflReport = attrs['pflReport']
            self.pflRfb = attrs['pflRfb']
            self.pflCfb = attrs['pflCfb']
            try:
                self.auxAoChannel = attrs['auxAoChannel']
                self.auxAoRangeMin = attrs['auxAoRangeMin']
                self.auxAoRangeMax = attrs['auxAoRangeMax']
                self.auxAoValue = attrs['auxAoValue']
            except:
                self.auxAoChannel = None
                self.auxAoRangeMin = None
                self.auxAoRangeMax = None                
                self.auxAoValue = 0

            try:                
                self.aiDriveChannel = attrs['aiDriveChannel']
            except KeyError:
                self.aiDriveChannel = None
            self.stopTime = attrs['StopTime']
            self.stopTimeLocal = attrs['StopTimeLocal']
            self.stopTimeUTC = attrs['StopTimeUTC']
            try:
                self.polarity = attrs['polarity']
            except KeyError:
                self.polarity = None
                
            
    def __init__(self, fileName):
        f = hdf.File(fileName, 'r')
        self.info = IvSweepCollection.Info(f.attrs)
        self.adrR = f['AdrResistance'].value
        self.adrt = f['AdrResistance_TimeStamps'].value
        self.Vexc = f['excitationWave_decimated'].value
        try:
            self.driveSignalRaw = f['DriveSignalRaw'] # Measured drive signal
            self.driveSignalDecimated = f['DriveSignalDecimated'].value # After decimation
            #self.Vbias = self.driveSignalDecimated
        except:
            pass
        self.Vbias = self.Vexc
        
        if 'HK' in f.keys():
            self.hk = HkImporter(f['HK'])
        else:
            self.hk = None
            
        self.hdfFile = f
        sweepKeys = [key for key in f if 'Sweep' in key]
        self.nSweeps = len(sweepKeys)
        
        #VexcMax = np.max(self.Vexc)
        #d = np.hstack([[0], np.diff(self.Vexc)])
        d = np.gradient(self.Vexc)
        dmax = np.max(np.abs(d))
        dTh = 0.5*dmax
        self.iRampUp1 = (d > +dTh) & (self.Vexc > 0)
        self.iRampDo1 = (d < -dTh) & (self.Vexc > 0)
        self.iRampDo2 = (d < -dTh) & (self.Vexc < 0)
        self.iRampUp2 = (d > +dTh) & (self.Vexc < 0)
        iZero = self.Vexc == 0
        x = np.where(iZero)[0]
        zeroRanges = np.split(x, np.where(np.diff(x)!= 1)[0]+1)
        self.iZeros = []
        for i, r in enumerate(zeroRanges):
            z = np.zeros_like(self.iRampDo1, dtype=np.bool)
            z[r] = True
            self.iZeros.append(z)
        
        #firstRampUp1 = np.argwhere(iRampUp1)[0][0]
        #lastRampUp2 = np.argwhere(iRampUp2)[0][-1]
        #self.iPre = iZero.copy(); self.iPre[firstRampUp1:] = False
        #self.iPost = iZero.copy(); self.iPost[:lastRampUp2+1] = False
        #self.iInter = 
        self.rampIndices = (self.iRampUp1, self.iRampDo1, self.iRampDo2, self.iRampUp2, self.iZeros ) #, self.iHold1)
    
    def sweep(self, n):
        return IvSweep(self.hdfFile['Sweep_%06d' % n], self.Vbias, self.rampIndices)
        
    def __len__(self):
        return self.nSweeps
        
    def __getitem__(self, key):
        if isinstance(key, slice):
           (start, step, stop) = key.indices(self.nSweeps)
           return [self[i] for i in xrange(start, step, stop)]
        else:
            if key < 0 : #Handle negative indices
                key += len( self )
            if key < 0 or key >= self.nSweeps:
                raise IndexError
        return self.sweep(key)

    def __iter__(self):
        for i in range(0, self.nSweeps):
            try:
                s = self.sweep(i)
            except IOError as e:
                print('Unable to load sweep:', e)
                s = None
            yield s
        
    def plot(self, stride=1):
        for sweep in self[::stride]:
            sweep.plot()
            
            
        
class IvSweep(object):
    '''Represents a single IV sweep (typically recorded using the IvCurveDaq.py software).
    Most functions are only available after the circuit parameters (Rbias, Rshunt, Rfb, and Mi/Mfb) have been applied
    with applyCircuitParameters.
    Additional functions become available, once the TES temperature has been calculated for each bias point (using *applyThermalModel*).'''
    
    def __init__(self, hdfRoot, Vbias, rampIndices):
        attrs = hdfRoot.attrs
        self.time = attrs['Time']
        self.timeLocal = attrs['TimeLocal']
        self.timeUTC = attrs['TimeUTC']
        self.Tadr = attrs['Tadr']
        self.auxAoValue = attrs['auxAoValue']
        self.Vbias = Vbias
        self.Vsquid = hdfRoot['Vsquid'].value
        
        self.iRampUp1, self.iRampDo1, self.iRampDo2, self.iRampUp2, self.iZeros = rampIndices
        
    def plotRaw(self):
        '''Plot the raw sweep data (Vsquid vs Vbias)'''
        mpl.plot(self.Vbias, self.Vsquid, '-', label='%.2f mK' % (self.Tadr*1E3))       
        
    def plot(self):
        '''Plot the Vtes vs Ites as calculated by applyCiruitParameters'''
        mpl.plot(self.Vtes, self.Ites, '-', label='%.2f mK' % (self.Tadr*1E3))       
        
    def squidOffsetVoltage(self, zeros=[0,1,2]):
        '''Determine the SQUID offset as the average of before (zero=0), between (zero=1) and after sweep (zero=2) data.
        '''
        Vof = []
        for z in zeros:
            Vof.append(np.mean(self.Vsquid[self.iZeros[z]]))
        return np.mean(Vof)
        
    def subtractSquidOffset(self, zeros=[0,1,2]):
        '''Subtract the SQUID offset, calculated by averaging over specified zero regions:
        0: before sweep
        1: between sweep
        2: after sweep data'''
        self.Vsquid -= self.squidOffsetVoltage(zeros)

    def findSlopeAndOffset(self, Vmax, Vmin=None, ramp=None):
        '''Return slop and intercept between Vmin (=-Vmax by default) and Vmax
        Optionally the data can be narrowed down by the *ramp* parameter,
        e.g. specifying to use only one or more of the sweeps: ramp=sweep.iRampUp1
        '''
        if Vmin is None:
            Vmin = -Vmax
        if Vmin > Vmax:
            Vmin,Vmax = Vmax,Vmin
        i = (self.Vbias > Vmin) & (self.Vbias < Vmax)
        if ramp is not None:
            i &= ramp
        slope, Vo = np.polyfit(self.Vbias[i], self.Vsquid[i], 1)
        return slope,Vo
        
    def findTesBias(self, Rb, Rs, Rsq):
        '''Calculate TES voltage, current, and power, using circuit parameters
        *Rb*  : bias resistance
        *Rs*  : shunt resistance
        *Rsq* : effective SQUID resistance (=Rfb * Mi/Mfb)
        
        This function supersedes applyCircuitParameters
        '''
        self.Rb = Rb
        self.Rs = Rs
        self.Rsq = Rsq
        self.Ites = self.Vsquid / Rsq
        self.Ibias = self.Vbias / Rb
        Is = self.Ibias - self.Ites
        self.Vtes = Rs * Is
        
    def applyCircuitParameters(self, Rb, Rfb, Rs, Mfb, Mi):
        '''Deprecated'''
        self.Rb = Rb
        self.Rfb = Rfb
        self.Rs = Rs
        self.Mfb = Mfb
        self.Mi = Mi
        self.Ites = Mfb/Mi * self.Vsquid/Rfb
        self.Ibias = self.Vbias / Rb
        Is = self.Ibias - self.Ites
        self.Vtes = Rs * Is

    @property        
    def Rtes(self):
        '''Calculate TES resistance; must run *applyCircuitParameters* first.'''
        return self.Vtes/self.Ites
        
    @property
    def Ptes(self):
        '''Calculate TES power; must run *applyCircuitParameters* first.'''
        return self.Vtes*self.Ites
        
    def applyThermalModel(self, thermalFunction, Tbase):
        '''Apply a thermal model function f(Tbase, power) to determine TES temperature.'''
        self.Ttes = thermalFunction(Tbase, self.Ptes)
        return self.Ttes
        
    def checkForOffsetShift(self, threshold=1E-3):
        V0s = []
        for zr in self.iZeros:
            V0s.append(np.mean(self.Vsquid[zr]))
        return np.abs(np.diff(V0s)) > threshold
        
    def findFluxJumps(self, ramp = None):
        if ramp is None:
            ramp = np.ones_like(self.Vsquid, dtype=np.bool)
        d = np.gradient(self.Vsquid)
        median = np.median(d[ramp])
        std = np.std(d[ramp])
        largeDerivatives =  (np.abs(d-median) > (4*std)) & ramp
        return largeDerivatives
        
    def fixFluxJump(self, position, deltaV, invalidate=5):
        self.Vsquid[position:] += deltaV
        self.Vsquid[position-invalidate:position+invalidate+1] = np.nan
        
    def fitRn(self, Vmin):
        i = np.abs(self.Vtes) > Vmin
        fit = np.polyfit(self.Ites[i], self.Vtes[i], 1)
        Rn = fit[0]
        return Rn

    def findCriticalCurrents(self, Vthreshold):
        iCritPos = np.where(self.iRampUp1 & (self.Vtes > Vthreshold))[0][0]
        IcPos = self.Ibias[iCritPos] # Below critical point all bias current flows through TES
        iCritNeg = np.where(self.iRampDo2 & (self.Vtes < -Vthreshold))[0][0]
        IcNeg = self.Ibias[iCritNeg]
        return IcPos, IcNeg
        
    def findBiasPoint(self, variable, goalValue):
        '''Find the bias point that is closest approach of variable to the required goalValue.
        Variable can be one of 'I', 'R', 'V', or 'P'. If the value specified is positve, the result
        will be from the positive sweep, if negative from the negative sweep.'''
        
        if goalValue > 0:
            iSelect = self.iRampDo1 & (self.Vtes>2E-10)
        else:
            iSelect = self.iRampDo2 & (self.Vtes<2E-10)
        if variable in ['I']:
            y = self.Ites
        elif variable in ['R']:
            y = self.Rtes; goalValue = abs(goalValue)
        elif variable in ['V']:
            y = self.Vtes
        elif variable in ['P']:
            y = self.Ptes; goalValue = abs(goalValue)
            
        i = np.argmin(np.abs(y[iSelect] - goalValue))
        Ites = self.Ites[iSelect][i]
        Vbias = self.Vbias[iSelect][i]
        Vtes = self.Vtes[iSelect][i]
        return (Vbias, Ites, Vtes)
        
    def findPointsCloseTo(self, variable, goalValue, n=3):
        '''Return the indices and values of the sweep data points that are closest in
        value to goalValue for specified variable.
        Returns the indices and the values of the variable at these points.
        E.g. findPointsCloseTo('R', 2E-3, n=5) will find the 5 points closest to Rtes=2mOhm.'''
        
        if goalValue > 0:
            iSelect = self.iRampDo1 & (self.Vtes>2E-10)
        else:
            iSelect = self.iRampDo2 & (self.Vtes<2E-10)
        if variable in ['I']:
            y = self.Ites
        elif variable in ['R']:
            y = self.Rtes; goalValue = abs(goalValue)
        elif variable in ['V']:
            y = self.Vtes
        elif variable in ['P']:
            y = self.Ptes; goalValue = abs(goalValue)
        elif variable in ['Vbias']:
            y = self.Vbias
        i = np.argsort(np.abs(y[iSelect] - goalValue))[0:n]
        indices, = np.nonzero(iSelect)
        i = indices[i]
        return i, y[i]
        
    def fitRtesCloseTo(self, variable, goalValue, n=3, order=1, doPlot=False):
        '''Find Rtes and its derivative with respect to variable.'''
        
        i, vs = self.findPointsCloseTo(variable, goalValue, n)
        Rs = self.Rtes[i]
        iSort = np.argsort(vs)
        fit = np.polyfit(vs[iSort], Rs[iSort], order)
        Rtes = np.polyval(fit, goalValue) 
        derivative = np.polyder(fit, 1) # Find first derivative
        dRtes_dv = np.polyval(derivative, goalValue)
        
        if doPlot:
            mpl.plot(vs, Rs, '.')
            mpl.plot(vs[iSort], np.polyval(fit, vs[iSort]), '-')
            mpl.scatter(goalValue, Rtes)
        return Rtes, dRtes_dv
        
    def findAlphaIvCloseTo(self, variable, goalValue, n=10, order=1, doPlot = False):
        '''Determine I0, R0, T0, and alpha_IV at *variable*=*goalValue*.
        *variable* : choose from 'I', 'V', 'R', 'Vbias'
        *n*: number of samples around the goal point to take into account
        *order*: order of the polynomial used for the local fit.
        *doPlot*: show diagnostic plots
        Returns: I0, R0, T0, alpha_IV
        '''
        i, vs = self.findPointsCloseTo(variable, goalValue, n)
        Rs = self.Rtes[i]
        Ts = self.Ttes[i]
        Is = self.Ites[i]
        iSort = np.argsort(vs)
        fitRvsVar = np.polyfit(vs[iSort], Rs[iSort], order)
        R0 = np.polyval(fitRvsVar, goalValue) # R at that point
        fitTvsVar = np.polyfit(vs[iSort], Ts[iSort], order)
        T0 = np.polyval(fitTvsVar, goalValue) # T at that point
        fitIvsVar = np.polyfit(vs[iSort], Is[iSort], order)
        I0 = np.polyval(fitIvsVar, goalValue) # I at that point (this is a little hackish)
        iSort = np.argsort(Ts)
        fitRvsT = np.polyfit(Ts[iSort], Rs[iSort], order)
        dRdT = np.polyder(fitRvsT, 1)
        dRdT0 = np.polyval(dRdT, T0)
        if doPlot:
            mpl.figure()
            mpl.plot(vs,Rs, '.')
            xfit = np.linspace(np.min(vs), np.max(vs), 100)
            mpl.plot(xfit, np.polyval(fitRvsVar,xfit), '-')
            mpl.scatter(goalValue, R0)
            mpl.ylabel('R')
            mpl.figure()
            mpl.plot(vs,Ts, '.')
            mpl.ylabel('T')
            mpl.plot(xfit, np.polyval(fitTvsVar,xfit), '-')
            mpl.scatter(goalValue, T0)
            mpl.figure()
            mpl.plot(Ts, Rs, '.')
            xfit = np.linspace(np.min(Ts), np.max(Ts), 100)
            mpl.plot(xfit, np.polyval(fitRvsT, xfit), '-')
            mpl.scatter(T0, R0)
            mpl.xlabel('T')
            mpl.ylabel('R')
            
        alphaIv = T0/R0 * dRdT0
        return I0, R0, T0, alphaIv
        
    def plotDetails(self):
        fig,pls = mpl.subplots(3,1,sharex=True)        
        pls[0].plot(self.Vbias)
        pls[0].set_ylabel('Vbias')
        pls[1].plot(self.Vsquid)
        pls[0].set_ylabel('Vsquid')
        pls[2].plot(np.gradient(self.Vsquid))
        pls[2].set_ylabel('dVsquid')

if __name__ == '__main__':
    fileName = 'D:\\Users\\Runs\\G4C\\IV\\TES2_IV_20171031_184923.h5'
    sweeps = IvSweepCollection(fileName)
    print('Number of sweeps:', len(sweeps))
    for i,sweep in enumerate(sweeps):
        print(i, sweep.checkForOffsetShift(1E-3))
    
    

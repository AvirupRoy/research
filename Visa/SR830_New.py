# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 10:15:32 2015

@author: wisp10
"""
from __future__ import print_function

from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
from Visa.VisaSetting import EnumSetting, IntegerSetting, NumericEnumSetting, FloatSetting, OnOffSetting, InstrumentWithSettings #, SettingCollection, AngleSetting
from Visa.VisaInstrument import VisaInstrument
import numpy as np
import warnings

class SR830LiaStatus(object):
    def __init__(self, statusByte):
        self._statusByte = statusByte
        
    @property
    def inputOverload(self):
        return bool(self._statusByte & 1)
        
    @property
    def filterOverload(self):
        return bool(self._statusByte & 2)
        
    @property
    def outputOverload(self):
        return bool(self._statusByte & 4)

    @property
    def anyOverload(self):
        return bool(self._statusByte & 7)

    @property
    def unlocked(self):
        return bool(self._statusByte & 8)

    @property
    def frequencyRangeChanged(self):
        return bool(self._statusByte & 16)
        
    @property
    def timeConstantRanged(self):
        return bool(self._statusByte & 32)
        
    @property
    def triggeredExternally(self):
        return bool(self._statusByte & 64)
    

class SR830(VisaInstrument, InstrumentWithSettings, QObject):
    #adcReadingAvailable = pyqtSignal(float, float)
    #resistanceReadingAvailable = pyqtSignal(float, float)
    auxInRead = pyqtSignal(int, float)
    inputOverloadRead = pyqtSignal(bool)
    filterOverloadRead = pyqtSignal(bool)
    outputOverloadRead = pyqtSignal(bool)
    
    
    readingAvailable = pyqtSignal(float, float, float)
    '''Emitted whenever a new reading is taken with snapSignal, provides X, Y, and f'''

    OffsetQuantityCodes = {'X': 1, 'Y': 2, 'R': 3}
    OffsetExpandCodes = {1:0, 10:1, 100:2}
    Channel1DisplayItems = {'X': 0, 'R':1, 'Xn':2,'AUX In 1':3, 'AUX In 2':4}
    Channel2DisplayItems = {'Y': 0, 'Theta':1, 'Yn':2,'AUX In 3':3, 'AUX In 4':4}
    
    def __init__(self, visaResource):
        QObject.__init__(self)
        InstrumentWithSettings.__init__(self)
        VisaInstrument.__init__(self, visaResource)
        self._x = None
        self._y = None
        self._f = None
        self._auxIn = [np.nan, np.nan, np.nan, np.nan]
        self.model = 'SR830'
        self.serial = '000000'
        if visaResource is not None:
            try:
                visaId = self.visaId()
                d = visaId.split(',')
                self.model = d[1]
                self.serial = d[2][3:]
                if not self.model in ['SR810', 'SR830', 'SR850']:
                    raise Exception('Unknown model %s' % self.model)
            except Exception as e:
                warnings.warn("Unable to obtain VISA ID: %s" % e)
            
            
        self.inputSource = EnumSetting('ISRC', 'input source', [(0, 'A (single ended)'), (1, 'A-B (differential)'), (2, 'I (1 MOhm)'), (3, 'I (100 MOhm)')], self)
        self.inputCoupling = EnumSetting('ICPL', 'input coupling', [(0, 'AC'), (1, 'DC')], self)
        self.inputGrounding = EnumSetting('IGND', 'input shield ground', [(0, 'FLOAT'), (1, 'GND')], self)
        self.inputFilters = EnumSetting('ILIN', 'input filters', [(0, 'None'), (1, '60 Hz'), (2, '120Hz'), (3, '60 & 120 Hz')], self)
        self.reserve = EnumSetting('RMOD', 'reserve', [(0, 'high reserve'), (1, 'normal'), (2, 'low noise')], self)
        self.syncDemodulator = OnOffSetting('SYNC', 'synchronous demodulator', self)
        self.auxOut = []
        for i in range(4):
            self.auxOut.append(FloatSetting('AUXV %i,' % (i+1), 'auxilliary output', -10.,+10., 'V', 1E-3, 3, self, queryString='AUXV? %i' % (i+1)))
            
        self.sineOut = FloatSetting('SLVL', 'sine out amplitude', 0.004, 5.000, 'V', step=0.002, decimals=3, instrument=self)
        self.referenceFrequency = FloatSetting('FREQ', 'reference frequency', 1E-3, 102E3, 'Hz', step=1E-4, decimals=4, instrument=self)
        #self.referencePhase = AngleSetting('PHAS', 'reference phase', self)
        self.referenceTrigger = EnumSetting('RSLP', 'reference trigger', [(0, 'sine'), (1, 'positive edge'),(2,'negative edge')], instrument=self)
        if self.model in ['SR810', 'SR830']:
            self.referenceSource = EnumSetting('FMOD', 'reference source', [(0, 'external'), (1, 'internal')], self)
        elif self.model == 'SR850':
            self.referenceSource = EnumSetting('FMOD', 'reference source', [(0, 'internal'), (1, 'sweep'), (2, 'external')], self)

        self.harmonic = IntegerSetting('HARM', 'harmonic', 1, 100, unit='', instrument=self)
        
        self.filterTc = NumericEnumSetting('OFLT', 'filter time constant', [(0,10E-6), (1, 30E-6), (2, 100E-6), (3, 300E-6), (4, 1E-3), (5, 3E-3), (6, 10E-3), (7, 30E-3), (8, 100E-3), (9,300E-3), (10, 1.), (11, 3.), (12, 10.), (13, 30.), (14, 100.), (15, 300.), (16, 1E3), (17, 3E3), (18, 10E3), (19, 30E3)], self, 's')
        self.filterSlope = NumericEnumSetting('OFSL', 'filter roll-off', [(0, 6), (1, 12), (2, 18), (3,24)], self, 'dB/oct.')
        self.sensitivity = NumericEnumSetting('SENS', 'sensitivity', [(0, 2E-9), (1, 5E-9), (2, 1E-8), (3, 2E-8), (4, 5E-8), (5, 1E-7), (6, 2E-7), (7, 5E-7), (8, 1E-6), (9, 2E-6), (10, 5E-6), (11,1E-5), (12,2E-5), (13, 5E-5), (14, 1E-4), (15, 2E-4), (16, 5E-4), (17, 1E-3), (18, 2E-3), (19, 5E-3), (20, 1E-2), (21, 2E-2), (22, 5E-2), (23,0.1), (24, 0.2), (25, 0.5), (26, 1.0)], self, unit='V')
        self.traceLoop = EnumSetting('SEND', 'buffer mode', [(0, 'single shot'), (1, 'loop')], self)
        self.traceRate = NumericEnumSetting('SRAT', 'sample data rate', [(0, 62.5E-3), (1, 125E-3), (2, 250E-3), (3, 500E-3), (4, 1.0), (5, 2.0), (6, 4.0), (7, 8.0), (8, 16.0), (9, 32.0), (10, 64.0), (11, 128.0), (12, 256.0), (13, 512.0)], self, 'Hz')
        
    
    @pyqtSlot()
    def readAll(self):
        self.inputSource.code
        self.inputCoupling.code
        self.inputGrounding.code
        self.inputFilters.code
        self.reserve.code
        self.syncDemodulator.enabled
        self.sineOut.value
        self.referenceFrequency.value
        self.referenceTrigger.code
        self.referenceSource.code
        self.harmonic.value
        self.filterTc.code
        self.filterSlope.code
        self.sensitivity.code
        for i in range(4):
            self.auxOut[i].value

    @pyqtSlot(int)
    def snapSignal(self, auxIn=None):
        '''Snap X,Y, and f and optionally one of the AUX inputs from the lock-in.
        Returns X,Y,f. Data are also cached in the LockIn instance and can be read as
        any combination of X,Y, R and Theta +  the AUX values.
        '''
        items = ['1','2','9'] #X,Y,f
        if auxIn is not None:
            items.append(str(auxIn+5))
        items = ','.join(items)
        result = self.queryString("SNAP ? %s" % items)
        d = result.split(',')
        self._x = float(d[0])
        self._y = float(d[1])
        self._f = float(d[2])
        self.readingAvailable.emit(self._x,self._y,self._f)
        if auxIn is not None:
            Vaux = float(d[3])
            self._auxIn[auxIn] = Vaux
            self.auxInRead.emit(auxIn, Vaux)
        return (self._x, self._y, self._f)
    
    @pyqtSlot(int)
    def snapSignalR(self, auxIn=None):
        '''Like snapSignal, but instead of X,Y this transfers R and theta.
        This was to test the idea that since R is always positive we may gain
        additional resolution by loosing the sign bit. In practice,
        this does not pan out. Deprecated.'''
        items = ['3', '4', '9'] # R, theta, f
        if auxIn is not None:
            items.append(str(auxIn+5))
        items = ','.join(items)
        result = self.queryString("SNAP ? %s" % items)
        d = result.split(',')
        r = float(d[0])
        theta = np.deg2rad(float(d[1]))
        self._x = r * np.cos(theta)
        self._y = r * np.sin(theta)
        self._f = float(d[2])
        self.readingAvailable.emit(self._x,self._y,self._f)
        if auxIn is not None:
            Vaux = float(d[3])
            self._auxIn[auxIn] = Vaux
            self.auxInRead.emit(auxIn, Vaux)
        return (self._x, self._y, self._f)
        
        
    def checkStatus(self):
        '''Query the staus register of the lock-in
        Returns: SR830LiaStatus
        Emits: inputOverloadRead(bool), filterOverloadRead(bool), outputOverloadRead(bool)
        '''
        lias = SR830LiaStatus(self.queryInteger('LIAS?'))
        self._lockinStatus = lias
        self.inputOverloadRead.emit(lias.inputOverload)
        self.filterOverloadRead.emit(lias.filterOverload)
        self.outputOverloadRead.emit(lias.outputOverload)
        return lias

    @property        
    def overload(self):
        '''Return if any overload (input, filter or output) has occured. Need to call checkStatus first.
        Deprecated.'''
        return self._lockinStatus.anyOverload
        
    @property
    def R(self):
        return np.sqrt(self._x**2+self._y**2)

    @property        
    def theta(self):
        return np.arctan2(self._y, self._x)
        
    @property
    def thetaDegree(self):
        return np.rad2deg(self.theta)
        
    @property
    def X(self):
        return self._x
        
    @property
    def Y(self):
        return self._y
    
    @property
    def f(self):
        return self._f
        
    @f.setter
    def f(self, newFrequency):
        self.referenceFrequency.value = newFrequency
                            
    def auxIn(self, channel):
        '''Read one of the auxillary inputs 
        channel (int): specify channel to be read (0-3)'''
        V =  self.queryFloat('OAUX? %i' % channel+1)
        self.auxInRead.emit(channel, V)
        return V
        
    def autoGain(self, block=True):
        '''Execute instrument internal auto-gain.
        block (bool): wait for operation to complete if True (default)
        '''
        self.commandString('AGAN')
        self.sensitivity._value = None
        if block:
            self.waitForOpc()
            
    def autoPhase(self, block=True):
        self.commandString('APHS')
        if block:
            self.waitForOpc()
            
    def autoReserve(self, block=True):
        self.commandString('ARSV')
        if block:
            self.waitForOpc()
                
    def waitForOpc(self):
        warnings.warn('waitForOpc not implemented/does not work!')
        pass
        #while self.queryInteger('*STB?')  & 2 == 0:
        #    pass
                        
    def verifyPresence(self):
        '''Check if instrument is actually present and responding.'''
        visaId = self.visaId()
        return 'SR830' in visaId
        
    def startTrace(self):
        '''Start recording trace data. Make sure to resetTrace first (as needed).'''
        self.commandString('STRT')
        
    def pauseTrace(self):
        '''Pause recording of trace data. Do this before reading when LOOP mode is on.'''
        self.commandString('PAUS')
        
    def resetTrace(self):
        '''Clear past trace data'''
        self.commandString('REST')
        
    def traceNumberOfPoints(self):
        '''Returns number of points in the trace buffer.'''
        return self.queryInteger('SPTS?')

    def readTraceAscii(self, display, start=0, count=None):
        '''Read trace buffer, transmitting data as ASCII
        *display*: 1 or 2
        *start*  : index of first point to transmit
        *count*  : number of points to transmit (if None, transmit all points)
        Returns the data as a numpy array
        '''
        if count is None:
            count = self.traceNumberOfPoints()
        buff = self.queryString('TRCA? %d,%d,%d' % (display,start,count))
        d = buff.split(',')[:-1]
        data = np.asarray([float(v) for v in d])
        return data
        
    def autoOffset(self, quantity):
        '''Automatically offset specified quantity
        quantity (str): 'X', 'Y', or 'Z'
        '''
        code = self.OffsetQuantityCodes[quantity]
        self.commandInteger('AOFF', code)

    def offsetExpand(self, quantity='X'):
        '''Returns the offset/expand settings for the specified quantity.
        quantity (str): 'X', 'Y', or 'R'
        returns: percentage, expandFactor (1, 10, or 100)'''
        code = self.OffsetQuantityCodes[quantity]
        r = self.queryString('OEXP? %d' % code)
        d = r.split(',')
        offsetPercent, expandCode = float(d[0]), int(d[1])
        expand = [k for k, v in self.OffsetExpandCodes.items() if v==expandCode]
        return offsetPercent, expand[0]
    
    def disableOffsetExpand(self, quantity = None):
        '''Disable offset/expand for specified quantity.
        quantity (str): 'X', 'Y', 'R', or None for all.'''
        if quantity is None:
            self.disableOffsetExpand('X')
            self.disableOffsetExpand('Y')
            self.disableOffsetExpand('R')
        else:
            self.setOffsetExpand(quantity, 0, 1)
        
    def setOffsetExpand(self, quantity, percent, expand):
        '''Set offset and expand parameters
        quantity (str) : 'X', 'Y', or 'R'
        percent (float): percentage of full scale sensitivity (from -105 to +105%)
        expand (int)   : expand factor 1, 10, or 100'''
        quantityCode = self.OffsetQuantityCodes[quantity]
        expandCode = self.OffsetExpandCodes[expand]
        self.commandString('OEXP %d,%.2f,%d' % (quantityCode, percent, expandCode))
    
    def setDisplay(self, channel, item, ratio = 0):
        '''Select the item displayed for specified channel.
        channel (int): Channel 1 or 2
        item : one of Channel1DisplayItem or Channel2DisplayItem
        ratio (int) : 0 for no ratio (default), 1 for ratio with first aux-in channel, 
        2 for ratio with second aux-in channel
        '''
        if channel == 1:
            itemCode = self.Channel1DisplayItems[item]
        elif channel == 2:
            itemCode = self.Channel2DisplayItems[item]
        else:
            raise IndexError
        self.commandString('DDEF %d,%d,%d' % (channel, itemCode, ratio))
        
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    #sr830 = SR830(None)
    #print(sr830.autoReserve)

    sr830 = SR830('GPIB0::12')
    if False:
        sr830.debug = True
        print("Present:", sr830.verifyPresence())
        print("Input source:", sr830.inputSource.string)
        print("Input coupling:", sr830.inputCoupling.string)
        print("Input shield ground:", sr830.inputGrounding.string)
        print("Input filters:", sr830.inputFilters.string)
        print("Harmonic:", sr830.harmonic.value)
        print("Synchronous demodulator enabled:", sr830.syncDemodulator.enabled)
        print("Reference source:", sr830.referenceSource.string)
        print("Reference trigger:", sr830.referenceTrigger.string)
        for i in range(4):
            print("AUX OUT",i,":", sr830.auxOut[i].value)
        
        #sr830.referenceFrequency.value = 333.8
        print("Reference frequency", sr830.referenceFrequency.value)
        #sr830.reserve.code = sr830.reserve.LOW_NOISE
        print("Reserve:", sr830.reserve.string)
        #sr830.sineOut.value = 3.945
        print("Sine out:", sr830.sineOut.value)
        print("Filter Tc:", sr830.filterTc.value)
        print("Filter roll-off:", sr830.filterSlope.value)
        print("Sensitivity:", sr830.sensitivity.string)
        for i in range(10):
            sr830.snapSignal() #auxIn=i%4)
            print("Signal: X=", sr830.X, "Y=",sr830.Y, "f=",sr830.f, "R=",sr830.R, "theta=",sr830.theta, "rad =",sr830.thetaDegree, "deg") 
            
        print(sr830.allSettingValues())
    
    import time
    
    
    sr830.disableOffsetExpand()
    # wait
    time.sleep(10)
    FS = sr830.sensitivity.value
    sr830.snapSignal()
    X,Y = sr830.X,sr830.Y
    
    offsetPercentX, offsetPercentY = int(1E2*X/FS), int(1E2*Y/FS)
    offsetPercentX = 0; offsetPercentY = 0
    expand = 1
    sr830.setOffsetExpand('X', offsetPercentX, expand)
    sr830.setOffsetExpand('Y', offsetPercentY, expand)
    time.sleep(15)
    X0 = 1E-2*offsetPercentX*FS
    Y0 = 1E-2*offsetPercentY*FS
    
    count = 500
    x = np.zeros((count,))
    y = np.zeros_like(x)
    t = np.zeros_like(x)

    for i in range(count):
        t[i] = time.time()
        sr830.snapSignal()
        deltaX, deltaY = sr830.X, sr830.Y
        x[i] = X0+deltaX
        y[i] = Y0+deltaY
        time.sleep(0.1)

    r = np.sqrt(x**2+y**2)
    dxs = np.sort(np.abs(np.diff(x)))
    print('Smallest DX>0:', dxs[dxs>0][:10])
    res = dxs[dxs>0][0]/(FS*1.1)
    print('Resolution:', res)
    print('Resolution:',-np.log(res)/np.log(2), 'bit')
    print('Mean X, Y"', np.mean(x), np.mean(y), 'V')
    print('Noise X:', np.std(x), 'V')
    print('Noise X:', -np.log(np.std(x)/FS)/np.log(2), 'bit')
    print('Noise Y:', np.std(y), 'V')
    print('Noise R:', np.std(r), 'V')
    import matplotlib.pyplot as mpl    
    mpl.plot(t, r, label='R')
    mpl.plot(t, x, label='snap X')
    mpl.plot(t, y, label='snap Y')
    mpl.legend(loc='best')
    mpl.show()
    
    if False:    
        sr830.traceRate.code = 7
        sr830.resetTrace()
        sr830.startTrace()
        count = 60
        x = np.zeros((count,))
        y = np.zeros_like(x)
        for i in range(count):
            sr830.snapSignal()
            x[i] = sr830.X
            y[i] = sr830.Y
            #print(sr830.X, sr830.Y)
            time.sleep(0.2)
        sr830.pauseTrace()
        X = sr830.readTraceAscii(1)
        Y = sr830.readTraceAscii(2)
    
        import matplotlib.pyplot as mpl    
        mpl.plot(x, label='snap X')
        mpl.plot(X, label='trace X')
        mpl.plot(y, label='snap Y')
        mpl.plot(Y, label='trace Y')
        mpl.legend(loc='best')
        mpl.show()

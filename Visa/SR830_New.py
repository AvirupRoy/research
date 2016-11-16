# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 10:15:32 2015

@author: wisp10
"""

from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
from Visa.VisaSetting import EnumSetting, IntegerSetting, NumericEnumSetting, FloatSetting, OnOffSetting, SettingCollection, InstrumentWithSettings, AngleSetting
from Visa.VisaInstrument import VisaInstrument
from numpy import arctan2, deg2rad, rad2deg, nan, sqrt

class SR830(VisaInstrument, InstrumentWithSettings, QObject):
    #adcReadingAvailable = pyqtSignal(float, float)
    #resistanceReadingAvailable = pyqtSignal(float, float)
    auxInRead = pyqtSignal(int, float)
    inputOverloadRead = pyqtSignal(bool)
    filterOverloadRead = pyqtSignal(bool)
    outputOverloadRead = pyqtSignal(bool)
    
    readingAvailable = pyqtSignal(float, float, float)
    '''Emitted whenever a new reading is taken with snapSignal, provides X, Y, and f'''
    
    def __init__(self, visaResource):
        VisaInstrument.__init__(self, visaResource)
        QObject.__init__(self)
        self._x = None
        self._y = None
        self._f = None
        self._auxIn = [nan, nan, nan, nan]
        self.model = 'SR830'
        self.serial = '000000'
        if visaResource is not None:
            self.clearGarbage()
            try:
                visaId = self.visaId()
                d = visaId.split(',')
                self.model = d[1]
                self.serial = d[2][3:]
                if not self.model in ['SR810', 'SR830', 'SR850']:
                    raise Exception('Unknown model %s' % self.model)
            except Exception,e:
                print "Unable to obtain VISA ID:",e
                pass
            
            
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
        items = ['1','2','9']
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
        
    def checkStatus(self):
        lias = self.queryInteger('LIAS?')        
        self._inputOverload = bool(lias & 1)
        self._filterOverload = bool(lias & 2)
        self._outputOverload = bool(lias & 4)
        self.inputOverloadRead.emit(self._inputOverload)
        self.filterOverloadRead.emit(self._filterOverload)
        self.outputOverloadRead.emit(self._outputOverload)

    @property        
    def overload(self):
        return self._inputOverload or self._outputOverload
        
    @property
    def R(self):
        return sqrt(self._x**2+self._y**2)

    @property        
    def theta(self):
        return arctan2(self._y, self._x)
        
    @property
    def thetaDegree(self):
        return rad2deg(self.theta)
        
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
        '''Read auxillary inputs 0-3'''
        V =  self.queryFloat('OAUX? %i' % channel+1)
        self.auxInRead.emit(channel, V)
        return V
        
    def autoGain(self, block=True):
        self.commmandString('AGAN')
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
        pass
                        
    def verifyPresence(self):
        visaId = self.visaId()
        return 'SR830' in visaId
        
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    sr830 = SR830(None)
    #print sr830.autoReserve

    sr830 = SR830('GPIB0::12')
    sr830.debug = True
    print "Present:", sr830.verifyPresence()
    print "Input source:", sr830.inputSource.string
    print "Input coupling:", sr830.inputCoupling.string
    print "Input shield ground:", sr830.inputGrounding.string
    print "Input filters:", sr830.inputFilters.string
    print "Harmonic:", sr830.harmonic.value
    print "Synchronous demodulator enabled:", sr830.syncDemodulator.enabled
    print "Reference source:", sr830.referenceSource.string
    print "Reference trigger:", sr830.referenceTrigger.string
    for i in range(4):
        print "AUX OUT",i,":", sr830.auxOut[i].value
    
    #sr830.referenceFrequency.value = 333.8
    print "Reference frequency", sr830.referenceFrequency.value
    #sr830.reserve.code = sr830.reserve.LOW_NOISE
    print "Reserve:", sr830.reserve.string
    #sr830.sineOut.value = 3.945
    print "Sine out:", sr830.sineOut.value
    print "Filter Tc:", sr830.filterTc.value
    print "Filter roll-off:", sr830.filterSlope.value
    print "Sensitivity:", sr830.sensitivity.string
    for i in range(10):
        sr830.snapSignal() #auxIn=i%4)
        print "Signal: X=", sr830.X, "Y=",sr830.Y, "f=",sr830.f, "R=",sr830.R, "theta=",sr830.theta, "rad =",sr830.thetaDegree, "deg" 
        
    print sr830.allSettingValues()
    
    
    

# -*- coding: utf-8 -*-
"""
Created on Thu Dec 03 11:56:00 2015

@author: wisp10
"""

from PyQt4.QtCore import QObject, pyqtSignal
from Visa.VisaSetting import EnumSetting, IntegerSetting, NumericEnumSetting, FloatSetting, OnOffSetting, SettingCollection, InstrumentWithSettings
from Visa.VisaInstrument import VisaInstrument

class Avs47(VisaInstrument, InstrumentWithSettings, QObject):
    adcReadingAvailable = pyqtSignal(float, float)
    resistanceReadingAvailable = pyqtSignal(float, float)
    
    def __init__(self, visaResource):
        VisaInstrument.__init__(self, visaResource)
        self.commandString('HDR 0') # Turn response headers off
        QObject.__init__(self)
        self.remote = OnOffSetting('REM', 'remote', self)
        self.muxChannel = IntegerSetting('MUX', 'mulitplexer channel', 0, 7, '', self)
        self.excitation = NumericEnumSetting('EXC', 'excitation', [(0, 0), (1, 3E-6), (2, 10E-6), (3, 30E-6), (4, 100E-6), (5, 300E-6), (6, 1E-3), (7, 3E-3)], self, 'V')
        self.range = NumericEnumSetting('RAN', 'range', [(0, float('nan')), (1, 2E0), (2, 2E1), (3, 2E2), (4, 2E3), (5, 2E4), (6, 2E5), (7, 2E6)], self, 'Ohm')
        self.input = EnumSetting('INP', 'input', [(0, 'grounded'), (1, 'measure'), (2, 'calibrate')], self)
        self.autoRange = OnOffSetting('ARN', 'auto-range', self)
        self.reference = IntegerSetting('REF', 'reference', 0, 20000, '', self)
        
    def sample(self):
        '''Takes a reading, but doesn't actually transfer the data'''
        self.commandString('ADC')
        
    def adcReading(self):
        adc = self.queryFloat('ADC?')
        return adc
        
    def resistanceReading(self):
        r = self.queryFloat('RES?')
        return r
        
    def verifyPresence(self):
        visaId = self.visaId()
        return 'AVS47' in visaId
       
        

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    avs = Avs47('GPIB0::20')
    print "Found:", avs.verifyPresence()
    print "Remote:", avs.remote.enabled
    print "Auto range:", avs.autoRange.enabled
    avs.remote.enabled = True
    print "Mux channel:", avs.muxChannel.value
    print "Excitation:", avs.excitation.code, avs.excitation.string
    print "Input:", avs.input.code, avs.input.string
    avs.sample()
#    avs.debug = True
    print "Resistance:", avs.adcReading()
    print "Range:", avs.range.code, avs.range.string, avs.range.value
    avs.remote.enabled = False
   
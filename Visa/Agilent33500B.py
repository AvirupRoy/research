# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 13:25:15 2017

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
#from Visa.VisaSetting import EnumSetting, IntegerSetting, NumericEnumSetting, FloatSetting, OnOffSetting, SettingCollection, InstrumentWithSettings, AngleSetting
from Visa.VisaInstrument import VisaInstrument
#from numpy import arctan2, deg2rad, rad2deg, nan, sqrt
#import warnings

class Agilent33500B(VisaInstrument, QObject):
    amplitudeChanged = pyqtSignal(float)        
    frequencyChanged = pyqtSignal(float)
    offsetChanged = pyqtSignal(float)
    waveformChanged = pyqtSignal(int)
    enabled = pyqtSignal(bool)
    def __init__(self, visaResource):
        QObject.__init__(self)
        VisaInstrument.__init__(self, visaResource)
        
    @pyqtSlot(float)        
    def setFrequency(self, frequency):
        self.commandFloat('FREQ', frequency)
        self._frequency = self.frequency()
        #self.frequencyChanged.emit(self._frequency)
        return self._frequency

    @pyqtSlot(float)        
    def setAmplitude(self, amplitude):
        self.commandFloat('VOLT', amplitude)
        self._amplitude = self.amplitude()
        self.amplitudeChanged.emit(self._amplitude)
        return self._amplitude
        
    def amplitude(self):
        return self.queryFloat('VOLT?')
    
    def frequency(self):
        return self.queryFloat('FREQ?')

    @pyqtSlot(bool)        
    def enable(self, enable=True):
        self.commandOnOff('OUTP', enable)
        self.enabled.emit(enable)

    @pyqtSlot()     
    def disable(self):
        self.enable(False)
        
    def isEnabled(self):
        return self.queryBool('OUTP?')

    def supportsOffset(self):
        return True
        
    @pyqtSlot(float)
    def setOffset(self, offset):
        self.commandFloat('VOLT:OFFS', offset)
        self._offset = self.offset()
        self.offsetChanged.emit(self._offset)
        return self._offset
    
    def offset(self):
        return self.queryFloat('VOLT:OFFS?')
        

if __name__ == "__main__":
    fg = Agilent33500B('USB0::2391::9991::MY57301033::0::INSTR')
    print fg.visaId()
#    #fg.setWaveform(fg.WaveformOptions.)
    
    print "Frequency:", fg.setFrequency(345125.)
    print "Amplitude:", fg.setAmplitude(0.1)
    print "Offset:", fg.setOffset(0.005)
#    fg.enable()
    fg.disable()
    print "Enabled:", fg.isEnabled()
##    fg.setWaveform(fg.WaveformOptions.TRI.Code)
#    print "Waveform:", fg.waveform()

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
#    class Waveform:
#        SINE = 'Sine'
#        SQUARE = 'Square'
#        TRIANGLE = 'Triangle'
#        RAMP = 'Ramp'
#        DC = 'DC'
#        
#        waveFormMap = {Waveform.SINE:'SIN', Waveform.SQUARE:'SQU', Waveform.TRIANGLE:'TRI', Waveform.RAMP:'RAMP'}
#        
#        def code(self, waveform):
            
        
    
        
    def __init__(self, visaResource):
        QObject.__init__(self)
        VisaInstrument.__init__(self, visaResource)
        
    def setWaveform(self, waveform):
        '''Allowable waveforms are: SIN, SQU, TRI, RAMP, PULS, PRBS, NOIS, ARB, DC'''
        self.commandString(':FUNC %s' % waveform)
        
    @pyqtSlot(float)        
    def setFrequency(self, frequency):
        self.commandFloat('FREQ', frequency)
        self._frequency = self.frequency()
        #self.frequencyChanged.emit(self._frequency)
        return self._frequency
        
    @pyqtSlot(float)
    def setPulseWidth(self, pw):
        self.commandFloat(':FUNC:PULS:WIDT', pw)
        self._pulseWidth = self.pulseWidth()
        return self._pulseWidth
        
    def pulseWidth(self):
        return self.queryFloat(':FUNC:PULS:WIDT?')
        
    @pyqtSlot(float)
    def setPulsePeriod(self, period):
        self.commandFloat(':FUNC:PULS:PER', period)
        self._pulsePeriod = self.pulsePeriod()
        return self._pulsePeriod

    def pulsePeriod(self):
        return self.queryFloat(':FUNC:PULS:PER?')
        
    @pyqtSlot(float)
    def setHighLevel(self, high):
        self.commandFloat(':VOLT:HIGH', high)
        self._highLevel = self.highLevel()
        return self._highLevel

    def highLevel(self):
        return self.queryFloat(':VOLT:HIGH?')
        
    @pyqtSlot(float)
    def setLowLevel(self, low):
        self.commandFloat(':VOLT:LOW', low)
        self._lowLevel = self.lowLevel()
        return self._lowLevel

    def lowLevel(self):
        return self.queryFloat(':VOLT:LOW?')

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
        
    def burstCount(self):
        return int(self.queryFloat('BURS:NCYC?'))
        
    def setBurstCount(self, n):
        self.commandInteger('BURS:NCYC', n)
        
    def setBurstPeriod(self, seconds):
        self.commandFloat('BURS:INT:PER', seconds)
        
    def burstPeriod(self):
        return self.queryFloat('BURS:INT:PER?')
        
    def setBurstMode(self, gated = False):
        if gated:
            self.commandString('BURS:MODE GAT')
        else:
            self.commandString('BURS:MODE TRIG')
            
    def burstPhase(self):
        return self.queryFloat('BURS:PHAS?')
        
    def setBurstPhase(self, degree):
        self.commandFloat('BURS:PHAS', degree)
        
    def enableBurst(self, enable=True):
        self.commandBool('BURS:STAT', enable)
        
    def displayMessage(self, message=''):
        self.commandString('DISP:TEXT "%s"' % message)
        
    def setTriggerSource(self, source):
        self.commandString('TRIG:SOUR %s' % source)
        
    class TriggerSource:
        Immediate = 'IMM'
        External = 'EXT'
        Timer = 'TIM'
        Bus = 'BUS'
        
    def setTriggerDelay(self, seconds):
        self.commandFloat('TRIG:DEL', seconds)
        
    def triggerDelay(self):
        return self.queryFloat('TRIG:DEL?')
        
    def setTriggerSlope(self, positive=True):
        slope = 'POS' if positive else 'NEG'
        self.commandString('TRIG:SLOP %s' % slope)

if __name__ == "__main__":
    fg = Agilent33500B('USB0::2391::9991::MY57301033::0::INSTR')
    print fg.visaId()
    print('Low:',fg.lowLevel())
    print('High:',fg.highLevel())
    print('Pulse period:', fg.pulsePeriod())
    print('Pulse width:', fg.pulseWidth())
    #fg.displayMessage('Hello!')
    fg.setPulseWidth(5E-3)
    fg.setWaveform('PULS')
    fg.setHighLevel(9.0)
    fg.setLowLevel(1.0)
    fg.setPulsePeriod(0.030)
    
    fg.setBurstCount(100)
    fg.setBurstPeriod(10.)
    fg.setBurstMode(gated=False)
    fg.setBurstPhase(0)
    fg.enableBurst()
    fg.enable()
    fg.setTriggerSource(fg.TriggerSource.External)
    fg.setTriggerDelay(0.2)
    fg.setTriggerSlope(False)
    print('Burst count:', fg.burstCount())
    print('Burst period:', fg.burstPeriod())
    print('Burst phase:', fg.burstPhase())
    
    
#    #fg.setWaveform(fg.WaveformOptions.)
    #fg.setWaveform('SIN')
#    print "Offset:", fg.setOffset(-0.2)
#    print "Frequency:", fg.setFrequency(323864.)
#    print "Amplitude:", fg.setAmplitude(50E-3)
#    print fg.amplitude()
#    print fg.frequency()
#    
#    #print "Amplitude:", fg.setAmplitude(0.1)
#    #print "Offset:", fg.setOffset(0.005)
##    fg.enable()
#    #fg.disable()
#    fg.enable()
#    print "Enabled:", fg.isEnabled()
##    fg.setWaveform(fg.WaveformOptions.TRI.Code)
#    print "Waveform:", fg.waveform()

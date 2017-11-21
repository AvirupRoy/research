# -*- coding: utf-8 -*-
"""
Created on Mon Jul 02 10:09:32 2012

@author: Randy Lafler and Felix Jaeckel
"""

from PyQt4.QtCore import QObject
#from Setting import Setting,NumericSettingAscending
from VisaInstrument import VisaInstrument

class Agilent34401A(VisaInstrument,QObject):
    def __init__(self, visaResourceName, parent=None):
        VisaInstrument.__init__(self, visaResourceName)
        QObject.__init__(self, parent)
    def voltageDc(self):
        result = self.queryFloat("MEAS:VOLT:DC?")
        return result
    def voltageDcRatio(self):
        result = self.queryFloat("MEAS:VOLT:DC:RAT?")
        return result
    def voltageAc(self):
        return self.queryFloat("MEAS:VOLT:AC?")
    def currentDc(self):
        return self.queryFloat("MEAS:CURR:DC?")
    def currentAc(self):
        return self.queryFloat("MEAS:CURR:AC?")
    def resistance(self):
        return self.queryFloat("MEAS:RES?")
    def resistance4Wire(self):
        return self.queryFloat("MEAS:FRES?")
    def frequency(self):
        return self.queryFloat("MEAS:FREQ?")
    def period(self):
        return self.queryFloat("MEAS:PER?")
    def continuity(self):
        return self.queryFloat("MEAS:CONT?")
    def diodeVoltage(self):
        return self.queryFloat("MEAS:DIODe?")
    def setBandwidth(self, bandwidth):
        self.commandString("DET:BAND %s" % bandwidth)
    def setInputImpedanceAuto(self, condition):
        self.commandString("INP:IMP:AUTO %s" % condition)
    def setAutoZero(self, condition):
        self.commandString("ZERO:AUTO %s" % condition)
    def setFunctionVoltageDc(self):
        self.commandString('SENS:FUNC "VOLT:DC"')
    def setFunctionVoltageAc(self):
        self.commandString('SENS:FUNC "VOLT:AC"')
    def setFunctionCurrentDc(self):
        self.commandString('SENS:FUNC "CURR:DC"')
    def reading(self):
        return self.queryFloat('READ?')

if __name__ == "__main__":
    dmm = Agilent34401A("GPIB0::22")
#    dmm.commandString('SENS:VOLT:DC:NPLC 10')
#    print "NPLC:", dmm.queryFloat('SENS:VOLT:DC:NPLC?')
    dmm.setFunctionVoltageDc()
    for i in range(1000):
#        #print 'DC=%.5g V' % dmm.voltageDc()
        print 'DC=%.5g V' % dmm.reading()

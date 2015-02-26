# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 11:08:31 2012

@author: jaeckel
"""

from VisaInstrument import VisaInstrument
from PyQt4 import QtCore

class Keithley6430(VisaInstrument, QtCore.QObject):
    #ldCurrentMeasured = QtCore.pyqtSignal(float)
    class MODE:
        CURRENT = 1
        VOLTAGE = 2

    def __init__(self, visaResourceName):
        super(Keithley6430, self).__init__(visaResourceName)

    def setComplianceCurrent(self, I):
        self.commandFloat(':SENS:CURR:PROT', I)

    def setComplianceVoltage(self, V):
        self.commandFloat(':SENS:VOLT:PROT', V)

    def setSourceFunction(self, function):
        if function == self.MODE.CURRENT:
            self.commandString(':SOUR:FUNC CURR')
        elif function == self.MODE.VOLTAGE:
            self.commandString(':SOUR:FUNC VOLT')
        else:
            raise "Unknown function"

    def sourceFunction(self):
        r = self.queryString(':SOUR:FUNC?')
        if r == 'CURRENT':
            return self.MODE.CURRENT
        elif r == 'VOLTAGE':
            return self.MODE.VOLTAGE

    def setSourceCurrentRange(self, I=None):
        if I is None:
            self.commandString(':SOUR:CURR:RANG:AUTO ON')
        else:
            self.commandFloat(':SOUR:CURR:RANG', I)

    def setSourceCurrent(self, I):
        self.commandFloat(':SOUR:CURR:LEV', I)

    def sourceCurrent(self):
        return self.queryFloat(':SOUR:CURR:LEV?')

    def setSourceVoltageRange(self, V=None):
        if V is None:
            self.commandString(':SOUR:VOLT:RANG:AUTO ON')
        else:
            self.commandFloat('SOUR:VOLT:RANG', V)

    def setSourceVoltage(self, V):
        self.commandFloat(':SOUR:VOLT:LEV', V)

    def sourceVoltage(self):
        return self.queryFloat(':SOUR:VOLT:LEV?')

    def setSenseFunction(self, function):
        if function == self.MODE.CURRENT:
            self.commandString(':SENS:FUNC CURR')
        elif function == self.MODE.VOLTAGE:
            self.commandString(':SENS:FUNC VOLT')
        else:
            raise "Unknown function"

    def senseFunction(self):
        r = self.queryString(':SENS:FUNC?')
        if r == 'CURRENT':
            return self.MODE.CURRENT
        elif r == 'VOLTAGE':
            return self.MODE.VOLTAGE

    def setSenseCurrentRange(self, I=None):
        if I is None:
            self.commandString(':SENS:CURR:RANG:AUTO ON')
        else:
            self.commandFloat(':SENS:CURR:RANG', I)

    def setSenseVoltageRange(self, I=None):
        if I is None:
            self.commandString(':SENS:CURR:RANG:AUTO ON')
        else:
            self.commandFloat(':SENS:CURR:RANG', I)

    def obtainReading(self):
        return self.queryFloat(':READ?')

    def enableOutput(self, enable=True):
        self.commandBool(':OUTP', enable)

    def disableOutput(self):
        self.enableOutput(False)


if __name__ == "__main__":
    #import visa
    #instrumentList = visa.get_instruments_list()
    #print instrumentList

    address = 'GPIB0::01' # Your serial number may be different
    sourceMeter = Keithley6430(address)
    print "Instrument ID:", ldDriver.visaId()

# -*- coding: utf-8 -*-
"""
Created on Wed May 20 17:47:45 2015

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from VisaInstrument import VisaInstrument
from PyQt4 import QtCore

class Agilent6641A(VisaInstrument, QtCore.QObject):
    '''Control of Agilent 6641A power supply'''
    def __init__(self, visaResourceName):
        super(Agilent6641A, self).__init__(visaResourceName)

    def voltageSetpoint(self):
        return self.queryFloat('VOLT?')

    def setVoltage(self, V):
        self.commandFloat('VOLT', V)

    def setCurrent(self, I):
        self.commandFloat('CURR', I)

    def currentSetpoint(self):
        return self.queryFloat('CURR?')

    def measureCurrent(self):
        return self.queryFloat('MEAS:CURR?')

    def measureVoltage(self):
        return self.queryFloat('MEAS:VOLT?')

    def outputEnabled(self):
        return self.queryBool(':OUTP?')

    def enableOutput(self, enable=True):
        self.commandBool(':OUTP', enable)

    def disableOutput(self):
        self.enableOutput(False)


if __name__ == "__main__":
    #import visa
    #instrumentList = visa.get_instruments_list()
    #print instrumentList
    address = 'GPIB0::5' # Your serial number may be different
    ps = Agilent6641A(address)
    print "Instrument ID:", ps.visaId()
 #   ps.setVoltage(0.0)
#    ps.enableOutput(False)
    print "Output enabled:", ps.outputEnabled()
    import time
    for i in range(6000):
        print ps.visaId()
#        print "Voltage setpoint:", ps.voltageSetpoint()
#        print "Current setpoint:", ps.currentSetpoint()
#        print "Measured voltage:", ps.measureVoltage()
#        print "Measured current:", ps.measureCurrent()
        time.sleep(0.05)

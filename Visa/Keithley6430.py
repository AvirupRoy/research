# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 11:08:31 2012

@author: jaeckel
"""

from VisaInstrument import VisaInstrument, CommunicationsError
from PyQt4 import QtCore
import logging

logger = logging.getLogger(__name__)

class Keithley6430(VisaInstrument, QtCore.QObject):
    #ldCurrentMeasured = QtCore.pyqtSignal(float)
    class MODE:
        CURRENT = 1
        VOLTAGE = 2
        RESISTANCE = 3

    class Reading:
        voltage = None
        current = None
        status = None
        resistance = None
        time = None


    class ELEMENTS:
        VOLTAGE = 'VOLT'
        CURRENT = 'CURR'
        RESISTANCE = 'RES'
        TIME = 'TIME'
        STATUS = 'STAT'

    class Status:
        Flags = {0: 'OFLO', 1:'FILTER', 3:'COMPL', 4:'OVP', 6:'NULL',11:'MEAS-V', 12:'MEAS-I', 13:'MEAS-OHM', 14:'SRC-V', 15:'SRC-I', 16:'RANGE'}
        def __init__(self, status):
            self._status = status


        @property
        def overRange(self):
            return self._status & 1

        @property
        def filter(self):
            return self._status & 2

        @property
        def null(self):
            return self._status & 64

        @property
        def measureVoltage(self):
            return self._status & (2**11)

        @property
        def measureCurrent(self):
            return self._status & (2**12)

        @property
        def measureOhm(self):
            return self._status & (2**13)

        @property
        def sourceVoltage(self):
            return self._status & (2**14)

        @property
        def sourceCurrent(self):
            return self._status & (2**15)

        @property
        def realCompliance(self):
            return self._status & 8

        @property
        def overVoltageProtection(self):
            return self._status & 16

        @property
        def rangeCompliance(self):
            return self._status & (2**16)

        def __str__(self):
            s = []
            for flag in self.Flags:
                if self._status & (2**flag):
                    s.append(self.Flags[flag])
            return ','.join(s)

    def __init__(self, visaResourceName):
        super(Keithley6430, self).__init__(visaResourceName)
        self._dataFormat = None
        self.specifyDataFormat([Keithley6430.ELEMENTS.VOLTAGE, Keithley6430.ELEMENTS.CURRENT, Keithley6430.ELEMENTS.STATUS])

    def specifyDataFormat(self, elements):
        s = ','.join(elements)
        self.commandString(':FORM:ELEM %s' % s)
        self._dataFormat = elements

    def dataFormat(self):
        s = self.queryString(':FORM:ELEM?')
        elements = s.split(',')
        format = []
        for element in elements:
            if not element in 'VOLT CURR RES TIME STAT':
                print "Unknown element:", element
            else:
                format.append(element)
        self._dataFormat = format
        return self._dataFormat

    def setComplianceCurrent(self, I):
        self.commandFloat(':SENS:CURR:PROT', I)

    def complianceCurrent(self):
        return self.queryFloat(':SENS:CURR:PROT?')

    def setComplianceVoltage(self, V):
        self.commandFloat(':SENS:VOLT:PROT', V)

    def complianceVoltage(self):
        return self.queryFloat(':SENS:VOLT:PROT?')


    def setSourceFunction(self, function):
        if function == self.MODE.CURRENT:
            self.commandString(':SOUR:FUNC CURR')
        elif function == self.MODE.VOLTAGE:
            self.commandString(':SOUR:FUNC VOLT')
        else:
            raise "Unknown function"

    def sourceFunction(self):
        r = self.queryString(':SOUR:FUNC?')
        if r == 'CURR':
            return self.MODE.CURRENT
        elif r == 'VOLT':
            return self.MODE.VOLTAGE
        else:
            raise Exception('Unknown source function:%s' % r)

    def setSourceCurrentRange(self, I=None):
        if I is None:
            self.commandString(':SOUR:CURR:RANG:AUTO ON')
        else:
            self.commandFloat(':SOUR:CURR:RANG', I)

    def setSourceCurrent(self, I):
        #self.commandString(':SOUR:CURR:LEV 0.00010038')
        self.commandFloat(':SOUR:CURR:LEV', I)

    def sourceCurrent(self):
        return self.queryFloat(':SOUR:CURR:LEV?')

    def setSourceVoltageRange(self, V=None):
        if V is None:
            self.commandString(':SOUR:VOLT:RANG:AUTO ON')
        else:
            self.commandFloat('SOUR:VOLT:RANG', V)

    def sourceVoltageRange(self):
        return self.queryFloat('SOUR:VOLT:RANG?')

    def setSourceVoltage(self, V):
        self.commandFloat(':SOUR:VOLT:LEV', V)

    def sourceVoltage(self):
        '''The Keithley likes to respond with garbage every once in a while. Try to recover automatically.'''
        try:
            v = self.queryFloat(':SOUR:VOLT:LEV?')
        except CommunicationsError:
            logger.warn('Corrupted response for source voltage query', exc_info = True)
            try:
                while True:
                    dummy = self.queryString('')
                    logger.warn("More garbage comming out of Keithley:%s", dummy)
                    if len(dummy) < 1:
                        break
            except:
                logger.warn("Executed read command to clear out garbage, no response. That's OK.", exc_info=True)
            logger.warn("Now trying IDN query...")
            r = self.visaId()
            if 'MODEL 6430' in r:
                logger.info('Communication re-established!')
            else:
                logger.warning("Response was: %s", r)
            v = self.queryFloat(':SOUR:VOLT:LEV?')
            logger.info("Seems to have worked itself out...")
        return v

    def setSenseFunction(self, function):
        if function == self.MODE.CURRENT:
            self.commandString(':SENS:FUNC "CURR:DC"')
        elif function == self.MODE.VOLTAGE:
            self.commandString(':SENS:FUNC "VOLT:DC"')
        elif function == self.MODE.RESISTANCE:
            self.commandString(':SENS:FUNC "RES"')
        else:
            raise "Unknown function"

    def senseFunction(self):
        r = self.queryString(':SENS:FUNC?')
        print "Sense function:", r
        if 'RES' in r:
            return self.MODE.RESISTANCE
        elif 'CURR:DC' in r:
            return self.MODE.CURRENT
        elif 'VOLT:DC' in r:
            return self.MODE.VOLTAGE
        else:
            raise Exception('Unknown sense function:%s' % r)

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

    def decodeReadingString(self, s):
        reading = self.Reading()
        if self._dataFormat is None:
            self.dataFormat()
        d = s.split(',')
        assert(len(d) == len(self._dataFormat))
        for i,value in enumerate(d):
            elem = self._dataFormat[i]
            if elem in ['VOLT','CURR','RES', 'TIME']:
                v = float(value)
                if v == 9.91e+37:
                    v = float('nan')
                if elem == 'VOLT':
                    reading.voltage = v
                elif elem == 'CURR':
                    reading.current = v
                elif elem == 'RES':
                    reading.resistance = v
                elif elem == 'TIME':
                    reading.time = v
            elif elem == 'STAT':
                status = self.Status(int(float(value)))
                reading.status = status
        return reading

    def measure(self):
        s = self.queryString(':MEAS?')
        return self.decodeReadingString(s)

    def obtainReading(self):
        s = self.queryString(':READ?')
        return self.decodeReadingString(s)

    def enableOutput(self, enable=True):
        self.commandBool(':OUTP', enable)

    def disableOutput(self):
        self.enableOutput(False)

    def outputEnabled(self):
        return self.queryBool(':OUTP?')



if __name__ == "__main__":
    #import visa
    #instrumentList = visa.get_instruments_list()
    #print instrumentList

    import time

    address = 'GPIB0::24' # Your serial number may be different
    sourceMeter = Keithley6430(address)
    print "Instrument ID:", sourceMeter.visaId()
    #sourceMeter.reset()

    if False:   # Source current, measure voltage
        sourceMeter.setSourceFunction(Keithley6430.MODE.CURRENT)
        print "Source function:", sourceMeter.sourceFunction()
        sourceMeter.setSenseFunction(Keithley6430.MODE.VOLTAGE)
        #print "Sense function:", sourceMeter.senseFunction()
        sourceMeter.setComplianceVoltage(5)
        sourceMeter.setSourceCurrentRange(1E-3)
        sourceMeter.setSourceCurrent(0.00010056)
        sourceMeter.enableOutput()
        print "Sourcing:",sourceMeter.sourceCurrent(),"A"
        for i in range(6):
            r = sourceMeter.obtainReading()
            print "V=", r.voltage, '(', r.status, ')'
            time.sleep(0.2)

    if True:    # Source voltage, measure current
        sourceMeter.setSourceFunction(Keithley6430.MODE.VOLTAGE)
        print "Source function:", sourceMeter.sourceFunction()
        sourceMeter.setComplianceCurrent(10E-3)
        sourceMeter.setSourceVoltageRange(2.)
        sourceMeter.setSourceVoltage(0.54321)
        sourceMeter.enableOutput()
        print "Sourcing:", sourceMeter.sourceVoltage(), "V"
        for i in range(6):
            r = sourceMeter.obtainReading()
            print "I=", r.current, '(', r.status, ')'
            time.sleep(0.25)

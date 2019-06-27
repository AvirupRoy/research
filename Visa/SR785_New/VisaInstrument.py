#  Copyright (C) 2012 Felix Jaeckel <fxjaeckel@gmail.com> and Randy Lafler <rlafler@unm.edu>

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
"""
@author: Felix Jaeckel
@contact: fxjaeckel@gmail.com
"""
try:
    import visa
except:
    import VisaSimulate as visa

from VisaExceptions import DeviceNotPresent


import logging

logger = logging.getLogger('VisaInstrument')
logger.warn('Using legacy VisaInstrument class')

import pyvisa.vpp43 as vpp43
#from vpp43_constants import *
#from visa_exceptions import *
#from pyvisa.vpp43_constants import VI_SUCCESS_MAX_CNT

from hexdump import hexdump

def readUnterminatedRawData(self, timeOut=0.1):
    """Read the unmodified string sent from the instrument to the computer.
    Do not pay attention to EOI or termination characters, but continue to
    read until time-out occurs.
    """
    #warnings.filterwarnings("ignore", "VI_SUCCESS_MAX_CNT")
    oldTimeOut = self.timeout
    self.timeout = timeOut
    count = 0
    chunk_size = 8192
    try:
        buffer = b""
        chunk = vpp43.read_ignore_timeout(self.vi, chunk_size)
        buffer += chunk
        while count < 2:
            if len(chunk) > 0:
                count = 0
            else:
                count += 1
            chunk = vpp43.read_ignore_timeout(self.vi, chunk_size)
            buffer += chunk
    finally:
        pass
#        _removefilter("ignore", "VI_SUCCESS_MAX_CNT")
    self.timeout = oldTimeOut
    return buffer


visa.GpibInstrument.readUnterminatedRawData = readUnterminatedRawData # Monkey-patching the pyvisa.GpibInstrument class

class VisaInstrument(object):
    def __init__(self, resourceName):
        self.Instrument = visa.instrument(resourceName)
        #self.Instrument.readUnterminatedRawData = readUnterminatedRawData(self) # Monkey-patching the pyvisa.Instrument class
        #self.Instrument.term_chars = visa.LF
        self.Instrument.term_chars = b""
        self.clearGarbage()
        self.debug = False

    def clearGarbage(self):
        oldTimeOut = self.Instrument.timeout
        self.Instrument.timeout = 0.3
        try:
            a = self.read_raw()
            print "Garbage:", a
        except:
            print "No garbage"
        self.Instrument.timeout = oldTimeOut
        print "Timeout back to:", self.Instrument.timeout

    def checkPresence(self):
        '''Reimplement to check for insturment presence (e.g. using visaId() query).'''
        return NotImplemented

    def queryBinary(self, query):
        '''This should probably be eliminated. See binaryTrasnfer function.'''
        self.Instrument.write(query)
        return self.Instrument.read_raw()

    def queryString(self, query):
        if self.debug:
            print "Query:", query
        a = self.Instrument.ask(query)
        if self.debug:
            print "Answer:", a
        return a

    def queryInteger(self, query):
        '''Send command and convert response string to integer'''
        return int(self.queryString(query))

    def queryFloat(self, query):
        '''Send command and convert response string to floating point'''
        return float(self.queryString(query))

    def queryBool(self, query):
        '''Send command and convert response string to boolean'''
        return bool(self.queryInteger(query))

    def binaryTransfer(self,query):
        '''Send command and read binary data response into a string (ignoring term chars)'''
        
        if self.debug:
            print "Query:", query
        self.Instrument.write(query)
        print "Term chars:", len(self.Instrument.term_chars)
        for c in self.Instrument.term_chars:
            print '0x%x' % ord(c)
        a = self.Instrument.read_raw()
        if self.debug:
            print "Answer:", a
        return a
        
    def readUnterminatedRawData(self, timeOut=0.1):
        return self.Instrument.readUnterminatedRawData(timeOut)

    def commandString(self, command):
        self.Instrument.write(command)
        if self.debug:
            print "Sending command:", command

    def commandInteger(self, command, value):
        self.commandString("%s %d" % (command,value))

    def commandFloat(self, command, value):
        self.commandString("%s %.6g" % (command,value))

    def commandBool(self, command, value):
        self.commandInteger(command, int(value))

    def commandOnOff(self, command, on):
        if on:
            self.commandString('%s ON' % command)
        else:
            self.commandString('%s OFF'% command)

    def visaId(self):
        return self.queryString("*IDN?")

    def reset(self):
        self.commandString("*RST")

    def clearStatus(self):
        self.commandString("*CLS")

    def serialPoll(self):
        '''Queries the serial poll byte.'''
        return self.queryInteger('*STB?')

    def statusByte(self):
        '''Return instrument status byte. Can be specialized by subclasses to provide instrument specific decoding.'''
        return self.STB()

    def STB(self):
        '''Return the instrument status byte (via a low level operation instead of regular query)'''
        from pyvisa import vpp43
        return vpp43.read_stb(self.Instrument.vi)

    def setTimeout(self, seconds=3):
        self.timeout = seconds

    def setEventStatusEnable(self, value):
        '''Sets the value of the 8-bit standard event status enable register (ESE)'''
        self.commandInteger('*ESE', value)

    def setESE(self, value):
        self.setEventStatusEnable(value)

    def eventStatusEnable(self):
        '''Returns the value of the 8-bit standard event status enable register (ESE). Can be speciallized by subclasses to provide instrument specific decoding.'''
        return self.ESE()

    def ESE(self):
        '''Returns the value of the 8-bit standard event status enable register (ESE)'''
        return self.queryInteger('*ESE?')

    def eventStatus(self):
        '''Returns value of the standard event status register (ESR). Can be specialized by subclasses to provide instrument specific decoding.'''
        return self.ESR()

    def ESR(self):
        '''Returns value of the standard event status register (ESR)'''
        return self.queryInteger('*ESR?')

    def enableOperationComplete(self):
        '''Enable the operation complete flag. Make sure to call this right before the operation that you are interested in.'''
        self.commandString('*OPC')

if __name__ == '__main__':
    v = VisaInstrument("GPIB1::10")
    print v.Instrument
    print v.visaId()

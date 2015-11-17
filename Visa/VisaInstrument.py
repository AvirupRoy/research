# -*- coding: utf-8 -*-
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



"""
Created on Thu Jun 21 09:45:24 2012
@summary: Error class for VISA instruments
@author: Felix Jaeckel and Randy Lafler
@contact: fxjaeckel@gmail.com
"""

import visa

import logging
logger = logging.getLogger(__name__)
#logger.addHandler(logging.NullHandler())

def findVisaResources():
    try:
        visaResources = visa.get_instruments_list()
    except Exception, e:
        print e
        visaResources = []
    return visaResources


class Error(Exception):
    """Base class for exceptions in the VISA module."""
    pass

class ParameterOutOfRange(Error):
    """Exception raised for numerical parameters that are out-of-range.

    Attributes:
        device   -- Device that caused the error
        item     -- Parameter that was out-of-range
        minValue -- Minimum allowed value
        maxValue -- Maximum allowed value
        units    -- Units of minValue and maxValue
    """
    def __init__(self, device, item, minValue, maxValue, units=''):
        self.device = device
        self.item = item
        self.minValue = minValue
        self.maxValue = maxValue
        self.units = units
        self.message = "%s: Parameter %s out of accepted range from %0.5f to %0.5f %s" % (self.device, self.item, self.minValue, self.maxValue, self.units)

class SettingInvalid(Error):
    """Exception raised for an invalid discrete setting .

    Attributes:
        device   -- Device that caused the error
        setting  -- Parameter that was out-of-range
    """
    def __init__(self, device, item):
        self.device = device
        self.item = item
        self.message = "%s: Illegal value for setting %s" % (self.device, self.item)

class CommunicationsError(Error):
    def __init__(self, device, item):
        self.device = device
        self.item = item
        self.message = "%s: Communication error %s" % (self.device, self.item)

class DeviceNotPresent(Error):

    def __init__(self, device, id):
        self.device = device
        self.id = id
        self.message = "%s: Device could not be identified (ID=%s)." % (self.device, self.id)

class VisaInstrument(object):
    def __init__(self, resourceName):
        logger.debug('VisaInstrument %s initializing', resourceName )
        self.resourceName = resourceName
        self.Instrument = visa.instrument(str(resourceName))
        self.Instrument.term_chars = visa.LF

    def checkPresence(self):
        return NotImplemented

    def queryString(self, query):
        logger.debug('QUERY %s:%s', self.resourceName, query)
        r = self.Instrument.ask(query)
        logger.debug('RESPONSE %s:%s', self.resourceName, r)
        return r

    def queryInteger(self, query):
        return int(self.queryString(query))

    def queryFloat(self, query):
        s = self.queryString(query)
        try:
            v = float(s)
        except ValueError:
            raise CommunicationsError(self.resourceName, 'Unexcpeted response')
        return v

    def queryBool(self, query):
        return bool(self.queryInteger(query))

    def commandString(self, command):
        logger.debug('COMMAND%s:%s', self.resourceName, command)
        self.Instrument.write(command)

    def commandInteger(self, command, value):
        self.commandString("%s %d" % (command,value))

    def commandFloat(self, command, value):
        self.commandString("%s %e" % (command,value))

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

    def statusByte(self):
        return self.Instrument.stb

#    def clear(self):
#        self.commandString("*CLR")

    def clearStatus(self):
        self.commandString("*CLS")

    def serialPoll(self):
        '''Queries the serial poll byte.'''
        return self.queryInteger('*STB?')

    def setTimeout(self, seconds=3):
        self.timeout = seconds

if __name__ == '__main__':
    v = VisaInstrument("GPIB1::23")
    print v.Instrument
    print v.visaId()

    import time

    with open('testdata2.txt', 'w') as f:
        while(True):
            V = v.queryFloat(':READ?')
            t = time.time()
            t2 = time.clock()
            print t, t2, V
            f.write('%.14g\t%.14g\t%.6g\n' % (t,t2,V))

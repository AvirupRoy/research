# -*- coding: utf-8 -*-
"""
Created on Thu Dec 03 14:39:48 2015

@author: wisp10
"""

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
Created on Fri Jun 29 10:39:44 2012
@summary: Interface class for Agilent 33220A function generator
@author: Felix Jaeckel and Randy Lafler
@contact: fxjaeckel@gmail.com
"""
from PyQt4.QtCore import QObject

from Visa.VisaSetting import EnumSetting, IntegerSetting, FloatSetting, OnOffSetting, SettingCollection, InstrumentWithSettings
            
class SR785UnitFloatSetting(FloatSetting):
    '''A specialization of FloatSetting to deal with the circumstance that the SR785 allows to specify a scale in conjunction with a float setting.'''
    def _queryValue(self):
            r = self.instrument.queryString(self.queryTemplate)
            if ',' in r:
                d = r.split(',')
                units = int(d[1])
                mult = self.unitScale[units]
                value = float(d[0])*mult
            else:
                value = float(r)
            return value

class AmplitudeFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E-3, 1:1., 2:1}

class SineAmplitudeFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E-3, 1:1E-3, 2:1E-3, 3:1., 4:1.}

class FrequencyFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E3, 1:1., 2:1E-3, 3:1E-6}

class TimeFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E-3, 1:1., 2:1}

class SR785InputRangeFloatEnumSetting(EnumSetting):
    @property
    def code(self):
        if not self.caching or self._code is None:
            if self.instrument is None:
                raise Exception("Unable to execute query!")
            r = self.instrument.queryString(self.queryString)
            if ',' in r:
                d = r.split(',')
                units = int(d[1])
                rawValue = int(d[0])
                if units == 0:
                    value = rawValue
                else:
                    raise Exception("Unsupported unit...")
            else:
                value = int(r)
#            value = '%d dBVpk' %value
            gains = np.linspace(-50,34,43)
            self._code = np.where(value == gains)[0][0]
            print "Code:", self._code
        self.changed.emit(self._code, False)
        return self._code
        
    @code.setter
    def code(self, newCode):
        if newCode in self.codes:
            if self.instrument:
                gains = np.linspace(-50,34,43)
                self.instrument.commandString('%s %d' %(self.command, gains[newCode]))
            else:
                raise Exception("No instrument object->can't execute command...")
            self._code = newCode
            self.changed.emit(newCode, True)
        else:
            raise Exception("Unsupported code")    


import struct
import numpy as np

from VisaInstrument import VisaInstrument

class SR785(VisaInstrument, InstrumentWithSettings, QObject):
    def __init__(self, visaResource, instrument=None):
#        VisaInstrument.__init__(self, visaResource)
        QObject.__init__(self, instrument)

    def readAll(self):
        self.source.readAll()
        self.display.readAll()
        self.sweptSine.readAll()
        self.fft.readAll()
        
        self.inputAutoOffset.enabled  # These are top level member and not a "SettingsCollection", so we have to handle them manually
        for inp in self.inputs:
            inp.readAll()

    def startMeasurement(self):
        self.commandString('STRT')

    def pauseMeasurement(self):
        self.commandString('PAUS')
#        self.paused = True
    def continueMeasurement(self):
#        if not self.paused:
#            raise Exception()
        self.commandString('CONT')

    def manualTrigger(self): # Perhaps move to Trigger class
        '''Send a manual trigger to the instrument'''
        self.commandString('TMAN')

    def frequencyOfBin(self, display, binNumber):
        return self.queryFloat('DBIN? %d, %d' %(display, binNumber))

    @property
    def displayStatus(self):
        #r = self.queryString('DSPS? %d, %f, %s' % (125, 531.35, 'bala'))
        return self.queryInteger('DSPS?')

if __name__ == "__main__":

#    a = Test('BLA', 'BLUB', [(0, 'floating'), (1, 'grounded'), (2, 'spinning'), (3, 'crashing'), (4, 'exploding')])
#    a.code = 2
#    print a.code
#    print a.string

    #a = EnumSetting('BLA', 'BLUB', [(0, 'floating'), (1, 'grounded'), (2, 'spinning'), (3, 'crashing'), (4, 'exploding')])
#    print "A code:", a.code
#    print "A string:", a.string

    sr = SR785('GPIB0::10')
    sr.debug = True
    #sr.enableCaching()
    sr.disableCaching()
#    sr.inputs[0].autoRange.enabled = True
#    sr.inputs[0].coupling.code = sr.inputs[0].coupling.AC
#    sr.inputs[0].coupling.code = sr.inputs[0].coupling.ICP
#
#    sr.source.type.code = sr.source.type.SINE
#    sr.inputAutoOffset.disabled = False
#
#    print "Source:"
#    print "Type:", sr.source.type.code
#    #print type(sr.source.type.string)
#    #print "Type:", sr.source.type.string
##    print "
#
#
##    for i,input in enumerate(sr.inputs):
##        print "Input", i
##        print "Input coupling:", input.coupling.string
##        print "Input grounding:", input.grounding.code
##        print "Auto range:", input.autoRange.enabled
    sr.display.measurementGroup.code = sr.display.measurementGroup.SWEPT_SINE
    sr.display.selectMeasurement(2, 'spectrum')
#
#    sr.sweptSine.settleCycles.value = 2
#    print "settle cycles:", sr.sweptSine.settleCycles.value
#    sr.sweptSine.settleTime.value = 10E-3
#    print "settle time:", sr.sweptSine.settleTime.value
#    sr.sweptSine.integrationTime.value = 10E-3
#    sr.sweptSine.integrationCycles.value = 2
#
#    sr.sweptSine.numberOfPoints.value = 10
#    sr.sweptSine.sweepType.code = sr.sweptSine.sweepType.LINEAR
#    sr.sweptSine.startFrequency.value = 15.
#    print "swept sine start frequency:", sr.sweptSine.startFrequency.value
#    sr.sweptSine.stopFrequency.value = 20E3
#    sr.sweptSine.repeat.code = sr.sweptSine.repeat.SINGLE_SHOT
#
#    sr.startMeasurement()
#    sr.manualTrigger()
#
#    print "Display status:", sr.displayStatus
#    finishedA = False
#    finishedB = False
#    while True:
#        status = sr.displayStatus
#        if status & sr.display.SSA:
#            finishedA = True
#        if status & sr.display.SSB:
#            finishedB = True
#        if finishedA and finishedB:
#            break
#        else:
#            print "Still measuring:", finishedA, finishedB, status

    display0 = sr.display.retrieveData(0)
    display1 = sr.display.retrieveData(1)

    import matplotlib.pyplot as mpl
    mpl.subplot(2,1,1)
    mpl.plot(display0, '-')
    mpl.subplot(2,1,2)
    mpl.plot(display1, '-')
    mpl.show()

    #response = sr.queryString('ACTD 0; DUMP;')
    #print "We have data:", response

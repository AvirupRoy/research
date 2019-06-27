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
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
from VisaInstrument import VisaInstrument
from Enum import SettingEnum

class NumericParameter():
    def __init__(self, name, units, minimum, maximum, resolution):
        self._name = name
        self._units = units
        self._min = minimum
        self._max = maximum
        self._resolution = resolution
    def name(self):
        return self._name
        
    def units(self):
        return self._units
        
    def minimum(self):
        return self._min
        
    def maximum(self):
        return self._max
    
    def resolution(self):
        return self._resolution
        

class Agilent33220A(VisaInstrument,QObject):
    amplitudeChanged = pyqtSignal(float)        
    frequencyChanged = pyqtSignal(float)
    offsetChanged = pyqtSignal(float)
    waveformChanged = pyqtSignal(int)
    enabled = pyqtSignal(bool)

    ParameterAmplitude = NumericParameter('amplitude', 'V', 0.010, 10, 0.001)
    ParameterFrequency = NumericParameter('frequency', 'Hz', 500E-6, 200E3, 0.1)
    WaveformOptions = SettingEnum({0: ('SIN', 'Sine'),
                                   1: ('SQU', 'Square'),
                                   2: ('TRI', 'Triangle'),
                                   3: ('RAMP','Ramp'),
                                   4: ('PULS', 'Pulse'),
                                   5: ('NOIS', 'Noise'),
                                   6: ('DC', 'DC'),
                                   7: ('USER', 'User defined')})
    
    def __init__(self, visaResource, parent=None):
        VisaInstrument.__init__(self, visaResource)
        QObject.__init__(self, parent)

    @pyqtSlot(int)        
    def setWaveform(self, waveformCode):
        waveform = self.WaveformOptions.fromCode(waveformCode)
        if waveform == self.WaveformOptions.TRI:
            self.setRampSymmetry(50)
            string = 'RAMP'
        elif waveform == self.WaveformOptions.RAMP:
            self.setRampSymmetry(100)
            string = 'RAMP'
        else:
            string = waveform.Name
        self.commandString('FUNC %s' % string)
        self.waveformChanged.emit(waveform.Code)
        
    def waveform(self):
        w = self.queryString('FUNC?')
        if w=='RAMP':
            symmetry = self.rampSymmetry()
            if symmetry == 100:
                return self.WaveformOptions.RAMP
            elif symmetry == 50:
                return self.WaveformOptions.TRI
            else:
                return None
        else:
            return self.WaveformOptions.fromName(w)

    @pyqtSlot(float)        
    def setRampSymmetry(self, symmetry):
        self.commandFloat('FUNC:RAMP:SYMM', symmetry)
        self._rampSymmetry = self.rampSymmetry()
        return self._rampSymmetry
        
    def rampSymmetry(self):
        return self.queryFloat("FUNC:RAMP:SYMM?")

    @pyqtSlot(float)        
    def setAmplitude(self, amplitude):
        self.commandFloat('VOLT', amplitude)
        self._amplitude = self.amplitude()
        self.amplitudeChanged.emit(self._amplitude)
        return self._amplitude
        
    def amplitude(self):
        return self.queryFloat('VOLT?')
    
    @pyqtSlot(float)        
    def setFrequency(self, frequency):
        self.commandFloat('FREQ', frequency)
        self._frequency = self.frequency()
        self.frequencyChanged.emit(self._frequency)
        return self._frequency
    
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
    # fg = Agilent33220A('GPIB0::16')
    #fg = Agilent33220A('TCPIP0::64.106.63.197::5025::SOCKET')
    fg = Agilent33220A('USB0::2391::9991::MY57301033::0::INSTR')
    print fg.visaId()
    #fg.setWaveform(fg.WaveformOptions.)
    print "Frequency:", fg.setFrequency(180)
    print "Amplitude:", fg.setAmplitude(1.0)
    print "Offset:", fg.setOffset(0.5)
    fg.enable()
    print "Enabled:", fg.isEnabled()
#    fg.setWaveform(fg.WaveformOptions.TRI.Code)
    print "Waveform:", fg.waveform()
    fg.disable()
  

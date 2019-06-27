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
Created on Tue Jul 03 11:16:47 2012

@author: Felix Jaeckel
"""

import numpy as np
from VisaInstrument import VisaInstrument, CommunicationsError
from struct import unpack, calcsize
 
class AgilentDSOX2004A(VisaInstrument):
    AnalogInputChannels = (1, 2, 3, 4)
    TriggerSources = ('CHAN1', 'CHAN2', 'CHAN3', 'CHAN4', 'EXT', 'LINE', 'WGEN')

    def __init__(self, address, parent=None):
        VisaInstrument.__init__(self, address)
        self.commandString(':WAV:FORM BYTE')    
        self.commandString(':WAV:UNS 1')
        self.commandString(':WAV:BYT LSBF')
    
    def resetToDefault(self):
        self.commandString(":SYST:PRES")

#   Timebase
    def timeBaseScale(self):
        return self.queryFloat(":TIM:SCAL?")
    def setTimeBaseScale(self, scale):
        self.commandFloat(':TIM:SCAL', scale)
    def setTimeBaseRange(self, span):
        self.commandFloat(":TIM:RANG %f", span)
    def timeBaseRange(self):
        return self.queryFloat(":TIM:RANG?")

# Acquisiton setup        
    def enableAutoscale(self):
        self.commandString(":AUToscale")
        
# Channel configuration
    def setChannelCoupling(self, channel, coupling):
        self.commandString("CHAN%i:COUPling %s" % (channel, coupling))
        
    def channelCoupling(self, channel):
        return self.queryString(":CHAN%i:COUP?" % channel)

    def setChannelLabel(self,channel, label):
        self.commandString(":CHAN%i:LAB %s" % (channel, label))
        
    def channelLabel(self, channel):
        return self.queryString(":CHAN%i:LAB?" % channel)

    def setChannelRange(self, channel, inputRange):
        self.commandString(":CHAN%i:RANG %g V" % (channel, inputRange))
        
    def channelRange(self, channel):
        return self.queryFloat(":CHAN%i:RANG?" % channel)
        
    def channelScale(self, channel):
        return self.queryFloat(":CHAN%i:SCAL?" % channel)
        
    def enableBandwidthLimit(self, channel, enable=True):
        self.commandBool(':CHAN%i:BWL' % channel, enable)
    def disableBandwidthLimit(self, channel):
        self.enableBandwidthLimit(channel, False)
        
    def enableDisplay(self, channel, enable=True):
        self.commandBool(':CHAN%i:DISP' % channel, enable)
    def disableDisplay(self, channel):
        self.enableDisplay(channel, False)
        
    def digitizeChannel(self, source):
        self.commandString(":DIGitize %s" % source)

# Trigger related commands        
    def setTriggerLevel(self, level):
        self.commandFloat(":TRIG:LEV", level)
        
    def triggerLevel(self):
        return self.queryFloat(":TRIG:LEV?")
        
    def setTriggerSource(self, source):
        self.commandString(":TRIG:SOUR %s" % source)
        
    def triggerSource(self):
        return self.queryString(":TRIG:SOUR?")
    
    class waveform:
        dataType = None
        dataFormat = None
        numberOfPoints = None
        counts = None
        xinc = None
        x0 = None
        xref = None
        yinc = None
        y0 = None
        yref = None
        t = None
        y = None
        
    def waveformPreamble(self):
        data = self.queryString(':WAV:PRE?').split(',')
        wave=self.waveform()
        dataFormat = int(data[0])
        if dataFormat == 0:
            wave.dataFormat = 'BYTE'
        elif dataFormat == 1:
            wave.dataFormat = 'WORD'
        elif dataFormat == 4:
            wave.dataFormat = 'ASCII'
        else:
            raise CommunicationsError('AgilentDSOX2004', 'Unrecognized dataform specified in waveform preamble.')
        wave.dataType = int(data[1])
        wave.numberOfPoints = int(data[2])
        wave.counts = int(data[3])
        wave.xinc = float(data[4])
        wave.x0 = float(data[5])
        wave.xref = int(data[6])
        wave.yinc = float(data[7])
        wave.y0 = float(data[8])
        wave.yref = int(data[9])
        return wave
        
    def maximumNumberOfSamples(self):
        return 50000
        
    def acquireWaveform(self, channel):
        self.commandString(':WAV:SOUR CHAN%i' % channel)
        wave = self.waveformPreamble()
        s = self.queryString(':WAV:DATA?')
        if (s[0] != '#'):
            raise CommunicationsError('AgilentDSOX2004', 'Waveform data packet did not start with #-sign.')
        n = int(s[1])
        numberOfBytes = int(s[2:n+2])
        data = s[n+2:]
 
        if wave.dataFormat == 'BYTE':
            form = '%dB' % numberOfBytes
            if len(data) != calcsize(form):
                raise CommunicationsError('AgilentDSOX2004', 'Data size mismatch when retrieving waveform (expected %d bytes, received %d bytes)' % (calcsize(form), len(data)))
            d = unpack(form, data)
            wave.y = (np.array(d)-wave.yref)*wave.yinc+wave.y0
        elif wave.dataFormat == 'WORD':
            form = '<%dH' % (numberOfBytes/2)
            if len(data) != calcsize(form):
                raise CommunicationsError('AgilentDSOX2004', 'Data size mismatch when retrieving waveform (expected %d bytes, received %d bytes)' % (calcsize(form), len(data)))
            d = unpack(form, data)
            wave.y = (np.array(d)-wave.yref)*wave.yinc+wave.y0
        elif wave.dataFormat == 'ASCII':
            wave.y = np.array(data.split(','))

        peak = False
        if (peak):
            m = 2
        else:
            m = 1
        wave.t = (np.array(range(0, wave.numberOfPoints))-wave.xref)*m*wave.xinc+wave.x0
        return wave

    
if __name__ == "__main__":
    import visa
    instrumentList = visa.get_instruments_list()
    print instrumentList

    dso = AgilentDSOX2004A(address="USB0::0x0957::0x179A::MY52141087")
    channel = 1
    print "Channel:", channel
    print "Trigger source:", dso.triggerSource()
    print "Time base scale: %f s/div" % dso.timeBaseScale()
    print "Time base full range: %f s" % dso.timeBaseRange()
    print "Y scale: %f V/div" % dso.channelScale(channel)
    print "Y range: %f V" % dso.channelRange(channel)
    import time
    t = time.time()
    for i in [0,1]:
        wave = dso.acquireWaveform(channel)
    elapsed = time.time() - t
    print "Total elapsed time:", elapsed

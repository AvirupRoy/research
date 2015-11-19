# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 20:52:41 2015

@author: jaeckel
"""

import vxi11
import numpy as np
from struct import unpack#, calcsize

class TektronixTds3000(object):
    
    AnalogInputChannels = (1, 2, 3, 4)
    TriggerSources = ('CHAN1', 'CHAN2', 'CHAN3', 'CHAN4', 'EXT', 'LINE', 'WGEN')

    def __init__(self, address):
        self.instr = vxi11.Instrument(address)
        self.commandString("HEADER OFF")
        
    def maximumNumberOfSamples(self):
        return 10000

    def commandString(self, command):
        self.instr.write(command)

    def commandInteger(self, command, integer):
        self.commandString("%s %d" % (command, integer))

    def commandFloat(self, command, value):
        self.commandString("%s %f" % (command, value))

    def queryString(self, query):
        return self.instr.ask(query)

    def queryFloat(self, query):
        return float(self.queryString(query))

    def queryInteger(self, query):
        return int(self.queryString(query))

    def identify(self):
        return self.queryString("*IDN?")

#    def waveformPreamble(self):
#        import re
#        preamble = self.queryString("WFMPRe?")
#        items = preamble.split(';')
#        pattern = re.compile(r'''((?:[^,"]|"[^"]*")+)''')
#        print "Preamble:", preamble
#        for item in items:
#            print item
#            pair = pattern.split(item)
#            print pair

    def setTriggerSource(self, triggerChannel):
        pass

    def setTimeBaseRange(self, timeBase):
        pass

    def setChannelCoupling(self, channel, coupling):
        if coupling in ['AC','DC','GND']:
            self.commandString("CH%i:COUP %s" % (channel, coupling))
        else:
            raise "Unknown coupling"

    def channelCoupling(self, channel):
        return self.queryString(":CH%i:COUP?" % channel)

    def setChannelRange(self, channel, inputRange):
        self.setChannelScale(channel, 0.1*inputRange)

    def channelRange(self, channel):
        return 10.*self.channelScale(channel)

    def setChannelScale(self, channel, scale):
        self.commandFloat("CH%i:SCAL" % channel, scale)

    def channelScale(self, channel):
        return self.queryFloat("CH%i:SCAL?" % channel)

    def waveformOffsetY(self):
        return self.queryFloat("WFMPre:YOFf?")

    def waveformY0(self):
        return self.queryFloat("WFMPre:YZero?")

    def waveformScaleY(self):
        return self.queryFloat("WFMPre:YMUlt?")

    def waveformScaleX(self):
        return self.queryFloat("WFMPre:XINcr?")

    def waveformX0(self):
        return self.queryFloat("WFMPre:XZero?")

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

    def acquireWaveform(self, source = 'CH1', start=1, stop=10000, double = False):
        wave = self.waveform()
        if double:
            width = 2
        else:
            width = 1

        self.commandString("DATA:SOURCE %s" % source)
        self.commandInteger("DATA:WIDTH", width)
        self.commandString("DATA:ENCDG RPBinary")
        self.commandString("WFMPRE:PT_Fmt Y")
        self.commandInteger("DATA:START", start)
        self.commandInteger("DATA:STOP", stop)
        wave.numberOfPoints = self.queryInteger("WFMPre:NR_Pt?")
        #print "Number of points:", numberOfPoints
        wave.yref = self.waveformOffsetY()
        wave.y0   = self.waveformY0()
        wave.yinc = self.waveformScaleY()

        wave.x0   = self.waveformX0()
        wave.xinc = self.waveformScaleX()

        data = self.instr.ask_raw("CURVE?")
        start = len(data)-width*wave.numberOfPoints-1
        data = data[start:-1]
        print len(data)
        if width == 1:
            form = '%dB' % wave.numberOfPoints
        elif width == 2:
            form = '<%dH' % wave.numberOfPoints

        d = unpack(form, data)
        wave.y = (np.array(d)-wave.yref)*wave.yinc+wave.y0
        wave.t = np.array(range(0, wave.numberOfPoints))*wave.xinc+wave.x0

        return wave

    def setTimeBase(self, base):
        pass
        #"HORizontal:SCAle"

if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    scope = TektronixTds3000("wisptek1.physics.wisc.edu")
    print scope.identify()
    scope.setChannelScale(1, 0.1)
    print "Scale:",scope.channelScale(1)
    for i in range(0, 2):
        wave = scope.acquireWaveform(source='CH1')
        mpl.plot(wave.t,wave.y, label='%d' % i)
    mpl.show()


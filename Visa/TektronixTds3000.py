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
        #print len(data)
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


from scipy.optimize import curve_fit

def sineWave(t, A, f, phase, offset):
    y = A*np.sin(2*np.pi*f*t+phase) + offset
    return y
    
    
def testCode1():    
    import matplotlib.pyplot as mpl
    scope = TektronixTds3000("wisptek1.physics.wisc.edu")
    print scope.identify()
    #scope.setChannelScale(1, 0.1)
    #print "Scale:",scope.channelScale(1)
    for i in range(1, 3):
        wave = scope.acquireWaveform(source='CH%d' % i)
        i1 = np.where(np.diff(wave.y)[1:] > +1)[0][0]+1
        i2 = np.where(np.diff(wave.y)[1:] < -1)[0][0]+1
        
        A = 0.5*np.max(wave.y[i1:i2]) - np.min(wave.y[i1:i2])
        f = 1./(0.5*(wave.t[i2]-wave.t[i1]))
        phase = 0.5*np.pi
        offset = np.mean(wave.y[0:i1])
        guess = [A, f, phase, offset]
        t0 = wave.t[i1]
        fit, pcov = curve_fit(sineWave, wave.t[i1:i2]-t0, wave.y[i1:i2], guess)
        #print fit        
        mpl.plot(wave.t,wave.y, 'o', label='data ch. %d' % i)
        tFit = np.linspace(wave.t[i1], wave.t[i2])-t0
        mpl.plot(tFit+t0, sineWave(tFit, *fit), '-', label='fit ch. %d' % i)
        print "Ch %d:" % i
        print "Sine fit: A=%.5g V, f=%.4g Hz, phase=%.3g deg, offset=%.4g V" % (fit[0], fit[1], fit[2]*180/np.pi, fit[3])
        
    mpl.xlabel('t [s]')
    mpl.ylabel('Signal [V]')
    mpl.show()
    
    

if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    import h5py as hdf
    
    #info = 'AVS-47 Bridge output (Range 2000K, excite 300uV, reading 0.0688V)'
    #fileName = 'AVS47_R2000K_300uV_68k4.h5'
    
    fileName = 'MagnetStepTo2.5V_FromZero.h5'
    info = 'Stepping magnet control from zero output to ramp at -2.5V.'

    channelIds = ['MagnetVoltage(x50)', 'Current [1A/V]', 'FET drive input', 'FB command voltage']    
    
    address = "wisptek1.physics.wisc.edu"
    scope = TektronixTds3000(address)
    print scope.identify()
    #scope.setChannelScale(1, 0.1)
    #print "Scale:",scope.channelScale(1)
    i = 1
    color = 'rgbc'
    
    f = hdf.File(fileName, 'w')
    f.attrs['Scope ID'] = scope.identify()
    f.attrs['Address'] = address
    f.attrs['Info'] = info
    for i in [2]:
        print "Ch %d:" % i
        wave = scope.acquireWaveform(source='CH%d' % i)
        grp = f.create_group('Channel%d' % i)
        grp.attrs['Channel info'] = channelIds[i-1]
        grp.create_dataset('t', data=wave.t)
        grp.create_dataset('y', data=wave.y)
        mpl.plot(wave.t*1E6,wave.y, '%s-' % color[i-1], label='Ch. %d (%s)' % (i, channelIds[i-1]))
    f.close()
        
    mpl.xlabel(u't [$\mu$s]')
    mpl.ylabel('Signal [V]')
    mpl.legend(loc='best')
    mpl.show()


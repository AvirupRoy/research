# -*- coding: utf-8 -*-
"""
Created on Tue Jun 19 10:56:14 2012
Comment (FJ): This class needs some serious loving.

@author: Randy Lafler
"""

import PyQt4.QtCore as Qt
from PyQt4.QtCore import QThread
import numpy as np
from createdExceptions import GpibExceptionOutOfRange as GoutR
import string
from VisaInstrument import VisaInstrument

import time
class SR830(VisaInstrument):
    # constants
    INPUT_A = 0
    INPUT_AB = 1
    INPUT_I1M = 2
    INPUT_I100M = 3
    SENS_min = 0
    SENS_max = SENS_1V = 26
    RESERVE_min = 0
    RESERVE_max = RESERVE_LOW = 2
    SLOPE_min = 0
    SLOPE_6dB = 0
    SLOPE_12dB = 1
    SLOPE_18dB = 2
    SLOPE_max = SLOPE_24dB = 3
    TC_min = 0
    TC_max = TC_30ks = 19

    # another way to make a dictionary
    menuSensitivity = dict(SENS_min = 0,
    SENS_2nV		= 0,
    SENS_5nV		= 1,
    SENS_10nV	= 2,
    SENS_20nV	= 3,
    SENS_50nV	= 4,
    SENS_100nV	= 5,
    SENS_200nV	= 6,
    SENS_500nV	= 7,
    SENS_1uV		= 8,
    SENS_2uV		= 9,
    SENS_5uV		= 10,
    SENS_10uV	= 11,
    SENS_20uV	= 12,
    SENS_50uV	= 13,
    SENS_100uV	= 14,
    SENS_200uV	= 15,
    SENS_500uV	= 16,
    SENS_1mV		= 17,
    SENS_2mV		= 18,
    SENS_5mV		= 19,
    SENS_10mV	= 20,
    SENS_20mV	= 21,
    SENS_50mV	= 22,
    SENS_100mV	= 23,
    SENS_200mV	= 24,
    SENS_500mV	= 25,
    SENS_1V		= 26,
    SENS_max 	= SENS_1V)
    menuTC = {0: '10 us', 1: '30 us', 2: '100 us', 3: '300 us', 4: '1 ms', 5: '3 ms', 6: '10 ms', 7: '30 ms', 8: '100 ms',
              9: '300 ms', 10: ' s', 11: '3 s', 12: '10 s', 13: '30 s', 14: '100 s', 15: '300 s',
              16: '1 ks', 17: '3 ks', 18: '10 ks', 19: '30 ks'}
    menuReserve = {0: 'High Reserve', 1: 'Normal Reserve', 2: 'Low Reserve'}
    menuInputSource = {INPUT_A: 'A', INPUT_AB: 'A-B', INPUT_I1M: "I (1M)", INPUT_I100M: "I (100)"}
    menuFilterSlope = {SLOPE_6dB: "6 dB", SLOPE_12dB: "12 dB", SLOPE_18dB: "18 dB", SLOPE_24dB: "24 dB"}

    INPUT_OVERLOAD_LIAS = 1
    FILTER_OVERLOAD_LIAS = 2
    OUTPUT_OVERLOAD_LIAS = 4

#    autoReserve = Qt.pyqtSignal(float)
#    autoGain = Qt.pyqtSignal(float)
#    autoPhase = Qt.pyqtSignal(float)
#    harmonic = Qt.pyqtSignal(float)
#    phaseDegree = Qt.pyqtSignal(float)
#    getTC = Qt.pyqtSignal(float)
#    getSensitivity = Qt.pyqtSignal(float)
#    setReserve = Qt.pyqtSignal(float)
#    setInputSource = Qt.pyqtSignal(float)
#    setInputFilters = Qt.pyqtSignal(float)
#    setInputCoupling = Qt.pyqtSignal(float)
#    setInputShield = Qt.pyqtSignal(float)
#    setReferenceSource = Qt.pyqtSignal(float)
#    setReferenceTrigger = Qt.pyqtSignal(float)
#    setReferenceFrequency = Qt.pyqtSignal(float)
#    setReferencePhaseDegree = Qt.pyqtSignal(float)
#    setReferencePhaseRadian = Qt.pyqtSignal(float)
#    setHarmonic = Qt.pyqtSignal(float)
#    setSineOutAmplitude = Qt.pyqtSignal(float)
#    setAuxOut = Qt.pyqtSignal(float)
#    setSync = Qt.pyqtSignal(float)
    def __init__(self, visa):
        super(SR830, self).__init__(visa)
        self.clearGarbage()

    def clearGarbage(self):
        oldTimeOut = self.Instrument.timeout
        self.Instrument.timeout = 0.3
        while True:
            try:
                a = self.read_raw()
                print "Garbage:", a
            except:
                print "No garbage"
                break
        self.Instrument.timeout = oldTimeOut
        print "Timeout back to:", self.Instrument.timeout


    def commandExecuting(self):
        # couldn't find a serialPoll type function
        # Query the serial poll status byte *STB?
        sp = self.statusByte()

        return not bool(sp & 2)

    def autoReserve(self):
        self.commandString("ARSV")
        while self.commandExecuting():
            time.sleep(0.1)

    def autoGain(self):
        self.commandString("AGAN")
        while self.commandExecuting():
            time.sleep(0.1)

    def autoPhaseCustom(self, samples):
        # needs to be fixed by Felix
        ts = self.tcSeconds()
        phaseRef = self.phaseRadian()
        x = 0
        y = 0
        for i in xrange(samples):
            self.snapSignal()
            x += self.X
            y += self.Y
            time.sleep(ts)
        phaseSig = np.arctan2(x,y)
        phaseNew = phaseRef + phaseSig
        self.setReferencePhaseRadian(phaseNew)
        return phaseNew

    def autoPhase(self):
        self.commandString("APHS")
        while (self.commandExecutin()):
            time.sleep(0.1)

    def autoGainCustom(self):
        # needs to be fixed by Felix
        r = self.snapRadius()
        ts = float(self.tcSeconds())*6+0.1
        s = float(self.sensitivity())
        s_old = s
        mustDecrease = self.isOverload()

        # Decrease sensitivity until it looks ok.
        ok = True
        while (ok and (r > self.sensitivityToVolt(s) or self.isOverload())):
            print "autoGainCustom Loop"
            ok = self.decreaseSensitivity(6)
            if not ok:
                self.setSensitivity(self.SENS_1V)
            s = self.sensitivity()
            time.sleep(ts)
            self.isOverload()
            r = self.snapRadius()
        # Increase sensitivity to the expected setting
        bRepeat = True
        # different
        while (bRepeat):
            s_new = self.findSensitivity(r)
            print "r=%f should go to sensitivity %f\n" %(r, self.sensitivityToVolt(s_new))
            if (mustDecrease and s_new < s_old):
                s_new = s+1
            if (s_new < s-6):
                bRepeat = True
                s_new = s-6
            else:
                bRepeat = False
            s = s_new
            print "Going to Sensitivity %s" % self.sensitivityToVolt(s)
            self.setSensitivity(s)
            time.sleep(ts)
            r = self.snapRadius()

            # slowly decrease if in trouble
            while (r > float(self.sensitivityToVolt(s))) or self.isOverload():
                print "autoGainCustom Loop 3"
                ok = self.decreaseSensitivity(1)
                s = s+1
                if not ok:
                    return
                time.sleep(ts)
                self.isOverload()
                r = self.snapRadius()

    def findSensitivity(self, r):
        s = self.SENS_1V
        print "r=", r
        while self.sensitivityToVolt(s-1) > r:
            print "Down:", s
            s -= 1
            if s == self.SENS_min:
                break
        return s

    def snapRadius(self):
        return self.queryFloat("OUTP ? 3")

    def regain(self, lower, higher):
        # needs to be fixed by Felix
        bChanged = False
        ts = self.tcSeconds()*5 + 0.1
        r = self.snapRadius()
        ovl = self.isOverload
        s = self.sensitivity()
        if (r > higher * self.sensitivityToVolt(s)):
            bChanged |= self.decreaseSensitivity(1)
            if (self.ov1):
                return bChanged
                # couldn't find a floatsleep function
                QThread.msleep(ts)
        # Can sensitivity be increased?
        ov1 = self.isOverload()
        if (not(ovl) & (r < lower*self.sensitivityToVolt(s))):
            self.increaseSensitivity(1)
            bChanged |= True
            time.sleep(ts)
        ok = True
        r=self.snapRadius()
        while((ov1 or (r>higher*self.sensitivityVoltage())) & ok):
            ok = self.decreaseSensitivity(1)
            bChanged |= ok
            time.sleep(ts)
        return bChanged

    def snapSignal(self):
        result = self.queryString("SNAP ? 1,2,9")
        d = result.split(',')
        self.X = float(d[0])
        self.Y = float(d[1])
        self.frequency = float(d[2])
        #self.snapSignal.emit(self.mx,self.mY,self.mFrequency)
        return (self.X, self.Y, self.frequency)

    def changeSensitivity(self, steps):
        s = self.sensitivity()
        snew = s + steps
        if snew > self.SENS_max:
            snew = self.SENS_max
        elif snew < self.SENS_min:
            snew = self.SENS_min
        self.setSensitivity(snew)
        return snew != s

    def increaseSensitivity(self, steps):
        return self.changeSensitivity(-steps)
    def decreaseSensitivity(self, steps):
        return self.changeSensitivity(+steps)
    def snapAuxInputs(self):
        result = self.queryString("SNAP ? 5,6,7,8")
        d = result.split(',')
        self._auxIn = [float(x) for x in d]
    def X(self):
        return self.X
    def Y(self):
        return self.Y
    def frequency(self):
        return self.Frequency
    def R(self):
        self.snapSignal()
        return (self.X*self.X+self.Y*self.Y)**(0.5)
    def signedR(self):
        return self.X >= 0
    def Phi(self):
        self.snapSignal()
        return np.arctan2(self.Y,self.X)
    def harmonic(self):
        harm = self.queryInteger("HARM?")
        #self.harmonic.emit(harm)
        return harm
#
    def auxIn(self, i):
        if ((i<1) or (i>4)):
            raise GoutR.outOfRange("AuxIN", "Aux in", 0 ,4)
#        try:
#            self.AuxIN(self, i)
#        except GoutR.outOfRange, e:
#            print e
        return self._auxIn[i-1]
    def phaseDegree(self):
        result = self.queryFloat("PHAS?")
        #self.phaseDegree.emit(result)
        return result
    def phaseRadian(self):
        return np.pi*float(self.phaseDegree())/180.0
    def lockinStatus(self):
        return self.queryInteger("LIAS?")

    def isOverload(self):
        ls = self.lockinStatus()
        ovlInput = bool(ls & self.INPUT_OVERLOAD_LIAS)
        ovlFilter = bool(ls & self.FILTER_OVERLOAD_LIAS)
        ovlOutput = bool(ls & self.OUTPUT_OVERLOAD_LIAS)
        themAll = (ovlInput or ovlFilter or ovlOutput)
        return themAll

    def setTC(self, tc):
        if ((tc < self.TC_min) or (tc > self.TC_max)):
            raise GoutR.outOfRange("setTC", "time constant", self.TC_min, self.TC_max)
        self.commandString("OFLT %d" % tc)
    def tc(self):
        result = self.queryInteger("OFLT?")
        return result
    def tcSeconds(self):
        return self.TCToSeconds(self.tc())
    def TCToSeconds(self, tc):
        Q = float(tc)/2
        t = pow(10.0,Q-5)
        if (tc % 2) != 0:
            t *= 3.0
        return t

    def setSensitivity(self, s):
        if ((s < self.SENS_min) or (s > self.SENS_max)):
            raise GoutR.outOfRange("setSensitivity","sensitivity", self.SENS_min, self.SENS_max)
        #self.setSensitivity.emit(s)
        self.commandString("SENS %d" % s)
    def sensitivity(self):
        result = self.queryInteger("SENS?")
        #self.getSensitivity.emit(result)
        return result
    def sensitivityVoltage(self):
        return self.sensitivityToVolt(self.sensitivity())

    def sensitivityToVolt(self, s):
        Q = int((s+1.)/3)
        V = pow(10.0, Q-9.)
        if (s+1) % 3 == 0:
            V *= 1.0
        elif (s+1) % 3 == 1:
            V *= 2.0
        elif (s+1) % 3 == 2:
            V *=5.0
        return V

    def setSync(self, on):
        self.commandString("SYNC %d" %on)
    def setFilterSlope(self, s):
        if ((s < self.SLOPE_min) or (s > self.SLOPE_max)):
            raise GoutR.outOfRange("setFilterScope", "Low Pass Filter Scope", self.SLOPE_min, self.SLOPE_max)
        self.commandString("OFSL %d" % s)
        #self.setFilterScope.emit(s)
    def filterSlope(self):
        result = self.queryInteger("OFSL?")
        return result

    def setReserve(self, r):
        if ((r < self.RESERVE_min) or (r > self.RESERVE_max)):
            raise GoutR.outOfRange("setReserve","reserve mode", self.RESERVE_min, self.RESERVE_max)
        self.commandString("RMOD %d" % r)
        #self.setReserve.emit(r)
    def reserve(self):
        result = self.queryInteger("RMOD?")
        return result
    def setInputSource(self, source):
        self.commandString("ISRC %d" % source)
        #self.setInputSource.emit(source)
    def setInputShield(self, shield):
        self.commandString("IGND %d" % shield)
        #self.setInputShield.emit(shield)
    def setInputCoupling(self, coupling):
        self.commandString("ICPL %d" % coupling)
        #self.setInputCoupling.emit(coupling)
    def setInputFilters(self, filters):
        self.commandString("ILIN %d" % filters)
        #self.setInputFilters.emit(filters)
    def inputSource(self):
        result = self.queryInteger("ISRC?")
        return result
    def inputShield(self):
        result = self.queryInteger("IGND?")
        return result
    def inputCoupling(self):
        result = self.queryInteger("ICPL?")
        return result
    def inputFilters(self):
        result = self.queryInteger("ILIN?")
        return result
    def setReferenceSource(self, source):
        self.commandString("FMOD %d" % source)
        #self.setReferenceSource.emit(source)
    def setReferenceTrigger(self, trigger):
        self.commandString("RSLP %d" % trigger)
        #self.setReferenceTrigger.emit(trigger)
    def referenceTrigger(self):
        result = self.queryInteger("RSLP?")
        return result
    def setReferenceFrequency(self, frequency):
        self.commandString("FREQ %f" % frequency)
    def referenceFrequency(self):
        result = self.queryFloat("FREQ?")
        return result
    def setReferencePhaseDegree(self, deg):
        if ((deg < -360.0) or (deg > 729.99)):
            raise GoutR.outOfRange("setReferencePhaseDegree","degree", -360, 729.99)
        self.commandString("PHAS %f" % deg)
        #self.setReferencePhaseDegree.emit(deg)
    def referencePhaseDegree(self):
        result = self.queryFloat("PHAS?")
        return result
    def setReferencePhaseRadian(self, rad):
        self.setReferencePhaseDegree(180*(rad/np.pi))
    def setHarmonic(self, harmonic):
        self.commandString("HARM %d" % harmonic)
        #self.setHarmonic.emit(harmonic)
    def setSineOutAmplitude(self, amplitude):
        if ((amplitude < 0.004) or (amplitude > 5.000)):
            raise GoutR("setSineOutAmplitude","amplitude", 0.004, 5.000)
        self.commandString("SLVL %f" % amplitude)
        #self.setSineOutAmplitude.emit(amplitude)
    def sineOutAmplitude(self):
        result = self.queryFloat("SLVL?")
        return result
    def setAuxOut(self, channel, voltage):
        if (channel>4) or (channel<1):
            raise GoutR.outOfRange("setAuxOut", "Channel", 1, 4)

        if (voltage<-10.5) or (voltage>+10.5):
            raise GoutR.outOfRange("setAuxOut", "Voltage", -10.5,10.5)
        self.commandString("AUXV %d,%f" % (channel, voltage))
        #self.setAuxOut.emit(i, V)
    def auxOut(self, i):
        V = self.queryFloat("AUXV? %d" % i)
        return V

if __name__ == '__main__':
    sr830 = SR830("GPIB0::12")
    channel = 1

    sr830.autoGain()
    #sr830.autoGainCustom()

    sr830.setAuxOut(1, 0.0)
    sr830.setAuxOut(2, 3.563)



    print sr830.auxOut(channel)
    sr830.setAuxOut(channel,0)
    print sr830.auxOut(channel)
    print sr830.snapSignal()

#    srs830.autoGain()
#    srs830.autoPhase()
#    srs830.autoReserve()
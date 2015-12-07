# -*- coding: utf-8 -*-
"""
A set of classes with identical interface to produce analog output voltages
Currently availabe: AnalogOutSR830, AnalogOutKeithley, AnalogOutDaq
The API is very simple:

ao = AnalogOutDaq('USB6002','ao1')
ao.setDrive(0)
print "Drive voltage:", ao.drive()
ao.clear()

Created on Tue Nov 10 14:20:30 2015

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""



class VoltageSourceSR830():
    def __init__(self, sr830, auxOutChannel = None):
        self.sr830 = sr830
        self.auxOutChannel = auxOutChannel

    def setDcDrive(self, V):
        self.sr830.setAuxOut(self.auxOutChannel, V)

    def dcDrive(self):
        return self.sr830.auxOut(self.auxOutChannel)

    def visaId(self):
        return self.sr830.visaId()

    def setAcDrive(self, f, Vac):
        self.sr830.setReferenceFrequency(f)
        self.sr830.setSineOutAmplitude(Vac)

    def acDrive(self):
        f = self.sr830.sineOutFrequency()
        Vac = self.sr830.sineOutAmplitude()
        return (f, Vac)

    def name(self):
        return 'SR830'

    def clear(self):
        if self.auxOutChannel is not None:
            self.sr830.setAuxOut(self.auxOutChannel, 0)
        self.sr830.setSineOutAmplitude(0.004)

from Visa.Keithley6430 import Keithley6430

class CurrentSourceKeithley():
    def __init__(self, visa, currentRange=100E-3, complianceVoltage=10):
        sm = Keithley6430(visa)
        sm.setSourceFunction(Keithley6430.MODE.CURRENT)
        sm.setSenseFunction(Keithley6430.MODE.VOLTAGE)
        sm.setComplianceVoltage(complianceVoltage)
        sm.setSourceCurrentRange(currentRange)
        sm.enableOutput()
        self.sm = sm

    def visaId(self):
        return self.sr830.visaId()

    def setDcDrive(self, mA):
        self.sm.setSourceCurrent(1E-3*mA)
        #self.sm.obtainReading()

    def dcDrive(self):
        return 1E3*self.sm.sourceCurrent()

    def clear(self):
        self.sm.disableOutput()

    def name(self):
        return 'Keithley6430'

class VoltageSourceKeithley():
    def __init__(self, visa, voltageRange=10, complianceCurrent=10E-3):
        sm = Keithley6430(visa)
        sm.setSourceFunction(Keithley6430.MODE.VOLTAGE)
        sm.setSenseFunction(Keithley6430.MODE.CURRENT)
        sm.setComplianceCurrent(complianceCurrent)
        sm.setSourceVoltageRange(voltageRange)
        sm.enableOutput()
        self.sm = sm

    def visaId(self):
        return self.sr830.visaId()

    def setDcDrive(self, V):
        self.sm.setSourceVoltage(V)
        #self.sm.obtainReading()

    def dcDrive(self):
        return self.sm.sourceVoltage()

    def clear(self):
        self.sm.disableOutput()

    def name(self):
        return 'Keithley6430'
    

import DAQ.PyDaqMx as daq

class VoltageSourceDaq():
    def __init__(self, device, channel, voltageMin=-10, voltageMax=+10):
        self.aoChannel = daq.AoChannel('%s/%s' % (device, channel), voltageMin, voltageMax)
        self.otask = daq.AoTask('Output')
        self.otask.addChannel(self.aoChannel)
        self.otask.start()

    def __del__(self):
        self.clear()

    def setDcDrive(self, V):
        self.V = V
        self.otask.writeData([V])

    def dcDrive(self):
        return self.V

    def visaId(self):
        return self.aoChannel.physicalChannel

    def clear(self):
        print "Clearing otask"
        if self.otask is not None:
            self.otask.stop()
            self.otask.clear()
            self.otask = None

    def name(self):
        return 'DAQ'

if __name__ == '__main__':
    #source = VoltageSourceDaq('USB6002','ao1')
    import time
    source = CurrentSourceKeithley('GPIB0::24')
    for V in range(-5, 5):
        source.setDcDrive(V)
        time.sleep(1)
    print "Drive:", source.dcDrive()
    source.clear()

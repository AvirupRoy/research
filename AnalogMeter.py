# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 21:25:38 2015

@author: wisp10
"""

class VoltmeterSR830():
    def __init__(self, sr830, auxInChannel = None):
        self.sr830 = sr830
        self.auxInChannel = auxInChannel

    def setRange(self, maxV):
        s = self.sr830.findSensivity(maxV)
        self.sr830.setSensitivty(s)

    def autoGain(self):
        self.sr830.autoGain()

    def measureDc(self):
        self.sr830.snapAuxInputs()
        V = self.sr830.auxIn(self.auxInChannel)
        return V

    def visaId(self):
        return self.sr830.visaId()

    def measureAc(self):
        X,Y,f = self.sr830.snapSignal()
        return X,Y,f

    def clear(self):
        pass

class VoltmeterDmm():
    class Function:
        UNKNOWN = 0
        DC = 1
        AC = 2

    def __init__(self, dmm):
        self.dmm = dmm
        self.function = self.Function.UNKNOWN

    def setRange(self, maxV):
        pass

    def measureAc(self):
        if self.function != self.Function.AC:
            self.dmm.setFunctionVoltageAc()
            self.function = self.Function.AC
        Vac = self.dmm.reading()
        return Vac

    def visaId(self):
        return self.dmm.visaId()

    def measureDc(self):
        if self.function != self.Function.DC:
            self.dmm.setFunctionVoltageDc()
            self.function = self.Function.DC
        V = self.dmm.reading()
        return V

    def clear(self):
        # @todo Would like to deassert the REN line here
        # Perhaps via gpib_control_ren
        pass

import DAQ.PyDaqMx as daq
import numpy as np

class VoltmeterDaq():
    def __init__(self, device, channel, voltageMin, voltageMax, samples=100, drop=30):
        self.aiChannel = daq.AiChannel('%s/%s' % (device, channel), voltageMin, voltageMax)
        self.itask = daq.AiTask('Input')
        self.itask.addChannel(self.aiChannel)
        self.itask.start()
        self.nSamples = samples
        self.nDrop = drop

    def __del__(self):
        self.clear()

    def visaId(self):
        return self.aiChannel.physicalChannel

    def measureDc(self):
        Vs = self.itask.readData(self.nSamples)[0]
        return np.mean(Vs[self.nDrop:])

    def measureAc(self):
        return np.nan

    def clear(self):
        print "Clearing itask"
        if self.itask is not None:
            self.itask.stop()
            self.itask.clear()
            self.itask = None

if __name__ == '__main__':
 #   from Visa.Agilent34401A import Agilent34401A
#    dmm = Agilent34401A('GPIB0::23')
#    vm = VoltmeterDmm(dmm)

#    from Visa.SR830 import SR830
#    sr830 = SR830('GPIB0::12')
#    vm = VoltmeterSR830(sr830, 1)

    vm = VoltmeterDaq('USB6002', 'ai3', -10, 10)

    for i in range(4):
        print "Vdc = ", vm.measureDc()

    for i in range(4):
        print "Vac = ", vm.measureAc()

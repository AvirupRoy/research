# -*- coding: utf-8 -*-
"""
Classes for ADR magnet control with abstraction to support generic power supply
Created on Wed May 20 17:59:13 2015
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from math import log
import logging
logger = logging.getLogger(__name__)

import DAQ.PyDaqMx as daq
import numpy as np

class DaqVoltageSource():
    class MODE:
        VOLTAGE = 1

    def __init__(self, deviceName, aoChannel, aiChannel, minVoltage=-2.0, maxVoltage=0, continuousReadback = True):
        self.Vreadback = None
        self.Vcommand = None
        self.dev = daq.Device(deviceName)
        self.ao = daq.AoChannel('%s/%s' % (deviceName,aoChannel), minVoltage, maxVoltage)
        self.otask = daq.AoTask('MagnetControl_Output')
        self.otask.addChannel(self.ao)
        self.otask.start()   # No timing necessary for on-demand tasks

        if continuousReadback:
            self.ai = daq.AiChannel('%s/%s' % (deviceName,aiChannel), -10, 10)
            self.itask = daq.AiTask('MagnetControl_Input')
            self.itask.addChannel(self.ai)
            self.itask.start()   # No timing necessary for on-demand tasks
        else:
            self.itask = None
            self.Vcommand = self.startupReadback(deviceName, aiChannel)

    def sourceVoltage(self):
        if self.Vcommand is None:
            self.obtainReading()
        return self.Vcommand

    def startupReadback(self, deviceName, aiChannel):
        ai = daq.AiChannel('%s/%s' % (deviceName,aiChannel), -10, 10)
        itask = daq.AiTask('MagnetControl_Input')
        itask.addChannel(ai)
        itask.start()   # No timing necessary for on-demand tasks
        Vai = itask.readData(1000)[0]
        itask.stop()

        Vreadback = np.mean(Vai)
        VaiStd = np.std(Vai)
        if VaiStd > 2E-3:
            logger.warn('High std. deviation on voltage read-back: %.5g V' % VaiStd)
        return Vreadback

    def obtainReading(self):
        if self.itask is not None:
            Vai = self.itask.readData(1000)[0]
            self.Vreadback = np.mean(Vai)
            VaiStd = np.std(Vai)
            if VaiStd > 2E-3:
                logger.warn('High std. deviation on voltage read-back: %.5g V' % VaiStd)

            if self.Vcommand is None:
                self.Vcommand = self.Vreadback

            if abs(self.Vcommand - self.Vreadback) > 5E-3:
                logger.warn('Readback (%.5g V) does not match command voltage (%.g V)!' % (self.Vreadback, self.Vcommand))

    def setSourceVoltage(self, V):
        self.otask.writeData([V])
        self.Vcommand = V

    def outputEnabled(self):
        return True

    def setSourceVoltageRange(self, range):
        pass

    def sourceFunction(self):
        return self.MODE.VOLTAGE

    def setSourceFunction(self, function):
        if function != self.MODE.VOLTAGE:
            raise Exception('Unsupported source function:%s' % function)

    def enableOutput(self, enable=True):
        if not enable:
            self.setSourceVoltage(0)

class MagnetSupplySourceMeter():
    MAX_CURRENT = 0.095

    def __init__(self, sourceMeter):
        self.sm = sourceMeter
        self.startup()

    def startup(self):
        sm = self.sm

        if sm.outputEnabled():
            if self.sm.sourceFunction() != sm.MODE.VOLTAGE:
                raise Exception('Source-meter output is on, but not sourcing voltage!')
            if self.sm.senseFunction() != sm.MODE.CURRENT:
                raise Exception('Source-meter output is on, but not measuring current!')
            if self.sm.sourceVoltageRange() != 2.1:
                print self.sm.sourceVoltageRange()
                raise Exception('Source-meter output is on, but not on 2V source range!')
            if self.sm.complianceCurrent() != 0.1:
                print self.sm.complianceCurrent()
                raise Exception('Source-meter output is on, but compliance current is not 0.1A!')
            self.Vsupply = sm.sourceVoltage()
            if self.Vsupply < 0:
                raise Exception('Source-meter output is on, but source voltage is negative!')
        else:
            sm.setSourceFunction(Keithley6430.MODE.VOLTAGE)
            sm.setSenseFunction(Keithley6430.MODE.CURRENT)
            sm.setSourceVoltageRange(2.1)
            sm.setComplianceCurrent(0.1)
            sm.setSourceVoltage(0)
            logger.info("Enabling output")
            sm.enableOutput()

        r = sm.obtainReading()
        self.I = r.current
        logger.info("Starting from %f A." % self.I)

    def supplyCurrent(self):
        r = self.sm.obtainReading()
        self.I = r.current
        return self.I

    def supplyVoltages(self):
        '''Return programmed and measured supply voltages, checking if they agree within 0.1V'''
        return (self.Vsupply, self.Vsupply)

    def setSupplyVoltage(self, V):
        self.sm.setSourceVoltage(V)
        self.Vsupply = self.sm.sourceVoltage()
        return self.Vsupply


class MagnetSupply():
    PROG_SLOPE = -1.598064
    PROG_INTERCEPT = -0.0030895
    MAX_CURRENT = 9.5

    def __init__(self, powerSupply, voltageSource):
        self.ps = powerSupply
        self.vs = voltageSource
        self.startup()

    def startup(self):
        psEnabled = self.ps.outputEnabled()
        V = self.ps.voltageSetpoint()

        self.ps.setCurrent(self.MAX_CURRENT)

        #I = self.ps.currentSetpoint()

        if abs(V) > 0.02: # Make sure progamming voltage is zero
            raise Exception('Need to start from 0 programming voltage, found %fV!' % V)

        self.I = self.ps.measureCurrent()
        logger.info("Starting from %f A." % self.I)

        self.Vprog = self.vs.sourceVoltage() # Restore old programming voltage, if any
        if self.Vprog > 0.02 or self.Vprog <= -2.0:
            raise Exception('Voltage source voltage (%f V) must be negative, and >=-2.0V' % self.Vprog)

        self.vs.setSourceVoltageRange(2.0)

        if self.vs.outputEnabled(): # Output on, make sure things are sensible
            if self.vs.sourceFunction() != self.vs.MODE.VOLTAGE:
                raise Exception('Source needs to be in voltage mode to continue.')
            self.Vprog = self.vs.sourceVoltage()
            if self.Vprog > 0.02:
                raise Exception('Invalid source voltage.')
        else:  # Output off
            if psEnabled and self.ps.measureCurrent() > 0.05:
                raise Exception('Voltage source is off, but power supply output is on and supplying?!')

            self.vs.setSourceFunction(self.vs.MODE.VOLTAGE)
            self.vs.setComplianceCurrent(10E-3)
            if self.Vprog > 0.02:
                self.Vprog = 0
            self.vs.setSourceVoltage(self.Vprog)
            self.vs.enableOutput(True)

        if not psEnabled and self.Vprog == 0: # Finally, enable power supply
            logger.info("Enabling output")
            self.ps.enableOutput()

    def programmingVoltageToSupplyVoltage(self, Vprog):
        """Calculate supply voltage for a given programming voltage"""
        if Vprog <= 0:
            Vsupply = self.PROG_SLOPE*Vprog + self.PROG_INTERCEPT
            return Vsupply
        else:
            raise Exception('Programming voltage must be negative, but it is %f V!' % Vprog)

    def supplyVoltageToProgrammingVoltage(self, Vsupply):
        """Caculate programming voltage for a given supply voltage"""
        if Vsupply >=0 and Vsupply <=8.:
            Vprog = (Vsupply-self.PROG_INTERCEPT)/self.PROG_SLOPE
            return Vprog
        else:
            raise Exception('Supply voltage must be positive and <=8 !')

    def supplyCurrent(self):
        return self.ps.measureCurrent()

    def supplyVoltages(self):
        '''Return programmed and measured supply voltages, checking if they agree within 0.1V'''
        Vprog = self.vs.sourceVoltage()
        VsupplyProg = self.programmingVoltageToSupplyVoltage(Vprog)
        VsupplyMeasured = self.ps.measureVoltage()

        if abs(VsupplyProg - VsupplyMeasured) > 0.3:
            raise Exception('Unacceptable difference between programmed (%f V) and measured (%f V) supply voltage!' % (VsupplyProg, VsupplyMeasured))

        return (VsupplyProg, VsupplyMeasured)

    def setSupplyVoltage(self, V):
        Vprog = self.supplyVoltageToProgrammingVoltage(V)
        self.vs.setSourceVoltage(Vprog)
        self.vs.obtainReading()
        try:
            Vprog = self.vs.sourceVoltage()
        except Exception:
            logger.warn("Can't confirm output voltage with Keithley 6430. Continue under assumption that it has been understood", exc_info=True)

        Vsupply = self.programmingVoltageToSupplyVoltage(Vprog)
        return Vsupply

from PyQt4.QtCore import QThread, pyqtSignal
import time
import os.path


from Zmq.Zmq import ZmqPublisher, ZmqSubscriber

class MagnetControlSubscriber(ZmqSubscriber):
    supplyVoltageReceived = pyqtSignal(float)
    supplyCurrentReceived = pyqtSignal(float)
    magnetVoltageReceived = pyqtSignal(float)

    def __init__(self, host='tcp://127.0.0.1', parent = None):
        ZmqSubscriber.__init__(self, 5556, host, parent = parent)

    def processMessage(self, message, tReceived):
        #print "Magnet message:", message
        timeStamp = message['timeStamp']
        if self.isExpired(tReceived, timeStamp):
            return
        origin = message['origin']
        if origin != 'MagnetControlThread':
            return
        item = message['item']
        value = message['data']
        if type(value) != float:
            return

        if item == 'Isupply':
            self.supplyCurrentReceived.emit(value)
        elif item == 'Vsupply':
            self.supplyVoltageReceived.emit(value)
        elif item == 'Vmagnet':
            self.magnetVoltageReceived.emit(value)
        else:
            pass

class History():
    def __init__(self, maxAge=5):
        self._maxAge = maxAge
        self.t = []
        self.y = []

    def append(self, t, y):
        self.y = np.append(self.y, y)
        self.t = np.append(self.t, t)
        tNewest = np.max(t)
        iRecent = self.t >= tNewest-self._maxAge
        self.y = self.y[iRecent]
        self.t = self.t[iRecent]

    def __str__(self):
        return "t=%s y=%s" % (self.t, self.y)

    def dydt(self, t=None):
        if t == None:
            t = time.time()
        nPoints = len(self.t)
        if nPoints < 2:
            return 0
        elif nPoints < 5:
            order = 1
        elif nPoints < 10:
            order = 2
        else:
            order = 3

        tCenter = np.mean(self.t)
        fit = np.polyfit(self.t-tCenter, self.y, order)
        der = np.polyder(fit)
        dydt = np.polyval(der, t-tCenter)
        return dydt

class MagnetControlThread(QThread):
    DIODE_I0 = 4.2575E-11 # A
    DIODE_A  = 37.699     # 1/V (=q_q/(k_B*T))
    quenchDetected = pyqtSignal()
    supplyVoltageUpdated = pyqtSignal(float)
    programmedSupplyVoltageUpdated = pyqtSignal(float)
    supplyCurrentUpdated = pyqtSignal(float)
    magnetVoltageUpdated = pyqtSignal(float)
    diodeVoltageUpdated = pyqtSignal(float)
    resistiveVoltageUpdated = pyqtSignal(float)
    resistanceUpdated = pyqtSignal(float)
    rampRateUpdated = pyqtSignal(float)

    def __init__(self, magnetSupply, dmm, parent=None):
        QThread.__init__(self, parent)
        self.ms = magnetSupply
        self.dmm = dmm
        self.interval = 0.25
        self.dIdtMax = 1./60. # max rate: 1 A/min = 1./60. A/s
        self.dIdt = 0.
        self.Rmax = 0.6
        self.inductance = 30.0 # 30 Henry
        self.Vmax = 2.5 # Maximum supply voltage
        self.Imax = 8.5
        self._quenched = False
        self.publisher = ZmqPublisher('MagnetControlThread', 5556, self)

    @property
    def quenched(self):
        return self._quenched

    @property
    def maximumCurrent(self):
        return self._Imax

    @maximumCurrent.setter
    def maximumCurrent(self, Imax):
        self._Imax = Imax

    @property
    def inductance(self):
        return self._L

    @inductance.setter
    def inductance(self, L):
        if L > 0:
            self._L = L
        else:
            raise Exception('Inductance must be positive.')

    def setRampRate(self, dIdt):
        '''Specify desired ramp rate in A/s.'''
        if self.quenched:
            self.dIdt = -0.5*self.dIdtMax # Fast ramp down
        else:
            self.dIdt = max(-self.dIdtMax, min(self.dIdtMax, dIdt))
        self.rampRateUpdated.emit(self.dIdt)

    def log(self, t):
        fileName = 'MagnetControl_%s.dat' % time.strftime('%Y%m%d')
        if not os.path.isfile(fileName):
            with open(fileName, 'a') as f:
                header = '#tUnix\tVsupply\tIsupply\tVmagnet\tVsupplyProg\n'
                f.write(header)
        text = '%.3f\t%.3f\t%.3f\t%.5g\t%.5f\n' % (t, self.supplyVoltage, self.supplyCurrent, self.magnetVoltage, self.programmedSupplyVoltage)
        with open(fileName, 'a') as f:
            f.write(text)

    def diodeVoltageDrop(self, current):
        '''Calculate approximate the diode voltage drop for a given current.
        '''
        if current < 0:
            raise Exception('Current must be positive')
        Vdiode = log(current/self.DIODE_I0+1)/self.DIODE_A
        return Vdiode

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, seconds):
        self._interval = float(seconds)

    def stop(self):
        self.stopRequested = True
        logger.debug("MagnetControlThread stop requested.")

    def triggerQuench(self):
        self._quenched = True
        logger.warning("Quench detected!")
        self.quenchDetected.emit()
        self.setRampRate(0) # This will set the ramp rate to ramp down

    def measureSupplyCurrent(self):
        I = self.ms.supplyCurrent()
        self.supplyCurrent = I
        self.supplyCurrentUpdated.emit(I)
        return I

    def measureSupplyVoltage(self):
        (Vprogrammed, Vmeasured) = self.ms.supplyVoltages()
        self.supplyVoltage = Vmeasured
        self.supplyVoltageUpdated.emit(Vmeasured)
        self.programmedSupplyVoltage = Vprogrammed
        self.programmedSupplyVoltageUpdated.emit(Vprogrammed)
        return Vprogrammed

    def measureMagnetVoltage(self):
        logger.info("Measuring magnet voltage")
        V = self.dmm.voltageDc()
        logger.info("Vmagnet=%fV" % V)
        self.magnetVoltage = V
        self.magnetVoltageUpdated.emit(V)
        return V

    def setSuppyVoltage(self, Vnew):
            if Vnew >= self.Vmax:
                Vnew = self.Vmax
                self.supplyLimit = True
            elif Vnew <= 0:
                Vnew = 0
                self.supplyLimit = True
            else:
                self.supplyLimit = False
            self.programmedSupplyVoltage = self.ms.setSupplyVoltage(Vnew)
            self.programmedSupplyVoltageUpdated.emit(self.programmedSupplyVoltage)

    def sleepPrecise(self,tOld):
            tSleep = int(1E3*(self.interval-time.time()+tOld-0.010))
            if tSleep>0.010:
                self.msleep(tSleep)
            while(time.time()-tOld < self.interval):
                pass

    def run(self):
        self.stopRequested = False
        logger.info("Thread starting")
        currentHistory = History(maxAge=3)
        dIdtThreshold = 50E-3 # 10mA/s
        mismatchCount = 0
        mismatch = False
        try:
            while not self.stopRequested:
                # First, take all measurements
                t = time.time()
                Isupply = self.measureSupplyCurrent()
                Vsupply = self.measureSupplyVoltage()
                Vmagnet = self.measureMagnetVoltage()
                self.publisher.publish('Isupply', Isupply)
                self.publisher.publish('Vsupply', Vsupply)
                self.publisher.publish('Vmagnet', Vmagnet)

                # Log all measurements
                self.log(t)

                # Check that Vmagnet matches L * dI/dt
                currentHistory.append(t, Isupply)
                dIdt = currentHistory.dydt()

                if abs(dIdt) > dIdtThreshold or abs(Vmagnet) > self.inductance*dIdtThreshold:
                    match = (dIdt /  (Vmagnet/self.inductance))-1.
                    if abs(match) > 0.5:
                        logger.warn("Mismatch between dIdt (%.4f A/s) and magnet voltage (%.5f V)." % (dIdt, Vmagnet))
                        mismatchCount += 1
                    else:
                        mismatchCount = 0
                else:
                    mismatchCount = 0

                # Check for quench
                if Isupply < 0:
                    Isupply = 0
                Vdiode = self.diodeVoltageDrop(Isupply)
                self.diodeVoltageUpdated.emit(Vdiode)
                V_R = Vsupply - Vmagnet - Vdiode
                self.resistiveVoltageUpdated.emit(V_R)
                if Isupply > 0.1:
                    R = V_R / Isupply
                else:
                    R = float('nan')
                self.resistanceUpdated.emit(R)
                if Isupply > 1:
                    if R > self.Rmax:
                        self.triggerQuench()

                #Compute new parameters
                VmagnetGoal = self.inductance*self.dIdt

                if Isupply >= self.Imax and self.dIdt > 0:
                    VmagnetGoal = 0

                errorTerm = (VmagnetGoal-Vmagnet)
                logger.info("Programmed supply voltage %f" % self.programmedSupplyVoltage)
                if mismatchCount > 5:
                    logger.warn("Mismatch between dIdt has persisted, ramping down supply!")
                    mismatch = True

                if not mismatch:
                    Vnew = Vsupply + errorTerm
                else:
                    Vnew = Vsupply - 0.1
                    if Vnew < 0:
                        break
                logger.info("Vnew=%f V"% Vnew)
                self.setSuppyVoltage(Vnew)
                self.sleepPrecise(t)

        except Exception:
            logger.warn("Exception:", exc_info=True)
        logger.info("MagnetControl ending")

class MagnetControlNoMagnetVoltageThread(MagnetControlThread):
    def measureMagnetVoltage(self):
        return None

    def run(self):
        self.stopRequested = False
        logger.info("Thread starting")
        currentHistory = History(maxAge=20)
        mismatch = False
        try:
            while not self.stopRequested:
                # First, take all measurements
                t = time.time()
                Isupply = self.measureSupplyCurrent()
                Vsupply = self.measureSupplyVoltage()
                # Check that Vmagnet matches L * dI/dt
                currentHistory.append(t, Isupply)
                dIdt = currentHistory.dydt(t)
                Vmagnet = dIdt * self.inductance
                self.magnetVoltage = Vmagnet
                self.magnetVoltageUpdated.emit(Vmagnet)

                self.publisher.publish('Isupply', Isupply)
                self.publisher.publish('Vsupply', Vsupply)
                self.publisher.publish('Vmagnet', Vmagnet)

                # Log all measurements
                self.log(t)

                # Check for quench
                Isupply = max(Isupply, 0)
                Vdiode = self.diodeVoltageDrop(Isupply)
                self.diodeVoltageUpdated.emit(Vdiode)
                V_R = Vsupply - Vmagnet - Vdiode
                self.resistiveVoltageUpdated.emit(V_R)
                if Isupply > 0.1:
                    R = V_R / Isupply
                else:
                    R = float('nan')
                self.resistanceUpdated.emit(R)
                if Isupply > 1:
                    if R > self.Rmax:
                        self.triggerQuench()

                #Compute new parameters
                VmagnetGoal = self.inductance*self.dIdt

                if Isupply >= self.Imax and self.dIdt > 0:
                    VmagnetGoal = 0

                if not mismatch:
                    Vnew = Vsupply + VmagnetGoal/10
                else:
                    Vnew = Vsupply - 0.1
                    if Vnew < 0:
                        break
                logger.info("Vnew=%f V"% Vnew)
                self.setSuppyVoltage(Vnew)
                self.sleepPrecise(t)

        except Exception:
            logger.warn("Exception:", exc_info=True)
        logger.info("MagnetControl ending")

def magnetSupplyTest():
    import sys
    from Visa.Agilent6641A import Agilent6641A
    from Visa.Keithley6430 import Keithley6430
    from Visa.Agilent34401A import Agilent34401A

    print "1"
    ps = Agilent6641A('GPIB0::5')
    if not '6641A' in ps.visaId():
        raise Exception('Agilent 6641A not found!')
    print "2"
    dmm = Agilent34401A('GPIB0::22')
    if not '34401A' in dmm.visaId():
        raise Exception('Agilent 34401A not found!')

    print "3"
    voltageSource = 'DAQ'
    if voltageSource == 'Keithley6430':
        vs = Keithley6430('GPIB0::24')
        visaId = vs.visaId()
        if not '6430' in visaId:
            raise Exception('Keithley 6430 not found!')
        else:
            logger.info('Have Keithley 6430:%s' % visaId)
    elif voltageSource == 'DAQ':
        vs = DaqVoltageSource('USB6002', 'ao0','ai0')
        logger.info('Have USB6002 voltage source')
    else:
        raise Exception("Don't know what to use as the programming source!")
    print "4"

    print "Starting MagnetSupply"
    magnetSupply = MagnetSupply(ps, vs)
    print "5"

    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('ADR3 Magnet Control')


    magnetThread = MagnetControlThread(magnetSupply, dmm)
    magnetThread.run()

    #QTimer.singleShot(2000, magnetThread.start)
    #magnetThread.run()
    try:
        app.exec_()
    except:
        print "Exiting"

def VoltageSupplyTestDaq():
    vs = DaqVoltageSource('USB6002', 'ao0','ai0')
    vs.enableOutput()
    vs.setSourceVoltageRange(2)
    vs.setSourceFunction(vs.MODE.VOLTAGE)
    vs.setSourceVoltage(0)
    print vs.sourceVoltage()
    print vs.obtainReading()

def testHistory():
    history = History()

    for t in np.arange(0, 10):
        y = 0.5*t**2+2*t-7
        history.append(t,y)
        print "History:", history
        print "dy/dt", history.dydt(t)

if __name__ == '__main__':
    #magnetSupplyTest()
    #testHistory()
#    VoltageSupplyTestDaq()
    from Visa.Keithley6430 import Keithley6430
    k6430 = Keithley6430('GPIB0::24')
    ms = MagnetSupplySourceMeter(k6430)

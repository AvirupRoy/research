# -*- coding: utf-8 -*-
"""
Classes for ADR magnet control with abstraction to support generic power supply
Created on Wed May 20 17:59:13 2015
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

import logging
logger = logging.getLogger(__name__)

from PyQt4.QtCore import QThread, pyqtSignal, QObject

from math import log
import DAQ.PyDaqMx as daq
import numpy as np
import time
import os.path
import sys
import traceback

from Zmq.Zmq import ZmqPublisher, ZmqSubscriber
from Zmq.Ports import RequestReply
from Zmq.Ports import PubSub
from Zmq.Zmq import ZmqRequestReplyThread, ZmqReply


class EmergencyException(Exception):
    pass

from MagnetSupply import History

class LinearTransform():
    def __init__(self, gain, offset, minimum=None, maximum=None):
        self._gain = gain
        self._offset = offset
        self._min = minimum
        self._max = maximum
        
    def transformForward(self, Vin):
        Vlim = Vin
        clipping = False
        if self._min is not None:
            if Vin < self._min:
                Vlim = self._min
                clipping = True
        if self._max is not None:
            if Vin > self._max:
                Vlim = self._max
                clipping = True
        Vout = self._gain * Vlim + self._offset
        return Vout, clipping
    
    def transformBackward(self, Vout):
        Vin = (Vout - self._offset) / self._gain
        Vlim = Vin
        if self._min is not None:
            if Vin < self._min:
                Vlim = self._min
                clipping = True
        if self._max is not None:
            if Vlim > self._max:
                Vlim = self._max
                clipping = True
        return Vin, clipping

class MagnetControlThread(QThread):
    '''Magnet control thread'''
    #MagnetVoltageTransform = LinearTransform(gain=17.479, offset=0, minimum=-3.4, maximum=3.4)
    MagnetVoltageGain = 17.387  # This is the gain off the diff-amp AD8424_4
    MagnetVoltageLimit = abs(3.4/MagnetVoltageGain)  # Careful: the common mode voltage range of that amp is quite limited
    
    
    OutputVoltageControlGain = 0.5 # The resistive divider the input has a gain of 0.5
    
    #CurrentFineTransform = LinearTransform(gain=58.2553, offset=0, minimum=-10.5, maximum=10.5)
    CurrentFineResistance = 59.922 # V/A
    
    #CurrentCoarseTransform = LinearTransform(gain=1.00704/1.05, offset=0, minimum=-10.5, maximum=10.5)
    CurrentCoarseResistance = 0.9594 # V/A
    
    #FetVoltageTransform = LinearTransform(gain=3.8609, offset=0, minimum=-10.5, maximum=10.5)
    FetVoltageMonitorGain = 3.8609 # about 4V/V 

    OutputVoltageLimit = 10./FetVoltageMonitorGain # This is the maximum we can read-out because of the 5x gain
    
    SupplyDeltaMin = 1.3
    SupplyDeltaMax = 1.6
    
    DIODE_I0 = 5.8214E-11 # units: A , used to estimate the voltage drop across the magnet
    DIODE_A  = 30.6092     # 1/V (=q_q/(k_B*T)) , used to estimate the voltage drop across the magnet

    analogFeedbackChanged = pyqtSignal(bool)    
    quenchDetected = pyqtSignal()
    diodeVoltageUpdated = pyqtSignal(float)
    resistiveVoltageUpdated = pyqtSignal(float)
    resistanceUpdated = pyqtSignal(float)
    rampRateUpdated = pyqtSignal(float)
    measurementAvailable = pyqtSignal(float, float, float, float, float, float, float, float)

    def __init__(self, powerSupply, parent=None):
        QThread.__init__(self, parent)
        self.ps = powerSupply
        print "Power supply", self.ps
        self.interval = 0.5 # Update interval
        self.dIdtMax = 1./60. # max rate: 1 A/min = 1./60. A/s
        self.dIdtTarget = 0.
        self.Rmax = 0.6 # Maximum R for quench detection
        self.inductance = 30.0 # 30 Henry
        self.VSupplyMax = 4.7 # Maximum supply voltage
        self.ISupplyMax = 8.9 # 9.0 # Maximum current permitted
        self.IOutputMax = 8.5 # 8.5 # Maximum current permitted
        self._quenched = False
        self.publisher = ZmqPublisher('MagnetControlThread', PubSub.MagnetControl, self)
        self.samplesPerChannel = 4000

        
    def programMagnetVoltage(self, V):
        if abs(V) > self.MagnetVoltageLimit:
            raise Exception('Programmed magnet voltage exceeded limit')
        Vprog = -V * self.MagnetVoltageGain
        self.magnetVControlTask.writeData([Vprog], autoStart = True)
        print "Magnet voltage set to:", Vprog

    def enableMagnetVoltageControl(self,enable = True):
        self.disableFeedbackTask.writeData([not enable], autoStart=True)
        self.analogFeedback = enable
        print "Analog feedback now:", self.analogFeedback
        self.analogFeedbackChanged.emit(enable)
        
    def resetIntegrator(self):
        self.resetIntegratorTask.writeData([True], autoStart = True)
        time.sleep(0.2)
        self.resetIntegratorTask.writeData([False], autoStart = True)

    @property
    def quenched(self):
        return self._quenched

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
            self.dIdtTarget = -0.1 / 60 # Fast ramp down
        else:
            self.dIdtTarget = max(-self.dIdtMax, min(self.dIdtMax, dIdt))
        if self.analogFeedback:
            self.programMagnetVoltage(self.dIdtTarget * self.inductance)
        else:
            pass # In digital mode, the thread loop takes care of applying the new dIdt
            
        self.rampRateUpdated.emit(self.dIdtTarget)

    def log(self, t):
        fileName = 'MagnetControl2_%s.dat' % time.strftime('%Y%m%d')
        if not os.path.isfile(fileName):
            with open(fileName, 'a') as f:
                header = '#tUnix\tVfet\tIcoarse\tVmagnet\tIfine\tVps\tIps\tAnalogFb\n'
                f.write(header)
                
        text = '%.3f\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%d\n' % (t, self.fetOutputVoltage, self.currentCoarse, self.magnetVoltage, self.currentFine, self.Vps, self.Ips, self.analogFeedback)
        with open(fileName, 'a') as f:
            f.write(text)

    def diodeVoltageDrop(self, current):
        '''Calculate approximate the diode voltage drop for a given current.
        '''
        if current > 0.02:
            Vdiode = log(current/self.DIODE_I0+1.)/self.DIODE_A
        else: # At smaller currents, basically the entire voltage drop is across the diode
            Vdiode = 0.998 * self.fetOutputVoltage
        self.diodeVoltageUpdated.emit(Vdiode)
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

    def setOutputVoltage(self, Vnew):
        if Vnew >= self.OutputVoltageLimit:
            Vnew = self.OutputVoltageLimit
            self.supplyLimit = True
        elif Vnew <= 0:
            Vnew = 0.
            self.supplyLimit = True
        else:
            self.supplyLimit = False
        Vprog = Vnew / self.OutputVoltageControlGain
        self.outputVoltageControlTask.writeData([Vprog], autoStart = True)
        self.VoutputProgrammed = Vnew
        
    def sleepPrecise(self,tOld):
            tSleep = int(1E3*(self.interval-time.time()+tOld-0.010))
            if tSleep>0.010:
                self.msleep(tSleep)
            while(time.time()-tOld < self.interval):
                pass
            
    def query(self, item):
        return self.publisher.query(item)

    def run(self):
        self.stopRequested = False
        logger.info("Thread starting")
        try:
            self.setupDaqChannels()
            self.initialize()
            self.setupDaqTasks()
        except Exception, e:
            print "Exception:", e
            traceback.print_exception(*sys.exc_info())
            return
        while not self.stopRequested:
            try:
                self.controlLoop()
            except EmergencyException, e:
                print "Encountered emergency:", e
                self.emergencyShutDown()
                break
            except Exception, e:
                print "Exception:", e
                traceback.print_exception(*sys.exc_info())
                self.programMagnetVoltage(0)
                break
                
    def emergencyShutDown(self):
        self.setOutputVoltage(0)
        self.programMagnetVoltage(-0.06)
        print "Emergency shutdown underway"

    def analogFeedbackEnabled(self):
        '''Return True if the analog feedback mode is enabled.'''
        task = daq.DiTask('Check feedback mode')
        task.addChannel(self.diLineDisableFeedbackCheck)
        enabled = np.unique(task.readData(10))
        self.analogFeedback = not enabled
        if len(enabled) > 1:
            raise Exception('Got inconsistent response from DI line read.')
        else:
            return not enabled
            
    def determineFetVoltage(self):
        task = daq.AiTask('Check FET voltage')
        task.addChannel(self.fetOutputMonitorChannel)
        V = task.readData(100)
        Vmean = np.mean(V)
        std = np.std(V)
        
        print "Vs:", V
        if Vmean > 10.5:
            return np.nan
            #raise Exception('Invalid FET voltage reading')
        if std > 0.1:
            raise Exception('FET voltage reading unstable')
        return Vmean / self.FetVoltageMonitorGain

    def determineMagnetVoltage(self):
        task = daq.AiTask('Check magnet voltage')
        task.addChannel(self.magnetVoltageChannel)
        V = task.readData(100)
        
        Vmean = np.mean(V)
        std = np.std(V)
        
        print "Vs:", V
        if abs(Vmean) > 10.5:
            raise Exception('Invalid magnet voltage reading')
        if std > 0.1:
            raise Exception('Magnet voltage reading unstable')
        return Vmean / self.MagnetVoltageGain
            
    def initialize(self):
    
        self.analogFeedback = self.analogFeedbackEnabled()            
        self.analogFeedbackChanged.emit(self.analogFeedback)
        print "Analog feedback is enabled:", self.analogFeedback
        self.fetOutputVoltage = self.determineFetVoltage()
        print "FET voltage:", self.fetOutputVoltage
        self.magnetVoltage = self.determineMagnetVoltage()
        print "Magnet voltage:", self.magnetVoltage
        
        self.VoutputProgrammed = self.fetOutputVoltage
        
        ps = self.ps
        
        powerSupplyEnabled = ps.outputEnabled()         # Agilent on?
        if powerSupplyEnabled:
            print "Power supply already enabled, checking setpoints..."
            if ps.currentSetpoint() != self.ISupplyMax:
                raise Exception('Magnet supply is not programmed to the correct maximum current')
            Vprog = ps.voltageSetpoint()
            if np.isfinite(self.fetOutputVoltage) and Vprog < (self.fetOutputVoltage + self.SupplyDeltaMin):
                raise Exception('Power supply voltage (%.3f V) is insufficient to guarantee regulation (FET output voltage= %.3f V)' % (Vprog, self.fetOutputVoltage))
        else:
            print "Enabling power supply"
            ps.setCurrent(self.ISupplyMax)
            ps.setVoltage(2.5)
            ps.enableOutput()

    def setupDaqChannels(self):
        # AI
        device = 'USB6002_A'
        self.fetOutputMonitorChannel = daq.AiChannel('%s/ai0' % device, -10., +10.)
        self.currentChannelCoarse    = daq.AiChannel('%s/ai1' % device, -10., +10.)
        self.currentChannelFine      = daq.AiChannel('%s/ai2' % device, -10., +10.)
        self.magnetVoltageChannel    = daq.AiChannel('%s/ai3' % device, -10., +10.)                
        
        # Digital        
        self.doLineDisableFeedback      = daq.DoChannel('%s/port1/line3' % device)
        self.diLineDisableFeedbackCheck = daq.DiChannel('%s/port1/line0' % device)
        self.doLineResetIntegrator      = daq.DoChannel('%s/port1/line2' % device)
        
        # AO
        self.magnetVoltageControlChannel = daq.AoChannel('%s/ao0' % device, -3.4, +3.4)
        self.outputVoltageControlChannel = daq.AoChannel('%s/ao1' % device, 0, self.OutputVoltageLimit / self.OutputVoltageControlGain)        

        
    def setupDaqTasks(self):
        self.magnetVControlTask = daq.AoTask('Magnet voltage control task')
        self.magnetVControlTask.addChannel(self.magnetVoltageControlChannel)
        self.disableFeedbackTask = daq.DoTask('Feedback disable task')
        self.disableFeedbackTask.addChannel(self.doLineDisableFeedback)
        self.resetIntegratorTask = daq.DoTask('Reset control')
        self.resetIntegratorTask.addChannel(self.doLineResetIntegrator)
        self.outputVoltageControlTask = daq.AoTask('Supply voltage control task')
        self.outputVoltageControlTask.addChannel(self.outputVoltageControlChannel)

        timing = daq.Timing(rate=50000, samplesPerChannel=2000)
        timing.setSampleMode(timing.SampleMode.FINITE)
        
        aiTask = daq.AiTask('AI Task FET Output')
        aiTask.addChannel(self.fetOutputMonitorChannel)
        aiTask.configureTiming(timing)
        self.aiTaskFetOutput = aiTask
        
        aiTask = daq.AiTask('AI Task Current Coarse')
        aiTask.addChannel(self.currentChannelCoarse)
        aiTask.configureTiming(timing)
        self.aiTaskCurrentCoarse = aiTask
        
        aiTask = daq.AiTask('AI Task Current Fine')
        aiTask.addChannel(self.currentChannelFine)
        aiTask.configureTiming(timing)
        self.aiTaskCurrentFine = aiTask
        
        aiTask = daq.AiTask('AI Task Magnet Voltage')
        aiTask.addChannel(self.magnetVoltageChannel)
        aiTask.configureTiming(timing)
        self.aiTaskMagnetVoltage = aiTask
        

#        aiTask = daq.AiTask('AI Task')
#        aiTask.addChannel(self.fetOutputMonitorChannel)
#        aiTask.addChannel(self.currentChannelCoarse)        
#        aiTask.addChannel(self.currentChannelFine)
#        aiTask.addChannel(self.magnetVoltageChannel)
#        print "f max:", aiTask.maxSampleClockRate()
#        timing = daq.Timing(rate=2, samplesPerChannel = 10)
#        aiTask.configureTiming(timing) 
#        aiTask.start()
        self.aiTask = aiTask
        
    def readDaqTask(self, task):
        task.start()
        V = task.readData(self.samplesPerChannel)[0]
        task.stop()
        return np.mean(V[100:]), np.std(V[100:])
        
    def readDaqData(self):
#        data = self.aiTask.readData(samplesPerChannel=1)
#        Vs = np.mean(data, axis=1, keepdims=True)
        V, Vstd = self.readDaqTask(self.aiTaskFetOutput)
        #print "FET output readout:", V, "V"
        if V > 10.5:
            V = np.nan
        self.fetOutputVoltage = V / self.FetVoltageMonitorGain
        
        V, Vstd = self.readDaqTask(self.aiTaskCurrentCoarse)
        #print "Coarse current readout:", V, "V"
        if V > 10:
            V = np.nan
        elif V < -0.2:
            V = np.nan
        self.currentCoarse = V / self.CurrentCoarseResistance
        
        V, Vstd = self.readDaqTask(self.aiTaskCurrentFine)
        #print "Fine current readout:", V, "V"
        if V > 10.0:
            V = np.nan
        elif V < -0.1:
            raise Exception('Fine current readback is negative (average %f V)!' % V)
        self.currentFine = V / self.CurrentFineResistance
        self.magnetVoltageStd = Vstd / np.abs(self.CurrentFineResistance) # todo : Remove this hack!

        
        V, Vstd = self.readDaqTask(self.aiTaskMagnetVoltage)
        #print "Magnet voltage readout:", V, "V"
        if abs(V) > 10:
            V = np.nan
        self.magnetVoltage = V / self.MagnetVoltageGain
        
    def controlLoop(self):
        currentHistory = History(maxAge=3)
        while not self.stopRequested:
            # First, take all measurements
            t = time.time()
            self.readDaqData()
            
            if np.isnan(self.currentCoarse):
                raise EmergencyException("Invalid value for coarse current readout.")

            self.Ips = self.ps.measureCurrent()
            self.Vps = self.ps.measureVoltage()
            
            if abs(self.Ips - self.currentCoarse) > 0.3:
                raise EmergencyException("Current read-outs do not match!")
            
            if np.isfinite(self.currentFine) and abs(self.currentFine - self.currentCoarse) > 0.15:
                raise EmergencyException("Fine and coarse current read-outs do not match!")
                
            self.measurementAvailable.emit(t, self.Ips, self.Vps, self.fetOutputVoltage, self.magnetVoltage, self.currentCoarse, self.currentFine, self.magnetVoltageStd)

            self.publisher.publish('Isupply', self.Ips)
            self.publisher.publish('Vsupply', self.fetOutputVoltage)
            self.publisher.publish('Vmagnet', self.magnetVoltage)
            self.publisher.publish('Imagnet', self.currentCoarse)
            #self.publisher.publish('dIdt', Vmagnet/self.inductance)

            # Log all measurements
            self.log(t)
            
            I = self.currentCoarse
            if I < 0:
                I = 0
                
            # Check that Vmagnet matches L * dI/dt
            currentHistory.append(t, I)
            dIdt = currentHistory.dydt()
            if np.isnan(self.magnetVoltage): # If the magnet voltage is outside the measurement range, use an estimate
                self.magnetVoltage = dIdt * self.inductance
            Vdiode = self.diodeVoltageDrop(I)
            V_R = self.fetOutputVoltage - self.magnetVoltage - Vdiode
            self.resistiveVoltageUpdated.emit(V_R)
            if I > 0.05:
                R = V_R / I
            else:
                R = float('nan')
            self.resistanceUpdated.emit(R)
            if self.currentCoarse > 1:
                if R > self.Rmax:
                    self.triggerQuench()
                    
            if self.analogFeedback:  # Analog feedback mode
                if I >= self.IOutputMax and self.dIdtTarget > 0:
                    self.programMagnetVoltage(0)
                self.setOutputVoltage(self.fetOutputVoltage) # Track the output so we can switch the feedback loop off at any time
            else:  # Digital feedback mode
                #Compute new parameters
                VmagnetGoal = self.inductance*self.dIdtTarget
                self.programMagnetVoltage(max(min(VmagnetGoal, self.MagnetVoltageLimit), -self.MagnetVoltageLimit)) # Track the magnet voltage so we can switch from digital to analog feedback
    
                if I >= self.IOutputMax and self.dIdtTarget > 0:
                    VmagnetGoal = 0
    
                errorTerm = (VmagnetGoal-self.magnetVoltage)
                print "Digital feedback - VmagnetGoal:", VmagnetGoal, "Magnet voltage:", self.magnetVoltage
                print "Old FET output voltage:", self.VoutputProgrammed
                Vnew = max(self.VoutputProgrammed + errorTerm, 0)
                print "Vnew:", Vnew
                self.setOutputVoltage(Vnew)
                
            self.updatePowerSupplyVoltage()
            
            self.sleepPrecise(t)
            
    def updatePowerSupplyVoltage(self):
        delta = self.Vps - self.fetOutputVoltage
        if delta < self.SupplyDeltaMin or delta > self.SupplyDeltaMax:
            newVps = self.fetOutputVoltage + 0.5*(self.SupplyDeltaMin+self.SupplyDeltaMax)
            newVps = min(max(1.5, newVps), self.VSupplyMax)
            print "Updating power supply voltage:", newVps
            self.ps.setVoltage(newVps)

def magnetSupplyTest():
    import sys
    
    from Visa.Agilent6641A import Agilent6641A

    ps = Agilent6641A('GPIB0::5')
    if not '6641A' in ps.visaId():
        raise Exception('Agilent 6641A not found!')

    print "Starting MagnetSupply"

    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('ADR3 Magnet Control')

    magnetThread = MagnetControlThread(ps)
    ps.currentSetpoint()
#    QTimer.singleShot(2000, magnetThread.start)
    magnetThread.run()
    try:
        app.exec_()
    except:
        print "Exiting"


if __name__ == '__main__':
    magnetSupplyTest()

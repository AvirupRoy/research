# -*- coding: utf-8 -*-
"""
Classes for ADR magnet control with abstraction to support generic power supply\
Version 3 runs Avirup's new hardware
Branched on Wed May 16 2018
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
@author: Avirup Roy <aroy22@wisc.edu>
"""

from __future__ import division

import logging
logger = logging.getLogger(__name__)

from PyQt4.QtCore import QThread, pyqtSignal, QSettings

from math import log
import DAQ.PyDaqMx as daq
import numpy as np
import time
import os.path
import sys
import traceback

from Zmq.Zmq import ZmqPublisher
from Zmq.Ports import PubSub
from Utility.Math import Integrator,History

class ShutdownException(Exception):
    pass

mAperMin = 1E-3/60

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
    MagnetVoltageGainLow  = 21.0 # Gain of composite instrumentation amplifier U8/U9/U16, determined by resistors R35=2k0, R34=20k0, R36=20k0
    MagnetVoltageGainHigh = MagnetVoltageGainLow * 21.0  # Above * gain of R45=20k0 / R42=1k0
    
    MagnetVoltageLimit = min(1.0, 9.0/MagnetVoltageGainLow)
    
    OutputVoltageControlGain = 0.5 # Resistive divider formed by R20(5k1)/C9(=5k1)
    
    Rsense = 20E-3 # Size of the 4-wire shunt resistor
    
    CurrentCoarseResistance = Rsense * 50.5 # Gain of U17, determined by R39=200Ohm
    CurrentFineResistance = CurrentCoarseResistance * 21.0 # Gain of R48=20k0/R49=1k0
    
    CurrentFineMaxReliable = 0.9 * 10./CurrentFineResistance # Above this current, don't consider it a good reading
    
    FetVoltageMonitorGain = 2.9412 # about 2.9412V/V gain of instrumentation amplifier AD8421 U15 set by R52||R53=5k1

    OutputVoltageLimit = 10./FetVoltageMonitorGain # This is the maximum we can read-out because of the 3x gain
    
    SupplyDeltaMin = 1.3 + 0.2
    SupplyDeltaMax = 1.6 + 0.2
    
    SupplyDeltaMin = 1.4# + 0.2
    SupplyDeltaMax = 1.5
    SupplyVoltageForLowCurrent = 3.5 # At low currents (when we are regulating), we keep the supply voltage fixed
    
    DIODE_I0 = 5.8214E-11 # units: A , used to estimate the voltage drop across the magnet
    DIODE_A  = 30.6092     # 1/V (=q_q/(k_B*T)) , used to estimate the voltage drop across the magnet
    
    Inductance = 30.0 # 30H
    RampRateLimitLowGain = MagnetVoltageLimit / Inductance
    RampRateLimitHighGain = (9.0/MagnetVoltageGainHigh) / Inductance

    #analogFeedbackChanged = pyqtSignal(bool)    
    controlModeChanged = pyqtSignal(str, float) 
    '''Signal indicates which control mode is active and the maximum dIdt in A/s'''
    outputVoltageCommanded = pyqtSignal(float)
    shutdownForced = pyqtSignal()
    diodeVoltageUpdated = pyqtSignal(float)
    resistiveVoltageUpdated = pyqtSignal(float)
    resistanceUpdated = pyqtSignal(float)
    rampRateUpdated = pyqtSignal(float)
    measurementAvailable = pyqtSignal(float, float, float, float, float, float, float, float, float, float)
    rawWaveformAvailable = pyqtSignal(str, np.ndarray)
    dIdtIntegralAvailable = pyqtSignal(float)
    feedbackGainChanged = pyqtSignal(str)
    message = pyqtSignal(str, str)

    def __init__(self, powerSupply, parent=None):
        QThread.__init__(self, parent)
        self.buffer = ''
        self.ps = powerSupply
        #print "Power supply", self.ps
        self.dIdtMax = 1000. * mAperMin # max rate: 1 A/min
        self.dIdtTarget = 0.
        self.Rmax = 1.0 # Maximum R for quench detection
        self.VSupplyMax = self.OutputVoltageLimit+self.SupplyDeltaMax # Maximum supply voltage
        #self.ISupplyLimit = 2.5 # 8.9 Maximum current permitted for supply
        #self.IOutputMax = 2. # 8.5 # Maximum current for magnet
        self.ISupplyLimit = 8.8 # 8.9 Maximum current permitted for supply
        self.IOutputMax = 8.5 # 8.5 # Maximum current for magnet
        self._forcedShutdown = False
        try:
            self.publisher = ZmqPublisher('MagnetControlThread', PubSub.MagnetControl, self) # TODO Temporarily replaced
        except Exception, e:
            self.warn('Unable to start ZMQ publisher: %s' % e)
            self.publisher = None
                    
        self.sampleRate = 50000
        self.discardSamples = 200
        self.samplesPerChannel = 10000 + self.discardSamples # 2500=50000/60*3 -> exact multiple of 60 Hz
        self.interval = 4*(self.samplesPerChannel/self.sampleRate+0.025) # Update interval
        self.VmagnetProgrammed = 0
        self.VoutputProgrammed = 0
        self.dIdtError = 0
        self.dIdtCorrectionEnabled = False
        self.dIdtErrorIntegrator = Integrator(T=30, dtMax=2)
        self.magnetVoltageGain = None
        

#    def __del__(self):
#        print "Deleting thread"
#        del self.publisher
#        super(self, MagnetControlThread).__del__()

    def setFetVsdGoal(self, Vsd, VsdTolerance):
        assert VsdTolerance > 0
        assert Vsd > 1
        assert VsdTolerance < Vsd
        self.SupplyDeltaMin = Vsd - 0.5*VsdTolerance
        self.SupplyDeltaMax = Vsd + 0.5*VsdTolerance
        
    def enableIdtCorrection(self, enabled = True):
        self.dIdtCorrectionEnabled = enabled
        
    def resetdIdtIntegrator(self):
        self.dIdtErrorIntegrator.reset()
        self.dIdtIntegralAvailable.emit(0)
        
    def outputVoltage(self):
        return self.VoutputProgrammed
                
    def programMagnetVoltage(self, V):
        '''Command a new magnet voltage, automatically changing gain on feedback loop as needed (with hysteresis).'''
        V = max(min(self.MagnetVoltageLimit, V),-self.MagnetVoltageLimit)
        mvGainThreshold = 10./self.MagnetVoltageGainHigh
        if abs(V) > 0.9 * mvGainThreshold:
            Vprog = -V * self.MagnetVoltageGainLow
            self.magnetVControlTask.writeData([Vprog], autoStart = True)
            self._setMagnetVoltageGain(self.MagnetVoltageGainLow)
            # Switch to low gain range if needed
        elif abs(V) < 0.8 * mvGainThreshold:
            self._setMagnetVoltageGain(self.MagnetVoltageGainHigh)
            Vprog = -V * self.MagnetVoltageGainHigh
            self.magnetVControlTask.writeData([Vprog], autoStart = True)
        else: # Somewhere between hysteresis points
            Vprog = -V * self.magnetVoltageGain
            self.magnetVControlTask.writeData([Vprog], autoStart = True)
        self.VmagnetProgrammed = V
        
#    def setFeedbackGain(self, gain):
        
        
    def _setMagnetVoltageGain(self, targetGain):
        if self.magnetVoltageGain == targetGain:
            return
        if targetGain == self.MagnetVoltageGainHigh:
            self.analogLoopGainTask.writeData([False, True], autoStart=True)
            self.magnetVoltageGain = targetGain
            self.feedbackGainChanged.emit('high')
            self.info('Analog feedback on high gain.')
        elif targetGain == self.MagnetVoltageGainLow:
            self.analogLoopGainTask.writeData([True, False], autoStart=True)
            self.magnetVoltageGain = targetGain
            self.feedbackGainChanged.emit('low')
            self.info('Analog feedback on low gain.')
        else:
            self.warn('Unsupported magnet voltage gain')
        
    def setControlMode(self, mode):
        mode = str(mode)
        if mode == 'Analog':
            self._enableAnalogFeedback(True)
            limit = 0.9*(self.MagnetVoltageLimit / self.Inductance)
        elif mode == 'Digital':
            self._enableAnalogFeedback(False)
            limit = 0.5 / self.Inductance
        elif mode == 'Manual':
            self._enableAnalogFeedback(False)
            self.requestedOutputVoltage = self.VoutputProgrammed
            limit = 0
        else:
            raise Exception('Unknown control mode: %s' % mode)
        self.controlModeChanged.emit(mode, limit)
        self.controlMode = mode

    def _enableAnalogFeedback(self,enable = True):
        self.disableFeedbackTask.writeData([not enable], autoStart=True)
        if enable:
            self.info('Analog feedback enabled.')
        else:
            self.info('Anlog feedback disabled.')

    @property
    def forcedShutdown(self):
        return self._forcedShutdown

    @property
    def inductance(self):
        return self._L

    @inductance.setter
    def inductance(self, L):
        assert(L > 0)
        self._L = L

    def setRampRate(self, dIdt):
        '''Specify desired ramp rate in A/s.'''
        if self.forcedShutdown:
            self.dIdtTarget = -600*mAperMin # Fast ramp down
        else:
            self.dIdtTarget = max(-self.dIdtMax, min(self.dIdtMax, dIdt))
            
        # Only in analog feedback mode without error correction will we do the update here (asynchronous).
        # Otherwise the update will happen in the control loop
        if self.controlMode == 'Analog' and not self.dIdtCorrectionEnabled:
            V = self.dIdtTarget * self.Inductance
            self.programMagnetVoltage(V)

        self.rampRateUpdated.emit(self.dIdtTarget)

    def log(self, t):
        ControlModeCode = {'Analog':0, 'Digital': 1, 'Manual': 2}
        code = ControlModeCode[self.controlMode] 
        text = '%.3f\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%d\n' % (t, self.fetOutputVoltage, self.currentCoarse, self.magnetVoltage, self.currentFine, self.Vps, self.Ips, self.dIdtTarget, self.VmagnetProgrammed, self.VoutputProgrammed, code)
        self.buffer += text
        if len(self.buffer) >= 2048:
            self.flushBuffer()
            
    def flushBuffer(self):
        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))
        fileName = os.path.join(path,'MagnetControl3_%s.dat' % time.strftime('%Y%m%d'))        
        try:
            if not os.path.isfile(fileName):
                self.buffer = '#tUnix\tVfet\tIcoarse\tVmagnet\tIfine\tVps\tIps\tdIdtTarget\tVmProg\tVoutProg\tAnalogFb\n' + self.buffer
            with open(fileName, 'a') as f:
                f.write(self.buffer)
            self.buffer = ''
        except Exception, e:
            self.warn('Writing log file failed: %s' % e)

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

    def forceShutdown(self):
        self.warn('Forced shutdown')
        self._shutdownForced = True
        #self.setRampRate(0)
        #self.setControlMode('Manual')
        #self.shutdownForced.emit()
        
    def commandOutputVoltage(self, V):
        if self.controlMode == 'Manual':
            self.requestedOutputVoltage = V
        else:
            self.warn('You may request a new output voltage only in manual mode')

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
        self.outputVoltageCommanded.emit(Vnew)
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
            self.setupDaqTasks()
            self.initialize()
        except Exception, e:
            self.fatalError('Encountered exception:%s' % e)
            traceback.print_exception(*sys.exc_info())
            return
            
        while not self.stopRequested:
            try:
                self.controlLoop()
            except ShutdownException, e:
                self.warn(e)
                self.emergencyShutDown()
                break
            except Exception, e:
                self.fatalError('Encountered exception: %s' % e)
                traceback.print_exception(*sys.exc_info())
                self.programMagnetVoltage(0)
                break
        self.flushBuffer()
                       
    def fatalError(self, message):
        self.message.emit('error', message)
        
    def warn(self, message):
        self.message.emit('warning', message)
        
    def info(self, message):
        self.message.emit('info', message)

    def analogFeedbackEnabled(self):
        '''Return True if the analog feedback mode is enabled.'''
        task = daq.DiTask('Check feedback mode')
        task.addChannel(self.diLineDisableFeedbackCheck)
        enabled = np.unique(task.readData(10))
        if len(enabled) > 1:
            self.fatalError('Got inconsistent response from DI line read. Please check/fix wiring')
            return
        else:
            return not enabled
                        
    def initialize(self):
        analogFeedback = self.analogFeedbackEnabled()            
        if analogFeedback:
            self.info('Analog feedback enabled')
            mode = 'Analog'
        else:
            self.info('Analog feedback disabled')
            mode = 'Digital' # or "Manual"
        self.setControlMode(mode)

        self._setMagnetVoltageGain(self.MagnetVoltageGainHigh)
        
        self.readDaqData()
            
        self.info('Found magnet with I=%.3f A, Vm=%.4f V'  % (self.currentCoarse, self.magnetVoltage))
        self.info('Found supply with Vfet=%.3f V' % self.fetOutputVoltage)
        self.VoutputProgrammed = self.fetOutputVoltage
        
        ps = self.ps
        
        powerSupplyEnabled = ps.outputEnabled()         # Agilent on?
        if powerSupplyEnabled:
            self.info("Power supply already enabled, checking setpoints...")
            Isupply = ps.currentSetpoint()
            if Isupply < self.ISupplyLimit:
                self.ISupplyLimit = Isupply-0.2
                self.IOutputMax = self.ISupplyLimit - 0.2
                self.warn('Magnet supply current limit (%.3f A) is below the expected maximum current. Adjusting internal current limit to %.3f A' % (Isupply, self.ISupplyLimit))
            elif Isupply > self.ISupplyLimit:
                self.warn('Magnet supply current limit (%.3f A) is above the expected maximum current.' % Isupply) 
                if self.currentCoarse < self.ISupplyLimit-0.2:
                    ps.setCurrent(self.ISupplyLimit)
                    self.info('Supply limit adjusted to (%.3f A)' % self.ISupplyLimit)
                else:
                    self.warn('Magnet current appears to be above supply limit. Something is seriously wrong. Bailing out.')
                
            Vprog = ps.voltageSetpoint()
            if np.isfinite(self.fetOutputVoltage) and Vprog < (self.fetOutputVoltage + self.SupplyDeltaMin):
                self.warn('Power supply voltage (%.3f V) is insufficient to guarantee regulation (FET output voltage= %.3f V)' % (Vprog, self.fetOutputVoltage))
        else:
            V = 0.5*(self.SupplyDeltaMin+self.SupplyDeltaMax)
            ps.setCurrent(self.ISupplyLimit)
            ps.setVoltage(V)
            ps.enableOutput()
            self.info("Enabled power supply with V=%.3f V and I=%.3f A" % (V, self.ISupplyLimit))
        self.rampRateUpdated.emit(self.magnetVoltage*self.Inductance)

    def setupDaqChannels(self):
        device = 'USB6002_B'

        # AI
        terminalConfig = daq.AiChannel.TerminalConfiguration.DIFF
        self.fetOutputMonitorChannel = daq.AiChannel('%s/ai0' % device, -10., +10., terminalConfig=terminalConfig)
        self.magnetVoltageChannel    = daq.AiChannel('%s/ai1' % device, -10., +10., terminalConfig=terminalConfig)
        self.currentChannelFine      = daq.AiChannel('%s/ai2' % device, -10., +10., terminalConfig=terminalConfig)
        self.currentChannelCoarse    = daq.AiChannel('%s/ai3' % device, -10., +10., terminalConfig=terminalConfig)

        # AO
        self.magnetVoltageControlChannel = daq.AoChannel('%s/ao0' % device, -10., +10.) # TODO Figure out proper limits
        self.outputVoltageControlChannel = daq.AoChannel('%s/ao1' % device, 0, self.OutputVoltageLimit / self.OutputVoltageControlGain)
        
        # Digital        
        self.doLineDisableFeedback      = daq.DoChannel('%s/port1/line0' % device) # HIGH=Disable, LOW=Enable
        self.diLineDisableFeedbackCheck = daq.DiChannel('%s/port2/line0' % device) # Readback for DisableFeedback
        self.doLineMagnetVoltageLoopGain = daq.DoChannel('%s/port1/line1' % device) # HIGH=21x, LOW=441x
        self.doLineMagnetVoltageReadoutGain = daq.DoChannel('%s/port1/line2' % device) # HIGH=441x, LOW=21x # Might be backwards
        
    def setupDaqTasks(self):
        self.magnetVControlTask = daq.AoTask('Magnet voltage control task')
        self.magnetVControlTask.addChannel(self.magnetVoltageControlChannel)
        
        self.disableFeedbackTask = daq.DoTask('Feedback disable task')
        self.disableFeedbackTask.addChannel(self.doLineDisableFeedback)
        
        self.analogLoopGainTask = daq.DoTask('Reset control')
        self.analogLoopGainTask.addChannel(self.doLineMagnetVoltageLoopGain)
        self.analogLoopGainTask.addChannel(self.doLineMagnetVoltageReadoutGain)
        
        self.outputVoltageControlTask = daq.AoTask('Supply voltage control task')
        self.outputVoltageControlTask.addChannel(self.outputVoltageControlChannel)

        timing = daq.Timing(rate=50000, samplesPerChannel=self.samplesPerChannel)
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
        
    def readDaqTask(self, task, item):
        for i in range(3): # 3 attempts
            try:
                task.start()
                V = task.readData(self.samplesPerChannel)[0]
                task.stop()
                self.rawWaveformAvailable.emit(item, V)
                return np.mean(V[self.discardSamples:]), np.std(V[self.discardSamples:])
            except daq.Error as e:
                self.warn('Exception in readDaqTask: %s' % str(e))
                self.sleep(1) # Wait 1s, then try again
        raise Exception('Unable to read DAQ after 3 attempts.')
        
    def readDaqData(self):
        '''Read and convert FET output voltage, magnet voltage, current coarse and fine readouts.'''
        V, Vstd = self.readDaqTask(self.aiTaskFetOutput, 'FET output')
        if V > 10.5:
            V = np.nan
        self.fetOutputVoltage = V / self.FetVoltageMonitorGain
        
        V, Vstd = self.readDaqTask(self.aiTaskCurrentCoarse, 'Current coarse')
        if V > 10:
            V = np.nan
        elif V < -0.2:
            V = np.nan
        self.currentCoarse = V / self.CurrentCoarseResistance
        
        V, Vstd = self.readDaqTask(self.aiTaskCurrentFine, 'Current fine')
        if V > 10.0:
            V = np.nan
        elif V < -0.1:
            self.warn('Fine current readback is negative (average %.3f V)!' % V)
            V = np.nan
        self.currentFine = V / self.CurrentFineResistance

        V, Vstd = self.readDaqTask(self.aiTaskMagnetVoltage, 'Magnet voltage')
        if abs(V) > 10:
            V = np.nan
        self.magnetVoltage = V / self.magnetVoltageGain
        
    def controlLoop(self):
        currentHistory = History(maxAge=10)
        #currentMismatchCount = 0

        while not self.stopRequested:
            # First, take all measurements
            t = time.time()
            self.readDaqData()
            
            if np.isnan(self.currentCoarse):
                self.warn('Invalid value for coarse current readout.')
                self.forceShutdown()

            self.Ips = self.ps.measureCurrent()
            self.Vps = self.ps.measureVoltage()
            
#            if abs(self.Ips - self.currentCoarse) > 0.3:
#                self.warn('Supply (%.3f A) and coarse (%.3f A) current read-outs do not match.' % (self.Ips, self.currentCoarse))
#                self.forceShutdown()
            
#            if self.currentFine <= self.CurrentFineMaxReliable and abs(self.currentFine - self.currentCoarse) > 0.05:
#                self.warn('Fine (%.3f A) and coarse (%.3f A) current read-outs do not match.' % (self.currentFine, self.currentCoarse))
#                currentMismatchCount += 1
#                if currentMismatchCount > 3:
#                    self.forceShutdown()
#            else:
#                currentMismatchCount = 0

            self.log(t)            # Log all measurements
           
            if np.isfinite(self.currentFine): # Figure out which current measurement to trust
                I = self.currentFine
            elif np.isfinite(self.currentCoarse):
                I = self.currentCoarse
            else:
                I = self.Ips

            if I < 0:
                I = 0

            currentHistory.append(t, I) # Compute dIdt from history
            self.dIdt = currentHistory.dydt()
            
            # Publish current measurements to the world
            self.measurementAvailable.emit(t, self.Ips, self.Vps, self.fetOutputVoltage, self.magnetVoltage, self.currentCoarse, self.currentFine, self.dIdt, self.VoutputProgrammed, self.VmagnetProgrammed)
            if self.publisher:
                self.publisher.publishDict('AdrMagnet', {'t':t,
                                                         'Isupply':self.Ips,
                                                         'Vfet': self.fetOutputVoltage,
                                                         'Vmagnet':self.magnetVoltage,
                                                         'ImagnetCoarse':self.currentCoarse,
                                                         'ImagnetFine':self.currentFine})
                self.publisher.publish('Isupply', self.Ips)
                self.publisher.publish('Vsupply', self.fetOutputVoltage)
                self.publisher.publish('Vmagnet', self.magnetVoltage)
                self.publisher.publish('Imagnet', self.currentCoarse)
                self.publisher.publish('ImagnetFine', self.currentFine)
                self.publisher.publish('dIdt',self.dIdt)
            
            # Estimate resistive voltage drop across magnet to check for quench
            Vdiode = self.diodeVoltageDrop(I)
            if np.isfinite(self.fetOutputVoltage) and np.isfinite(self.magnetVoltage):
                V_R = self.fetOutputVoltage - self.magnetVoltage - Vdiode
                self.resistiveVoltageUpdated.emit(V_R)
                if I > 0.05:
                    R = V_R / I
                else:
                    R = float('nan')
                self.resistanceUpdated.emit(R)
                if self.currentCoarse > 1.: # Check for possible quench
                    if R > self.Rmax:
                        self.warn('Estimated wiring resistance (%.4f Ohm) exceeded threshold (%.4f Ohm). Assuming quench.' % (R, self.Rmax))
                        self.forceShutdown()

            if np.isnan(self.magnetVoltage): # If the magnet voltage is outside the measurement range, use an estimate
                self.magnetVoltage = self.dIdt * self.Inductance
                    
            # If ramp rate is small, accumulate dIdt error integral
            dIdtMax = 10.*mAperMin
            if abs(self.dIdtTarget) < dIdtMax and abs(self.dIdt) < dIdtMax:
                err = self.dIdtTarget-self.dIdt
                if self.dIdtErrorIntegrator.lastTime < t-1800:
                    self.dIdtErrorIntegrator.reset()
                dIdtError = self.dIdtErrorIntegrator.append(t, err)
                self.dIdtIntegralAvailable.emit(dIdtError)
                if abs(dIdtError) < dIdtMax:
                    self.dIdtError = dIdtError
                else:
                    self.dIdtError = 0

            # Check current limits
            if I >= self.IOutputMax:
                if I >= self.IOutputMax+0.2:
                    self.warn('Maximum output current significantly exceeded.')
                    self.forceShutdown()
                elif self.dIdtTarget > 0:
                    self.info('Maximum current reached, halting ramp.')
                    self.setRampRate(0)
                    
            if self.controlMode == 'Analog':  # Analog feedback mode
                V = self.dIdtTarget * self.Inductance
                if self.dIdtCorrectionEnabled: # Only when error correction is enabled the magnet voltage should get updated here.
                    V += self.dIdtError * self.Inductance
                    self.programMagnetVoltage(V)
                self.setOutputVoltage(self.fetOutputVoltage) # Track the output so we can switch the feedback loop off at any time
            elif self.controlMode == 'Digital':  # Digital feedback mode
                if self.dIdtCorrectionEnabled:
                    VmagnetGoal = self.Inductance*(self.dIdtTarget+self.dIdtError)
                else:
                    VmagnetGoal = self.Inductance*self.dIdtTarget
                self.programMagnetVoltage(VmagnetGoal) # Track the magnet voltage so we can switch from digital to analog feedback
                errorTerm = (VmagnetGoal-self.magnetVoltage)
                Vnew = max(self.VoutputProgrammed + errorTerm, 0)
                self.setOutputVoltage(Vnew)
            elif self.controlMode == 'Manual':
                self.setOutputVoltage(self.requestedOutputVoltage)
                pass
            
            self.updatePowerSupplyVoltage()
            self.sleepPrecise(t)
            
    def updatePowerSupplyVoltage(self):
        delta = self.Vps - self.fetOutputVoltage
#        if self.Ips > 1.5: # For high currents, try to keep FET Vds small to minimize power dissipation
        if delta < self.SupplyDeltaMin or delta > self.SupplyDeltaMax:
            newVps = self.fetOutputVoltage + 0.5*(self.SupplyDeltaMin+self.SupplyDeltaMax)
            newVps = min(max(1.5, newVps), self.VSupplyMax)
            self.ps.setVoltage(newVps)
#        else: # At low currents, keep supply voltage fixed to eliminate potential disturbances from step changes in Vds
#            if self.Vps != self.SupplyVoltageForLowCurrent:
#                self.ps.setVoltage(self.SupplyVoltageForLowCurrent)

def magnetSupplyTest():
   
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

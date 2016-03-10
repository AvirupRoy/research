# -*- coding: utf-8 -*-
"""
Classes for ADR magnet control with abstraction to support generic power supply
Created on Wed May 20 17:59:13 2015
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

import logging
logger = logging.getLogger(__name__)

from PyQt4.QtCore import QThread, pyqtSignal

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
    shutdownForced = pyqtSignal()
    diodeVoltageUpdated = pyqtSignal(float)
    resistiveVoltageUpdated = pyqtSignal(float)
    resistanceUpdated = pyqtSignal(float)
    rampRateUpdated = pyqtSignal(float)
    measurementAvailable = pyqtSignal(float, float, float, float, float, float, float, float, float, float)
    dIdtIntegralAvailable = pyqtSignal(float)
    message = pyqtSignal(str, str)

    def __init__(self, powerSupply, parent=None):
        QThread.__init__(self, parent)
        self.ps = powerSupply
        print "Power supply", self.ps
        self.dIdtMax = 1000. * mAperMin # max rate: 1 A/min
        self.dIdtTarget = 0.
        self.Rsense = 0.02 # 20mOhm sense resistor
        self.Rmax = 0.6 # Maximum R for quench detection
        self.inductance = 30.0 # 30 Henry
        self.VSupplyMax = 4.7 # Maximum supply voltage
        self.ISupplyLimit = 8.9 # 8.9 # Maximum current permitted
        self.IOutputMax = 8.5 # 8.5 # Maximum current permitted
        self._forcedShutdown = False
        self.publisher = ZmqPublisher('MagnetControlThread', PubSub.MagnetControl, self)
        self.sampleRate = 50000
        self.discardSamples = 200
        self.samplesPerChannel = 5000 + self.discardSamples # 2500=50000/60*3 -> exact multiple of 60 Hz
        self.interval = 4*(self.samplesPerChannel/self.sampleRate+0.025) # Update interval
        self.VmagnetProgrammed = 0
        self.VoutputProgrammed = 0
        self.dIdtError = 0
        self.dIdtCorrectionEnabled = False

#    def __del__(self):
#        print "Deleting thread"
#        del self.publisher
#        super(self, MagnetControlThread).__del__()
        
    def enableIdtCorrection(self, enabled = True):
        self.dIdtCorrectionEnabled = enabled
                
    def programMagnetVoltage(self, V):
        V = max(min(self.MagnetVoltageLimit, V),-self.MagnetVoltageLimit)
        Vprog = -V * self.MagnetVoltageGain
        self.magnetVControlTask.writeData([Vprog], autoStart = True)
        self.VmagnetProgrammed = V

    def enableMagnetVoltageControl(self,enable = True):
        self.disableFeedbackTask.writeData([not enable], autoStart=True)
        self.analogFeedback = enable
        if enable:
            self.info('Analog feedback enabled.')
        else:
            self.info('Digital feedback enabled.')
        self.analogFeedbackChanged.emit(enable)
        
    def resetIntegrator(self):
        self.resetIntegratorTask.writeData([True], autoStart = True)
        time.sleep(0.2)
        self.resetIntegratorTask.writeData([False], autoStart = True)

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
        # The actual update happens inside the control loop
        self.rampRateUpdated.emit(self.dIdtTarget)

    def log(self, t):
        fileName = 'MagnetControl2_%s.dat' % time.strftime('%Y%m%d')
        if not os.path.isfile(fileName):
            with open(fileName, 'a') as f:
                header = '#tUnix\tVfet\tIcoarse\tVmagnet\tIfine\tVps\tIps\tdIdtTarget\tVmProg\tVoutProg\tAnalogFb\n'
                f.write(header)
                
        text = '%.3f\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%.5g\t%d\n' % (t, self.fetOutputVoltage, self.currentCoarse, self.magnetVoltage, self.currentFine, self.Vps, self.Ips, self.dIdtTarget, self.VmagnetProgrammed, self.VoutputProgrammed, self.analogFeedback)
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

    def forceShutdown(self):
        self.warn('Forced shutdown')
        self._shutdownForced = True
        self.setRampRate(0)
        self.enableMagnetVoltageControl(False)
        self.shutdownForced.emit()

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
            self.setupDaqTasks()
            self.initialize()
        except Exception, e:
            print "Exception:", e
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
                       
    def fatalError(self, message):
        self.message.emit('error', message)
        raise Exception(message)
        
    def warn(self, message):
        self.message.emit('warning', message)
        
    def info(self, message):
        self.message.emit('info', message)

    def analogFeedbackEnabled(self):
        '''Return True if the analog feedback mode is enabled.'''
        task = daq.DiTask('Check feedback mode')
        task.addChannel(self.diLineDisableFeedbackCheck)
        enabled = np.unique(task.readData(10))
        self.analogFeedback = not enabled
        if len(enabled) > 1:
            self.fatalError('Got inconsistent response from DI line read. Please check/fix wiring')
        else:
            return not enabled
                        
    def initialize(self):
        self.analogFeedback = self.analogFeedbackEnabled()            
        if self.analogFeedback:
            self.info('Analog feedback enabled')
        else:
            self.info('Anlog feedback disabled')
        self.analogFeedbackChanged.emit(self.analogFeedback)
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
                    ps.setCurrentSetpoint(self.ISupplyLimit)
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
            self.info("Enabled power supply with V=%f V and I=%f A" % (V, self.ISupplyLimit))
        self.rampRateUpdated.emit(self.magnetVoltage*self.inductance)

    def setupDaqChannels(self):
        # AI
        device = 'USB6002_A'
        terminalConfig = daq.AiChannel.TerminalConfiguration.DIFF
        self.fetOutputMonitorChannel = daq.AiChannel('%s/ai0' % device, -10., +10., terminalConfig=terminalConfig)
        self.currentChannelCoarse    = daq.AiChannel('%s/ai1' % device, -10., +10., terminalConfig=terminalConfig)
        self.currentChannelFine      = daq.AiChannel('%s/ai2' % device, -10., +10., terminalConfig=terminalConfig)
        self.magnetVoltageChannel    = daq.AiChannel('%s/ai3' % device, -10., +10., terminalConfig=terminalConfig)
        
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
        
    def readDaqTask(self, task):
        task.start()
        V = task.readData(self.samplesPerChannel)[0]
        task.stop()
        return np.mean(V[self.discardSamples:]), np.std(V[self.discardSamples:])
        
    def readDaqData(self):
        '''Read and convert FET output voltage, magnet voltage, current coarse and fine readouts.'''
        V, Vstd = self.readDaqTask(self.aiTaskFetOutput)
        if V > 10.5:
            V = np.nan
        self.fetOutputVoltage = V / self.FetVoltageMonitorGain
        
        V, Vstd = self.readDaqTask(self.aiTaskCurrentCoarse)
        if V > 10:
            V = np.nan
        elif V < -0.2:
            V = np.nan
        self.currentCoarse = V / self.CurrentCoarseResistance
        
        V, Vstd = self.readDaqTask(self.aiTaskCurrentFine)
        if V > 10.0:
            V = np.nan
        elif V < -0.1:
            self.warn('Fine current readback is negative (average %f V)!' % V)
            V = np.nan
        self.currentFine = V / self.CurrentFineResistance

        V, Vstd = self.readDaqTask(self.aiTaskMagnetVoltage)
        if abs(V) > 10:
            V = np.nan
        self.magnetVoltage = V / self.MagnetVoltageGain
        
    def controlLoop(self):
        currentHistory = History(maxAge=10)
        dIdtErrorIntegrator = Integrator(T=30, dtMax=2)
        while not self.stopRequested:
            # First, take all measurements
            t = time.time()
            self.readDaqData()
            
            if np.isnan(self.currentCoarse):
                self.warn('Invalid value for coarse current readout.')
                self.forceShutdown()

            self.Ips = self.ps.measureCurrent()
            self.Vps = self.ps.measureVoltage()
            
            if abs(self.Ips - self.currentCoarse) > 0.3:
                self.warn('Supply (%.3f A) and coarse (%.3f A) current read-outs do not match.' % (self.Ips, self.currentCoarse))
                self.forceShutdown()
            
            if np.isfinite(self.currentFine) and abs(self.currentFine - self.currentCoarse) > 0.15:
                self.warn('Fine (%.3f A) and coarse (%.3f A) current read-outs do not match.' % (self.currentFine, self.currentCoarse))
                self.forceShutdown()

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
            self.publisher.publish('Isupply', self.Ips)
            self.publisher.publish('Vsupply', self.fetOutputVoltage)
            self.publisher.publish('Vmagnet', self.magnetVoltage)
            self.publisher.publish('Imagnet', self.currentCoarse)
            self.publisher.publish('ImagnetFine', self.currentFine)
            self.publisher.publish('dIdt',self.dIdt)

                
            if np.isnan(self.magnetVoltage): # If the magnet voltage is outside the measurement range, use an estimate
                self.magnetVoltage = self.dIdt * self.inductance
            
            # Estimate resistive voltage drop across magnet to check for quench
            Vdiode = self.diodeVoltageDrop(I)
            V_R = self.fetOutputVoltage - self.magnetVoltage - Vdiode
            self.resistiveVoltageUpdated.emit(V_R)
            if I > 0.05:
                R = V_R / I
            else:
                R = float('nan')
            self.resistanceUpdated.emit(R)
            
            if self.currentCoarse > 1.: # Check for possible quench
                if R > self.Rmax:
                    self.warn('Estimated wiring resistance (%.4f ) exceeded threshold. Assuming quench.' % (R, self.Rmax))
                    self.forceShutdown()
                    
            # If ramp rate is small, accumulate dIdt error integral
            dIdtMax = 10.*mAperMin
            if abs(self.dIdtTarget) < dIdtMax and abs(self.dIdt) < dIdtMax:
                err = self.dIdtTarget-self.dIdt
                if dIdtErrorIntegrator.lastTime < t-1800:
                    dIdtErrorIntegrator.reset()
                dIdtError = dIdtErrorIntegrator.append(t, err)
                self.dIdtIntegralAvailable.emit(dIdtError)
                if abs(dIdtError) < dIdtMax:
                    self.dIdtError = dIdtError
                else:
                    self.warn('Excessive dIdt error integral estimate: %f' % dIdtError)

            # Check current limits
            if I >= self.IOutputMax:
                if I >= self.IOutputMax+0.2:
                    self.warn('Maximum output current significantly exceeded.')
                    self.forceShutdown()
                elif self.dIdtTarget > 0:
                    self.info('Maximum current reached, halting ramp.')
                    self.setRampRate(0)
                    
            if self.analogFeedback:  # Analog feedback mode
                V = self.dIdtTarget * self.inductance
                if self.dIdtCorrectionEnabled:
                    V += self.dIdtError * self.inductance
                self.programMagnetVoltage(V)
                self.setOutputVoltage(self.fetOutputVoltage) # Track the output so we can switch the feedback loop off at any time
            else:  # Digital feedback mode
                if self.dIdtCorrectionEnabled:
                    VmagnetGoal = self.inductance*(self.dIdtTarget+self.dIdtError)
                else:
                    VmagnetGoal = self.inductance*self.dIdtTarget
                self.programMagnetVoltage(VmagnetGoal) # Track the magnet voltage so we can switch from digital to analog feedback
                errorTerm = (VmagnetGoal-self.magnetVoltage)
                Vnew = max(self.VoutputProgrammed + errorTerm, 0)
                self.setOutputVoltage(Vnew)
                
            self.updatePowerSupplyVoltage()
            self.sleepPrecise(t)
            
    def updatePowerSupplyVoltage(self):
        delta = self.Vps - self.fetOutputVoltage
        if delta < self.SupplyDeltaMin or delta > self.SupplyDeltaMax:
            newVps = self.fetOutputVoltage + 0.5*(self.SupplyDeltaMin+self.SupplyDeltaMax)
            newVps = min(max(1.5, newVps), self.VSupplyMax)
            self.ps.setVoltage(newVps)

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

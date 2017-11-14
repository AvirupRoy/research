# -*- coding: utf-8 -*-
"""
Record TES I-V curves using a single DAQ device with AO and AI.
Produces triangular sweeps (up and down) and records data to HDF5 file.
New code started at Tsinghua October/November 2016

# v0.3: Fixed decimation to be zero_phase
# v0.4: Introduced AuxAoRamping, even between sweeps
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

OrganizationName = 'McCammon Astrophysics'
OrganizationDomain = 'wisp.physics.wisc.edu'
ApplicationName = 'IvCurveDaq'
Version = '0.4'

from LabWidgets.Utilities import compileUi, saveWidgetToSettings, restoreWidgetFromSettings
compileUi('IvCurveDaqUi')
import IvCurveDaqUi as ui 
from PyQt4.QtGui import QWidget, QMessageBox
from PyQt4.QtCore import QThread, QSettings, pyqtSignal
#from MeasurementScripts.NoiseVsBiasAndTemperature import Squid
from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote

import DAQ.PyDaqMx as daq
import time
import numpy as np
#import scipy.signal import decimate
from Utility.Decimate import decimate
import pyqtgraph as pg
import traceback

from Zmq.Subscribers import TemperatureSubscriber_RuOx2005, TemperatureSubscriber
from Zmq.Zmq import RequestReplyThreadWithBindings
from Zmq.Ports import RequestReply

def iterativeDecimate(y, factor):
    ynew = y
    while factor > 8:
        ynew = decimate(ynew, 8, ftype='fir', zero_phase=True)
        factor /= 8
    ynew = decimate(ynew, factor, ftype='fir', zero_phase=True)
    return ynew


class DaqThread(QThread):
    error = pyqtSignal(str)
    dataReady = pyqtSignal(float, float, float, np.ndarray)
    driveDataReady = pyqtSignal(float, float, np.ndarray)

    def __init__(self, deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig, parent=None):
        super(DaqThread, self).__init__(parent)
        self.deviceName = deviceName
        self.aoChannel = aoChannel
        self.aoRange = aoRange
        self.aiChannel = aiChannel
        self.aiRange = aiRange
        self.aiTerminalConfig = aiTerminalConfig
        self.aiDriveChannel = None
        self.squid = None
        self.auxAoRamper = None
        
    def setAuxAoRamper(self, auxAoRamper):
        self.auxAoRamper = auxAoRamper
        
    def enableDriveRecording(self, aiDriveChannel):
        self.aiDriveChannel = aiDriveChannel
        
    def setWave(self, wave):
        self.wave = wave
        
    def setSquid(self, squid):
        self.squid = squid
        
    def setSampleRate(self, rate):
        self.sampleRate = rate

    def stop(self):
        self.stopRequested = True
        
    def abort(self):
        self.stopRequested = True
        self.abortRequested = True
        
    def sweepCount(self):
        return self.sweepCount
        
    def updateAoVoltage(self, V):
        self.newAuxAoVoltage = V
        
    def run(self):
        self.sweepCount = 0
        self.stopRequested = False
        self.abortRequested = False
        try:
            d = daq.Device(self.deviceName)
            d.findTerminals()
            nSamples = len(self.wave)
            timing = daq.Timing(rate = self.sampleRate, samplesPerChannel = nSamples)
            timing.setSampleMode(timing.SampleMode.FINITE)
            dt = 1./self.sampleRate
            print "Samples:", len(self.wave)

            aoChannel = daq.AoChannel('%s/%s' % (self.deviceName, self.aoChannel), self.aoRange.min, self.aoRange.max)
            aoTask = daq.AoTask('AO')
            aoTask.addChannel(aoChannel)
            aoTask.configureTiming(timing)
            aoTask.configureOutputBuffer(2*len(self.wave))
            #aoTask.digitalEdgeStartTrigger('/%s/ai/StartTrigger' % self.deviceName) # The cheap USB DAQ doesn't support this?!

            if self.aiDriveChannel is not None: # Record drive signal on a different AI channel first
                aiChannel = daq.AiChannel('%s/%s' % (self.deviceName, self.aiDriveChannel), self.aoRange.min, self.aoRange.max)
                aiChannel.setTerminalConfiguration(self.aiTerminalConfig)
                aiTask = daq.AiTask('AI')
                aiTask.addChannel(aiChannel)
                aiTask.configureTiming(timing)
                aoTask.writeData(self.wave)
                aoTask.start()    
                aiTask.start()
                t = time.time() # Time of the start of the sweep
                while aiTask.samplesAvailable() < nSamples and not self.abortRequested:
                    self.msleep(10)
                    
                data = aiTask.readData(nSamples)
                self.driveDataReady.emit(t, dt, data[0])
                aiTask.stop()
                try:
                    aoTask.stop()
                except:
                    pass
                del aiTask
                del aiChannel

            aiChannel = daq.AiChannel('%s/%s' % (self.deviceName, self.aiChannel), self.aiRange.min, self.aiRange.max)
            aiChannel.setTerminalConfiguration(self.aiTerminalConfig)
            aiTask = daq.AiTask('AI')
            aiTask.addChannel(aiChannel)
            aiTask.configureTiming(timing)
            
            while not self.stopRequested:
                if self.auxAoRamper is not None:
                    self.auxAoRamper.rampTo(self.newAuxAoVoltage)
                    VauxAo = self.auxAoRamper.voltage()
                else:
                    VauxAo = 0
                    
                aoTask.writeData(self.wave)
                if self.squid is not None:
                    print "Resetting SQUID:",
                    self.squid.resetPfl()
                    print "Done"
                    self.msleep(100)
                aoTask.start()    
                aiTask.start()
                t = time.time() # Time of the start of the sweep
                while aiTask.samplesAvailable() < nSamples and not self.abortRequested:
                    self.msleep(10)
                    
                data = aiTask.readData(nSamples)
                self.dataReady.emit(t, VauxAo, dt, data[0])
                self.sweepCount += 1
                aiTask.stop()
                try:
                    aoTask.stop()
                except:
                    pass

        except Exception:
            exceptionString = traceback.format_exc()
            self.error.emit(exceptionString)
        finally:
            del d
            
import h5py as hdf


class AuxAoRamper(object):
    def __init__(self, deviceName, aoChannel, aoRange):
        aoChannel = daq.AoChannel('%s/%s' % (deviceName, aoChannel), aoRange.min, aoRange.max)
        aoTask = daq.AoTask('AO auxilliary')
        aoTask.addChannel(aoChannel)
        self.channel = aoChannel
        self.auxAoTask = aoTask
        self.rampStepSize = 0.01
        self.auxAoVoltage = 0

#   Destructor            
#    if self.auxAoTask is not None:
#        self.auxAoTask.stop()
#        del self.auxAoTask
#        self.auxAoTask = None

    def voltage(self):
        return self.auxAoVoltage

    def setTo(self, Vgoal):
        '''Change the AO voltage in a single step'''
        self.auxAoTask.writeData([Vgoal], autoStart=True)
        self.auxAoVoltage = Vgoal

    def rampTo(self, Vgoal):
        '''Ramp the AO voltage to Vgoal in steps of rampStepSize'''
        Vstart = self.auxAoVoltage
        Vramp = np.linspace(Vstart, Vgoal, int(abs(Vgoal-Vstart)/self.rampStepSize)+1)
        for V in Vramp:
            self.auxAoTask.writeData([V], autoStart=True)
        self.auxAoTask.writeData([Vgoal], autoStart=True)
        self.auxAoVoltage = Vgoal
    
        

class IvCurveWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(IvCurveWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = None
        self.hdfFile = None
        self._fileName = ''
        self.plot.addLegend()
        self.plot.setLabel('left', 'SQUID response', units='V')
        self.plot.setLabel('bottom', 'bias voltage', units='s')
        self.curves = []
        self.startPb.clicked.connect(self.startMeasurement)
        self.stopPb.clicked.connect(self.stopMeasurement)

#        self.aoRangeCombo.currentIndexChanged.connect(self.updateAoRange)
#        self.auxAoChannelCombo.currentIndexChanged.connect(self.updateAuxAoRange)

        self.osr = OpenSquidRemote(port = 7894)
        squids = self.osr.findSquids()
        self.tesCombo.addItem('None')
        self.tesCombo.addItems(squids)

        self.settingsWidgets = [self.deviceCombo, self.aoChannelCombo, self.aoRangeCombo, self.aiChannelCombo, self.aiRangeCombo, self.aiTerminalConfigCombo, self.aiDriveChannelCombo, self.recordDriveCb, self.maxDriveSb, self.slewRateSb, self.zeroHoldTimeSb, self.peakHoldTimeSb, self.betweenHoldTimeSb, self.decimateCombo, self.sampleRateSb, self.sampleLe, self.commentLe, self.enablePlotCb, self.auxAoChannelCombo, self.auxAoRangeCombo, self.auxAoSb, self.auxAoEnableCb, self.polarityCombo,
                                self.tesCombo, self.pflResetCb]
        self.deviceCombo.currentIndexChanged.connect(self.updateDevice)
        for w in [self.maxDriveSb, self.slewRateSb, self.zeroHoldTimeSb, self.peakHoldTimeSb, self.betweenHoldTimeSb, self.sampleRateSb]:
            w.valueChanged.connect(self.updateInfo)
        self.decimateCombo.currentIndexChanged.connect(self.updateInfo)
        self.polarityCombo.currentIndexChanged.connect(self.updateInfo)
        self.auxAoSb.valueChanged.connect(self.updateAuxOutputVoltage)
        self.auxAoEnableCb.toggled.connect(self.toggleAuxOut)
        self.auxAoRamper = None
        self.restoreSettings()
        self.adrTemp = TemperatureSubscriber_RuOx2005(self)
        self.adrTemp.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.adrTemp.adrResistanceReceived.connect(self.collectAdrResistance)
        self.adrTemp.start()   
      
        self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.IvCurveDaq, parent=self)
        boundWidgets = {'sampleName':self.sampleLe, 'auxAoEnable':self.auxAoEnableCb, 'auxVoltage':self.auxAoSb, 
                        'maxDrive':self.maxDriveSb, 'slewRate':self.slewRateSb,
                        'start':self.startPb, 'stop': self.stopPb, 'totalTime': self.totalTimeSb,
                        'sweepCount':self.sweepCountSb}
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        self.serverThread.bindToFunction('fileName', self.fileName)
        self.serverThread.start() 
        
        pens = 'rgbc'
        for i in range(4):
            curve = pg.PlotDataItem(pen=pens[i], name='Curve %d' % i)
            self.plot.addItem(curve)
            self.curves.append(curve)
        
    def fileName(self):
        return self._fileName
            
    def toggleAuxOut(self, enabled):
        if enabled:
            deviceName = str(self.deviceCombo.currentText())
            aoChannel = str(self.auxAoChannelCombo.currentText())
            aoRange = self.aoRanges[self.auxAoRangeCombo.currentIndex()]
            self.auxAoRamper = AuxAoRamper(deviceName, aoChannel, aoRange)
            self.auxAoRamper.setTo(self.auxAoSb.value())
        else:
            del self.auxAoRamper
            self.auxAoRamper = None
            
    def threadRunning(self):
        if self.thread is not None:
            return self.thread.isRunning()
        else:
            return False

    def updateAuxOutputVoltage(self):
        V = self.auxAoSb.value()
        if self.threadRunning():
            self.thread.updateAoVoltage(V)
        elif self.auxAoRamper is not None:
            try:
                self.auxAoRamper.rampTo(V)            
            except Exception:
                exceptionString = traceback.format_exc()
                self.reportError(exceptionString)
            
#    def updateAuxAoRange(self):
#        #auxAoChannel = str(self.auxAoChannelCombo.currentText())
#        r = self.aoRanges[self.auxAoRangeCombo.currentIndex()]
#        #self.auxAoSb.setMaximum(r.max)
#        #self.auxAoSb.setMinimum(r.min)
#        if self.auxAoEnableCb.isChecked(): # If output is already on, we have to kill the old task and make a new one
#            self.toggleAuxOut(False)
#            self.toggleAuxOut(True)
            
    def collectAdrResistance(self, R):
        if self.hdfFile is None:
            return
        
        timeStamp = time.time()
        self.dsTimeStamps.resize((self.dsTimeStamps.shape[0]+1,))
        self.dsTimeStamps[-1] = timeStamp
        
        self.dsAdrResistance.resize((self.dsAdrResistance.shape[0]+1,))
        self.dsAdrResistance[-1] = R

    def populateDevices(self):
        self.deviceCombo.clear()
        system = daq.System()
        devices = system.findDevices()
        for dev in devices:
            self.deviceCombo.addItem(dev)
    
#    def updateAoRange(self):
#        aoRange = self.aoRanges[self.aoRangeCombo.currentIndex()]
#        self.maxDriveSb.setMaximum(aoRange.max)      
            
        
    def updateDevice(self):
        self.aiChannelCombo.clear()
        self.aiDriveChannelCombo.clear()
        self.aoChannelCombo.clear()
        self.aiRangeCombo.clear()
        self.aoRangeCombo.clear()
        self.auxAoRangeCombo.clear()
        self.auxAoChannelCombo.clear()
        
        deviceName = str(self.deviceCombo.currentText())
        if len(deviceName) < 1:
            return
        device = daq.Device(deviceName)

        aiChannels = device.findAiChannels()
        for channel in aiChannels:
            self.aiChannelCombo.addItem(channel)
            self.aiDriveChannelCombo.addItem(channel)
        
        aoChannels = device.findAoChannels()
        for channel in aoChannels:
            self.aoChannelCombo.addItem(channel)
            self.auxAoChannelCombo.addItem(channel)
            
        self.aiRanges = device.voltageRangesAi()
        for r in self.aiRanges:
            self.aiRangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))

        self.aoRanges = device.voltageRangesAo()            
        for r in self.aoRanges:
            self.aoRangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))
            self.auxAoRangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))
        
        if len(aiChannels):
            aiChannel = daq.AiChannel('%s/%s' % (deviceName, aiChannels[0]), self.aiRanges[0].min, self.aiRanges[0].max)
            aiTask = daq.AiTask('TestInputSampleRate')
            aiTask.addChannel(aiChannel)
            aiSampleRate = aiTask.maxSampleClockRate()
        else:
            aiSampleRate = 0

        if len(aoChannels):
            aoChannel = daq.AoChannel('%s/%s' % (deviceName, aoChannels[0]), self.aoRanges[0].min, self.aoRanges[0].max)
            aoTask = daq.AoTask('TestOutputSampleRate')
            aoTask.addChannel(aoChannel)
            aoSampleRate = aoTask.maxSampleClockRate()
        else:
            aoSampleRate = 0
            
        rate = min(aiSampleRate, aoSampleRate)
        self.sampleRateSb.setMaximum(int(1E-3*rate))
        self.updateInfo()

    def terminalConfiguration(self):
        t = str(self.aiTerminalConfigCombo.currentText())
        tc = daq.AiChannel.TerminalConfiguration
        terminalConfigDict = {'RSE': tc.RSE, 'DIFF': tc.DIFF, 'NRSE': tc.NRSE}
        return terminalConfigDict[t]
            
    def updateInfo(self):
        tz = self.zeroHoldTimeSb.value()
        tr = self.maxDriveSb.value() / self.slewRateSb.value()
        tp = self.peakHoldTimeSb.value()
        tb = self.betweenHoldTimeSb.value()
        f = self.sampleRateSb.value()*1E3
        polarity = self.polarityCombo.currentText()
        if polarity == 'bipolar':
            ttotal = 2*tz + 2*(2*tr+tp) + tb
        elif polarity == 'IvsB':
            ttotal = 2*tz + 4*tr + tb
        else:
            ttotal = 2*tz + 1*(2*tr+tp)
        self.ttotal = ttotal
        self.totalTimeSb.setValue(ttotal)
        samplesPerSweep = int(np.ceil(ttotal*f/float(self.decimateCombo.currentText())))
        self.samplesPerSweepSb.setValue(samplesPerSweep)
        
    def restoreSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        self.populateDevices()
        for w in self.settingsWidgets:
            restoreWidgetFromSettings(s, w)
            
        
    def saveSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        for w in self.settingsWidgets:
            saveWidgetToSettings(s, w)
        
    def closeEvent(self, event):
        if self.thread is not None:
            event.ignore()
            return
        self.saveSettings()
        super(IvCurveWidget, self).closeEvent(event)
                
    def removeAllCurves(self):
        for curve in self.curves:
            curve.setData([],[])
        self.nSweeps = 0
        self.sweepCountSb.setValue(self.nSweeps)

    def startMeasurement(self):
        self.removeAllCurves()
        f = self.sampleRateSb.value()*1E3
        Vmax = self.maxDriveSb.value()

        polarity = self.polarityCombo.currentText()
        
        if polarity == 'IvsB':
            whold1 = -Vmax*np.ones(int(self.zeroHoldTimeSb.value()*f))
            wrs = np.linspace(-Vmax,+Vmax, int(2*Vmax/self.slewRateSb.value()*f))
            whold2 = Vmax*np.ones((int(self.betweenHoldTimeSb.value()*f),), dtype=float)
            wave = np.hstack([whold1, wrs, whold2, wrs[::-1], whold1])
        else:
            wz = np.zeros((int(self.zeroHoldTimeSb.value()*f),), dtype=float) # Zero
            wr = np.linspace(0,Vmax, int(Vmax/self.slewRateSb.value()*f) ) # Ramp
            wp = np.ones((int(self.peakHoldTimeSb.value()*f),), dtype=float) * Vmax # Hold at peak
            wb = np.zeros((int(self.betweenHoldTimeSb.value()*f),), dtype=float) # Hold between
            
            if polarity == 'bipolar':
                wave = np.hstack([wz, wr, wp, wr[::-1], wb, -wr, -wp, -wr[::-1], wz]) # Up down and back
            elif polarity == 'positive only':
                wave = np.hstack([wz, wr, wp, wr[::-1], wz]) # Positive only
            elif polarity == 'negative only':
                wave = np.hstack([wz, -wr, wp, -wr[::-1], wz]) # Positive only
            else:
                raise Exception('Unsupported polarity choice')

        squidId = str(self.tesCombo.currentText())
        if squidId != 'None':
            squid = Pfl102Remote(self.osr, squidId)
        else:
            squid = None
        self.squid = squid
        
        self.decimation = int(self.decimateCombo.currentText())
        self.x = iterativeDecimate(wave, self.decimation)

        deviceName = str(self.deviceCombo.currentText())
        aoChannel = str(self.aoChannelCombo.currentText())
        aiChannel = str(self.aiChannelCombo.currentText())
        aiTerminalConfig = self.terminalConfiguration()
        aiRange = self.aiRanges[self.aiRangeCombo.currentIndex()]
        aoRange = self.aoRanges[self.aoRangeCombo.currentIndex()]

        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))
        fileName = path + '/IV/%s_%s.h5' % (self.sampleLe.text(), time.strftime('%Y%m%d_%H%M%S'))
        self._fileName = fileName
        hdfFile = hdf.File(fileName, mode='w')
        hdfFile.attrs['Program'] = ApplicationName
        hdfFile.attrs['Version'] = Version
        hdfFile.attrs['Decimation'] = 'Iterative decimate using customized scipy code with filtfilt.'
        hdfFile.attrs['Sample'] = str(self.sampleLe.text())
        hdfFile.attrs['Comment'] = str(self.commentLe.text())
        t = time.time()
        hdfFile.attrs['StartTime'] = t
        hdfFile.attrs['StartTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
        hdfFile.attrs['StartTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(t))
        hdfFile.attrs['Vmax'] = Vmax
        hdfFile.attrs['sampleRate'] = f
        hdfFile.attrs['decimation'] = self.decimation
        hdfFile.attrs['deviceName'] = deviceName
        hdfFile.attrs['aoChannel'] = aoChannel
        hdfFile.attrs['aoRangeMin'] = aoRange.min; hdfFile.attrs['aoRangeMax'] = aoRange.max
        hdfFile.attrs['aiChannel'] = aiChannel
        hdfFile.attrs['aiRangeMin'] = aiRange.min; hdfFile.attrs['aiRangeMax'] = aiRange.max
        hdfFile.attrs['aiTerminalConfig'] = str(self.aiTerminalConfigCombo.currentText())
        hdfFile.attrs['zeroHoldTime'] = self.zeroHoldTimeSb.value()
        hdfFile.attrs['peakHoldTime'] = self.peakHoldTimeSb.value()
        hdfFile.attrs['betweenHoldTime'] = self.betweenHoldTimeSb.value()
        hdfFile.attrs['slewRate'] = self.slewRateSb.value()
        hdfFile.attrs['polarity'] = str(polarity)
        hdfFile.attrs['resetPflEverySweep'] = bool(self.pflResetCb.isChecked())
        
        if squid is not None:
            hdfFile.attrs['pflReport'] = str(squid.report())
            hdfFile.attrs['pflRfb'] = squid.feedbackR()
            hdfFile.attrs['pflCfb'] = squid.feedbackC()
        
        if self.auxAoRamper is not None:
            hdfFile.attrs['auxAoChannel'] = str(self.auxAoRamper.channel)
            auxAoRange = self.aoRanges[self.auxAoRangeCombo.currentIndex()]
            hdfFile.attrs['auxAoRangeMin'] = auxAoRange.min; hdfFile.attrs['auxAoRangeMax'] = auxAoRange.max 
            hdfFile.attrs['auxAoValue'] = self.auxAoSb.value()

        ds = hdfFile.create_dataset('excitationWave', data=wave, compression='lzf', shuffle=True, fletcher32=True); ds.attrs['units'] = 'V'
        ds = hdfFile.create_dataset('excitationWave_decimated', data=self.x, compression='lzf', shuffle=True, fletcher32=True); ds.attrs['units'] = 'V'
        self.dsTimeStamps = hdfFile.create_dataset('AdrResistance_TimeStamps', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsTimeStamps.attrs['units'] = 's'
        self.dsAdrResistance = hdfFile.create_dataset('AdrResistance', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsAdrResistance.attrs['units'] = 'Ohms'
        self.hdfFile = hdfFile
        
        thread = DaqThread(deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig, parent=self)
        thread.setWave(wave)
        self.wave = wave
        thread.setSampleRate(f)
        thread.dataReady.connect(self.collectData)
        thread.setAuxAoRamper(self.auxAoRamper)
        thread.updateAoVoltage(self.auxAoSb.value())

        if self.recordDriveCb.isChecked():
            aiDriveChannel = str(self.aiDriveChannelCombo.currentText())
            hdfFile.attrs['aiDriveChannel'] = aiDriveChannel
            thread.enableDriveRecording(aiDriveChannel)
            thread.driveDataReady.connect(self.collectDriveData)

        if self.pflResetCb.isChecked():        
            thread.setSquid(squid)
        thread.error.connect(self.reportError)
        self.enableWidgets(False)
        self.thread = thread
        self.t0 = None
        thread.start()
        thread.finished.connect(self.threadFinished)
        
    def reportError(self, message):
        QMessageBox.critical(self, 'Exception encountered!', message)

    def stopMeasurement(self):
        if self.thread is None:
            return
        if self.stopPb.text() == 'Stop':
            self.thread.stop()
            self.stopPb.setText('Abort')
        else:
            self.thread.abort()

    def threadFinished(self):
        self.closeFile()
        self.thread = None
        self.squid = None
        self.stopPb.setText('Stop')
        self.enableWidgets(True)
        
    def closeFile(self):
        if self.hdfFile is not None:
            t = time.time()
            self.hdfFile.attrs['StopTime'] = t
            self.hdfFile.attrs['StopTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
            self.hdfFile.attrs['StopTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(t))
            self.hdfFile.close()
            del self.hdfFile
            self.hdfFile = None
            
    def enableWidgets(self, enable):
        self.driveGroupBox.setEnabled(enable)
        self.inputGroupBox.setEnabled(enable)
        self.auxAoChannelCombo.setEnabled(enable)
        self.auxAoRangeCombo.setEnabled(enable)
        self.auxAoEnableCb.setEnabled(enable)
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)

    def collectDriveData(self, timeStamp, dt, data):
        ds = self.hdfFile.create_dataset('DriveSignalRaw', data=data, compression='lzf', shuffle=True, fletcher32=True)
        ds.attrs['units'] = 'V'
        data = iterativeDecimate(data, self.decimation)
        ds = self.hdfFile.create_dataset('DriveSignalDecimated', data=data, compression='lzf', shuffle=True, fletcher32=True)
        ds.attrs['units'] = 'V'

    def collectData(self, timeStamp, auxAoVoltage, dt, data):
        Tadr = self.temperatureSb.value()
        if self.t0 is None:
            self.t0 = timeStamp
        data = iterativeDecimate(data, self.decimation)
        
        currentSweep = self.nSweeps; self.nSweeps += 1
        self.sweepCountSb.setValue(self.nSweeps)
        try:
            grp = self.hdfFile.create_group('Sweep_%06d' % currentSweep)
            grp.attrs['Time'] = timeStamp
            grp.attrs['TimeLocal'] =  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeStamp))
            grp.attrs['TimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(timeStamp))
            grp.attrs['Tadr'] = Tadr
            grp.attrs['auxAoValue'] = auxAoVoltage
            ds = grp.create_dataset('Vsquid', data=data, compression='lzf', shuffle=True, fletcher32=True)
            ds.attrs['units'] = 'V'
        except Exception:
            exceptionString = traceback.format_exc()
            self.reportError(exceptionString)
            self.stopMeasurement()

        if self.enablePlotCb.isChecked():
            self.curves[currentSweep % len(self.curves)].setData(self.x, data)


if __name__ == '__main__':
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARN)
    #logging.getLogger('Zmq.Zmq').setLevel(logging.WARN)
   
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ApplicationName)    

#    import psutil, os
#    p = psutil.Process(os.getpid())
#    p.set_nice(psutil.HIGH_PRIORITY_CLASS)
    
    from PyQt4.QtGui import QApplication, QIcon
    app = QApplication([])
    app.setOrganizationDomain(OrganizationDomain)
    app.setApplicationName(ApplicationName)
    app.setApplicationVersion(Version)
    app.setOrganizationName(OrganizationName)
    #app.setWindowIcon(QIcon('../Icons/LegacyDaqStreaming.png'))
    widget = IvCurveWidget()
    widget.setWindowTitle('%s (%s)' % (ApplicationName, Version))
    widget.show()
    app.exec_()

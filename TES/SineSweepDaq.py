# -*- coding: utf-8 -*-
"""
Record sine-sweep transfer functions using a single DAQ device with AO and AI.
Based on IvCurveDaq code
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
from __future__ import division

OrganizationName = 'McCammon Astrophysics'
OrganizationDomain = 'wisp.physics.wisc.edu'
ApplicationName = 'SineSweepDaq'
Version = '0.1'

from LabWidgets.Utilities import compileUi, saveWidgetToSettings, restoreWidgetFromSettings
compileUi('SineSweepDaqUi')
import SineSweepDaqUi as ui 
from PyQt4.QtGui import QWidget, QMessageBox
from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QObject
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import DAQ.PyDaqMx as daq
import time
import numpy as np
import traceback
import warnings

from Zmq.Subscribers import TemperatureSubscriber, TemperatureSubscriber_RuOx2005

from Zmq.Zmq import RequestReplyThreadWithBindings
from Zmq.Ports import RequestReply

rad2deg = 180/np.pi
TwoPi = 2.*np.pi

class SineWaveformGenerator(object):
    def __init__(self, amplitude, offset, phaseStep, startingPhase=0):
        self.amplitude = amplitude
        self.offset = offset
        self.phase = startingPhase
        self.phaseStep = phaseStep
        self.samplesGenerated = 0
        self.nMax = 0
        
    def setNumberOfSamples(self, nMax):
        self.nMax = nMax

    def nextSample(self):
        self.nMax = 0
        return self.generateSamples(1)
        
    def generateSamples(self, n):
        if self.nMax > 0:
            n = min(n, self.nMax-self.samplesGenerated)
            if n == 0:
                return None,None
        phases = self.phase+np.arange(0, n, 1)*self.phaseStep
        phases %= TwoPi
        assert(len(phases)==n)
        self.phase = (self.phase + n*self.phaseStep) % TwoPi
        self.samplesGenerated += len(phases)
        return phases, self.amplitude*np.sin(phases)+self.offset

class LockIn(object):
    def __init__(self):
        self.reset()

    @property
    def R(self):
        return np.sqrt(self.X**2+self.Y**2)

    @property
    def Theta(self):
        return np.arctan2(self.Y, self.X)
        
    def reset(self):
        self.X = 0
        self.Y = 0
        self.dc = 0
        self.nSamples = 0
        self.min = +1E50
        self.max = -1E50
                
    def integrateData(self, phases, data):
        if self.nSamples == 0:
            pass
            #assert abs(phases[0] < 1E-5)
        nOld = self.nSamples
        nTotal = nOld+len(data)
        wOld = nOld/nTotal
        s, c = np.sin(phases), np.cos(phases)
        X = 2.*np.sum(s*data)
        Y = 2.*np.sum(c*data)
        DC = np.sum(data)
        self.X = wOld * self.X + X/nTotal
        self.Y = wOld * self.Y + Y/nTotal
        self.dc = wOld* self.dc + DC/nTotal
        self.min = min(self.min, np.min(data))
        self.max = max(self.max, np.max(data))
        self.nSamples = nTotal

class DaqThread(QThread):
    error = pyqtSignal(str)
    dataReady = pyqtSignal(float, float, float, float, float, float, float) # time, frequency, X, Y, dc, max, min
    
    waveformAvailable = pyqtSignal(np.ndarray, np.ndarray)
    #driveDataReady = pyqtSignal(float, float, np.ndarray)

    def __init__(self, deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig, parent=None):
        super(DaqThread, self).__init__(parent)
        self.deviceName = deviceName
        self.aoChannel = aoChannel
        self.aoRange = aoRange
        self.aiChannel = aiChannel
        self.aiRange = aiRange
        self.aiTerminalConfig = aiTerminalConfig
        self.aiDriveChannel = None
        

    def setExcitation(self, amplitude, offset):
        self.amplitude = amplitude
        self.offset = offset
        
    def setParameters(self, fs, settlePeriods, measurePeriods):
        self.fGoals = fs
        self.settlePeriods = settlePeriods
        self.measurePeriods = measurePeriods
        
    def enableDriveRecording(self, aiDriveChannel):
        self.aiDriveChannel = aiDriveChannel
        
    def setSampleRate(self, rate):
        self.sampleRate = rate

    def stop(self):
        self.stopRequested = True
        
    def abort(self):
        self.stopRequested = True
        self.abortRequested = True
        
    def run(self):
        self.stopRequested = False
        self.abortRequested = False
        chunkSize = 2**16
        preLoads = 6
        try:
            d = daq.Device(self.deviceName)
            timing = daq.Timing(rate = self.sampleRate, samplesPerChannel = chunkSize)
            timing.setSampleMode(timing.SampleMode.CONTINUOUS)

            aoChannel = daq.AoChannel('%s/%s' % (self.deviceName, self.aoChannel), self.aoRange.min, self.aoRange.max)
            aiChannel = daq.AiChannel('%s/%s' % (self.deviceName, self.aiChannel), self.aiRange.min, self.aiRange.max)
            #print 'Ai terminal config', self.aiTerminalConfig, type(self.aiTerminalConfig)
            aiChannel.setTerminalConfiguration(self.aiTerminalConfig)
            sampleRate = self.sampleRate
            
            for fGoal, settlePeriods, measurePeriods in zip(self.fGoals, self.settlePeriods, self.measurePeriods):
                if self.stopRequested:
                    break
                measureSamples = int(np.round(measurePeriods*sampleRate/fGoal)) # Figure out how many samples
                f = measurePeriods*sampleRate/measureSamples# Now the correct frequency for that number of samples
                #fs.append(f)
                phaseStep = TwoPi*f/sampleRate
                settleSamples = int(sampleRate * settlePeriods/f)
                startPhase = - settleSamples*phaseStep
                totalSamples = settleSamples + measureSamples
                print "fGoal, f, periods, phaseStep, settle samples, measure samples, total samples", fGoal, f, measurePeriods, phaseStep, settleSamples, measureSamples, totalSamples
                g = SineWaveformGenerator(amplitude=self.amplitude, offset=self.offset, phaseStep=phaseStep, startingPhase=startPhase)
                g.setNumberOfSamples(totalSamples)
                
                aoTask = daq.AoTask('AO')
                aoTask.addChannel(aoChannel)
                aoTask.configureTiming(timing)
                aoTask.configureOutputBuffer(preLoads*chunkSize)
                aoTask.disableRegeneration()
                if 'ai/StartTrigger' in d.findTerminals():
                    aoTask.digitalEdgeStartTrigger('/%s/ai/StartTrigger' % self.deviceName) # The cheap USB DAQ doesn't support this?!

                lia = LockIn()
                samplesRead = 0
                
                aiTask = daq.AiTask('AI')
                aiTask.addChannel(aiChannel)
                aiTask.configureTiming(timing)
                phaseSet = []    
                for i in range(preLoads):
                    phases, wave = g.generateSamples(chunkSize)
                    if wave is not None:
                        phaseSet.append(phases)
                        aoTask.writeData(wave)
                aiTask.setUsbTransferRequestSize(aiChannel.physicalChannel, 2*chunkSize)
                aoTask.setUsbTransferRequestSize(aoChannel.physicalChannel, 2*chunkSize)
                #print('Chunksize:', chunkSize)
                        
                aoTask.start()
                aiTask.start()
                while not self.stopRequested:
                    phases, wave = g.generateSamples(chunkSize)
                    if wave is not None:
                        aoTask.writeData(wave)
                        phaseSet.append(phases)
                
                    samplesRemaining = totalSamples-samplesRead
                    if samplesRemaining > 0:
                        data = aiTask.readData(min(chunkSize, samplesRemaining))
                        samples = data[0]
                        nNewSamples = len(samples)
                        samplesRead += nNewSamples
                        phases = phaseSet.pop(0)
                        #print phases.shape, len(phaseSet)
                        if samplesRead <= settleSamples:
                            pass
                        elif samplesRead > settleSamples+chunkSize: # Entire chunk is good
                            lia.integrateData(phases, samples)
                            self.waveformAvailable.emit(phases, samples)
                        elif samplesRead > settleSamples: # Special case for first chunk
                            i = settleSamples - samplesRead
                            lia.integrateData(phases[i:], samples[i:])
                    else:
                        break
                            
                del aiTask; aiTask = None
                del aoTask; aoTask = None
                if g.samplesGenerated != totalSamples:
                    warnings.warn('Not all samples were generated')
                if lia.nSamples != measureSamples:
                    warnings.warn('Did not record expected number of samples')
                phase, V = g.nextSample()
                
                aoTask = daq.AoTask('AO_Final') # Now write one last sample that is back at the offset
                aoTask.addChannel(aoChannel)
                aoTask.writeData(V, autoStart = True)
                if abs(V[0])-self.offset > 1E-3:
                    warnings.warn('Output and end was not zero as expected.')
                
            #    print "Done!"
                #print lia.X, lia.Y, lia.R, rad2deg*lia.Theta
                t = time.time()
                self.dataReady.emit(t, f, lia.X, lia.Y, lia.dc, lia.min, lia.max)
                # Could adjust amplitude here based on R

        except Exception:
            exceptionString = traceback.format_exc()
            self.error.emit(exceptionString)
        finally:
            del d
            
import h5py as hdf

class Sweep(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._t = []
        self._f = []
        self._X = []
        self._Y = []
        self._dc = []
        self._Vmin = []
        self._Vmax = []

    @property
    def t(self):
        return np.asarray(self._t)
    @property
    def f(self):
        return np.asarray(self._f)
    @property
    def X(self):
        return np.asarray(self._X)        
    @property
    def Y(self):
        return np.asarray(self._Y)
    @property
    def dc(self):
        return np.asarray(self._dc)
    @property
    def R(self):
        return np.sqrt(self.X**2+self.Y**2)
    @property
    def Theta(self):
        return np.unwrap(np.arctan2(self.Y,self.X))
    @property
    def Vmin(self):
        return np.asarray(self._Vmin)
    @property
    def Vmax(self):
        return np.asarray(self._Vmax)
        
    def collectData(self, t, f, X, Y, dc, Vmin, Vmax):
        self._t.append(t)
        self._f.append(f)
        self._X.append(X)
        self._Y.append(Y)
        self._dc.append(dc)
        self._Vmin.append(Vmin)
        self._Vmax.append(Vmax)
        
    def toHdf(self, grp):
        grp.create_dataset('t', data=self.t)
        grp.create_dataset('f', data=self.f)
        grp.create_dataset('X', data=self.X)
        grp.create_dataset('Y', data=self.Y)
        grp.create_dataset('dc', data=self.dc)
        grp.create_dataset('Vmin', data=self.Vmin)
        grp.create_dataset('Vmax', data=self.Vmax)
        print "Done writing data"

    
#from Zmq.Zmq import ZmqPublisher
#from Zmq.Ports import PubSub
#from OpenSQUID.OpenSquidRemote import OpenSquidRemote#, SquidRemote
class SineSweepWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(SineSweepWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = None
        self.hdfFile = None
        self._fileName = ''
        
        self.wavePlot.addLegend()
        self.wavePlot.setLabel('left', 'Voltage', units='V')
        self.wavePlot.setLabel('bottom', 'Phase', units='[rad]')
        self.excitationCurve = pg.PlotDataItem(pen='r', name='Excitation')
        self.wavePlot.addItem(self.excitationCurve)
        self.responseCurve = pg.PlotDataItem(pen='b', name='Response')
        self.wavePlot.addItem(self.responseCurve)
        self.wavePlot.setXRange(0,2*np.pi)
        self.startPb.clicked.connect(self.startMeasurement)
        self.stopPb.clicked.connect(self.stopMeasurement)
        self.settingsWidgets = [self.deviceCombo, self.aoChannelCombo, self.aoRangeCombo,
                                self.aiChannelCombo, self.aiRangeCombo, self.aiTerminalConfigCombo,
                                self.aiDriveChannelCombo, self.recordDriveCb, self.sampleLe, self.commentLe,
                                self.enablePlotCb, self.auxAoChannelCombo, self.auxAoRangeCombo,
                                self.auxAoSb, self.auxAoEnableCb, self.sampleRateSb,
                                self.offsetSb, self.amplitudeSb, self.fStopSb, self.fStartSb,
                                self.fStepsSb, self.settlePeriodsSb, self.measurePeriodsSb,
                                self.minSettleTimeSb, self.minMeasureTimeSb]
        self.sampleRateSb.valueChanged.connect(lambda x: self.fStopSb.setMaximum(x*1E3/2))
        self.fStopSb.valueChanged.connect(self.fStartSb.setMaximum)
        self.fStartSb.valueChanged.connect(self.fStopSb.setMinimum)
        self.deviceCombo.currentIndexChanged.connect(self.updateDevice)
        self.restoreSettings()
        #self.updateDevice()
        self.updateInfo()
        for w in [self.sampleRateSb, self.fStopSb, self.fStartSb, self.fStepsSb, self.settlePeriodsSb, self.measurePeriodsSb, self.minSettleTimeSb, self.minMeasureTimeSb]:
            w.valueChanged.connect(self.updateInfo)
        self.adrTemp = TemperatureSubscriber(self)
        self.adrTemp.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.adrTemp.adrResistanceReceived.connect(self.collectAdrResistance)
        self.adrTemp.start()        
        self.auxAoSb.valueChanged.connect(self.updateAuxOutputVoltage)
        self.auxAoEnableCb.toggled.connect(self.toggleAuxOut)
        self.auxAoTask = None
        self.curve1 = pg.PlotDataItem(symbol='o', symbolSize=7, pen='b', name='')
        self.curve2 = pg.PlotDataItem(symbol='o', symbolSize=7, pen='r', name='')
        self.plot1.addItem(self.curve1)
        self.plot1.setLogMode(x=True)
        self.plot1.setLabel('bottom', 'f', units='Hz')
        self.plot2.addItem(self.curve2)
        self.plot2.setLogMode(x=True)
        self.plot2.setLabel('bottom', 'f', units='Hz')
        self.plot2.setXLink(self.plot1)
        self.plot1.showGrid(x=True, y=True)
        self.plot2.showGrid(x=True, y=True)
        self.plotxy.setLabel('bottom', 'X', units='')
        self.plotxy.setLabel('left', 'Y', units='')
        self.plotxy.setAspectLocked()
        self.curvexy = pg.PlotDataItem(symbol='o', symbolSize=7, pen='b', name='')
        self.plotxy.addItem(self.curvexy)
        self.plotCombo.currentIndexChanged.connect(self.yAxisChanged)
        self.plotCombo.setCurrentIndex(self.plotCombo.currentIndex())
        
        self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.SineSweepDaq, parent=self)
        boundWidgets = {'sample': self.sampleLe, 'comment': self.commentLe,
                        'samplingRate': self.sampleRateSb, 
                        'auxAo': self.auxAoSb, 'rampRate': self.rampRateSb,
                        'offset':self.offsetSb, 'amplitude':self.amplitudeSb,
                        'settlePeriods': self.settlePeriodsSb, 'minSettleTime': self.minSettleTimeSb,
                        'measurePeriods': self.measurePeriodsSb, 'minMeasureTime': self.minMeasureTimeSb,
                        'totalTime': self.totalTimeSb,
                        'fStart': self.fStartSb, 'fStop': self.fStopSb,
                        'fSteps': self.fStepsSb, 'start': self.startPb, 'stop': self.stopPb}
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        self.serverThread.bindToFunction('fileName', self.fileName)
        self.serverThread.start() 
                
    def toggleAuxOut(self, enabled):
        if enabled:
            deviceName = str(self.deviceCombo.currentText())
            aoChannel = str(self.auxAoChannelCombo.currentText())
            aoRange = self.aoRanges[self.auxAoRangeCombo.currentIndex()]
            aoChannel = daq.AoChannel('%s/%s' % (deviceName, aoChannel), aoRange.min, aoRange.max)
            aoTask = daq.AoTask('AO auxilliary')
            aoTask.addChannel(aoChannel)
            self.auxAoTask = aoTask
            self.updateAuxOutputVoltage()
        else:
            if self.auxAoTask is not None:
                self.auxAoTask.stop()
                del self.auxAoTask
                self.auxAoTask = None

    def updateAuxOutputVoltage(self):
        if self.auxAoTask is None:
            return
        try:
            self.auxAoTask.writeData([self.auxAoSb.value()], autoStart=True)
        except Exception:
            exceptionString = traceback.format_exc()
            self.reportError(exceptionString)
            
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
            aiTask = daq.AiTask('TestInputSampleRate_SineSweepDaq')
            aiTask.addChannel(aiChannel)
            aiSampleRate = aiTask.maxSampleClockRate()
            del aiTask
        else:
            aiSampleRate = 0

        if len(aoChannels):
            aoChannel = daq.AoChannel('%s/%s' % (deviceName, aoChannels[0]), self.aoRanges[0].min, self.aoRanges[0].max)
            aoTask = daq.AoTask('TestOutputSampleRate_SineSweepDaq')
            aoTask.addChannel(aoChannel)
            aoSampleRate = aoTask.maxSampleClockRate()
            del aoTask                
        else:
            aoSampleRate = 0
        
        rate = min(aiSampleRate, aoSampleRate)

        self.sampleRateSb.setMaximum(int(1E-3*rate))
        if rate < 1:
            return
        self.updateInfo()

    def terminalConfiguration(self):
        t = str(self.aiTerminalConfigCombo.currentText())
        tc = daq.AiChannel.TerminalConfiguration
        terminalConfigDict = {'RSE': tc.RSE, 'DIFF': tc.DIFF, 'NRSE': tc.NRSE}
        return terminalConfigDict[t]
            
    def updateInfo(self):
        nSettle = self.settlePeriodsSb.value(); nMeasure = self.measurePeriodsSb.value();
        tSettleMin = self.minSettleTimeSb.value(); tMeasureMin = self.minMeasureTimeSb.value()
        fStart = self.fStartSb.value(); fStop = self.fStopSb.value(); n=self.fStepsSb.value()
        fs = np.logspace(np.log10(fStart), np.log10(fStop), n)
        nMeasure = np.maximum(np.ceil(tMeasureMin*fs), nMeasure) # Compute the number of (integer) measurement periods for each frequency
        
        fSample = self.sampleRateSb.value()*1E3 # Now figure out which frequencies we can actually exactly synthesize
        k = np.ceil(nMeasure*fSample/fs)
        fs = nMeasure*fSample/k

        if False:        
            fBad = 15.  # Now eliminate uneven harmonics of 15 Hz
            fBadMax = 500 # But only below 500 Hz
            iBad = (np.abs(np.mod(fs, 2*fBad)-fBad) < 2) & (fs < fBadMax)
        else:
            iBad = np.zeros_like(fs, dtype=np.bool)
        self.pointsSkippedSb.setValue(np.count_nonzero(iBad))
        fs = fs[~iBad]
        self.nMeasure = nMeasure[~iBad]
        self.fGoals = fs
        periods = 1./fs
        self.nSettle = np.maximum(np.ceil(tSettleMin/periods), nSettle) # Compute the number of (integer) settle periods for each frequency
        tTotal = np.sum((self.nSettle+self.nMeasure) * periods) # TODO probably should add time for DAQmx setup overhead?
        self.totalTimeSb.setValue(tTotal)
        self.plot1.setXRange(np.log10(fStart), np.log10(fStop))
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
        super(SineSweepWidget, self).closeEvent(event)
                
    def startMeasurement(self):
        sampleRate = self.sampleRateSb.value()*1E3
        deviceName = str(self.deviceCombo.currentText())
        aoChannel = str(self.aoChannelCombo.currentText())
        aiChannel = str(self.aiChannelCombo.currentText())
        aiTerminalConfig = self.terminalConfiguration()
        aiRange = self.aiRanges[self.aiRangeCombo.currentIndex()]
        aoRange = self.aoRanges[self.aoRangeCombo.currentIndex()]
        offset = self.offsetSb.value()
        amplitude = self.amplitudeSb.value()
        fStart = self.fStartSb.value()
        fStop = self.fStopSb.value()
        fSteps = self.fStepsSb.value()
        settlePeriods = self.settlePeriodsSb.value(); measurePeriods = self.measurePeriodsSb.value()
        minSettleTime = self.minSettleTimeSb.value(); minMeasureTime = self.minMeasureTimeSb.value()

        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))
        fileName = path+'/TF/%s_%s.h5' % (self.sampleLe.text(), time.strftime('%Y%m%d_%H%M%S'))
        self._fileName = fileName
        hdfFile = hdf.File(fileName, mode='w')
        hdfFile.attrs['Program'] = ApplicationName
        hdfFile.attrs['Version'] = Version
        hdfFile.attrs['Sample'] = str(self.sampleLe.text())
        hdfFile.attrs['Comment'] = str(self.commentLe.text())
        hdfFile.attrs['StartTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S')
        hdfFile.attrs['StartTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())
        hdfFile.attrs['sampleRate'] = sampleRate
        hdfFile.attrs['offset'] = offset
        hdfFile.attrs['amplitude'] = amplitude
        hdfFile.attrs['fStart'] = fStart
        hdfFile.attrs['fStop'] = fStop
        hdfFile.attrs['fSteps'] = fSteps
        hdfFile.attrs['settlePeriods'] = settlePeriods
        hdfFile.attrs['measurePeriods'] = measurePeriods
        hdfFile.attrs['minSettleTime'] = minSettleTime
        hdfFile.attrs['minMeasureTime'] = minMeasureTime
        hdfFile.attrs['deviceName'] = deviceName
        hdfFile.attrs['aoChannel'] = aoChannel
        hdfFile.attrs['aoRangeMin'] = aoRange.min; hdfFile.attrs['aoRangeMax'] = aoRange.max
        hdfFile.attrs['aiChannel'] = aiChannel
        hdfFile.attrs['aiRangeMin'] = aiRange.min; hdfFile.attrs['aiRangeMax'] = aiRange.max
        hdfFile.attrs['aiTerminalConfig'] = str(self.aiTerminalConfigCombo.currentText())
        
        if self.auxAoTask is not None:
            hdfFile.attrs['auxAoChannel'] = str(self.auxAoTask.channels[0])
            auxAoRange = self.aoRanges[self.auxAoRangeCombo.currentIndex()]
            hdfFile.attrs['auxAoRangeMin'] = auxAoRange.min; hdfFile.attrs['auxAoRangeMax'] = auxAoRange.max 
            hdfFile.attrs['auxAoValue'] = self.auxAoSb.value()

        self.dsTimeStamps = hdfFile.create_dataset('AdrResistance_TimeStamps', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsTimeStamps.attrs['units'] = 's'
        self.dsAdrResistance = hdfFile.create_dataset('AdrResistance', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsAdrResistance.attrs['units'] = 'Ohms'
        self.hdfFile = hdfFile
        
        thread = DaqThread(deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig, parent=self)
        thread.setSampleRate(sampleRate)
        thread.setParameters(self.fGoals, self.nSettle, self.nMeasure)
        thread.setExcitation(amplitude, offset)
        self.sweep = Sweep(parent=self)
        thread.dataReady.connect(self.collectData)
        thread.waveformAvailable.connect(self.showWaveform)

#        if self.recordDriveCb.isChecked():
#            aiDriveChannel = str(self.aiDriveChannelCombo.currentText())
#            hdfFile.attrs['aiDriveChannel'] = aiDriveChannel
#            thread.enableDriveRecording(aiDriveChannel)
        
        thread.error.connect(self.reportError)
        self.enableWidgets(False)
        self.thread = thread
        thread.start()
        thread.finished.connect(self.threadFinished)
        
    def fileName(self):
        return self._fileName
        
    def reportError(self, message):
        tString = time.strftime('%Y%m%d_%H%M%S')
        QMessageBox.critical(self, 'Exception encountered at %s!' % (tString), message) # WORK

    def stopMeasurement(self):
        if self.thread is None:
            return
        if self.stopPb.text() == 'Stop':
            self.thread.stop()
            self.stopPb.setText('Abort')
        else:
            self.thread.abort()

    def threadFinished(self):
        grp = self.hdfFile.create_group('Sweep')
        self.sweep.toHdf(grp)
        self.closeFile()
        self.thread = None
        self.stopPb.setText('Stop')
        self.enableWidgets(True)
        
    def closeFile(self):
        if self.hdfFile is not None:
            t = time.time()
            self.hdfFile.attrs['StopTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
            self.hdfFile.attrs['StopTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(t))
            self.hdfFile.close()
            del self.hdfFile
            self.hdfFile = None
            
    def enableWidgets(self, enable):
        self.driveGroupBox.setEnabled(enable)
        self.inputGroupBox.setEnabled(enable)
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)
        
    def showWaveform(self, phases, y):
        self.responseCurve.setData(phases, y)

    def collectData(self, *args):
        try:
            self.sweep.collectData(*args)
            f = args[1]
            self.currentFrequencySb.setValue(f)
            self.updatePlot()
        except Exception as e:
            print "Exception:",e
            
    def yAxisChanged(self):
        yAxis = str(self.plotCombo.currentText())
        if yAxis=='X/Y':
            self.plot1.setLabel('left', 'X', units='')
            self.plot2.setLabel('left', 'Y', units='')
        elif yAxis=='R/Phi':
            self.plot1.setLabel('left', 'R', units='')
            self.plot2.setLabel('left', 'Phi', units='deg')
        elif yAxis=='Vmax/Vmin':
            self.plot1.setLabel('left', 'Vmax', units='V')
            self.plot2.setLabel('left', 'Vmin', units='V')
        elif yAxis=='R/Vdc':
            self.plot1.setLabel('left', 'R', units='')
            self.plot2.setLabel('left', 'Vdc', units='V')
        ylog = yAxis[0] == 'R'
        self.plot1.setLogMode(x=True, y=ylog)
        self.updatePlot()

    def updatePlot(self):
        yAxis = str(self.plotCombo.currentText())
        s = self.sweep
        x = s.f
        if yAxis=='X/Y':
            y1 = s.X
            y2 = s.Y
        elif yAxis=='R/Phi':
            y1 = s.R
            y2 = rad2deg*s.Theta
        elif yAxis=='Vmax/Vmin':
            y1 = s.Vmax
            y2 = s.Vmin
        elif yAxis=='R/Vdc':
            y1 = s.R
            y2 = s.dc
        else:
            warnings.warn("Unsupported y-axis: %s" % yAxis)
            return
        self.curve1.setData(x,y1)
        self.curve2.setData(x,y2)
        X = s.X; Y = s.Y
        self.curvexy.setData(X, Y)
#        Xmin = np.min(X); Xmax = np.max(X)
#        Ymin = np.min(Y); Ymax = np.max(Y)
#        deltaX = Xmax-Xmin; deltaY = Ymax-Ymin
#        delta = 0.5*max(deltaX, deltaY)
#        Xmean = 0.5*(Xmin+Xmax)
#        Ymean = 0.5*(Ymin+Ymax)
#        self.plotxy.setXRange(Xmean-delta, Xmean+delta)
#        self.plotxy.setYRange(Ymean-delta, Ymean+delta)

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
    
    from PyQt4.QtGui import QApplication #, QIcon
    app = QApplication([])
    app.setOrganizationDomain(OrganizationDomain)
    app.setApplicationName(ApplicationName)
    app.setApplicationVersion(Version)
    app.setOrganizationName(OrganizationName)
    #app.setWindowIcon(QIcon('../Icons/LegacyDaqStreaming.png'))
    widget = SineSweepWidget()
    widget.setWindowTitle('%s (%s)' % (ApplicationName, Version))
    widget.show()
    app.exec_()

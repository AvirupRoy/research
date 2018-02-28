# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 10:00:42 2018

@author: calorim
"""
from __future__ import division, print_function

OrganizationName = 'McCammon Astrophysics'
OrganizationDomain = 'wisp.physics.wisc.edu'
ApplicationName = 'PulseCollector'
Version = '0.1'
    
from LabWidgets.Utilities import saveWidgetToSettings, restoreWidgetFromSettings, widgetValue #, compileUi
#compileUi('SineSweepDaqUi')

import DAQ.PyDaqMx as daq
import time
import numpy as np
#import scipy.signal as signal
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#pg.setConfigOption('grid', ')

import logging

#import traceback
#import gc
#import warnings
from Utility.Decimate import decimate


from PyQt4.QtGui import QMainWindow, QWidget, QGroupBox, QCheckBox, QFormLayout, QComboBox, QSpinBox, QDockWidget, QHBoxLayout, QVBoxLayout, QAction, QStyle, QToolBar, QKeySequence, QTableWidget, QDoubleSpinBox
from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QObject, pyqtSlot, QTimer
from PyQt4.Qt import Qt

import pyqtgraph as pg

from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote
from Visa.VisaWidgets import VisaCombo
from Zmq.Subscribers import HousekeepingSubscriber
from Utility.HkLogger import HkLogger

from Utility.HdfWriter import HdfVectorWriter
from Zmq.Zmq import RequestReplyThreadWithBindings
from Zmq.Ports import RequestReply

class WithSettings(object):
    def saveSettings(self, s, groupName = None):
        if groupName is not None:
            s.beginGroup(groupName)
        try:
            for key in self.settingsWidgets:
                saveWidgetToSettings(s, self.settingsWidgets[key], key)
        finally:
            if groupName is not None:
                s.endGroup()

    def saveToHdf(self, hdfRoot):
        for key in self.settingsWidgets:
            v = widgetValue(self.settingsWidgets[key])
            if not type(v) in [int, float, bool, str]:
                v = str(v)
            hdfRoot.attrs[key] = v
            
    
    def restoreSettings(self, s, groupName = None):
        if groupName is not None:
            s.beginGroup(groupName)
        try:
            for key in self.settingsWidgets:
                restoreWidgetFromSettings(s, self.settingsWidgets[key], key)
        finally:
            if groupName is not None:
                s.endGroup()


class DaqSettingsWidget(WithSettings, QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QFormLayout()
        self.deviceCombo = QComboBox()
        self.aiChannelCombo = QComboBox()
        self.aiRangeCombo = QComboBox()
        self.aiTerminalConfigCombo = QComboBox()
        self.triggerTerminalCombo = QComboBox()
       
        
        self.sampleRateSb = QSpinBox()
        self.sampleRateSb.setSuffix(' kS/s')
        
        self.recordLengthSb = QSpinBox()
        self.recordLengthSb.setRange(10, 2000)
        self.recordLengthSb.setSuffix(' ms')
        self.preTriggerSb = QSpinBox()
        self.preTriggerSb.setRange(5, 50)
        self.preTriggerSb.setValue(25)
        self.preTriggerSb.setSuffix(' %')
        
        self.decimationCombo = QComboBox()
        decimations = [str(2**n) for n in range(0, 9)]
        self.decimationCombo.addItems(decimations)

        self.nSamplesSb = QSpinBox()
        self.nSamplesSb.setReadOnly(True)
        self.nSamplesSb.setMaximum(100000000)
        self.nSamplesSb.setButtonSymbols(QSpinBox.NoButtons)
        
        self.saveRawCb = QCheckBox()
        self.saveRawCb.setToolTip('Check to save raw (undecimated) baseline and template pulse averages')
        
        layout.addRow('&Device', self.deviceCombo)
        layout.addRow('AI &channel', self.aiChannelCombo)
        layout.addRow('AI &range', self.aiRangeCombo)
        layout.addRow('&Terminal config', self.aiTerminalConfigCombo)
        layout.addRow('&Trigger terminal', self.triggerTerminalCombo)
        layout.addRow('&Sample rate', self.sampleRateSb)
        layout.addRow('&Record length', self.recordLengthSb)
        layout.addRow('&Pre-trigger samples', self.preTriggerSb)
        layout.addRow('&Decimation', self.decimationCombo)
        layout.addRow('Decimated # of sa&mples', self.nSamplesSb)
        layout.addRow('&Save raw avg', self.saveRawCb)
        
        self.sampleRateSb.valueChanged.connect(self.update)
        self.recordLengthSb.valueChanged.connect(self.update)
        self.decimationCombo.currentIndexChanged.connect(self.update)
        
        self.deviceCombo.currentIndexChanged.connect(self._updateDevice)
        self._populateDevices()
        self.setLayout(layout)
        self.settingsWidgets = {'device':self.deviceCombo, 'aiChannel':self.aiChannelCombo,
                                'aiTerminalConfig':self.aiTerminalConfigCombo,
                                'triggerTerminal':self.triggerTerminalCombo,
                                'sampleRate': self.sampleRateSb,
                                'recordLength': self.recordLengthSb,
                                'preTrigger': self.preTriggerSb,
                                'decimation': self.decimationCombo}
                                
    def update(self):
        nSamples = int(self.samples()/self.decimation())
        self.nSamplesSb.setValue(nSamples)
        
    def _populateDevices(self):
        self.deviceCombo.clear()
        system = daq.System()
        devices = system.findDevices()
        for dev in devices:
            self.deviceCombo.addItem(dev)
        
    def _updateDevice(self):
        self.aiChannelCombo.clear()
        self.aiRangeCombo.clear()
        #self.aiChannelCombo.clear()
       # self.aoChannelCombo.clear()
        #self.aoRangeCombo.clear()
        #self.auxAoRangeCombo.clear()
        #self.auxAoChannelCombo.clear()
        
        deviceName = str(self.deviceCombo.currentText())
        if len(deviceName) < 1:
            return
        device = daq.Device(deviceName)

        aiChannels = device.findAiChannels()
        self.aiChannelCombo.addItems(aiChannels)
            
        self.aiRanges = device.voltageRangesAi()
        for r in self.aiRanges:
            self.aiRangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))
        
        if len(aiChannels):
            aiChannel = daq.AiChannel('/%s/%s' % (deviceName, aiChannels[0]), self.aiRanges[0].min, self.aiRanges[0].max)
            aiTask = daq.AiTask('TestInputSampleRate')
            aiTask.addChannel(aiChannel)
            aiSampleRate = aiTask.maxSampleClockRate()
        else:
            aiSampleRate = 0
            
        triggerLines = device.findTerminals()
        self.triggerTerminalCombo.clear()
        self.triggerTerminalCombo.addItems(triggerLines)

        self.aiTerminalConfigCombo.addItems(['RSE', 'NRSE', 'DIFF', 'PSEUDO-DIFF']) # TODO get this info from the DAQ device...

        self.sampleRateSb.setMaximum(int(1E-3*aiSampleRate))
        
    def aiChannel(self):
        channelId = '%s/%s' % (str(self.deviceCombo.currentText()), str(self.aiChannelCombo.currentText()))
        aiRange = self.aiRanges[self.aiRangeCombo.currentIndex()]
        t = str(self.aiTerminalConfigCombo.currentText())
        tc = daq.AiChannel.TerminalConfiguration
        terminalConfigDict = {'RSE': tc.RSE, 'DIFF': tc.DIFF, 'NRSE': tc.NRSE}
        terminalConfig = terminalConfigDict[t]
        return daq.AiChannel(channelId, aiRange.min, aiRange.max, terminalConfig=terminalConfig)
        
    def recordLength(self):
        return 1E-3*self.recordLengthSb.value()
        
    def sampleRate(self):
        return 1E3*self.sampleRateSb.value()
        
    def preTriggerSamples(self):
        return int(0.01 * self.preTriggerSb.value() * self.samples())
        
    def triggerTerminal(self):
        channelId = '/%s/%s' % (str(self.deviceCombo.currentText()), str(self.triggerTerminalCombo.currentText()))
        return channelId
        
    def samples(self):
        return int(self.recordLength() * self.sampleRate())
        
    def decimation(self):
        return int(str(self.decimationCombo.currentText()))
        
    def aiTiming(self):
        timing = daq.Timing(self.sampleRate())
        timing.setSampleMode(timing.SampleMode.FINITE)
        timing.setSamplesPerChannel(self.samples())
        return timing
        
class TracePlotWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        
        gb = QGroupBox('Show')
        glb = QVBoxLayout()
        rawCb = QCheckBox('&Raw')
        templateCb = QCheckBox('&Template')
        minMaxCb = QCheckBox('&Min/Max')
        baselineCb = QCheckBox('&Baseline')
        templateCb.toggled.connect(self.toggleTemplate)
        glb.addWidget(rawCb)
        glb.addWidget(templateCb)
        glb.addWidget(minMaxCb)
        glb.addWidget(baselineCb)
        gb.setLayout(glb)
        
        vl = QVBoxLayout()
        vl.addWidget(gb)
        vl.addStretch()
        
        layout.addLayout(vl)
        
        self.plot = pg.PlotWidget()
        self.plot.addLegend()
        self.plot.setLabel('left', 'SQUID response', units='V')
        self.plot.setLabel('bottom', 'time', units='s')
        
        self.rawCurve = pg.PlotDataItem(pen='k', name='raw')
        self.templateCurve = pg.PlotDataItem(pen='g', name='avg. template')
        self.minCurve = pg.PlotDataItem(pen='b', name='min')
        self.maxCurve = pg.PlotDataItem(pen='b', name='max')
        self.plot.addItem(self.rawCurve)
        self.plot.addItem(self.templateCurve)
        #self.plot.addItem(self.templateCurve)
        
        layout.addWidget(self.plot)
        self.setLayout(layout)
        
    def setTimeVector(self, t):
        self.t = t
        
    def setRawPulse(self, data):
        self.rawCurve.setData(self.t, data)
        
    def setTemplatePulse(self, data):
        self.templateCurve.setData(self.t, data)
        
    def toggleTemplate(self, checked):
        if checked:
            self.templateCurve.show()
        else:
            self.templateCurve.hide()


class PulseWidthSb(QDoubleSpinBox):
    def __init__(self, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setObjectName('PulseWidthSb')
        self.setSuffix(' us')
        self.setRange(0.001, 10)
        self.setDecimals(3)
        self.setSingleStep(0.001)
        self.setValue(1.)
        self.setAccelerated(True)
        self.setSpecialValueText('Off')
        self.setToolTip('Set laser pulse width.')
        
class CountSb(QSpinBox):
    def __init__(self, parent=None):
        QSpinBox.__init__(self, parent)
        self.setObjectName('CountSb')
        self.setRange(0, 1000000)
        self.setReadOnly(True)
        self.setButtonSymbols(QSpinBox.NoButtons)
        self.setValue(0)
        
class HighLevelSb(QDoubleSpinBox):
    def __init__(self, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setObjectName('HighLevelSb')
        self.setSuffix(' V')
        self.setRange(0.001, 10.)
        self.setDecimals(3)
        self.setSingleStep(0.001)
        self.setValue(8.0)
        self.setAccelerated(True)
        self.setToolTip('Set the high level voltage of the laser drive.')

class LdSettingsWidget(WithSettings, QWidget):
    testPulseParametersChanged = pyqtSignal(float, float)
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setRowCount(3)
        table.setHorizontalHeaderLabels(['High level', 'Pulse width', 'Count'])
        table.setVerticalHeaderLabels(['Baseline', 'Template', 'Test'])
        
        self.baselineCountSb = CountSb()
        self.templateCountSb = CountSb()
        self.testCountSb = CountSb()
        
        self.templateHlSb = HighLevelSb()
        self.testHlSb = HighLevelSb()
        
        self.templatePwSb = PulseWidthSb()
        self.testPwSb = PulseWidthSb()
        
        self.testPwSb.valueChanged.connect(self._testChanged)
        self.testHlSb.valueChanged.connect(self._testChanged)
        
        table.setCellWidget(0, 2, self.baselineCountSb)

        table.setCellWidget(1, 0, self.templateHlSb)
        table.setCellWidget(1, 1, self.templatePwSb)
        table.setCellWidget(1, 2, self.templateCountSb)

        table.setCellWidget(2, 0, self.testHlSb)
        table.setCellWidget(2, 1, self.testPwSb)
        table.setCellWidget(2, 2, self.testCountSb)
        layout = QHBoxLayout()
        layout.addWidget(table)
        
        l = QFormLayout()
        self.visaCombo = VisaCombo()
        l.addRow('&Function generator', self.visaCombo)
        self.lowLevelSb = HighLevelSb()
        l.addRow('Low &level', self.lowLevelSb)
        layout.addLayout(l)
        self.pulsePeriodSb = QDoubleSpinBox()
        self.pulsePeriodSb.setRange(10, 10000)
        self.pulsePeriodSb.setSuffix(' ms')
        self.pulsePeriodSb.setValue(200)
        l.addRow('Pulse &period', self.pulsePeriodSb)
        
        self.setLayout(layout)
        self.settingsWidgets = {'templateHighLevel': self.templateHlSb,
                                'templatePulseWidth': self.templatePwSb,
                                'testHighLevel': self.testHlSb,
                                'testPulseWidth': self.testPwSb,
                                'lowLevel': self.lowLevelSb,
                                'fgVisa': self.visaCombo,
                                'pulsePeriod': self.pulsePeriodSb}
                                
    def _testChanged(self):
        self.testPulseParametersChanged.emit(*self.pulseParametersTest())
        
    def setTemplatePulseParameters(self, highLevel, pulseWidth):
        self.templateHlSb.setValue(highLevel)
        self.templatePwSb.setValue(pulseWidth)
    
    def setTestPulseParameters(self, highLevel, pulseWidth):
        self.testHlSb.setValue(highLevel)
        self.testPwSb.setValue(pulseWidth)
        
    def pulseParametersTemplate(self):
        return self.templatePwSb.value()*1E-6, self.templateHlSb.value()

    def pulseParametersTest(self):
        return self.testPwSb.value()*1E-6, self.testHlSb.value()
        
    def pulseParametersBaseline(self):
        return self.templatePwSb.value()*1E-6, self.lowLevelSb.value()+0.01
        
    def pulser(self):
        from Visa.Agilent33500B import Agilent33500B
        visaResource = str(self.visaCombo.currentText())
        fg = Agilent33500B(visaResource)
        pulser = Pulser(fg)
        ll = self.lowLevelSb.value()
        pulser.setLowLevel(ll)
        pp = self.pulsePeriodSb.value()*1E-3
        pulser.setPulsePeriod(pp)
        return pulser
        
    def updatePulseCounts(self, countsDict):
        self.baselineCountSb.setValue(countsDict[PulseType.Baseline])
        self.templateCountSb.setValue(countsDict[PulseType.Template])
        self.testCountSb.setValue(countsDict[PulseType.Test])

class BiasSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setObjectName('HighLevelSb')
        self.setSuffix(' V')
        self.setRange(-10., 10.)
        self.setDecimals(4)
        self.setSingleStep(0.0003)
        self.setValue(0.0)
        self.setAccelerated(True)

class FeedbackResistanceCombo(QComboBox):
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        
class FeedbackCapacitanceCombo(QComboBox):
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)

class Pulser():
    def __init__(self, functionGenerator):
        self.fg = functionGenerator
    
    def setLowLevel(self, level):
        self.fg.setLowLevel(level)
        
    def setPulsePeriod(self, period):
        self.fg.setPulsePeriod(period)
    
    def setPulseParameters(self, pw, highLevel):
        self.fg.setHighLevel(highLevel)
        self.fg.setPulseWidth(pw)
        
    def startPulses(self):
        self.fg.enable()
        
    def stopPulses(self):
        self.fg.disable()

class PulseType:
    Template = 0
    Baseline = 1
    Test = 2

class IvThread(QThread):
    logger = logging.getLogger('IvThread')
    def __init__(self, aoTask, aiTask, nSamples, parent=None):
        QThread.__init__(self, parent)
        self.aoTask = aoTask
        self.aiTask = aiTask
        self.nSamples = nSamples
        self.data = []
        self.tStart = 0
        self.tStop = 0
        
    def run(self):
        self.logger.info('Thread running')
        data = []
        try:
            self.aoTask.start()
            self.aiTask.start()

            self.tStart = time.time() # Start of sweep
            while len(data)  < self.nSamples:
                self.msleep(100)
                newData = self.aiTask.readData()[0]
                if data is not None:
                    data = np.hstack([data, newData])
                else:
                    data = newData
            self.tStop = time.time() # End of sweep
            self.data = data
            self.aiTask.stop()
            self.aoTask.stop()
        except Exception as e:
            self.logger.error('Exception encountered: %s', str(e))

        finally:
            self.aiTask.clear()
            self.aoTask.clear()
        
        
class MeasurementThread(QThread):
    logger = logging.getLogger('MeasurementThread')
    pulseRecorded = pyqtSignal(float, bool, int, float, float, np.ndarray) # time, reset, pulseType, pulse width, high level, data
    squidReset = pyqtSignal(float)
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.pws = {}
        self.hls = {}
        self.aiTask = None
        self.squid = None
        self.resetEveryPulse = False
        self.samplesPerChannel = 0
        
    def setAiTask(self, aiTask, samplesPerChannel):
        self.aiTask = aiTask
        self.samplesPerChannel = samplesPerChannel
        
    def setSquid(self, squid, resetEveryPulse, resetThreshold):
        self.squid = squid
        self.resetEveryPulse = resetEveryPulse
        self.resetThreshold = resetThreshold
        
    def setPulser(self, pulser):
        self.pulser = pulser
        
    def setPulseParameters(self, pulseType, pw, highLevel):
        self.pws[pulseType] = pw
        self.hls[pulseType] = highLevel
        
    def stop(self):
        self.stopRequested = True
        
    def run(self):
        self.logger.info('Thread running')
        self.stopRequested = False
        task = self.aiTask
        samplesPerChannel = self.samplesPerChannel
        
        started = False
        i = 0
        data = [0]
        try:
            while not self.stopRequested:
                if np.max(np.abs(data)) > self.resetThreshold or self.resetEveryPulse:
                    self.squid.resetPfl()
                    #self.squidReset.emit(time.time())
                    reset = True
                    self.msleep(10)
                else:
                    reset = False
                pulseType = i % len(self.pws)
                pw = self.pws[pulseType]; highLevel = self.hls[pulseType]
                self.pulser.setPulseParameters(pw, highLevel)
                task.start()
                self.logger.info('Started DAQ task')
                if not started:
                    self.pulser.startPulses()
                    started = True
                data = task.readData(samplesPerChannel)[0]
                t = time.time()
                task.stop()
                i += 1
                self.pulseRecorded.emit(t, reset, pulseType, pw, highLevel, data)
            
            self.pulser.stopPulses()
            
        except Exception as e:
            self.logger.error('Exception encountered: %s', str(e))

        finally:
            task.clear()
            self.logger.info('Thread done')

            
class TesSettingsWidget(WithSettings, QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QFormLayout()

        self.tesCombo = QComboBox()
        layout.addRow('TES', self.tesCombo)
        self.normalBiasSb = BiasSpinBox()
        self.normalBiasSb.setToolTip('Bias used to drive TES normal')
        layout.addRow('&Normal bias', self.normalBiasSb)
        self.biasSb = BiasSpinBox()
        self.normalBiasSb.setToolTip('Bias point for data taking')
        layout.addRow('&Bias', self.biasSb)
        self.ivFbRCombo = FeedbackResistanceCombo()
        self.ivFbCCombo = FeedbackCapacitanceCombo()
        layout.addRow('&IV FB R', self.ivFbRCombo)
        layout.addRow('&IV FB C', self.ivFbCCombo)

        self.fbRCombo = FeedbackResistanceCombo()
        self.fbCCombo = FeedbackCapacitanceCombo()
        for combo in [self.fbCCombo, self.ivFbCCombo]:
            combo.addItems(['1.5nF', '15nF', '150nF'])
            
        for combo in [self.fbRCombo, self.ivFbRCombo]:
            combo.addItems(['100 kOhm', '10 kOhm', '1 kOhm'])
            
        layout.addRow('&FB R', self.fbRCombo)
        layout.addRow('&FB C', self.fbCCombo)

        self.recordIvCb = QCheckBox()
        layout.addRow('&Record IV', self.recordIvCb)
        self.resetEveryPulseCb = QCheckBox()
        layout.addRow('&Reset every pulse', self.resetEveryPulseCb)

        self.autoResetSb = QDoubleSpinBox()
        self.autoResetSb.setRange(0.1, 10)
        self.autoResetSb.setDecimals(2)
        self.autoResetSb.setSuffix(' V')
        layout.addRow('&Auto-reset threshold', self.autoResetSb)
        
        self.setLayout(layout)
        self.populate()
        self.settingsWidgets = {'tes':self.tesCombo, 'normalBias': self.normalBiasSb,
                                'bias': self.biasSb,
                                'ivFbR': self.ivFbRCombo, 'ivFbC': self.ivFbCCombo,
                                'fbR': self.fbRCombo, 'fbC': self.fbCCombo,
                                'recordIv': self.recordIvCb, 
                                'resetEveryPulseCombo': self.resetEveryPulseCb,
                                'autoResetThreshold': self.autoResetSb}

    def autoResetThreshold(self):
        return self.autoResetSb.value()
        
    def populate(self):        
        self.osr = OpenSquidRemote(port = 7894)
        squids = self.osr.findSquids()
        self.tesCombo.addItem('None')
        self.tesCombo.addItems(squids)
        
def iterativeDecimate(y, factor):
    ynew = y
    while factor > 8:
        ynew = decimate(ynew, 8, ftype='fir', zero_phase=True)
        factor //= 8
    ynew = decimate(ynew, factor, ftype='fir', zero_phase=True)
    return ynew

from Utility.RunningStats import RunningStats
import h5py as hdf

class PulseCollectorMainWindow(QMainWindow):
    logger = logging.getLogger('PulseCollectorMainWindow')
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('{0} {1}'.format(ApplicationName, Version))
        self.daqSettings = DaqSettingsWidget()
        self.daqDock = QDockWidget('DAQ settings')
        self.daqDock.setWidget(self.daqSettings)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.daqDock) #  | Qt.RightDockWidgetArea
        
        self.tracePlotWidget = TracePlotWidget()
        self.setCentralWidget(self.tracePlotWidget)
        
        self.ldSettingsWidget = LdSettingsWidget()
        self.ldDock = QDockWidget('Pulser settings')
        self.ldDock.setWidget(self.ldSettingsWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.ldDock)
        
        self.tesSettingsWidget = TesSettingsWidget()
        self.tesDock = QDockWidget('TES/SQUID')
        self.tesDock.setWidget(self.tesSettingsWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tesDock)
        
        self.exitAction = QAction("E&xit", self, shortcut=QKeySequence.Quit,
                               statusTip="Exit the application", triggered=self.close)
                               
        self.startAction = QAction(self.standardIcon(QStyle.SP_MediaPlay), "S&tart", self, shortcut=QKeySequence.New,
                               statusTip="Start the acquisition", triggered=self.start)
        self.stopAction = QAction(self.standardIcon(QStyle.SP_MediaStop), "Sto&p", self, shortcut=QKeySequence.New,
                               statusTip="Stop the acquisition", triggered=self.stop)
                               
        self.stopAction.setEnabled(False)

        tb = QToolBar()                               
        tb.addAction(self.startAction)
        tb.addAction(self.stopAction)
        self.addToolBar(tb)
        
        self.thread = None
        self.hkSub = HousekeepingSubscriber(self)
        self.hkSub.start()
        QTimer.singleShot(2000, self.restoreSettings)
        self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.PulseCollector, parent=self)
        boundWidgets = {'testPulseWidth': self.ldSettingsWidget.testPwSb, 
                        'testHighLevel': self.ldSettingsWidget.testHlSb,
                        'testPulseCount': self.ldSettingsWidget.testCountSb,
                        'pulseLowLevel': self.ldSettingsWidget.lowLevelSb,
                        'biasFinal': self.tesSettingsWidget.biasSb }
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        #self.serverThread.bindToFunction('fileName', self.fileName)
        self.serverThread.bindToFunction('start', self.start)
        self.serverThread.bindToFunction('stop', self.stop)
        self.serverThread.start() 

    def standardIcon(self, icon):
        return self.style().standardIcon(icon)

    def closeEvent(self, event):
        if self.thread is not None:
            event.ignore()
            return
        self.saveSettings()
        super(PulseCollectorMainWindow, self).closeEvent(event)

    def start(self):
        self._startFile()        
        self.recordIvCurve()
        
    def recordIvCurve(self):
        aiChannel = self.daqSettings.aiChannel()
        sampleRate = 250E3
        slewRate = 1.0
        nHold0 = int(0.1*sampleRate)
        hold0 = np.zeros((nHold0,))
        Vbias = self.tesSettingsWidget.biasSb.value()
        VbiasNormal = self.tesSettingsWidget.normalBiasSb.value()
        nRamp1 = int(abs(VbiasNormal/slewRate*sampleRate))
        ramp1 = np.linspace(0, VbiasNormal, nRamp1)
        nHold1 = int(0.1*sampleRate)
        hold1 = np.ones((nHold1,)) * VbiasNormal
        nRamp2 = int(abs(VbiasNormal-Vbias)/slewRate*sampleRate)
        ramp2 = np.linspace(VbiasNormal, Vbias, nRamp2)
        nHold2 = int(0.2*sampleRate)
        hold2 = np.ones((nHold2,)) * Vbias
        wave = np.hstack([hold0, ramp1, hold1, ramp2, hold2])
        
        nSamples = len(wave)
        g = self.hdfFile.require_group('IV')
        a = g.attrs
        a['nHold0'] = nHold0
        a['nHold1'] = nHold1
        a['nHold2'] = nHold2
        a['nRamp1'] = nRamp1
        a['nRamp2'] = nRamp2
        a['sampleRate'] = sampleRate
        a['slewRate'] = slewRate
        a['VbiasNormal'] = VbiasNormal
        a['Vbias'] = Vbias
        
        timing = daq.Timing(sampleRate, samplesPerChannel=nSamples)
        timing.setSampleMode(timing.SampleMode.FINITE)

        aiTask = daq.AiTask('PulseAiTask')
        aiTask.addChannel(aiChannel)
        aiTask.configureTiming(timing)
        aoTask = daq.AoTask('BiasTask')
        deviceName = str(self.daqSettings.deviceCombo.currentText())  # Hack
        aoChannel = daq.AoChannel('/%s/AO0' % deviceName, -5, +5) # Hack
        aoTask.addChannel(aoChannel)
        
        aoTask.configureTiming(timing)
        aoTask.digitalEdgeStartTrigger('/%s/ai/StartTrigger' % deviceName) # The cheap USB DAQ doesn't support this?!
        aoTask.writeData(wave)

        if self.squid is not None:        
            self.squid.resetPfl()
        
        self.ivThread = IvThread(aoTask, aiTask, nSamples, parent=self)
        self.ivThread.finished.connect(self.collectIvResults)
        self.ivThread.start()
        self.statusBar().showMessage('Recording IV curve, going to bias point.')
        
    def collectIvResults(self):
        self.statusBar().showMessage('IV measurement finished.')
        
        g = self.hdfFile.require_group('IV')
        g.create_dataset('Vsquid', data=np.float32(self.ivThread.data))
        g.attrs['tStart'] = self.ivThread.tStart
        g.attrs['tStop'] = self.ivThread.tStop
        del self.ivThread; self.ivThread = None
        self.recordPulses()
        
    def recordPulses(self):
        self.templateStats = RunningStats()
        self.baselineStats = RunningStats()
        
        self.pulseCounts = {PulseType.Baseline: 0, PulseType.Template: 0, PulseType.Test: 0}
        self.ldSettingsWidget.updatePulseCounts(self.pulseCounts)
        
        aiChannel = self.daqSettings.aiChannel()
        timing = self.daqSettings.aiTiming()
        preTriggerSamples = self.daqSettings.preTriggerSamples()
        triggerTerminal = self.daqSettings.triggerTerminal()
        self.decimation = self.daqSettings.decimation()
        aiTask = daq.AiTask('PulseAiTask')
        aiTask.addChannel(aiChannel)
        aiTask.configureTiming(timing)
        self.sampleRate = timing.rate
        self.logger.info('Sampling configured for %d samples at %d S/s', timing.samplesPerChannel, timing.rate)
        aiTask.digitalEdgeReferenceTrigger(triggerTerminal, preTriggerSamples)
        self.logger.info('Edge reference trigger on %s for %d pre-trigger samples', triggerTerminal, preTriggerSamples)
        t = (np.arange(timing.samplesPerChannel)-preTriggerSamples)/timing.rate
        self.tracePlotWidget.setTimeVector(t[::self.decimation])
        
        thread = MeasurementThread()
        thread.setSquid(self.squid, self.tesSettingsWidget.resetEveryPulseCb.isChecked(), self.tesSettingsWidget.autoResetThreshold())
        
        thread.setPulseParameters(PulseType.Baseline, *self.ldSettingsWidget.pulseParametersBaseline())
        thread.setPulseParameters(PulseType.Template, *self.ldSettingsWidget.pulseParametersTemplate())
        thread.setPulseParameters(PulseType.Test, *self.ldSettingsWidget.pulseParametersTest())
        self.ldSettingsWidget.testPulseParametersChanged.connect(lambda pw,hl: thread.setPulseParameters(PulseType.Test, pw, hl))
        
        pulser = self.ldSettingsWidget.pulser()
        thread.setPulser(pulser)
        
        thread.setAiTask(aiTask, timing.samplesPerChannel)
        thread.started.connect(self.threadStarted)
        thread.finished.connect(self.threadFinished)
        thread.pulseRecorded.connect(self.processPulse)
        self.thread = thread

        self.logger.info('Starting thread')
        thread.start()
        self.statusBar().showMessage('Collecting pulses...')

    def _startFile(self):        
        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))
        self.squidId = str(self.tesSettingsWidget.tesCombo.currentText())
        fileName = path + '/IV/%s_%s.h5' % (self.squidId, time.strftime('%Y%m%d_%H%M%S'))
        self._fileName = fileName
        hdfFile = hdf.File(fileName, mode='w')
        hdfFile.attrs['Program'] = ApplicationName
        hdfFile.attrs['Version'] = Version
        hdfFile.attrs['Decimation'] = 'Iterative decimate using customized scipy code with filtfilt.'
        hdfFile.attrs['Sample'] = self.squidId
        #hdfFile.attrs['Comment'] = ''
        t = time.time()
        hdfFile.attrs['StartTime'] = t
        hdfFile.attrs['StartTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
        hdfFile.attrs['StartTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(t))

        g = hdfFile.create_group('HK')
        self.hkLogger = HkLogger(g, self.hkSub)
        self.daqSettings.saveToHdf(hdfFile.require_group('Acquisition'))
        self.ldSettingsWidget.saveToHdf(hdfFile.require_group('LaserDiodePulser'))
        self.tesSettingsWidget.saveToHdf(hdfFile.require_group('TES'))
        
        self.hdfVector = HdfVectorWriter(hdfFile, [('pulseEndTimes', float), ('resets', bool), ('pulseTypes', int), ('ldPulseWidths', float), ('ldPulseHighLevels', float)], self)
        self.hdfFile = hdfFile
        self.pulseCount = 0

        if self.squidId != 'None':
            squid = Pfl102Remote(self.tesSettingsWidget.osr, self.squidId)
            hdfFile.attrs['pflReport'] = str(squid.report())
            hdfFile.attrs['pflRfb'] = squid.feedbackR()
            hdfFile.attrs['pflCfb'] = squid.feedbackC()
        else:
            squid = None
            
        self.squid = squid
        

    def _closeFile(self):
        if self.hdfFile is not None:
            del self.hkLogger; self.hkLogger = None
            t = time.time()
            self.hdfFile.attrs['StopTime'] = t
            self.hdfFile.attrs['StopTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
            self.hdfFile.attrs['StopTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(t))
            self.hdfFile.close()
            del self.hdfFile
            self.hdfFile = None
        
    def stop(self):
        if self.thread is not None:
            self.logger.info('Asking thread to stop')
            self.thread.stop()

    def threadStarted(self):
        self.logger.info('Thread started')
        self.startAction.setEnabled(False)
        self.stopAction.setEnabled(True)
        
    def threadFinished(self):
        self.statusBar().showMessage('Finished collecting pulses.')
        self.logger.info('Thread finished')
        self.startAction.setEnabled(True)
        self.stopAction.setEnabled(False)
        del self.thread; self.thread = None
        self._closeFile()
        
    def processPulse(self, time, reset, pulseType, pw, hl, data):
        self.logger.info('Processing pulse: %s', str(data.shape))
        
        print('Decimation:', self.decimation)
        ydec = iterativeDecimate(data, self.decimation)
        
        self.pulseCounts[pulseType] += 1
        self.ldSettingsWidget.updatePulseCounts(self.pulseCounts)

        self.tracePlotWidget.setRawPulse(ydec)

        if not self.hdfFile is None:
            dsName = 'Pulse%06d' % self.pulseCount
            self.pulseCount += 1
            ds = self.hdfFile.create_dataset(dsName, data=np.float32(ydec), compression='lzf', shuffle=True, fletcher32=True)
            ds.attrs['signal'] = 'Vsquid'
            ds.attrs['units'] = 'V'
            ds.attrs['endTime'] = time
            ds.attrs['pulseType'] = pulseType
            ds.attrs['ldPulseWidth'] = pw
            ds.attrs['ldPulseHighLevel'] = hl
            ds.attrs['sampleRate'] = self.sampleRate
            self.hdfFile.attrs['pulseCount'] = self.pulseCount
            self.hdfVector.writeData(pulseEndTimes=time, resets=reset, pulseTypes=pulseType, ldPulseWidths=pw, ldPulseHighLevels=hl)

        if pulseType == PulseType.Template:
            self.templateStats.push(ydec)
            self.tracePlotWidget.setTemplatePulse(self.templateStats.mean())
            print('Updated template')
        elif pulseType == PulseType.Baseline:
            self.baselineStats.push(ydec) # This doesn't make a whole lot of sense. It's really the PSD that we need to average
            #self.tracePlotWidget.setBaselinePulse(self.baselineStats.mean())
    
    def saveSettings(self, s=None):
        self.logger.info('Saving settings')
        if s is None:
            s = QSettings()
        
        self.daqSettings.saveSettings(s, 'DAQ')
        self.ldSettingsWidget.saveSettings(s, 'LaserDiodePulser')
        self.tesSettingsWidget.saveSettings(s, 'TES')
        self.statusBar().showMessage('Settings saved.')
        
    def restoreSettings(self, s=None):
        self.logger.info('Restoring settings')
        if s is None:
            s = QSettings()
        
        self.daqSettings.restoreSettings(s, 'DAQ')
        self.ldSettingsWidget.restoreSettings(s, 'LaserDiodePulser')
        self.tesSettingsWidget.restoreSettings(s, 'TES')
        self.statusBar().showMessage('Settings restored.')

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #h = logging.StreamHandler()
    #logger.addHandler(h)
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
    
    mw = PulseCollectorMainWindow()
    mw.show()
    exitCode = app.exec_()
    #if exitCode == mw.EXIT_CODE_REBOOT:
    #    restartProgram()

    app = QApplication([])

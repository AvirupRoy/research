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
    
from LabWidgets.Utilities import saveWidgetToSettings, restoreWidgetFromSettings #, compileUi
#compileUi('SineSweepDaqUi')

import DAQ.PyDaqMx as daq
import time
import numpy as np
#import scipy.signal as signal
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
#pg.setConfigOption('grid', ')

import traceback
import gc
import warnings

from PyQt4.QtGui import QMainWindow, QWidget, QGroupBox, QCheckBox, QFormLayout, QComboBox, QSpinBox, QDockWidget
from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QObject, pyqtSlot
from PyQt4.Qt import Qt

import pyqtgraph as pg

#from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote
#from Utility.HkLogger import HkLogger

class DaqSettingsWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QFormLayout()
        self.deviceCombo = QComboBox()
        self.aiChannelCombo = QComboBox()
        self.aiRangeCombo = QComboBox()
        self.terminalConfigCombo = QComboBox()
        self.sampleRateSb = QSpinBox()
        layout.addRow('&Device', self.deviceCombo)
        layout.addRow('AI &channel', self.aiChannelCombo)
        layout.addRow('AI &range', self.aiRangeCombo)
        layout.addRow('&Terminal config', self.terminalConfigCombo)
        layout.addRow('&Sample rate', self.sampleRateSb)
        self.deviceCombo.currentIndexChanged.connect(self._updateDevice)
        self._populateDevices()
        self.setLayout(layout)
        
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
        for channel in aiChannels:
            self.aiChannelCombo.addItem(channel)
            
        self.aiRanges = device.voltageRangesAi()
        for r in self.aiRanges:
            self.aiRangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))
        
        if len(aiChannels):
            aiChannel = daq.AiChannel('%s/%s' % (deviceName, aiChannels[0]), self.aiRanges[0].min, self.aiRanges[0].max)
            aiTask = daq.AiTask('TestInputSampleRate')
            aiTask.addChannel(aiChannel)
            aiSampleRate = aiTask.maxSampleClockRate()
        else:
            aiSampleRate = 0

        self.sampleRateSb.setMaximum(int(1E-3*aiSampleRate))
        

class PulseCollectorMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('{0} {1}'.format(ApplicationName, Version))
        self.daqSettings = DaqSettingsWidget()
        self.daqDock = QDockWidget('DAQ settings')
        self.daqDock.setWidget(self.daqSettings)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, self.daqDock) #  | Qt.RightDockWidgetArea
        
        #self.osr = OpenSquidRemote(port = 7894)
        #squids = self.osr.findSquids()
        #self.tesCombo.addItem('None')
        #self.tesCombo.addItems(squids)
        

if __name__ == '__main__':
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    logger.addHandler(h)
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

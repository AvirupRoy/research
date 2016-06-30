# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 15:34:01 2016

@author: wisp10
"""
from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QString
from PyQt4.QtGui import QWidget, QCheckBox, QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox

from PyQt4 import uic
with open('TektronixScope_GuiUi.py', 'w') as f:
    uic.compileUi('TektronixScope_GuiUi.ui', f)
    print "Done compiling UI"

import TektronixScope_GuiUi as Ui

OrganizationName = 'McCammon X-ray Astro Physics'
ApplicationName = 'TektronixScope'

import pyqtgraph as pg
from TektronixTds3000 import TektronixTds3000
import numpy as np
from Zmq.Zmq import ZmqPublisher
from Zmq.Ports import PubSub
import time


class ScopeThread(QThread):
    error = pyqtSignal(QString)
    dataReady = pyqtSignal(int, np.ndarray, np.ndarray)

    def __init__(self, scope, parent=None):
        super(ScopeThread, self).__init__(parent)
        self.scope = scope

    def stop(self):
        self.stopRequested = True
        
    def setActiveChannels(self, channels):
        self.activeChannels = channels

    def run(self):
        try:
            self.stopRequested = False
            while not self.stopRequested:
                for channel in self.activeChannels:
                    wave = self.scope.acquireWaveform(source='CH%d' % channel)
                    self.dataReady.emit(channel, wave.t, wave.y)
                self.msleep(100)
            
        except Exception, e:
            print "Exception", e

class TektronixScopeWidget(Ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(TektronixScopeWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = None
        self.hdfFile = None
        self.columns = {'enabled':0, 'save': 1, 'coupling':2, 'mode':3, 'gain':4, 'label':5}
        self.plot.addLegend()
        self.plot.setLabel('left', 'voltage', units='V')
        self.plot.setLabel('bottom', 'time', units='s')
        self.activeChannels = [1, 2]
        pens = 'ybmr'
        self.curves = []
        for ch in self.activeChannels:
            curve = pg.PlotDataItem(pen=pens[ch], name='Channel %d' % ch)
            self.plot.addItem(curve)
            self.curves.append(curve)
        
        self.connectToInstrument()
        self.publisher = ZmqPublisher('TektronixScope', port=PubSub.TektronixScope)

    def removeAllCurves(self):
        for curve in self.curves:
            self.plot.removeItem(curve)
            del curve
        self.curves = []
        self.plot.plotItem.legend.items = []
        
    def connectToInstrument(self):
        address = "wisptek1.physics.wisc.edu"
        print "Connecting to instrument:", address
        scope = TektronixTds3000(address)
        print scope.identify()
        for source in scope.TriggerSources:
            self.triggerSourceCombo.addItem(source)
            
        self.triggerSourceCombo.currentIndexChanged.connect(self.update)
        self.scope = scope
        self.thread = ScopeThread(self.scope, self)
        self.thread.setActiveChannels(self.activeChannels)
        self.thread.dataReady.connect(self.collectData)
        self.thread.start()
        
    def collectData(self, channel, t, y):
        dt = t[1]-t[0]
        timeStamp = time.time()
        dataSet = {'t': timeStamp, 'dt': dt}
        print "Sample rate:", 1./dt
        
        self.publisher.publish(channel, dataSet, arrays={'CH%d' % channel: y})

        for i,ch in enumerate(self.activeChannels):
            if ch == channel:
                self.curves[i].setData(t, y)

    def populateUi(self):
        s = QSettings(OrganizationName, ApplicationName)

    def saveSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        
    def endThread(self):
        self.thread.stop()
        self.thread.wait(2000)
        self.thread = None
        
    def closeEvent(self, e):
        if self.thread is not None:
            self.endThread()
        self.saveSettings()
        super(TektronixScopeWidget, self).closeEvent(e)
        

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName(ApplicationName)
    app.setApplicationVersion('0.1')
    app.setOrganizationName(OrganizationName)
    widget = TektronixScopeWidget()
    widget.show()
    app.exec_()

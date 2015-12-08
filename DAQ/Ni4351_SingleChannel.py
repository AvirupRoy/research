# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 13:10:58 2015

@author: wisp10
"""

from PyNi435x import Ni435x

from PyQt4 import QtGui
from PyQt4.QtCore import QThread,pyqtSignal

import DaqGuiUi

class MeasurementThread(QThread):
    def setDaqDevice(self, deviceId):
        self.deviceId = deviceId
        
    def setChannel(self, channel):
        self.channel = channel
        
    def enableGroundReference(self, enable = True):
        self.groundRefEnabled = enable
        
    def setPowerLineFrequency(self, plf=60):
        self.plf = plf
        
    def setReadingRate(self, rate):
        self.readingRate = rate
        
    def setRange(self, V):
        self.range = V
        
    def stop(self):
        self._stopRequested = True
    
    def run(self):
        try:
            self._stopRequested = False
            daq = Ni435x(self.deviceId)        
            daq.setScanList([self.channel])
            if self.plf == 60:
                daq.setPowerLineFrequency(daq.PowerlineFrequency.F60Hz)
            elif self.plf == 50:
                daq.setPowerLineFrequency(daq.PowerlineFrequency.F50Hz)
            daq.enableGroundReference([self.channel], self.groundRefEnabled)
            daq.setReadingRate(self.readingRate)
            daq.setRange(-self.range, +self.range)
            
            while not self._stopRequested:
                pass
        except:
            pass
            
        
class MainWidget(QtGui.QWidget, DaqGuiUi.Ui_Form):
    def __init__(self, dev, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.device = dev
        self.populateUi()
        self.startPb.clicked.connect(self.startMeasurement)
        
    def populateUi(self):
        ranges = self.device.voltageRangesAi()
        for r in ranges:
            self.inputRangeCombo.addItem('%.3f - %.3f V' % (r.min, r.max))
            
    def startMeasurement(self):
        self.msmThread = MeasurementThread()
        self.msmThread.start()
        self.msmThread.finished.connect(self.measurementStopped)
        self.stopPb.clicked.connect(self.msmThread.requestStop)
        self.startPb.setEnabled(False)
        self.stopPb.setEnabled(True)
    
    def measurementStopped(self):
        self.stopPb.setEnabled(False)
        self.startPb.setEnabled(True)
        print "Done"
        
    def stopMeasurement(self):
        pass
    

if __name__ == '__main__':
    from PyQt4 import uic
    uic.compileUiDir('.')
    dev = daq.Device('Dev1')
    
    app = QtGui.QApplication([])
    
    mw = MainWidget(dev)
    mw.show()
    app.exec_()

# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 13:10:58 2015

@author: wisp10
"""

import PyDaqMx as daq


from PyQt4 import QtGui
from PyQt4.QtCore import QThread,pyqtSignal
from LabWidgets.Utilities import compileUi
compileUi('DaqGuiUi')
import DaqGuiUi

class MeasurementThread(QThread):
    def requestStop(self):
        self.stopRequested = True
        
    def run(self):
        self.stopRequested = False
        
        for i in range(100):
            print i
            self.msleep(500)
            if self.stopRequested:
                break
        
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
        
#    def stopMeasurement(self):
#        pass
    

if __name__ == '__main__':
    dev = daq.Device('Dev1')
    
    app = QtGui.QApplication([])
    
    mw = MainWidget(dev)
    mw.show()
    app.exec_()

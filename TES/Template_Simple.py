# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 13:10:58 2015

@author: wisp10
"""


from PyQt4 import QtGui
from PyQt4.QtCore import QThread, pyqtSignal
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
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.startPb.clicked.connect(self.startMeasurement)
            
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
            

if __name__ == '__main__':
    app = QtGui.QApplication([])
    
    mw = MainWidget()
    mw.show()
    app.exec_()

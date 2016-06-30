# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 23:47:22 2015

@author: wisp10
"""

import time
#import datetime

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

#from math import isnan

import SR830_GuiUi as Ui

#from Zmq.Zmq import ZmqPublisher
#from Zmq.Ports import PubSub #,RequestReply

#from LabWidgets.Utilities import connectAndUpdate, saveWidgetToSettings, restoreWidgetFromSettings
import pyqtgraph as pg
from PyQt4.QtGui import QWidget, QFileDialog
from PyQt4.QtCore import QSettings, QTimer, QString #,pyqtSignal

from SR830_New import SR830

#from Utility.Utility import PeriodicMeasurementThread

#import gc
#gc.set_debug(gc.DEBUG_LEAK)

class SR830_Widget(Ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(SR830_Widget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('SR830 lock-in')
        self.timer = None
        
        self.selectFilePb.clicked.connect(self.selectFile)
        self.loggingEnableCb.toggled.connect(self.toggleLogging)
        self.loggingEnableCb.setEnabled(False)

        axis = pg.DateAxisItem(orientation='bottom')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis})
        self.plot.addLegend()
        self.verticalLayout.addWidget(self.plot)
        self.curve1 = pg.PlotCurveItem(name='X', symbol='o', pen='b')
        self.curve2 = pg.PlotCurveItem(name='Y', symbol='o', pen='r')
        self.curve3 = pg.PlotCurveItem(name='R', symbol='o', pen='g')
        self.plot.addItem(self.curve1)
        self.plot.addItem(self.curve2)
        self.plot.addItem(self.curve3)
        self.clearData()
        self.restoreSettings()
        
        self.logFile = None
        self.sr830 = None
        self.controlPb.clicked.connect(self.control)
        #self.auxIn1Indicator.setUnit('V')
        #self.auxIn2Indicator.setUnit('V')
        #self.auxIn3Indicator.setUnit('V')
        #self.auxIn4Indicator.setUnit('V')
        self.rIndicator.setUnit('V')
        self.xIndicator.setUnit('V')
        self.yIndicator.setUnit('V')
        self.fIndicator.setUnit('Hz')
        
    def selectFile(self):
        fileName = QFileDialog.getSaveFileName(parent=self, caption='Select a file to write to', directory=self.fileNameLe.text(), filter='*.dat;*.txt')
        self.fileNameLe.setText(fileName)        
        validFile = len(fileName) > 0
        self.loggingEnableCb.setEnabled(validFile)
        
    def toggleLogging(self, enable):
        if enable:
            f = open(self.fileNameLe.text(), 'a')
            f.write("# SR830_GUI\n")
            f.write("# Comment:%s\n" % self.commentLe.text())
            
            self.logFile = f
            self.commentLe.setReadOnly(True)
            self.fileNameLe.setReadOnly(True)
            self.selectFilePb.setEnabled(False)
        else:
            self.logFile.close()
            self.logFile = None            
            self.commentLe.setReadOnly(False)
            self.fileNameLe.setReadOnly(False)
            self.selectFilePb.setEnabled(True)
        
    def closeEvent(self, event):
        if self.timer:
            self.timer.stop()
            
        self.saveSettings()
        
    def restoreSettings(self):
        s = QSettings()
        visa = s.value('visa', QString(), type=QString)
        i = self.visaCombo.findText(visa)
        self.visaCombo.setCurrentIndex(i)
        
    def saveSettings(self):
        s = QSettings()
        visa = self.visaCombo.currentText()
        s.setValue('visa', visa)
        
    def control(self):
        if self.sr830 is not None:
            self.stop()
        else:
            self.start()

    def stop(self):
        self.timer.stop()
        self.timer = None
        self.sr830 = None     
        self.controlPb.setText('Start')
        
    def start(self):
        visa = str(self.visaCombo.currentText())
        self.sr830 = SR830(visa)
        self.sr830.clearGarbage()
        self.sr830.debug = True
        self.auxIn = 0
        
        #Input
        self.sr830.inputSource.bindToEnumComboBox(self.inputSourceCombo)
        self.sr830.inputCoupling.bindToEnumComboBox(self.inputCouplingCombo)
        self.sr830.inputGrounding.bindToEnumComboBox(self.inputShieldGroundCombo)
        self.sr830.inputFilters.bindToEnumComboBox(self.inputFiltersCombo)
        self.sr830.sensitivity.bindToEnumComboBox(self.sensitivityCombo)
        self.sr830.inputOverloadRead.connect(self.inputOverloadLed.setValue)

        #Filter
        self.sr830.filterSlope.bindToEnumComboBox(self.filterRolloffCombo)
        self.sr830.filterTc.bindToEnumComboBox(self.filterTcCombo)
        self.sr830.syncDemodulator.bindToCheckBox(self.syncCb)
        self.sr830.filterOverloadRead.connect(self.filterOverloadLed.setValue)

        #Reference
        self.sr830.referenceSource.bindToEnumComboBox(self.referenceCombo)
        self.sr830.referenceFrequency.bindToSpinBox(self.frequencySb)
        self.frequencySb.setKeyboardTracking(False)
        self.sr830.sineOut.bindToSpinBox(self.amplitudeSb)
        self.amplitudeSb.setKeyboardTracking(False)
        #@todo Phase goes here
        self.sr830.harmonic.bindToSpinBox(self.harmonicSb)
        self.harmonicSb.setKeyboardTracking(False)
        self.sr830.referenceTrigger.bindToEnumComboBox(self.referenceTriggerCombo)

        # AUX out
        aout = {0:self.auxOut1Sb, 1:self.auxOut2Sb, 2:self.auxOut3Sb, 3:self.auxOut4Sb}        
        for i in range(4):
            self.sr830.auxOut[i].bindToSpinBox(aout[i])
            
        try:
            r = self.sr830.queryString('')
            print "Garbarge:", r
        except:
            print "No garbage"
        
        self.sr830.readAll()
        
        self.sr830.readingAvailable.connect(self.collectReading)
        self.sr830.auxInRead.connect(self.collectAuxIn)
        self.controlPb.setText('Stop')
        self.timer = QTimer()
        self.timer.setInterval(int(1E3*self.intervalSb.value()))
        self.intervalSb.valueChanged.connect(lambda x: self.timer.setInterval(int(1E3*x)))
        self.timer.timeout.connect(self.snapSignal)
        self.timer.start()
        
    def snapSignal(self):
        if self.auxInGroupBox.isChecked():
            self.sr830.snapSignal(self.auxIn)
            self.auxIn += 1
            self.auxIn %= 4
        else:
            self.sr830.snapSignal()
        self.sr830.checkStatus()
        
    def clearData(self):
        self.ts = []
        self.xs = []
        self.ys = []
        self.Rs = []
        self.fs = []
                
    def collectReading(self, X, Y, f):
        t = time.time()
        R = self.sr830.R
        self.xIndicator.setValue(X)
        self.yIndicator.setValue(Y)
        self.fIndicator.setValue(f)
        self.rIndicator.setValue(R)
        self.thetaIndicator.setValue(self.sr830.thetaDegree)
        self.ts.append(t)
        self.xs.append(X)
        self.ys.append(Y)
        self.Rs.append(R)
        self.fs.append(f)
        self.curve1.setData(self.ts, self.xs)
        self.curve2.setData(self.ts, self.ys)
        self.curve3.setData(self.ts, self.Rs)
        if self.logFile is not None:
            self.logFile.write('%.3f\t%.7g\t%.7g\t%.7g\n' % (t, f, X, Y))
        
    def collectAuxIn(self, auxIn, voltage):
        auxMap = {0:self.auxIn1Indicator, 1:self.auxIn2Indicator, 2:self.auxIn3Indicator, 3:self.auxIn4Indicator}
        auxMap[auxIn].setValue(voltage)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    app.setApplicationName('SR830_GUI')
    app.setApplicationVersion('0.1')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setOrganizationName('McCammon X-ray Astrophysics')
    mainWindow = SR830_Widget()
    mainWindow.show()
    app.exec_()
  
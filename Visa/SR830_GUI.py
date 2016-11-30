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
from Zmq.Zmq import ZmqPublisher

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
        
        self.logFileName = None
        self.sr830 = None
        self.controlPb.clicked.connect(self.control)
        #self.auxIn1Indicator.setUnit('V')
        #self.auxIn2Indicator.setUnit('V')
        #self.auxIn3Indicator.setUnit('V')
        #self.auxIn4Indicator.setUnit('V')
        self.rIndicator.setUnit('V')
        self.rIndicator.setPrecision(4)
        self.xIndicator.setUnit('V')
        self.xIndicator.setPrecision(4)
        self.yIndicator.setUnit('V')
        self.yIndicator.setPrecision(4)
        self.fIndicator.setUnit('Hz')
        self.clearPb.clicked.connect(self.clearData)
#        self.publisher = ZmqPublisher('SR830', port=5789, parent=self)
        
    def selectFile(self):
        fileName = QFileDialog.getSaveFileName(parent=self, caption='Select a file to write to', directory=self.fileNameLe.text(), filter='*.dat;*.txt')
        self.fileNameLe.setText(fileName)        
        validFile = len(fileName) > 0
        self.loggingEnableCb.setEnabled(validFile)
        
    def toggleLogging(self, enable):
        if enable:
            fileName = self.fileNameLe.text() 
            with open(fileName, 'a') as of:
                of.write("#SR830_GUI\n")
                of.write("#Model:%s\n" % self.sr830.model)
                of.write("#Serial:%s\n" % self.sr830.serial)
                of.write("#VISA:%s\n" % self.visaAddress)
                of.write("#Comment:%s\n" % self.commentLe.text())
                of.write('#Date=%s\n' % time.strftime('%Y%m%d-%H%M%S'))
                settings = self.sr830.allSettingValues()
                for key in settings:
                        of.write('#SR830/%s=%s\n' % ( key, settings[key] ))
                of.write('#t\tf\tX\tY\n')

                self.logFileName = fileName
            self.commentLe.setReadOnly(True)
            self.fileNameLe.setReadOnly(True)
            self.selectFilePb.setEnabled(False)
        else:
            self.logFileName = None
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
        self.auxInGroupBox.setChecked(s.value('auxIn', True, type=bool))     
        
    def saveSettings(self):
        s = QSettings()
        visa = self.visaCombo.currentText()
        s.setValue('visa', visa)
        s.setValue('auxIn', self.auxInGroupBox.isChecked())
        
        
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
        self.visaAddress = str(self.visaCombo.currentText())
        self.sr830 = SR830(self.visaAddress)
        self.sr830.debug = False
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
        
        self.visaId = self.sr830.visaId()
        
        self.setWindowTitle('%s %s (%s)' % (self.sr830.model, self.visaAddress, self.sr830.serial))

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
        self.updatePlot()
        
    def updatePlot(self):
        self.curve1.setData(self.ts, self.xs)
        self.curve2.setData(self.ts, self.ys)
        self.curve3.setData(self.ts, self.Rs)
                
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
        
        #self.publisher.publish(item='%s %s' % (self.sr830.serial, self.visaAddress), data={'X':X, 'Y':Y, 'f':f})
        if self.logFileName is not None:
            with open(self.logFileName, 'a') as of:
                of.write('%.3f\t%.7g\t%.7g\t%.7g\n' % (t, f, X, Y))
        self.updatePlot()
        
    def collectAuxIn(self, auxIn, voltage):
        auxMap = {0:self.auxIn1Indicator, 1:self.auxIn2Indicator, 2:self.auxIn3Indicator, 3:self.auxIn4Indicator}
        auxMap[auxIn].setValue(voltage)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    from PyQt4.QtGui import QApplication, QIcon
    app = QApplication([])
    app.setApplicationName('SR830_GUI')
    app.setApplicationVersion('0.1')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setOrganizationName('McCammon X-ray Astrophysics')

    import ctypes
    myappid = u'WISCXRAYASTRO.ADR3.SR830' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    mainWindow = SR830_Widget()
    mainWindow.setWindowIcon(QIcon('../Icons/SR830.ico'))
    mainWindow.show()
    app.exec_()
  
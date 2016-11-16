# -*- coding: utf-8 -*-
"""
Program to control and log the Piezo voltage/current
Created on 2015-11-16
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

from PyQt4.QtGui import QWidget, QMessageBox
from PyQt4.QtCore import pyqtSignal, QThread, QSettings

from Visa.Keithley6430 import Keithley6430

import PiezoControlUi as ui

import numpy as np
import time


import pyqtgraph as pg

class PiezoControlThread(QThread):
    measurementReady = pyqtSignal(float, float, float)
    rampComplete = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, sourceMeter, parent=None):
        QThread.__init__(self, parent)
        self.sourceMeter = sourceMeter
        self.interval = 1.0
        self.ramping = False
        #self.publisher = ZmqPublisher('DiodeThermometerThread', 5558, self)

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, seconds):
        self._interval = float(seconds)

    def stop(self):
        self.stopRequested = True

    def sleepPrecise(self,tOld):
            tSleep = int(1E3*(self.interval-time.time()+tOld-0.010))
            if tSleep>0.010:
                self.msleep(tSleep)
            while(time.time()-tOld < self.interval):
                pass
            
    def startRamp(self, target, rate):
        self.target = target
        self.rate = rate
        self.ramping = True
        
    def stopRamp(self):
        self.ramping = False

    def run(self):
        self.stopRequested = False
        sourceMeter = self.sourceMeter
        #logger.info("Thread starting")

        try:
            #sourceMeter.setSourceFunction(Keithley6430.MODE.CURRENT)
            #sourceMeter.setSenseFunction(Keithley6430.MODE.VOLTAGE)
            #sourceMeter.setComplianceVoltage(5)
            #sourceMeter.setSourceCurrentRange(10E-6)
            #sourceMeter.setSourceCurrent(10E-6)
            #sourceMeter.enableOutput()
            smRange = 1E-7
            #sourceMeter.setSenseCurrentRange(smRange)
            Iold = None
            while not self.stopRequested:
                t = time.time()
                r = sourceMeter.obtainReading()
                V = r.voltage
                I = r.current
                if Iold is not None:
                    Iavg = (I+2*Iold)/3
                    if  abs(Iavg) < 0.07*smRange and smRange > 100E-9:
                        smRange = 0.1*smRange
                        print "Range down to:", smRange
                        sourceMeter.setSenseCurrentRange(smRange)
                    elif abs(Iavg) > 0.9 * smRange and smRange < 1E-6:
                        smRange = 10*smRange
                        print "Range up to:", smRange
                        sourceMeter.setSenseCurrentRange(smRange)
                #Iold = I

                print "V=", V, '(', r.status, ')'
                self.measurementReady.emit(t, V, I)
                if self.ramping:
                    delta = self.rate * self.interval
                    if self.target >= V:
                        newV = min(V + delta, self.target)
                    elif self.target < V:
                        newV = max (V - delta, self.target)
                    print "New voltage:", newV
                    sourceMeter.setSourceVoltage(newV)
                    if newV == self.target:
                        self.ramping = False
                        self.rampComplete.emit()
                        
 
                self.sleepPrecise(t)
        except Exception,e:
            self.error.emit(e)
        finally:
            pass
            #sourceMeter.disableOutput()

#import pyqtgraph as pg
import os

from Zmq.Zmq import RequestReplyThreadWithBindings
from Zmq.Ports import RequestReply

class PiezoControlWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(PiezoControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.voltageIndicator.setUnit('V')
        self.currentIndicator.setUnit('A')
        self.powerIndicator.setUnit('W')
        self.outputFile = None

        axis = pg.DateAxisItem(orientation='bottom')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis})
        self.verticalLayout.addWidget(self.plot)

        self.plot.addLegend()
        self.curve = pg.PlotCurveItem(name='DC', symbol='o', pen='g', )
        self.plot.setLabel('bottom', 'time')
        self.plot.addItem(self.curve)

        self.clearData()

        self.msmThread = None
        self.restoreSettings()
        self.startPb.clicked.connect(self.startPbClicked)
        self.stopPb.clicked.connect(self.stopPbClicked)
        self.clearPb.clicked.connect(self.clearData)
        self.yAxisCombo.currentIndexChanged.connect(self.updatePlot)
        
        self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.PiezoControl, parent=self)
        boundWidgets = {'rampRate':self.rampRateSb, 'rampTarget':self.rampTargetSb, 'go':self.goPb}
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        self.serverThread.start()

    def displayError(self, error):
        QMessageBox.critical(self, 'Error in measurement thread', error)

    def startPbClicked(self):
        address = str(self.k6430VisaCombo.currentText())
        sourceMeter = Keithley6430(address)
        self.visaId = sourceMeter.visaId()
        thread = PiezoControlThread(sourceMeter = sourceMeter, parent = self)
        thread.measurementReady.connect(self.collectMeasurement)
        thread.error.connect(self.displayError)
        thread.finished.connect(self.threadFinished)
        self.stopPb.clicked.connect(thread.stop)
        self.msmThread = thread

        self.enableWidgets(False)
        self.msmThread.start()
        print "Thread started"
        #self.goPb.clicked.connect(self.startRamp)
        self.goPb.toggled.connect(self.goToggled)
        self.msmThread.rampComplete.connect(self.rampComplete)
        
    def goToggled(self, checked):
        if checked:
            target = self.rampTargetSb.value()
            rate = self.rampRateSb.value()
            if self.msmThread is not None:
                self.msmThread.startRamp(target, rate)
        else:
            self.msmThread.stopRamp()
            
    def rampComplete(self):
        old = self.goPb.blockSignals(True)
        self.goPb.setChecked(False)
        self.goPb.blockSignals(old)
        
    def threadFinished(self):
        self.startPb.setEnabled(True)
        self.stopPb.setEnabled(False)

    def clearData(self):
        self.ts = []
        self.Vs = []
        self.Is = []
        self.updatePlot()

    def collectMeasurement(self, t, V, I):
        dateString = time.strftime('%Y%m%d')
        fileName = 'PiezoControl_%s.dat' % dateString
        exists = os.path.isfile(fileName)
        with open(fileName, 'a') as of:
            if not exists:
                of.write('#PiezoControl.py\n')
                of.write('#Date=%s\n' % time.strftime('%Y%m%d-%H%M%S'))
                of.write('#InstrumentId=%s\n' % self.visaId )
                of.write('#'+'\t'.join(['time', 'V', 'I'])+'\n')
            of.write("%.3f\t%.2f\t%.6g\n" % (t, V, I) )

        self.voltageIndicator.setValue(V)
        self.currentIndicator.setValue(I)
        P = V*I
        self.powerIndicator.setValue(P)
        
        self.ts.append(t)
        self.Vs.append(V)
        self.Is.append(I)
        self.updatePlot()

    def updatePlot(self):
        x = np.asarray(self.ts)

        yAxis = self.yAxisCombo.currentText()
        if yAxis == 'Voltage':
            y = self.Vs
            self.plot.setLabel('left', 'V', units='V')
        elif yAxis == 'Current':
            y = self.Is
            self.plot.setLabel('left', 'I', units='A')
        self.curve.setData(x, y)

    def updateStatus(self, message):
        self.stateLineEdit.setText(message)

    def enableWidgets(self, enable=True):
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)

    def stopPbClicked(self):
        self.msmThread.stop()
        self.msmThread.wait(2000)
        self.stop = True

    def closeEvent(self, e):
        if self.msmThread is not None:
            self.msmThread.stop()
            self.msmThread.wait(2000)
        self.saveSettings()
        super(PiezoControlWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
#        saveCombo(self.dmmVisaCombo, s)

    def restoreSettings(self):
        s = QSettings()
#        restoreCombo(self.sr830VisaCombo, s)

        
if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.WARN)

    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('Piezo Control')
    mw = PiezoControlWidget()
    mw.show()
    app.exec_()

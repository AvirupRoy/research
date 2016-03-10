# -*- coding: utf-8 -*-
"""
Program to monitor diode thermometer using Keithley 6430
Created on 2015-11-16
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

from PyQt4.QtGui import QWidget, QMessageBox
from PyQt4.QtCore import pyqtSignal, QThread, QSettings

from Visa.Keithley6430 import Keithley6430

import DiodeThermometerUi as ui

import numpy as np
import time


import pyqtgraph as pg

class DiodeThermometerThread(QThread):
    measurementReady = pyqtSignal(float, float)
    error = pyqtSignal(str)

    def __init__(self, sourceMeter, parent=None):
        QThread.__init__(self, parent)
        self.sourceMeter = sourceMeter
        self.interval = 1.0
        #self.publisher = ZmqPublisher('DiodeThermometerThread', 5558, self)

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, seconds):
        self._interval = float(seconds)

    def stop(self):
        self.stopRequested = True
        #logger.debug("MagnetControlThread stop requested.")

    def sleepPrecise(self,tOld):
            tSleep = int(1E3*(self.interval-time.time()+tOld-0.010))
            if tSleep>0.010:
                self.msleep(tSleep)
            while(time.time()-tOld < self.interval):
                pass

    def run(self):
        self.stopRequested = False
        sourceMeter = self.sourceMeter
        #logger.info("Thread starting")
        try:
            sourceMeter.setSourceFunction(Keithley6430.MODE.CURRENT)
            sourceMeter.setSenseFunction(Keithley6430.MODE.VOLTAGE)
            sourceMeter.setComplianceVoltage(5)
            sourceMeter.setSourceCurrentRange(10E-6)
            sourceMeter.setSourceCurrent(10E-6)
            sourceMeter.enableOutput()
            while not self.stopRequested:
                t = time.time()
                r = sourceMeter.obtainReading()
                V = r.voltage
                print "V=", V, '(', r.status, ')'
                self.measurementReady.emit(t, V)
                self.sleepPrecise(t)
        except Exception,e:
            self.error.emit(e)
        finally:
            sourceMeter.disableOutput()

import pyqtgraph as pg
import os

class DiodeThermometerWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(DiodeThermometerWidget, self).__init__(parent)
        self.sr830 = None
        self.setupUi(self)
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

    def displayError(self, error):
        QMessageBox.critical(self, 'Error in measurement thread', error)
        

    def startPbClicked(self):
        address = str(self.k6430VisaCombo.currentText())
        sourceMeter = Keithley6430(address)
        print "Instrument ID:", sourceMeter.visaId()
        
        cal = self.calibrationCombo.currentText()
        if cal == 'DT470':
            self.diodeCalibration = DT470Thermometer()
        elif cal == 'DT670':
            self.diodeCalibration = DT670Thermometer()

        thread = DiodeThermometerThread(sourceMeter = sourceMeter, parent = self)
        thread.measurementReady.connect(self.collectMeasurement)
        thread.error.connect(self.displayError)
        thread.finished.connect(self.threadFinished)
        self.stopPb.clicked.connect(thread.stop)
        self.msmThread = thread

        self.enableWidgets(False)
        self.msmThread.start()
        print "Thread started"
        
    def threadFinished(self):
        self.startPb.setEnabled(True)
        self.stopPb.setEnabled(False)

    def clearData(self):
        self.ts = []
        self.Vs = []
        self.Ts = []
        self.updatePlot()

    def collectMeasurement(self, t, V):
        T = self.diodeCalibration.calculateTemperature(V)

        dateString = time.strftime('%Y%m%d')
        fileName = 'DiodeThermometer_%s.dat' % dateString
        exists = os.path.isfile(fileName)
        with open(fileName, 'a') as of:
            if not exists:
                of.write('#DiodeThermometery.py\n')
                of.write('#Date=%s\n' % time.strftime('%Y%m%d-%H%M%S'))
                of.write('#Calibration=%s\n' % self.diodeCalibration.name())
                of.write('#'+'\t'.join(['time', 'V', 'T'])+'\n')
                
            of.write("%.3f\t%.6f\t%.4f\n" % (t, V, T) )

        self.voltageSb.setValue(V)
        self.temperatureSb.setValue(T)
        self.ts.append(t)
        self.Ts.append(T)
        self.Vs.append(V)
        self.updatePlot()

    def updatePlot(self):
        x = np.asarray(self.ts)

        yAxis = self.yAxisCombo.currentText()
        if yAxis == 'Voltage':
            y = self.Vs
            self.plot.setLabel('left', 'V', units='V')
        elif yAxis == 'Temperature':
            y = self.Ts
            self.plot.setLabel('left', 'T', units='K')

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
        super(DiodeThermometerWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
#        saveCombo(self.dmmVisaCombo, s)

    def restoreSettings(self):
        s = QSettings()
#        restoreCombo(self.sr830VisaCombo, s)

import numpy as np
class DT470Thermometer(object):
    def __init__(self):
        super(DT470Thermometer, self).__init__()
        self.loadCalibrationData()
        i = np.argsort(self.V) # Make sure they are sorted in order of increasing V
        self.V = self.V[i]
        self.T = self.T[i]
        
    def loadCalibrationData(self):
        curve10FileName = 'D:\Users\Labview\FJ\Lakeshore_Curve10.dat.txt'
        d = np.genfromtxt(curve10FileName)
        self.T = d[:,0]
        self.V = d[:,1]
        
    def name(self):
        return 'Lakeshore DT470 Curve 10'
        
    def calculateTemperature(self, V):
        return np.interp(V, self.V, self.T, left=np.nan, right=np.nan)

class DT670Thermometer(DT470Thermometer):
    def loadCalibrationData(self):
        fileName = 'Calibration\Lakeshore_DT670.dat'
        d = np.genfromtxt(fileName, skip_header=1, names=True)
        self.T = d['TK']
        self.V = d['V']

    def name(self):
        return 'Lakeshore DT670'
    
        
if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.WARN)

    from PyQt4.QtGui import QApplication
    
    diode = DT470Thermometer()

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('Diode Thermometer')
    mw = DiodeThermometerWidget()
    mw.show()
    app.exec_()

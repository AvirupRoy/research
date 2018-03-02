# -*- coding: utf-8 -*-
"""
Program to monitor diode thermometer using Agilent DMM readout
Created on 2015-11-16
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""


from LabWidgets.Utilities import compileUi
compileUi('DiodeThermometerV2Ui')
import DiodeThermometerV2Ui as ui

from PyQt4.QtGui import QWidget, QMessageBox
from PyQt4.QtCore import pyqtSignal, QThread, QSettings

from Visa.Agilent34401A import Agilent34401A

import numpy as np
import time
from Calibration.DiodeThermometers import DT470Thermometer, DT670Thermometer, Si70Thermometer
from Utility.Math import pruneData        

import pyqtgraph as pg

class DiodeThermometerThread(QThread):
    measurementReady = pyqtSignal(float, float)
    error = pyqtSignal(str)

    def __init__(self, dmm, parent=None):
        QThread.__init__(self, parent)
        self.dmm = dmm
        self.interval = 10.0
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
        dmm = self.dmm
        #logger.info("Thread starting")
        dmm.setFunctionVoltageDc()
        try:
            while not self.stopRequested:
                t = time.time()
                V = dmm.reading()
                self.measurementReady.emit(t, V)
                self.sleepPrecise(t)
        except Exception,e:
            self.error.emit(e)
        finally:
            pass

#import pyqtgraph as pg
from LabWidgets.Utilities import saveWidgetToSettings, restoreWidgetFromSettings
import os

class DiodeThermometerWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(DiodeThermometerWidget, self).__init__(parent)
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
        self.settingsWidgets = [self.dmmVisaCombo, self.currentCombo, self.thermometerCombo, self.yAxisCombo]
        self.restoreSettings()
        self.startPb.clicked.connect(self.startPbClicked)
        self.stopPb.clicked.connect(self.stopPbClicked)
        self.clearPb.clicked.connect(self.clearData)
        self.yAxisCombo.currentIndexChanged.connect(self.updatePlot)

    def displayError(self, error):
        QMessageBox.critical(self, 'Error in measurement thread', error)

    def startPbClicked(self):
        address = str(self.dmmVisaCombo.currentText())
        self.dmm = Agilent34401A(address)
        self.visaId = self.dmm.visaId()
        
        thermo = self.thermometerCombo.currentText()
        if 'DT-470' in thermo:
            self.diodeCalibration = DT470Thermometer()
        elif 'DT-670' in thermo:
            self.diodeCalibration = DT670Thermometer()
        elif 'Si70' in thermo:
            self.diodeCalibration = Si70Thermometer()
        
        if thermo == 'Magnet stage DT-470':
            self.suffix = 'Magnet'
        elif thermo == '3K stage DT-670':
            self.suffix = '3K'
        elif thermo == '60K stage Si70':
            self.suffix = '60K'
        
        current = self.currentCombo.currentText()
        if '10' in current:
            self.I = 10E-6
        else:
            self.I = 1E-6

        thread = DiodeThermometerThread(dmm = self.dmm, parent = self)
        thread.measurementReady.connect(self.collectMeasurement)
        thread.error.connect(self.displayError)
        thread.finished.connect(self.threadFinished)
        self.stopPb.clicked.connect(thread.stop)
        self.msmThread = thread

        self.enableWidgets(False)
        self.msmThread.start()
        
    def threadFinished(self):
        self.enableWidgets(True)

    def clearData(self):
        self.ts = []
        self.Vs = []
        self.Ts = []
        self.updatePlot()

    def collectMeasurement(self, t, V):
        T = self.diodeCalibration.calculateTemperature(V)

        dateString = time.strftime('%Y%m%d')
        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))
        fileName = os.path.join(path, 'DiodeThermometer%s_%s.dat' % (self.suffix, dateString))
        exists = os.path.isfile(fileName)
        with open(fileName, 'a') as of:
            if not exists:
                of.write(u'#DiodeThermometer2.py\n')
                of.write(u'#Date=%s\n' % time.strftime('%Y%m%d-%H%M%S'))
                of.write(u'#Instrument=%s\n' % self.visaId)
                of.write(u'#Thermometer=%s\n' % self.thermometerCombo.currentText())
                of.write(u'#Current=%s\n' % str(self.currentCombo.currentText()))
                of.write(u'#Calibration=%s\n' % self.calibration.name)
                of.write(u'#'+'\t'.join(['time', 'V', 'T', 'I'])+'\n')
                
            of.write("%.3f\t%.6f\t%.4f\t%.0e\n" % (t, V, T, self.I) )

        self.voltageSb.setValue(V)
        self.temperatureSb.setValue(T)
        self.ts.append(t)
        self.Ts.append(T)
        self.Vs.append(V)
        self.ts = pruneData(self.ts)
        self.Ts = pruneData(self.Ts)
        self.Vs = pruneData(self.Vs)
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
        self.thermometerCombo.setEnabled(enable)
        self.currentCombo.setEnabled(enable)
        self.dmmVisaCombo.setEnabled(enable)
        
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
        for widget in self.settingsWidgets:
            saveWidgetToSettings(s, widget)

    def restoreSettings(self):
        s = QSettings()
        for widget in self.settingsWidgets:
            restoreWidgetFromSettings(s, widget)


        
if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.WARN)

    from PyQt4.QtGui import QApplication, QIcon
    
    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('Diode Thermometer')

    import ctypes
    myappid = u'WISCXRAYASTRO.ADR3.DiodeThermometer' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)  

    mw = DiodeThermometerWidget()
    mw.setWindowIcon(QIcon('Icons/DiodeThermomter.ico'))
    mw.show()
    app.exec_()

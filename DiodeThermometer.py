# -*- coding: utf-8 -*-
"""
Program to monitor diode thermometer using Keithley 6430
Created on 2015-11-16
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

from PyQt4.QtGui import QWidget
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QSettings

import Transition2Ui as ui

from Visa.Keithley6430 import Keithley6430

import numpy as np
import time


import pyqtgraph as pg

class DiodeThermometerThread(QThread):
    voltageMeasured = pyqtSignal(float)
    errorDetected = pyqtSignal(str)

    def __init__(self, sourceMeter, parent=None):
        QThread.__init__(self, parent)
        self.sourceMeter = sourceMeter
        self.interval = 0.25
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
                for i in range(6):
                    t = time.time()
                    r = sourceMeter.obtainReading()
                    V = r.voltage
                    print "V=", V, '(', r.status, ')'
                    self.voltageMeasured()
                    self.sleepPrecise(t)
        except Exception,e:
            self.errorDetected.emit(e)




class DiodeThermometerWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(DiodeThermometerWidget, self).__init__(parent)
        self.sr830 = None
        self.setupUi(self)
        self.outputFile = None

        self.plot.addLegend()
        self.curveDc = pg.PlotCurveItem(name='DC', symbol='o', pen='g', )
        self.plot.addItem(self.curveAcY)

        self.clearData()

        self.msmThread = None
        self.restoreSettings()
        #self.plot = self.plotWidget.canvas.ax.plot([], 'o', label='')
        self.startPb.clicked.connect(self.startPbClicked)
        self.stopPb.clicked.connect(self.stopPbClicked)
        self.clearPb.clicked.connect(self.clearData)
        self.yAxisCombo.currentIndexChanged.connect(self.updatePlot)

    def startPbClicked(self):
        address = str(self.k6430VisaCombo.currentText())
        sourceMeter = Keithley6430(address)
        print "Instrument ID:", sourceMeter.visaId()
        self.enableWidgets(False)

        thread = , self)
        thread.measurementReady.connect(self.collectMeasurement)
        thread.error.connect(self.errorDisplay.append)
        thread.finished.connect(self.runNextMeasurement)
        self.rampRateSb.valueChanged.connect(thread.setRampRate)
        self.stopPb.clicked.connect(self.thread.stop)

        timeString = time.strftime('%Y%m%d-%H%M%S')
        fileName = self.sampleLineEdit.text()+'_%s_Sweep.dat' % timeString
        self.outputFile = open(fileName, 'a+')
        self.outputFile.write('#Program=Transition2.py\n')
        self.outputFile.write('#Date=%s\n' % timeString)
        self.outputFile.write('#Comment=%s\n' % self.commentLineEdit.text())
        self.outputFile.write('#Source=%s\n' % self.sourceModeCombo.currentText())
        self.outputFile.write('#DC source ID=%s\n' % instrumentVisaId(self.dcSource))
        self.outputFile.write('#'+'\t'.join(['time', 'T', 'Vdc', 'f', 'X', 'Y', 'state', 'enabled' ])+'\n')
        self.msmThread.start()
        print "Thread started"

    def clearData(self):
        self.ts = []
        self.Vdcs = []
        self.updatePlot()

    def collectMeasurement(self, t, T, Vdc, f, X, Y, state, enabled):
        string = "%.3f\t%.6f\t%.6g\t%.4g\t%.6g\t%.6g\t%d\t%d\n" % (t, T, Vdc, f, X, Y, state, enabled)
        self.outputFile.write(string)

        #print "Collecting data:", enabled, state, t
        self.ts.append(t)
        self.Ts.append(T)
        self.Vdcs.append(Vdc)
        self.updatePlot()

    def updatePlot(self):
        t0 = self.ts[0] if len(self.ts) > 0 else 0
        x = np.asarray(self.ts) - t0
        self.plot.setLabel('bottom', 'time', units='s')

        yAxis = self.yAxisCombo.currentText()
        if yAxis == 'Voltage':
            dc = self.Vdcs
            self.plot.setLabel('left', 'V', units='V')
        elif yAxis == 'Resistance':
            dc = self.Rdcs
            self.plot.setLabel('left', 'R', units=u'Ω')

        self.curveDc.setData(x, dc)

    def updateStatus(self, message):
        self.stateLineEdit.setText(message)

    def enableWidgets(self, enable=True):
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)

    def stopPbClicked(self):
        self.msmThread.stop()
        self.stop = True

    def closeEvent(self, e):
        if self.msmThread is not None:
            self.msmThread.stop()
        self.saveSettings()
        super(DiodeThermometerWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
        s.setValue('sampleId', self.sampleLineEdit.text())
        s.setValue('comment', self.commentLineEdit.text())
        saveCombo(self.sourceModeCombo, s)
        s.setValue('acDriveImpedance', self.acDriveImpedanceSb.value() )
        s.setValue('dcDriveImpedance', self.dcDriveImpedanceSb.value() )
        s.setValue('acDriveEnable', self.acGroupBox.isChecked() )
        s.setValue('dcDriveEnable', self.dcGroupBox.isChecked() )
        saveCombo(self.dcSourceCombo, s)
        saveCombo(self.dcReadoutCombo, s)
        s.setValue('dcSource', self.dcSourceCombo.currentText() )
        s.setValue('dcReadout', self.dcReadoutCombo.currentText() )
        s.setValue('minTemp', self.minTempSb.value())
        s.setValue('maxTemp', self.maxTempSb.value())
        s.setValue('rampRate', self.rampRateSb.value())
        s.setValue('preampGain', self.preampGainSb.value())
        s.setValue('geometry', self.saveGeometry())
        saveCombo(self.sr830VisaCombo, s)
        saveCombo(self.dmmVisaCombo, s)

        s.beginGroup('ai'); self.aiConfig.saveSettings(s); s.endGroup()
        s.beginGroup('ao'); self.aoConfig.saveSettings(s); s.endGroup()

        nRows = self.biasTable.rowCount()
        s.beginWriteArray('biasTable', nRows)
        for row in range(nRows):
            s.setArrayIndex(row)
            s.setValue('f', self.biasTable.cellWidget(row,0).value())
            s.setValue('Vac', self.biasTable.cellWidget(row,1).value())
            s.setValue('Vdc', self.biasTable.cellWidget(row,2).value())
            s.setValue('cycles', self.biasTable.cellWidget(row,3).value())
        s.endArray()


    def restoreSettings(self):
        s = QSettings()
        self.sampleLineEdit.setText(s.value('sampleId', '', type=QString))
        self.commentLineEdit.setText(s.value('comment', '', type=QString))
        restoreCombo(self.sourceModeCombo, s)
        self.acDriveImpedanceSb.setValue(s.value('acDriveImpedance', 10E3, type=float))
        self.dcDriveImpedanceSb.setValue(s.value('dcDriveImpedance', 10E3, type=float))
        self.acGroupBox.setChecked(s.value('acDriveEnable', True, type=bool))
        self.dcGroupBox.setChecked(s.value('dcDriveEnable', True, type=bool))
        restoreCombo(self.dcSourceCombo, s)
        restoreCombo(self.dcReadoutCombo, s)
        self.minTempSb.setValue(s.value('minTemp', 0.05, type=float))
        self.maxTempSb.setValue(s.value('maxTemp', 0.20, type=float))
        self.rampRateSb.setValue(s.value('rampRate', 10., type=float))
        self.preampGainSb.setValue(s.value('preampGain', 1., type=float))
        restoreCombo(self.sr830VisaCombo, s)
        restoreCombo(self.dmmVisaCombo, s)

if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.WARN)

    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('Diode Thermometer')
    mw = DiodeThermometerWidget()
    mw.show()
    app.exec_()

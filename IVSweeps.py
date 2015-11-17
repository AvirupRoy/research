# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 17:15:17 2015

@author: wisp10
"""


from SR830 import SR830
from Agilent34401A import Agilent34401A
from PyQt4.QtGui import QWidget, QDoubleSpinBox, QSpinBox, QHeaderView
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QSettings, QString, QByteArray

import IVSweepsUi
import time
from Transition import TemperatureSubscriber
import numpy as np

class IVSweepMeasurement(QThread):
    readingAvailable = pyqtSignal(float,float,float,float)
    def __init__(self, sr830, dmm, parent=None):
        QThread.__init__(self, parent)
        self.sr830 = sr830
        self.dmm = dmm
        self.paused = False
        self.T = np.nan

    def setFileName(self, fileName):
        self.fileName = fileName

    def setVoltages(self, voltages):
        self.voltages = voltages

    def stop(self):
        self.stopRequested = True

    def pause(self, pause=True):
        self.paused = pause

    def unpause(self):
        self.pause(False)

    def updateTemperature(self, T):
        self.T = T

    def run(self):
        self.stopRequested = False
        print "Thread running"
        self.dmm.setFunctionVoltageDc()
        self.dmm.commandString('SENS:VOLT:DC:NPLC 10')
        with open(self.fileName, 'a+') as f:
            print "File:", f
            while not self.stopRequested:
                voltages = self.voltages
                self.sr830.setAuxOut(1,voltages[0])
                self.sleep(1)
                for Vsource in voltages:
                    self.sr830.setAuxOut(1,Vsource)
                    self.msleep(150)
                    t = time.time()
                    Vmeas = self.dmm.reading()
                    self.readingAvailable.emit(t,Vsource,Vmeas,self.T)
                    string = "%.3f\t%.3f\t%.7f\t%.6f\n" % (t, Vsource, Vmeas, self.T)
                    f.write(string)
                    while(self.paused):
                        self.msleep(100)
                    if self.stopRequested:
                        break

        self.sr830.setAuxOut(1,0)


from PyQt4.Qwt5 import Qwt, QwtPlotCurve, QwtPlot

class IVSweepWidget(IVSweepsUi.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(IVSweepWidget, self).__init__(parent)
        self.setupUi(self)
        self.restoreSettings()
        self.msmThread = None
        self.startPb.clicked.connect(self.startPbClicked)
        self.adrTemp = TemperatureSubscriber(self)
        self.adrTemp.adrTemperature.connect(self.temperatureSb.setValue)
        self.adrTemp.start()
        self.plot.setAxisTitle(QwtPlot.yLeft, 'Vmeas')
        self.plot.setAxisTitle(QwtPlot.xBottom, 'Vdrive')
        self.curve = QwtPlotCurve('')
        self.curve.attach(self.plot)
        self.clearData()
        self.clearPb.clicked.connect(self.clearData)

    def clearData(self):
        self.Vdrive = []
        self.Vmeas = []
        self.curve.setData(self.Vdrive, self.Vmeas)
        self.plot.replot()

    def updateData(self, t,Vsource,Vmeas,T):
        self.Vdrive.append(Vsource)
        self.Vmeas.append(Vmeas)
        self.curve.setData(self.Vdrive, self.Vmeas)
        self.plot.replot()

    def startPbClicked(self):
        self.dmm = Agilent34401A(str(self.dmmCombo.currentText()))
        if not '34401A' in self.dmm.visaId():
            print 'Agilent DMM not found.'
            return
        self.sr830 = SR830(str(self.sr830Combo.currentText()))
        if not 'SR830' in self.sr830.visaId():
            print 'SR830 not found.'
            return
        self.enableWidgets(False)
        fileName = self.sampleLineEdit.text()+'_IV.dat'
        self.msmThread = IVSweepMeasurement(self.sr830, self.dmm, self)
        self.msmThread.setFileName(fileName)
        self.msmThread.readingAvailable.connect(self.updateData)
        Vs1 = np.linspace(self.startVSb.value(), self.stopVSb.value(), self.stepsSb.value())
        Vs2 = np.linspace(self.stopVSb.value(), self.stop2VSb.value(), self.steps2Sb.value())
        Vs = np.append(Vs1,Vs2[1:])
        Vs = np.append(Vs,Vs[-2::-1])
        print Vs
        self.msmThread.setVoltages(Vs)
        self.adrTemp.adrTemperature.connect(self.msmThread.updateTemperature)
        self.msmThread.finished.connect(self.finished)
        self.stopPb.clicked.connect(self.msmThread.stop)
        self.msmThread.start()
        print "Thread started"

    def finished(self):
        self.enableWidgets(True)
#        self.updateStatus('Completed')

    def enableWidgets(self, enable=True):
        self.sampleLineEdit.setEnabled(enable)
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(~enable)
        self.dcDriveImpedanceSb.setEnabled(enable)

    def closeEvent(self, e):
        if self.msmThread:
            self.msmThread.stop()
        if self.adrTemp:
            self.adrTemp.stop()
        self.saveSettings()
        super(IVSweepWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
        s.setValue('sampleId', self.sampleLineEdit.text())
        s.setValue('dcDriveImpedance', self.dcDriveImpedanceSb.value() )
        s.setValue('startV', self.startVSb.value())
        s.setValue('stopV', self.stopVSb.value())
        s.setValue('step', self.stepsSb.value())
        s.setValue('stop2V', self.stop2VSb.value())
        s.setValue('step2', self.steps2Sb.value())

        s.setValue('preampGain', self.preampGainSb.value())
        s.setValue('geometry', self.saveGeometry())
        s.setValue('sr830Visa', self.sr830Combo.currentText())
        s.setValue('dmmVisa', self.dmmCombo.currentText())

    def restoreSettings(self):
        s = QSettings()
        self.sampleLineEdit.setText(s.value('sampleId', '', type=QString))
        self.dcDriveImpedanceSb.setValue(s.value('dcDriveImpedance', 10E3, type=float))
        self.startVSb.setValue(s.value('startV', 0, type=float))
        self.stopVSb.setValue(s.value('stopV', 3, type=float))
        self.stepsSb.setValue(s.value('steps', 10, type=int))
        self.stop2VSb.setValue(s.value('stop2V', 6, type=float))
        self.steps2Sb.setValue(s.value('steps2', 10, type=int))
        self.preampGainSb.setValue(s.value('preamGain', 1., type=float))
        i = self.sr830Combo.findText(s.value('sr830Visa', '', type=str))
        self.sr830Combo.setCurrentIndex(i)
        i = self.dmmCombo.findText(s.value('dmmVisa', '', type=str))
        self.dmmCombo.setCurrentIndex(i)

        geometry = s.value('geometry', QByteArray(), type=QByteArray)
        self.restoreGeometry(geometry)

from Transition import ExceptionHandler

if __name__ == '__main__':
    import sys
    import logging

    logging.basicConfig(level=logging.WARNING)

    exceptionHandler = ExceptionHandler()
    sys._excepthook = sys.excepthook
    sys.excepthook = exceptionHandler.handler


    from PyQt4.QtGui import QApplication
    #from PyQt4.QtCore import QTimer

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('IVSweep')

    mw = IVSweepWidget()
    mw.show()
    app.exec_()

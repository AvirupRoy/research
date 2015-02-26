# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 22:03:13 2015

@author: jaeckel
"""

import time

from PyQt4.QtGui import QApplication, QWidget, QPen, QFileDialog
from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QTimer, QString, QFileInfo
from PyQt4.Qwt5 import QwtPlotCurve, QwtPlot
from PyQt4.Qt import Qt

from PowerSensorUi import Ui_Form      # My own widget

class Thermistor(object):
    def __init__(self):
        self.a = 0.00163262813407
        self.b = 0.000245889470447
        self.c = 7.11197544349e-08

    def temperature(self, R):
        lnR = np.log(R)
        T = 1./(self.a+self.b*lnR+self.c*lnR**3)


class WorkerThread(QThread):
    readingsAvailable = pyqtSignal(float, float, float, float)

    def __init__(self, sourceMeter):
        QThread.__init__(self)
        self.sourceMeter = sourceMeter
        self.thermistor = Thermistor()

    def run(self):
        V = self.sourceMeter.measureVoltage()
        I = self.sourceMeter.current()
        R = V/I
        T = self.thermistor.temperature(R)
        P = V*I
        self.readingsAvailable.emit(time.time(), V, I, T)

class PowerSensorWidget(QWidget, Ui_Form):
    def __init__(self, sourceMeter):
        QWidget.__init__(self)
        self.setWindowTitle('Power Sensor')

        self.sourceMeter = sourceMeter
        self.setupUi(self)

        self.workerThread = None

        plot = self.temperaturePlot
        plot.setAxisTitle(QwtPlot.yLeft, 'T [K]')
        plot.setAxisTitle(QwtPlot.xBottom, 't [s]')
        plot.setCanvasBackground(Qt.black)
        plot.setTitle('Sensor temperature')
        curve = QwtPlotCurve('Temperature')
        curve.setPen(QPen(Qt.white))
        curve.attach(plot)
        self.temperatureCurve = curve

        plot = self.powerPlot
        plot.setAxisTitle(QwtPlot.yLeft, 'P [mW]')
        plot.setAxisTitle(QwtPlot.xBottom, 't [s]')
        plot.setCanvasBackground(Qt.black)
        plot.setTitle('Sensor power')
        curve = QwtPlotCurve('Power')
        curve.setPen(QPen(Qt.white))
        curve.attach(plot)
        self.powerCurve = curve
        self.clearData()

#        self.timer = QTimer()
#        self.timer.setInterval(500)
#        self.timer.timeout.connect(self.measure)

        self.loadSettings()

    def loadSettings(self):
        settings = QSettings()
        self.targetVoltageSb.setValue(settings.value('TargetVoltage', 0.0, type=float))

    def saveSettings(self):
        settings = QSettings()
        settings.setValue('TargetVoltage', self.targetVoltageSb.value())

    def closeEvent(self, e):
        self.saveSettings()

    def clearData(self):
        self.t = []
        self.power = []
        self.T = []
        self.temperatureCurve.setData(self.t, self.T)
        self.powerCurve.setData(self.t, self.power)
        self.plot.replot()

   def startTask(self, chargingMode):
        thread = WorkerThread(self.sourceMeter)
        thread.finished.connect(self.taskFinished)
        thread.started.connect(self.taskStarted)
        thread.readingsAvailable.connect(self.updateReadings)
        #thread.voltageUpdated.connect(self.updateVoltage)
        #thread.heaterEnabled.connect(self.updateHeater)
        self.workerThread = thread
        thread.start()

    def taskStarted(self):
        pass
        #self.enableOperationButtons(False)

    def taskFinished(self):
        #self.Jobs[-1]['tstop'] = MatlabDate()
        #self.timer.stop()
        #self.enableOperationButtons(True)
        self.workerThread.deleteLater()

   def updateReadings(self, t, V, I, T):
        """Measure and record SQUID output through digital voltmeter."""
        P = V*I
        self.power.append(P)
        self.T.append(T)
        self.t.append(t)
        self.curve.setData(self.t, self.Squid)
        self.plot.replot()


if __name__ == '__main__':
    import sys
    from Keithley6430 import Keithley6430

    sourceMeter = Keithley6430('GPIB0::10')
    print 'Using source meter:', sourceMeter.visaId()

    app = QApplication(sys.argv)
    QApplication.setOrganizationName("BoydLabUNM");
    QApplication.setOrganizationDomain("phonon.phys.unm.edu");
    QApplication.setApplicationName("PersistentSwitchCharger");
    mainWindow = PersistentSwitchWidget(fg, dmm)
    mainWindow.show()

    app.exec_()

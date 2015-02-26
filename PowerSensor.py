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

class WorkThread(QThread):
    voltageUpdated = pyqtSignal(float)

    def __init__(self, fg):
        QThread.__init__(self)

   def run(self):
       pass

class PersistentSwitchWidget(QWidget, Ui_Form):
    def __init__(self,fg, dmm):
        QWidget.__init__(self)
        #self.setupUi(self)
        self.setWindowTitle('Persistent Switch Charger')

        self.fg = fg
        self.dmm = dmm
        self.setupUi(self)

        self.psThread = None

        self.chargeButton.clicked.connect(self.triggerCharging)
        self.dischargeButton.clicked.connect(self.triggerDischarging)
        self.clearButton.clicked.connect(self.clearData)
        self.saveButton.clicked.connect(self.save)

        self.plot.setAxisTitle(QwtPlot.yLeft, 'V [V]')
        self.plot.setAxisTitle(QwtPlot.xBottom, 't [s]')
        self.plot.setCanvasBackground(Qt.black)
        self.plot.setTitle('SQUID output')
        self.curve = QwtPlotCurve('SQUID response')
        self.curve.setPen(QPen(Qt.white))
        self.curve.attach(self.plot)
        self.clearData()

        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.measure)

        self.loadSettings()

    def loadSettings(self):
        settings = QSettings()
        self.targetVoltageSb.setValue(settings.value('TargetVoltage', 0.0, type=float))
        self.chargingRateSb.setValue(settings.value('chargingRate', 10.0, type=float))
        self.fastRateSb.setValue(settings.value('fastRate', 20.0, type=float))
        self.holdTimeSb.setValue(settings.value('holdTime', 10, type=int))
        self.pulseHeightSb.setValue(settings.value('pulseHeight', 7.5, type=float))
        self.pulseWidthSb.setValue(settings.value('pulseWidth', 1.0, type=float))
        self.repetitionRateSb.setValue(settings.value('repetitionRate', 5.0, type=float))

    def saveSettings(self):
        settings = QSettings()
        settings.setValue('TargetVoltage', self.targetVoltageSb.value())
        settings.setValue('chargingRate', self.chargingRateSb.value())
        settings.setValue('fastRate', self.fastRateSb.value())
        settings.setValue('holdTime', self.holdTimeSb.value())
        settings.setValue('pulseHeight', self.pulseHeightSb.value())
        settings.setValue('pulseWidth', self.pulseWidthSb.value())
        settings.setValue('repetitionRate', self.repetitionRateSb.value())
    def closeEvent(self, e):
        self.saveSettings()

    def clearData(self):
        self.t = []
        self.Squid = []
        self.Drive = []
        self.curve.setData(self.t, self.Squid)
        self.t0 = None
        self.t0Matlab = None
        self.driveVoltage = 0.0
        self.Jobs = []
        self.plot.replot()
   def startTask(self, chargingMode):
        self.psThread = PersistentSwitchThread(fg)
        self.psThread.finished.connect(self.taskFinished)
        self.psThread.started.connect(self.taskStarted)
        self.psThread.voltageUpdated.connect(self.updateVoltage)
        self.psThread.heaterEnabled.connect(self.updateHeater)
         self.psThread.start()
    def taskStarted(self):
        self.enableOperationButtons(False)

    def taskFinished(self):
        self.Jobs[-1]['tstop'] = MatlabDate()
        self.timer.stop()
        self.enableOperationButtons(True)
        self.psThread.deleteLater()

   def measure(self):
        """Measure and record SQUID output through digital voltmeter."""
        if not self.t0:
            self.t0 = time.time()
            self.t0Matlab = MatlabDate()
        v = self.dmm.voltageDc()
        self.Squid.append(v)
        self.Drive.append(self.driveVoltage)
        self.t.append(time.time()-self.t0)
        self.curve.setData(self.t, self.Squid)
        self.plot.replot()

if __name__ == '__main__':
    import sys
    sys.path.append('..\\') # For VISA
    from VISA.Keithley6430 import Keithley6430

    sourceMeter = Keithley6430('GPIB0::10')
    print 'Using source meter:', sourceMeter.visaId()

    app = QApplication(sys.argv)
    QApplication.setOrganizationName("BoydLabUNM");
    QApplication.setOrganizationDomain("phonon.phys.unm.edu");
    QApplication.setApplicationName("PersistentSwitchCharger");
    mainWindow = PersistentSwitchWidget(fg, dmm)
    mainWindow.show()

    app.exec_()

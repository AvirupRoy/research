# -*- coding: utf-8 -*-
"""
Created on Fri May 22 13:03:06 2015
GUI to control the magnet via Agilent 6641A power supply and programming voltage provided by either Keithley 6430 or NI DAQ

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S', filename='MagnetControl.log', filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)

from MagnetSupply2 import MagnetControlThread
from MagnetSupply import MagnetControlRequestReplyThread
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSignal, QObject, QSettings, QByteArray

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

import MagnetControl2Ui

from Zmq.Ports import RequestReply
import pyqtgraph as pg
import time
import numpy as np

from Utility.Math import pruneData

mA_per_min = 1E-3/60.
mOhm = 1E-3

class MagnetControlWidget(MagnetControl2Ui.Ui_Widget, QWidget):
    '''The GUI for magnet control'''
    def __init__(self, parent=None):
        super(MagnetControlWidget, self).__init__(parent)
        self.setupUi(self)
        
        self.rampRateSb.valueChanged.connect(self.rampRateChanged)
        self.controlModeCombo.currentIndexChanged.connect(self.controlModeChanged)
        self.magnetThread = None
        axis = pg.DateAxisItem(orientation='bottom')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis})
        self.plot.setBackground('w')
        self.plot.plotItem.showGrid(x=True, y=True)
        self.verticalLayout_3.addWidget(self.plot)
        self.curve = pg.PlotCurveItem(name='Actual', symbol='o', pen='k')
        self.plot.addItem(self.curve)
        self.clearData()
        self.yaxisCombo.currentIndexChanged.connect(self.switchPlotAxis)
        self.switchPlotAxis()
        self.runPb.clicked.connect(self.run)
        self.magnetThread = None
        self.restoreSettings()
        
    def run(self):
        if self.magnetThread is not None:
            self.stopThreads()
        else:
            self.startThreads()
        
            
    def controlModeChanged(self, index):
        mode = self.controlModeCombo.currentText()
        if self.magnetThread is None:
            return
        self.magnetThread.setControlMode(mode)
            
    def clearData(self):
        self.ts = [] # Time 
        self.Iss = [] # Supply current
        self.Vss = [] # Supply voltage
        self.Vfets = [] # FET output voltage
        self.Vms = [] # Magnet voltage
        self.Ics = [] # Current (coarse)
        self.Ifs = [] # Current (fine)
        self.updatePlot()

    def switchPlotAxis(self):
        yaxis = self.yaxisCombo.currentText()
        yax = self.plot.getAxis('left')
        if yaxis == 'Supply I':
            yax.setLabel('I supply', 'A')
        elif yaxis == 'Supply V':
            yax.setLabel('V supply', 'V')
        elif yaxis == 'Magnet V':
            yax.setLabel('V magnet', 'V')
        elif yaxis == 'FET V':
            yax.setLabel('V FET', 'V' )
        elif yaxis == 'Magnet I (coarse)':
            yax.setLabel('I magnet (coarse)', 'A')
        elif yaxis == 'Magnet I (fine)':
            yax.setLabel('I magnet (fine)', 'A')
        self.updatePlot()
        plotItem = self.plot.getPlotItem()
        vb = plotItem.getViewBox()
        vb.enableAutoRange(pg.ViewBox.YAxis, True)
        vb.enableAutoRange(pg.ViewBox.YAxis, False)
        
    def updatePlot(self):
        yaxis = self.yaxisCombo.currentText()
        if yaxis == 'Supply I':
             y = self.Iss
        elif yaxis == 'Supply V':
            y = self.Vss
        elif yaxis == 'Magnet V':
            y = self.Vms
        elif yaxis == 'FET V':
            y = self.Vfets
        elif yaxis == 'Magnet I (coarse)':
            y = self.Ics
        elif yaxis == 'Magnet I (fine)':
            y = self.Ifs
        
        self.curve.setData(self.ts, y)

    def collectData(self, time, supplyCurrent, supplyVoltage, fetVoltage, magnetVoltage, currentCoarse, currentFine, dIdt, VoutputProgrammed, VmagnetProgrammed):
        '''Collect the data for plotting'''
        self.ts.append(time)
        self.Iss.append(supplyCurrent)
        self.Vss.append(supplyVoltage)
        self.Vfets.append(fetVoltage)
        self.Vms.append(magnetVoltage)
        self.Ics.append(currentCoarse)
        self.Ifs.append(currentFine)
        self.supplyCurrentSb.setValue(supplyCurrent)
        self.supplyVoltageSb.setValue(supplyVoltage)
        self.outputVoltageSb.setValue(fetVoltage)
        self.magnetVoltageSb.setValue(magnetVoltage)
        self.currentCoarseSb.setValue(currentCoarse)
        self.currentFineSb.setValue(currentFine)
        self.dIdtSb.setValue(dIdt/mA_per_min)
        
        if np.isfinite(currentFine):
            I = currentFine
        elif np.isfinite(currentCoarse):
            I = currentCoarse
        else:
            I = supplyCurrent
        
        self.I = I
        V_sd = supplyVoltage-fetVoltage
        self.fetSourceDrainVoltageSb.setValue(V_sd)
        self.fetPowerSb.setValue(I*V_sd)
        self.magnetPowerSb.setValue(I*magnetVoltage)
        if self.magnetThread is not None:
            self.resistorPowerSb.setValue(I**2*self.magnetThread.Rsense)        

        maxLength = 20000
        self.ts  = pruneData(self.ts, maxLength)
        self.Iss = pruneData(self.Iss, maxLength)
        self.Vss = pruneData(self.Vss, maxLength)
        self.Vfets = pruneData(self.Vfets, maxLength)
        self.Vms = pruneData(self.Vms, maxLength)
        self.Ics = pruneData(self.Ics, maxLength)
        self.Ifs = pruneData(self.Ifs, maxLength)
        self.updatePlot()
        
    def updateDiodeVoltage(self, Vdiode):
        self.diodeVoltageSb.setValue(Vdiode)
        self.diodePowerSb.setValue(self.I* Vdiode)

    def startThreads(self):
        from Visa.Agilent6641A import Agilent6641A
        ps = Agilent6641A('GPIB0::5')
        visaId = ps.visaId()
        if not '6641A' in visaId:
            self.collectMessage('error', 'Agilent 6641A not found!')
            return
        self.collectMessage('info', 'Using Agilent 6641A (%s)' % visaId)
        self.ps = ps            
        magnetThread = MagnetControlThread(self.ps)
        self.magnetThread = magnetThread
        magnetThread.message.connect(self.collectMessage)
        magnetThread.controlModeChanged.connect(self.updateControlMode)
        magnetThread.outputVoltageCommanded.connect(self.maybeUpdateCommandedVoltage)
        magnetThread.diodeVoltageUpdated.connect(self.updateDiodeVoltage)
        magnetThread.resistanceUpdated.connect(self.updateResistance)
        magnetThread.resistiveVoltageUpdated.connect(self.resistiveDropSb.setValue)
        magnetThread.measurementAvailable.connect(self.collectData)
        magnetThread.dIdtIntegralAvailable.connect(self.updatedIdtIntegral)
        magnetThread.enableIdtCorrection(self.dIdtCorrectionCb.isChecked())
        magnetThread.finished.connect(self.threadFinished)
        magnetThread.started.connect(self.threadStarted)
        self.outputVoltageCommandSb.valueChanged.connect(magnetThread.commandOutputVoltage)
        self.dIdtCorrectionCb.toggled.connect(magnetThread.enableIdtCorrection)
        self.magnetThread.start()
        self.remoteControlThread = MagnetControlRequestReplyThread(port=RequestReply.MagnetControl, parent=self)
        self.remoteControlThread.changeRampRate.connect(self.changeRampRate)
        self.remoteControlThread.associateMagnetThread(self.magnetThread)
        self.remoteControlThread.allowRequests(self.zmqRemoteEnableCb.isChecked())
        self.zmqRemoteEnableCb.toggled.connect(self.remoteControlThread.allowRequests)
        self.remoteControlThread.start()
        
        
        
    def maybeUpdateCommandedVoltage(self, V):
        if self.controlModeCombo.currentText != 'Manual':
            self.outputVoltageCommandSb.setValue(V)
        
    def stopThreads(self):
        self.remoteControlThread.stop()
        self.magnetThread.stop()
        self.remoteControlThread.wait(2000)
        self.magnetThread.wait(2000)
        self.magnetThread.deleteLater()
        self.remoteControlThread.deleteLater()
        self.remoteControlThread = None
        self.magnetThread = None


    def threadStarted(self):
        self.runPb.setText('Stop')

    def threadFinished(self):
        self.runPb.setText('Run')
    
    def collectMessage(self, kind, message):
        if kind == 'info':
            color = 'black'
            pass
        elif kind == 'warning':
            color = 'orange'
            pass
        elif kind == 'error':
            color = 'red'
            pass
        timeString = time.strftime("%H:%M:%S")
        text = '<font color="%s">%s: %s</font><br>' % (color, timeString, message)
        self.messagesTextEdit.appendHtml(text)

    def updatedIdtIntegral(self, Apers):
        self.dIdtIntegralSb.setValue(Apers/mA_per_min)
        
    def updateControlMode(self, mode, rampLimit):
        i = self.controlModeCombo.findText(mode)

        old = self.controlModeCombo.blockSignals(True)
        self.controlModeCombo.setCurrentIndex(i)
        self.controlModeCombo.blockSignals(old)
        
        limit = rampLimit / mA_per_min
        self.rampRateSb.setMinimum(-limit)
        self.rampRateSb.setMaximum(+limit)
        if mode == 'Manual':
            self.outputVoltageCommandSb.setReadOnly(False)
            self.outputVoltageCommandSb.blockSignals(False)
#            self.outputVoltageCommandSb.setValue(self.magnetThread.outputVoltage())
        else:
            self.outputVoltageCommandSb.blockSignals(True)
            self.outputVoltageCommandSb.setReadOnly(True)
            
#    def updateOutputVoltageCommand(self, V):
#        old = self.outputVoltageCommandSb.blockSignals(True)
#        self.outputVoltageCommandSb.setValue(V)
#        self.outputVoltageCommandSb.blockSignals(old)
        
    def changeRampRate(self, A_per_s):
        self.rampRateSb.setValue(A_per_s / mA_per_min)
        
    def rampRateChanged(self, rate):
        if abs(rate) < 120.:
            self.controlModeCombo.setEnabled(True)
        A_per_s = rate*mA_per_min
        if self.magnetThread:
            self.magnetThread.setRampRate(A_per_s)

    def updateRampRateDisplay(self, rate):
        block = self.rampRateSb.blockSignals(True)
        self.rampRateSb.setValue(rate/mA_per_min)
        self.rampRateSb.blockSignals(block)

    def updateResistance(self, R):
        self.resistanceSb.setValue(R/mOhm)
        self.wiringPowerSb.setValue(self.I**2*R)

    def closeEvent(self, e):
        print "Closing"
        if self.magnetThread:
            self.stopThreads()
        self.saveSettings()
        super(MagnetControlWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
        s.setValue('ZmqRemoteEnable', self.zmqRemoteEnableCb.isChecked())
        s.setValue('dIdtCorrectionEnable', self.dIdtCorrectionCb.isChecked())
        s.setValue('plotYAxis', self.yaxisCombo.currentText())
        s.setValue("windowGeometry", self.saveGeometry())

    def restoreSettings(self):
        s = QSettings()
        self.zmqRemoteEnableCb.setChecked(s.value('ZmqRemoteEnable', False, type=bool))        
        self.dIdtCorrectionCb.setChecked(s.value('dIdtCorrectionEnable', False, type=bool))
        i = self.yaxisCombo.findText(s.value('plotYAxis', '', type=str))
        self.yaxisCombo.setCurrentIndex(i)
        self.restoreGeometry(s.value("windowGeometry", '', type=QByteArray))

class ExceptionHandler(QObject):
    errorSignal = pyqtSignal()
#    silentSignal = pyqtSignal()

    def __init__(self):
        super(ExceptionHandler, self).__init__()

    def handler(self, exctype, value, traceback):
        self.errorSignal.emit()
        print "ERROR CAPTURED", value, traceback
        sys._excepthook(exctype, value, traceback)

if __name__ == '__main__':
    import sys

    exceptionHandler = ExceptionHandler()
    sys._excepthook = sys.excepthook
    sys.excepthook = exceptionHandler.handler


    from PyQt4.QtGui import QApplication, QIcon

    import ctypes
    myappid = u'WISCXRAYASTRO.ADR3.MAGNETCONTROL.2' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('ADR3 Magnet Control')
    app.setWindowIcon(QIcon('Icons/solenoid-round-150rg.png'))

    mw = MagnetControlWidget()
    mw.show()
    app.exec_()

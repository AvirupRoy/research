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

def pruneData(y, maxLength=20000, fraction=0.3): # This is copied from AVS47, should put somewhere else
    if len(y) < maxLength:
        return y
    start = int(fraction*maxLength)
    firstSection = 0.5*(np.asarray(y[0:start:2])+np.asarray(y[1:start+1:2]))
    return np.hstack( (firstSection, y[start+1:]) ).tolist()

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
        self.verticalLayout_3.addWidget(self.plot)
        self.curve = pg.PlotCurveItem(name='Actual', symbol='o', pen='g')
        self.plot.addItem(self.curve)
        self.clearData()
        self.yaxisCombo.currentIndexChanged.connect(self.switchPlotAxis)
        self.switchPlotAxis()
        self.runPb.clicked.connect(self.run)
        self.magnetThread = None
        
    def run(self):
        if self.magnetThread is not None:
            self.stopThreads()
        else:
            self.startThreads()
        
    def rampRateChanged(self, value):
        if abs(value) < 120.:
            self.controlModeCombo.setEnabled(True)
            
    def controlModeChanged(self, index):
        mode = self.controlModeCombo.currentText()
        enable = mode == 'Analog'
        if self.magnetThread is not None:
            self.magnetThread.enableMagnetVoltageControl(enable)
            
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
        magnetThread.analogFeedbackChanged.connect(self.updateAnalogFeedbackStatus)
        magnetThread.diodeVoltageUpdated.connect(self.updateDiodeVoltage)
        magnetThread.resistanceUpdated.connect(self.updateResistance)
        magnetThread.resistiveVoltageUpdated.connect(self.resistiveDropSb.setValue)
        magnetThread.measurementAvailable.connect(self.collectData)
        magnetThread.dIdtIntegralAvailable.connect(self.updatedIdtIntegral)
        magnetThread.enableIdtCorrection(self.dIdtCorrectionCb.isChecked())
        self.dIdtCorrectionCb.toggled.connect(magnetThread.enableIdtCorrection)
        self.magnetThread.start()
        self.rampRateSb.valueChanged.connect(self.applyNewRampRate)
        self.remoteControlThread = MagnetControlRequestReplyThread(port=RequestReply.MagnetControl, parent=self)
        self.remoteControlThread.changeRampRate.connect(self.changeRampRate)
        self.remoteControlThread.associateMagnetThread(self.magnetThread)
        self.remoteControlThread.allowRequests(self.zmqRemoteEnableCb.isChecked())
        self.zmqRemoteEnableCb.toggled.connect(self.remoteControlThread.allowRequests)
        self.remoteControlThread.start()
        self.runPb.setText('Stop')
        
    def stopThreads(self):
        self.remoteControlThread.stop()
        self.magnetThread.stop()

        self.remoteControlThread.wait(2000)
        self.magnetThread.wait(2000)
        self.magnetThread.deleteLater()
        self.remoteControlThread.deleteLater()
        self.remoteControlThread = None
        self.magnetThread = None
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
        
    def updateAnalogFeedbackStatus(self, enabled):
        mode = 'Analog' if enabled else 'Digital'
        i = self.controlModeCombo.findText(mode)
        old = self.controlModeCombo.blockSignals(True)
        self.controlModeCombo.setCurrentIndex(i)
        if enabled:
            self.rampRateSb.setMinimum(-380.)
            self.rampRateSb.setMaximum(+380.)
        else:
            self.rampRateSb.setMinimum(-800.)
            self.rampRateSb.setMaximum(+800.)
        self.controlModeCombo.blockSignals(old)
        
    def changeRampRate(self, A_per_s):
        self.rampRateSb.setValue(A_per_s / mA_per_min)
        
    def applyNewRampRate(self, rate):
        A_per_s = rate*mA_per_min
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
        self.yaxisCombo.setCurrentIndex(self.yaxisCombo.findText(s.value('plotYAxis', '', dtype=str)))
        self.restoreGeometry(s.value("windowGeometry", '', dtype=QByteArray))

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

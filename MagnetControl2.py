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

from MagnetSupply2 import MagnetControlThread #, MagnetControlRequestReplyThread
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSignal, QObject, QSettings

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

import MagnetControl2Ui

from Zmq.Ports import RequestReply
import pyqtgraph as pg

import numpy as np
def pruneData(y, maxLength=20000, fraction=0.3): # This is copied from AVS47, should put somewhere else
    if len(y) < maxLength:
        return y
    start = int(fraction*maxLength)
    firstSection = 0.5*(np.asarray(y[0:start:2])+np.asarray(y[1:start+1:2]))
    return np.hstack( (firstSection, y[start+1:]) ).tolist()


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
        #self.plot = self.plotWidget.canvas.ax.plot([], 'o', label='')
        
    def rampRateChanged(self, value):
        if abs(value) < 120.:
            self.controlModeCombo.setEnabled(True)
            
    def controlModeChanged(self, index):
        mode = self.controlModeCombo.currentText()
        if mode == 'Analog':
            self.rampRateSb.setMinimum(-380.)
            self.rampRateSb.setMaximum(+380.)
            enable = True
        elif mode == 'Digital':
            self.rampRateSb.setMinimum(-800.)
            self.rampRateSb.setMaximum(+800.)
            enable = False
        if self.magnetThread is not None:
            self.magnetThread.enableMagnetVoltageControl(enable)
            
    def clearData(self):
        self.ts = [] # Time 
        self.Iss = [] # Supply current
        self.Vss = [] # Supply voltage
        self.Vfets = [] # FET output voltage
        self.Vms = [] # Magnet voltage
        self.VmStds = [] # Magnet voltage std
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
        elif yaxis == 'Magnet V std':
            yax.setLabel('V magnet std', 'V')
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
        elif yaxis == 'Magnet V std':
            y = self.VmStds
        elif yaxis == 'FET V':
            y = self.Vfets
        elif yaxis == 'Magnet I (coarse)':
            y = self.Ics
        elif yaxis == 'Magnet I (fine)':
            y = self.Ifs
        
        self.curve.setData(self.ts, y)

    def collectData(self, time, supplyCurrent, supplyVoltage, fetVoltage, magnetVoltage, currentCoarse, currentFine, magnetVoltageStd):
        '''Collect the data for plotting'''
        self.ts.append(time)
        self.Iss.append(supplyCurrent)
        self.Vss.append(supplyVoltage)
        self.Vfets.append(fetVoltage)
        self.Vms.append(magnetVoltage)
        self.VmStds.append(magnetVoltageStd)
        self.Ics.append(currentCoarse)
        self.Ifs.append(currentFine)
        self.supplyCurrentSb.setValue(supplyCurrent)
        self.supplyVoltageSb.setValue(supplyVoltage)
        self.outputVoltageSb.setValue(fetVoltage)
        self.magnetVoltageSb.setValue(magnetVoltage)
        self.currentCoarseSb.setValue(currentCoarse)
        self.currentFineSb.setValue(currentFine)

        maxLength = 20000
        self.ts  = pruneData(self.ts, maxLength)
        self.Iss = pruneData(self.Iss, maxLength)
        self.Vss = pruneData(self.Vss, maxLength)
        self.Vfets = pruneData(self.Vfets, maxLength)
        self.Vms = pruneData(self.Vms, maxLength)
        self.VmStds = pruneData(self.VmStds, maxLength)
        self.Ics = pruneData(self.Ics, maxLength)
        self.Ifs = pruneData(self.Ifs, maxLength)
        self.updatePlot()

    def associateControlThread(self, magnetThread):
        self.magnetThread = magnetThread
        self.quitPb.clicked.connect(self.close)
        self.pausePb.clicked.connect(self.updateStatus)
        magnetThread.analogFeedbackChanged.connect(self.updateAnalogFeedbackStatus)
        magnetThread.diodeVoltageUpdated.connect(self.diodeVoltageSb.setValue)
        magnetThread.resistanceUpdated.connect(self.updateResistance)
        magnetThread.resistiveVoltageUpdated.connect(self.resistiveDropSb.setValue)
        magnetThread.measurementAvailable.connect(self.collectData)
        self.rampRateSb.valueChanged.connect(self.applyNewRampRate)
        self.magnetThread.finished.connect(self.close)
#        self.remoteControlThread = MagnetControlRequestReplyThread(port=RequestReply.MagnetControl, parent=self)
#        self.remoteControlThread.changeRampRate.connect(self.changeRampRate)
#        self.remoteControlThread.associateMagnetThread(self.magnetThread)
#        self.remoteControlThread.allowRequests(self.zmqRemoteEnableCb.isChecked())
#        self.zmqRemoteEnableCb.toggled.connect(self.remoteControlThread.allowRequests)
#        self.remoteControlThread.start()
        
    def updateAnalogFeedbackStatus(self, enabled):
        mode = 'Analog' if enabled else 'Digital'
        i = self.controlModeCombo.findText(mode)
        old = self.controlModeCombo.blockSignals(True)
        self.controlModeCombo.setCurrentIndex(i)
        self.controlModeCombo.blockSignals(old)
    def changeRampRate(self, A_per_s):
        mA_per_min = A_per_s / (1E-3/60)
        self.rampRateSb.setValue(mA_per_min)
        
    def applyNewRampRate(self, rate):
        A_per_s = rate*(1E-3/60)
        self.magnetThread.setRampRate(A_per_s)

    def updateRampRateDisplay(self, rate):
        block = self.rampRateSb.blockSignals(True)
        mA_per_min = rate/(1E-3/60)
        self.rampRateSb.setValue(mA_per_min)
        self.rampRateSb.blockSignals(block)

    def updateResistance(self, R):
        self.resistanceSb.setValue(R*1E3)

    def closeEvent(self, e):
        print "Closing"
#        self.remoteControlThread.stop()
#        try:
#            self.remoteControlThread.wait()
#            self.remoteControlThread.deleteLater()
#        except:
#            pass
        self.magnetThread.stop()
        try:
            self.magnetThread.wait()
            self.magnetThread.deleteLater()
        except:
            pass
        self.saveSettings()
        super(MagnetControlWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
        s.setValue('ZmqRemoteEnable', self.zmqRemoteEnableCb.isChecked())

    def restoreSettings(self):
        s = QSettings()
        self.zmqRemoteEnableCb.setChecked(s.value('ZmqRemoteEnable', False, type=bool))        

    def updateStatus(self):
        print "Updating status"
        print "Running?", self.magnetThread.isRunning()
        print "Finished?", self.magnetThread.isFinished()

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

    powerSupply = 'Agilent6641A'
    #powerSupply = 'Keithley6430'
    if powerSupply == 'Agilent6641A':
        print "Checking for Agilent 6641A..."
        from Visa.Agilent6641A import Agilent6641A
        ps = Agilent6641A('GPIB0::5')
        visaId = ps.visaId()
        if not '6641A' in visaId:
            raise Exception('Agilent 6641A not found!')
        else:
            logger.info('Have Agilent 6641A:%s' % visaId)

    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QTimer

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('ADR3 Magnet Control')

    magnetThread = MagnetControlThread(ps, app)
    QTimer.singleShot(2000, magnetThread.start)

    mw = MagnetControlWidget()
    mw.associateControlThread(magnetThread)
    mw.show()
    app.exec_()

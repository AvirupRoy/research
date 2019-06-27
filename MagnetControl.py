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

from MagnetSupply import MagnetControlThread, MagnetControlNoMagnetVoltageThread, MagnetControlRequestReplyThread
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSignal, QObject, QSettings
import MagnetControlUi
from Zmq.Ports import RequestReply
import pyqtgraph as pg

import numpy as np
def pruneData(y, maxLength=20000, fraction=0.3): # This is copied from AVS47, should put somewhere else
    if len(y) < maxLength:
        return y
    start = int(fraction*maxLength)
    firstSection = 0.5*(np.asarray(y[0:start:2])+np.asarray(y[1:start+1:2]))
    return np.hstack( (firstSection, y[start+1:]) ).tolist()


class MagnetControlWidget(MagnetControlUi.Ui_Widget, QWidget):
    '''The GUI for magnet control'''
    def __init__(self, parent=None):
        super(MagnetControlWidget, self).__init__(parent)
        self.setupUi(self)
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
        
    def clearData(self):
        self.ts = []
        self.Iss = []
        self.Vss = []
        self.Vms = []
        self.updatePlot()

    def switchPlotAxis(self):
        yaxis = self.yaxisCombo.currentText()
        if yaxis == 'Supply I':
            self.plot.getAxis('left').setLabel('I supply', 'A')
        elif yaxis == 'Supply V':
            self.plot.getAxis('left').setLabel('V supply', 'V')
        elif yaxis == 'Magnet V':
            self.plot.getAxis('left').setLabel('V magnet', 'V')
        self.updatePlot()
        plotItem = self.plot.getPlotItem()
        vb = plotItem.getViewBox()
        vb.enableAutoRange(pg.ViewBox.YAxis, True)
        vb.enableAutoRange(pg.ViewBox.YAxis, False)
        
    def updatePlot(self):
        yaxis = self.yaxisCombo.currentText()
        if yaxis == 'Supply I':
            self.curve.setData(self.ts, self.Iss)
        elif yaxis == 'Supply V':
            self.curve.setData(self.ts, self.Vss)
        elif yaxis == 'Magnet V':
            self.curve.setData(self.ts, self.Vms)

    def collectData(self, time, supplyCurrent, supplyVoltage, magnetVoltage):
        '''Collect the data for plotting'''
        self.ts.append(time)
        self.Iss.append(supplyCurrent)
        self.Vss.append(supplyVoltage)
        self.Vms.append(magnetVoltage)

        maxLength = 20000
        self.ts  = pruneData(self.ts, maxLength)
        self.Iss = pruneData(self.Iss, maxLength)
        self.Vss = pruneData(self.Vss, maxLength)
        self.Vms = pruneData(self.Vms, maxLength)
        self.updatePlot()

    def associateControlThread(self, magnetThread):
        self.magnetThread = magnetThread
        self.quitPb.clicked.connect(self.close)
        self.pausePb.clicked.connect(self.updateStatus)
        magnetThread.supplyVoltageUpdated.connect(self.supplyVoltageSb.setValue)
        magnetThread.programmedSupplyVoltageUpdated.connect(self.programmedSupplyVoltageSb.setValue)
        magnetThread.supplyCurrentUpdated.connect(self.supplyCurrentSb.setValue)
        magnetThread.magnetVoltageUpdated.connect(self.magnetVoltageSb.setValue)
        magnetThread.diodeVoltageUpdated.connect(self.diodeVoltageSb.setValue)
        magnetThread.resistanceUpdated.connect(self.updateResistance)
        magnetThread.resistiveVoltageUpdated.connect(self.resistiveDropSb.setValue)
        magnetThread.measurementAvailable.connect(self.collectData)
        self.rampRateSb.valueChanged.connect(self.applyNewRampRate)
        self.magnetThread.finished.connect(self.close)
        self.remoteControlThread = MagnetControlRequestReplyThread(port=RequestReply.MagnetControl, parent=self)
        self.remoteControlThread.changeRampRate.connect(self.changeRampRate)
        self.remoteControlThread.associateMagnetThread(self.magnetThread)
        self.remoteControlThread.allowRequests(self.zmqRemoteEnableCb.isChecked())
        self.zmqRemoteEnableCb.toggled.connect(self.remoteControlThread.allowRequests)
        self.remoteControlThread.start()

    def changeRampRate(self, A_per_s):
        mA_per_min = A_per_s / (1E-3/60)
        self.rampRateSb.setValue(mA_per_min)
        
    def applyNewRampRate(self, rate):
        self.magnetThread.setRampRate(rate*(1E-3/60))

    def updateRampRateDisplay(self, rate):
        block = self.rampRateSb.blockSignals(True)
        mA_per_min = rate/(1E-3/60)
        self.rampRateSb.setValue(mA_per_min)
        self.rampRateSb.blockSignals(block)

    def updateResistance(self, R):
        self.resistanceSb.setValue(R*1E3)

    def closeEvent(self, e):
        print "Closing"
        self.remoteControlThread.stop()
        try:
            self.remoteControlThread.wait()
            self.remoteControlThread.deleteLater()
        except:
            pass
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

    haveMagnetVoltage = True

    if haveMagnetVoltage:
        print "Checking for Agilent 34401A..."
        from Visa.Agilent34401A import Agilent34401A
        dmm = Agilent34401A('GPIB0::22')
        visaId = dmm.visaId()
        if not '34401A' in visaId:
            raise Exception('Agilent 34401A not found!')
        else:
            logger.info('Have Agilent 34401A:%s' % visaId)

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


        voltageSource = 'DAQ'
        if voltageSource == 'Keithley6430':
            print "Checking for Keithley 6430..."
            from Visa.Keithley6430 import Keithley6430
            vs = Keithley6430('GPIB0::24')
            visaId = vs.visaId()
            if not '6430' in visaId:
                raise Exception('Keithley 6430 not found!')
            else:
                logger.info('Have Keithley 6430:%s' % visaId)
        elif voltageSource == 'DAQ':
            print "Checking for DAQ USB6002..."
            from MagnetSupply import DaqVoltageSource
            vs = DaqVoltageSource('USB6002', 'ao0','ai0', continuousReadback=False)
            logger.info('Have USB6002 voltage source')
        else:
            raise Exception("Don't know what to use as the programming source!")

        from MagnetSupply import MagnetSupply
        magnetSupply = MagnetSupply(ps, vs)

    elif powerSupply == 'Keithley6430':
        print "Checking for Keithley 6430..."
        from Visa.Keithley6430 import Keithley6430
        from MagnetSupply import MagnetSupplySourceMeter
        k6430 = Keithley6430('GPIB0::24')
        visaId = k6430.visaId()
        if not '6430' in visaId:
            raise Exception('Keithley 6430 not found!')
        else:
            logger.info('Have Keithley 6430:%s' % visaId)
        magnetSupply = MagnetSupplySourceMeter(k6430)

    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QTimer

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('ADR3 Magnet Control')

    if haveMagnetVoltage:
        magnetThread = MagnetControlThread(magnetSupply, dmm, app)
    else:
        magnetThread = MagnetControlNoMagnetVoltageThread(magnetSupply, None, app)
    QTimer.singleShot(2000, magnetThread.start)

    mw = MagnetControlWidget()
    mw.associateControlThread(magnetThread)
    mw.show()
    app.exec_()

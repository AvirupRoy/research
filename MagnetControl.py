# -*- coding: utf-8 -*-
"""
Created on Fri May 22 13:03:06 2015
GUI to control the magnet via Agilent 6641A power supply and programming voltage provided by either Keithley 6430 or NI DAQ

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""


import logging
#logging.basicConfig(filename='MagnetControl.log',level=logging.WARN)

logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='MagnetControl.log',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

from MagnetSupply import MagnetControlThread, MagnetControlNoMagnetVoltageThread
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSignal
import MagnetControlUi

from Zmq.Zmq import ZmqRequestReplyThread

class MagnetControlRequestReplyThread(ZmqRequestReplyThread):
    rampRateRequested = pyqtSignal(float)

    def __init__(self, parent=None):
        ZmqRequestReplyThread.__init__(self, port=7000, parent=parent)
        self.allowRequests()

    def allowRequests(self, allow=True):
        self.requestsAllowed = allow

    def denyRequests(self):
        self.allowRequests(False)

    def handleCommand(self, command, data):
        if command=='RAMPRATE':
            self.rampRateRequested.emit(float(data))
            return 'OK'
        else:
            return 'UNKNOWN COMMAND'

    def handleQuery(self, query):
        return 'NOT SUPPORTED'

    def processRequest(self, origin, timeStamp, request):
        '''Default request handler. By default the requestReceived signal is triggered. Override in subclasses as needed. Use send reply to send the reply (mandatory!).'''
        print "Processing request"
        if self.requestsAllowed:
            print "Allowed"
            d = request.split(' ')
            print "d=", d
            if len(d) == 2:
                command = d[0].upper()
                data = d[1]
                r = self.handleCommand(command,data)
            elif len(d) == 1 and request[-1]=='?':
                query = request[:-1].upper()
                r = self.handleQuery(query)
            else:
                r = 'ILLEGAL REQUEST'
        else:
            r = 'DENIED'
        self.sendReply(r)

class MagnetControlWidget(MagnetControlUi.Ui_Widget, QWidget):
    def __init__(self, parent=None):
        super(MagnetControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.magnetThread = None
        self.plot = self.plotWidget.canvas.ax.plot([], 'o', label='')

    def associateControlThread(self, magnetThread):
        self.magnetThread = magnetThread
        self.quitPb.clicked.connect(self.close)
        self.pausePb.clicked.connect(self.updateStatus)
        magnetThread.supplyVoltageUpdated.connect(self.supplyVoltageSb.setValue)
        magnetThread.programmedSupplyVoltageUpdated.connect(self.programmedSupplyVoltageSb.setValue)
        magnetThread.supplyCurrentUpdated.connect(self.supplyCurrentSb.setValue)
        magnetThread.supplyCurrentUpdated.connect(self.maybeTurn)
        magnetThread.magnetVoltageUpdated.connect(self.magnetVoltageSb.setValue)
        magnetThread.diodeVoltageUpdated.connect(self.diodeVoltageSb.setValue)
        magnetThread.resistanceUpdated.connect(self.updateResistance)
        magnetThread.resistiveVoltageUpdated.connect(self.resistiveDropSb.setValue)
        self.rampRateSb.valueChanged.connect(self.applyNewRampRate)
        self.magnetThread.finished.connect(self.close)
        self.remoteControlThread = MagnetControlRequestReplyThread(self)
        self.remoteControlThread.rampRateRequested.connect(self.rampRateSb.setValue)
        self.remoteControlThread.start()

    def maybeTurn(self, current):
        if not self.cycleCb.isChecked():
            return
        rampRate = self.rampRateSb.value()
        if  rampRate > 0 and current >= self.maxCurrentSb.value():
            self.rampRateSb.setValue(-rampRate)
        elif rampRate < 0 and current <= self.minCurrentSb.value():
            self.rampRateSb.setValue(-rampRate)

 #   def updateData(self, time, supplyVoltage, supplyCurrent, magnetVoltage):
 #       self.time.append


    def applyNewRampRate(self, rate):
        self.magnetThread.setRampRate(rate*(1E-3/60))

    def updateRampRateDisplay(self, rate):
        block = self.rampRateSb.blockSignals(True)
        self.rampRateSb.setValue(rate/(1E-3/60))
        self.rampRateSb.blockSignals(block)

    def updateResistance(self, R):
        self.resistanceSb.setValue(R*1E3)

    def closeEvent(self, e):
        print "Closing"
        self.magnetThread.stop()
        self.remoteControlThread.stop()
        self.saveSettings()
        #self.magnetThread.deleteLater()
        super(MagnetControlWidget, self).closeEvent(e)

    def saveSettings(self):
        pass

    def restoreSettings(self):
        pass

    def updateStatus(self):
        print "Updating status"
        print "Running?", self.magnetThread.isRunning()
        print "Finished?", self.magnetThread.isFinished()


from PyQt4.QtCore import QObject

class ExceptionHandler(QObject):

    errorSignal = pyqtSignal()
    silentSignal = pyqtSignal()

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

    #powerSupply = 'Agilent6641A'
    powerSupply = 'Keithley6430'
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

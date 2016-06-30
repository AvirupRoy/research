# -*- coding: utf-8 -*-
"""
Created on Wed Oct 07 12:31:58 2015

@author: wisp10
"""


from PyQt4 import QtGui #, QtNetwork
from PyQt4.QtCore import QThread, pyqtSignal, QByteArray
from PyQt4.QtNetwork import QTcpSocket

from struct import pack, unpack
import numpy as np

class ApcAccessThread(QThread):
    dataAvailable = pyqtSignal(float, float, float, float, float, str) # line voltage, battery voltage, loadPercent, batteryCharge, temperature, status
    lineVoltageAvailable = pyqtSignal(float)
    batteryVoltageAvailable = pyqtSignal(float)
    loadPercentAvailable = pyqtSignal(float)
    batteryChargeAvailable = pyqtSignal(float)
    temperatureAvailable = pyqtSignal(float)

    statusAvailable = pyqtSignal(str)
    errorDetected = pyqtSignal(str)

    def __init__(self, host, port, parent=None):
        super(ApcAccessThread, self).__init__(parent)
        self.host = host
        self.port = port

    def stop(self):
        self.stopRequested = True
        print "Stop requested!"

    def sendMessage(self, message):
        l = len(message)
        d = pack('>H', l) + message
        self.socket.write(QByteArray(d))
        if not self.socket.waitForBytesWritten(3000):
            self.errorDetected.emit('Unable to send: %s' % self.socket.errorString())

    def processPayload(self, payload):
        def checkUnits(s, units):
            d = s.split(' ')
            print "d=", d
            if d[1] == units:
                return float(d[0])
            else:
                print "Units:",d[1]

        d = payload.split(':')
        if len(d) != 2:
            return
        key = d[0].strip()
        value = d[1].strip()
        print "Processed:", key, value
        
        
        if key == 'LINEV':
            self.lineVoltage = checkUnits(value, 'Volts')
            self.lineVoltageAvailable.emit(self.lineVoltage)
        elif key == 'BATTV':
            self.batteryVoltage = checkUnits(value, 'Volts')
            self.batteryVoltageAvailable.emit(self.batteryVoltage)
        elif key == 'STATUS':
            self.status = value.strip()
            self.statusAvailable.emit(self.status)
        elif key == 'LOADPCT':
            self.loadPercent = checkUnits(value, 'Percent')
            self.loadPercentAvailable.emit(self.loadPercent)
        elif key == 'BCHARGE':
            self.batteryCharge = checkUnits(value, 'Percent')
            self.batteryChargeAvailable.emit(self.batteryCharge)
        elif key == 'ITEMP':
            self.celsius = checkUnits(value, 'C')
            print "Celsius", self.celsius
            self.temperatureAvailable.emit(self.celsius)
        else:
            pass

    def run(self):
        try:
            self.stopRequested = False
            self.socket = QTcpSocket()
            socket = self.socket
            while not self.stopRequested:
                if socket.state() == QTcpSocket.UnconnectedState:
                    socket.connectToHost(self.host, self.port)
                    if not socket.waitForConnected(3000):
                        self.errorDetected.emit('Unable to connect: %s' % socket.errorString())

                self.sendMessage('status')
                data = ''
                k = 0
                readMore = True
                self.lineVoltage = np.nan
                self.batteryVoltage = np.nan
                self.status = ''
                self.loadPercent = np.nan
                self.batteryCharge = np.nan
                self.celsius = np.nan

                while readMore and not self.stopRequested:

                    if not socket.waitForReadyRead(2000):
                        self.errorDetected.emit('Timeout waiting for data')
                        break
                    data += socket.readAll()
                    l = len(data)
                    while k+2 <= l:
                        lenPayload = unpack('>H', data[k:k+2])[0]
                        if lenPayload == 0: # No more data expected
                            self.dataAvailable.emit(self.lineVoltage, self.batteryVoltage, self.loadPercent, self.batteryCharge, self.celsius, self.status)
                            print "Completed receive"
                            readMore = False
                            break
                        start = k+2
                        end = k+2+lenPayload
                        if end > l: # Payload incomplete
                            break
                        pl = str(data[start:end])
                        self.processPayload(pl)
                        k = end
                for i in range(50):
                    self.msleep(100)
                    if self.stopRequested:
                        break

        except Exception,e:
            print "Exception:", e


import LabWidgets.Utilities as ut
ui = ut.compileAndImportUi('ApcUpsWidget')
ProgramName = 'APC UPS'
OrganizationName = 'McCammon X-ray Astrophysics'

import time
import os
import pyqtgraph as pg
class ApcUpsWidget(ui.Ui_Form, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.quitPb.clicked.connect(self.close)
        self.clearData()
        self.plotCombo.currentIndexChanged.connect(self.updatePlot)

        self.curve = pg.PlotCurveItem(pen='k')
        self.plot.addItem(self.curve)
        self.plot.setBackground('w')
        self.plot.plotItem.showGrid(x=True, y=True)
        self.plot.plotItem.enableAutoRange(pg.ViewBox.XYAxes, True)

        self.batteryVoltageIndicator.setUnit('V')
        self.lineVoltageIndicator.setUnit('V')
        self.batteryVoltageIndicator.setPrecision(1)
        self.lineVoltageIndicator.setPrecision(1)
        self.temperatureIndicator.setUnit('C')
        self.temperatureIndicator.setPrecision(1)
        self.startThread()


    def startThread(self):
        ups = ApcAccessThread('127.0.0.1', 3551)
        ups.batteryVoltageAvailable.connect(self.batteryVoltageIndicator.setValue)
        ups.lineVoltageAvailable.connect(self.lineVoltageIndicator.setValue)
        ups.loadPercentAvailable.connect(self.loadIndicator.setPercentage)
        ups.batteryChargeAvailable.connect(self.chargeIndicator.setPercentage)
        ups.temperatureAvailable.connect(self.temperatureIndicator.setCelsius)
        ups.statusAvailable.connect(self.statusIndicator.setValue)
        ups.errorDetected.connect(self.addErrorMessage)
        ups.setParent(self)
        ups.start()
        ups.dataAvailable.connect(self.logData)
        self.ups = ups
        
    def clearData(self):
        self.ts = []
        self.Vlines = []
        self.Vbats = []
        self.loads = []
        self.charges = []
        self.Ts = []
        
    def logData(self, lineVoltage, batteryVoltage, loadPercent, batteryCharge, celsius, status):
        t = time.time()
        string = "%.3f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t'%s'\n" % (t, lineVoltage, batteryVoltage, loadPercent, batteryCharge, celsius, status)
        timeString = time.strftime('%Y%m%d', time.localtime(t))
        fileName = 'APC_UPS_%s.dat' % timeString
        if not os.path.isfile(fileName): # Maybe create new file
            with open(fileName, 'a+') as f:
                f.write('#ApcUpsAccess.py\n')
                f.write('#Date=%s\n' % timeString)
                f.write('#'+'\t'.join(['time', 'Vline', 'Vbat', 'loadPercent', 'batteryCharge', 'Celsius', 'Status'])+'\n')

        with open(fileName, 'a') as f:
            f.write(string)

        self.ts.append(t)
        self.Vlines.append(lineVoltage)
        self.Vbats.append(batteryVoltage)
        self.loads.append(loadPercent)
        self.charges.append(batteryCharge)
        self.Ts.append(celsius)
        self.updatePlot()
        
    def updatePlot(self):
        yaxis = self.plotCombo.currentText()
        if yaxis == 'Line voltage':
            y = self.Vlines
        elif yaxis == 'Battery voltage':
            y = self.Vbats
        elif yaxis == 'Load':
            y = self.loads
        elif yaxis == 'Charge':
            y = self.charges
        elif yaxis == 'Temperature':
            y = self.Ts
            
        self.curve.setData(self.ts, y)
        
        
    def closeEvent(self, event):
        self.ups.stop()
        self.ups.wait(2000)

    def addErrorMessage(self, message):
        self.errorEdit.append(message)

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    widget = ApcUpsWidget()
    widget.show()
    sys.exit(app.exec_())
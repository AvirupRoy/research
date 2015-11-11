# -*- coding: utf-8 -*-
"""
Created on Wed Oct 07 12:31:58 2015

@author: wisp10
"""


from PyQt4 import QtGui #, QtNetwork
from PyQt4.QtCore import QThread, pyqtSignal, QByteArray,QDataStream
from PyQt4.QtNetwork import QUdpSocket,QTcpSocket

from struct import pack, unpack

class ApcAccessThread(QThread):
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
            lineV = checkUnits(value, 'Volts')
            self.lineVoltageAvailable.emit(lineV)
        elif key == 'BATTV':
            battV = checkUnits(value, 'Volts')
            self.batteryVoltageAvailable.emit(battV)
        elif key == 'STATUS':
            self.statusAvailable.emit(value.strip())
        elif key == 'LOADPCT':
            load = checkUnits(value, 'Percent')
            self.loadPercentAvailable.emit(load)
        elif key == 'BCHARGE':
            batteryCharge = checkUnits(value, 'Percent')
            self.batteryChargeAvailable.emit(batteryCharge)
        elif key == 'ITEMP':
            celsius = checkUnits(value, 'C')
            print "Celsius", celsius
            self.temperatureAvailable.emit(celsius)
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
                while readMore and not self.stopRequested:
                    if not socket.waitForReadyRead(2000):
                        self.errorDetected('Timeout waiting for data')
                        break
                    data += socket.readAll()
                    l = len(data)
                    while k+2 <= l:
                        lenPayload = unpack('>H', data[k:k+2])[0]
                        if lenPayload == 0: # No more data expected
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


import ApcUpsWidgetUi
class ApcUpsWidget(ApcUpsWidgetUi.Ui_Form, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.batteryVoltageIndicator.setUnit('V')
        self.lineVoltageIndicator.setUnit('V')
        self.batteryVoltageIndicator.setPrecision(1)
        self.lineVoltageIndicator.setPrecision(1)
        self.temperatureIndicator.setUnit('C')
        self.temperatureIndicator.setPrecision(1)

    def addErrorMessage(self, message):
        self.errorEdit.append(message)

if __name__ == '__main__':

    import sys
#    from PyQt4.QtCore import QTimer

    app = QtGui.QApplication(sys.argv)
    ups = ApcAccessThread('127.0.0.1', 3551)
    ups.start()
    widget = ApcUpsWidget()
    widget.show()
    ups.batteryVoltageAvailable.connect(widget.batteryVoltageIndicator.setValue)
    ups.lineVoltageAvailable.connect(widget.lineVoltageIndicator.setValue)
    ups.loadPercentAvailable.connect(widget.loadIndicator.setPercentage)
    ups.batteryChargeAvailable.connect(widget.chargeIndicator.setPercentage)
    ups.temperatureAvailable.connect(widget.temperatureIndicator.setCelsius)
    ups.statusAvailable.connect(widget.statusIndicator.setValue)
    ups.errorDetected.connect(widget.addErrorMessage)
    widget.destroyed.connect(ups.stop)
    ups.setParent(widget)
#    timer = QTimer()
    #timer.singleShot(35, ups.stop)
    sys.exit(app.exec_())
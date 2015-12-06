# -*- coding: utf-8 -*-
"""
Various ZmqSubscribers
Created on Thu Aug 27 14:16:57 2015
@author:Felix Jaeckel <fxjaeckel@gmail.com>
"""

from Zmq import ZmqSubscriber
from Ports import PubSub
from PyQt4.QtCore import pyqtSignal

class TemperatureSubscriber(ZmqSubscriber):
    adrTemperatureReceived = pyqtSignal(float)
    adrResistanceReceived = pyqtSignal(float)
    def __init__(self, parent=None):
        ZmqSubscriber.__init__(self, port=PubSub.AdrTemperature, parent=parent)
        self.floatReceived.connect(self.processFloat)
        self.maxAge = 3

    def processFloat(self, origin, item, value, timeStamp):
        if item == u'ADR_Temperature':
            self.adrTemperatureReceived.emit(value)
        elif item == u'ADR_Sensor_R':
            self.adrResistanceReceived.emit(value)


if __name__ == '__main__':
    from PyQt4.QtGui import QApplication, QDoubleSpinBox
    app = QApplication([])
    widget = QDoubleSpinBox()
    widget.setDecimals(7)
    widget.setMinimum(0)
    widget.setMaximum(1000)
    widget.setSuffix(' K')
    widget.setReadOnly(True)
    sub = TemperatureSubscriber(widget)
    sub.adrTemperatureReceived.connect(widget.setValue)
    widget.show()
    sub.start()
    app.exec_()
    
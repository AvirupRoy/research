# -*- coding: utf-8 -*-
"""
Various ZmqSubscribers
Created on Thu Aug 27 14:16:57 2015
@author:Felix Jaeckel <fxjaeckel@gmail.com>
"""

from Zmq import ZmqSubscriber
from PyQt4.QtCore import pyqtSignal

class TemperatureSubscriber(ZmqSubscriber):
    adrTemperatureReceived = pyqtSignal(float)
    def __init__(self, parent=None):
        ZmqSubscriber.__init__(self, port=5555, parent=parent)
        self.floatReceived.connect(self.processFloat)
        self.maxAge = 3

    def processFloat(self, origin, item, value, timeStamp):
        if item == u'ADR_Temperature':
            self.adrTemperatureReceived.emit(value)

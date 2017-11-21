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
#        ZmqSubscriber.__init__(self, port=PubSub.AdrTemperature, parent=parent)
        ZmqSubscriber.__init__(self, port=PubSub.LockinThermometerAdr, parent=parent)
        self.floatReceived.connect(self.processFloat)
        self.maxAge = 3

    def processFloat(self, origin, item, value, timeStamp):
        if item == u'ADR_Temperature':
            self.adrTemperatureReceived.emit(value)
        elif item == u'ADR_Sensor_R':
            self.adrResistanceReceived.emit(value)
            
class TemperatureSubscriber_RuOx2005(ZmqSubscriber):
    adrTemperatureReceived = pyqtSignal(float)
    adrResistanceReceived = pyqtSignal(float)
    def __init__(self, parent=None):
#        ZmqSubscriber.__init__(self, port=PubSub.AdrTemperature, parent=parent)
        ZmqSubscriber.__init__(self, port=PubSub.LockinThermometerRuOx2005, parent=parent)
        self.floatReceived.connect(self.processFloat)
        self.maxAge = 3

    def processFloat(self, origin, item, value, timeStamp):
        if item == u'ADR_Temperature':
            self.adrTemperatureReceived.emit(value)
        elif item == u'ADR_Sensor_R':
            self.adrResistanceReceived.emit(value)

class HousekeepingSubscriber(ZmqSubscriber):
    '''A subscriber that collects information from the aggregator (ZmqForward.py),
    which collects it from all the publishers.
    TODO:
    *Periodically remove non-active thermometers from the dictionaries
    *Diodes
    *Implement other housekeeping (magnet)
    '''
    thermometerReadingReceived = pyqtSignal(str, float, float, float) # sensorName, time, resistance, temperature
    thermometerListUpdated = pyqtSignal(object)
    adrTemperatureReceived = pyqtSignal(float) # For legacy apps
    adrResistanceReceived = pyqtSignal(float) # For legacy apps
    
    def __init__(self, parent=None):
        ZmqSubscriber.__init__(self, port=PubSub.Housekeeping, parent=parent)
        self.dictReceived.connect(self.processDict)
        self.thermometerTimeStamp = {}
        self.thermometerResistance = {}
        self.thermometerTemperature = {}
        self.sensors = []
        
    def processDict(self, origin, item, dictionary):
        if origin in ['LockinThermometer', 'Avs47SingleChannel']: # Handle thermometers
            sensor = item
            if not sensor in self.sensors:
                self.sensors.append(sensor)
                self.thermometerListUpdated.emit(self.sensors)
            t = dictionary['t']
            R = dictionary['R']
            T = dictionary['T']
            self.thermometerTimeStamp[sensor] = t
            self.thermometerResistance[sensor] = R
            self.thermometerTemperature[sensor] = T
            self.thermometerReadingReceived.emit(sensor, t, R, T)
            if sensor == 'RuOx2005Thermometer':
                self.adrTemperatureReceived.emit(T)
                self.adrResistanceReceived.emit(R)
        else: # Handle other things, such as magnet
            #print (origin, item, dictionary)
            pass
        
def testHousekeepingSubscriber():
    from PyQt4.QtGui import QApplication, QWidget, QFormLayout, QLineEdit
    app = QApplication([])
    
    widget = QWidget()
    layout = QFormLayout()
    sensorCombo = QLineEdit()
    timeLe = QLineEdit()
    resistanceLe = QLineEdit()
    temperatureLe = QLineEdit()
    layout.addRow('Sensor', sensorCombo)
    layout.addRow('Time', timeLe)
    layout.addRow('Resistance', resistanceLe)
    layout.addRow('Temperature', temperatureLe)
    widget.setLayout(layout)
    widget.show()
    def readingReceived(sensor, t, R, T):
        sensorCombo.setText(sensor)
        timeLe.setText(str(t))
        resistanceLe.setText(str(R))
        temperatureLe.setText(str(T))
    sub = HousekeepingSubscriber(widget)
    sub.thermometerReadingReceived.connect(readingReceived)
    sub.start()
    app.exec_()
        

def testTemperatureSubscriber():
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
    

if __name__ == '__main__':
    testHousekeepingSubscriber()    

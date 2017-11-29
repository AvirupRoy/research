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
    *Implement other housekeeping (PID?)
    '''
    thermometerReadingReceived = pyqtSignal(str, float, float, float) # sensorName, time, resistance, temperature
    thermometerListUpdated = pyqtSignal(object)
    adrTemperatureReceived = pyqtSignal(float) # For legacy apps
    adrResistanceReceived = pyqtSignal(float) # For legacy apps
    magnetReadingsReceived = pyqtSignal(float, float, float, float) # time, Vmagnet, ImagnetCoarse, ImagnetFine
    tesBiasReceived = pyqtSignal(float, float) # time, TES bias voltage
    fieldCoilBiasReceived = pyqtSignal(float, float) # time, coil bias voltage
    
    def __init__(self, parent=None):
        ZmqSubscriber.__init__(self, port=PubSub.Housekeeping, parent=parent)
        self.dictReceived.connect(self.processDict)
        self.thermometerTimeStamp = {}
        self.thermometerResistance = {}
        self.thermometerTemperature = {}
        self.thermometerPower = {}
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
            P = dictionary['P']
            self.thermometerTimeStamp[sensor] = t
            self.thermometerResistance[sensor] = R
            self.thermometerTemperature[sensor] = T
            self.thermometerPower[sensor] = P
            self.thermometerReadingReceived.emit(sensor, t, R, T, P)
            if sensor == 'RuOx2005Thermometer':
                self.adrTemperatureReceived.emit(T)
                self.adrResistanceReceived.emit(R)
        elif origin in ['MagnetControlThread']:  # Handle magnet
            self.tMagnet = dictionary['t']
            self.Isupply = dictionary['Isupply']
            self.Vfet = dictionary['Vfet']
            self.Vmagnet = dictionary['Vmagnet']
            self.ImagnetCoarse = dictionary['ImagnetCoarse']
            self.ImagnetFine   = dictionary['ImagnetFine']
            self.magnetReadingsReceived.emit(self.tMagnet, self.Vmagnet, self.ImagnetCoarse, self.ImagnetFine)
        elif origin in ['TesBiasDAQ']:
            t = dictionary['t']
            Vbias = dictionary['Vbias']
            self.tesBiasReceived.emit(t, Vbias)
        elif origin in ['FieldCoilBiasDAQ']:
            t = dictionary['t']
            Vcoil = dictionary['Vcoil']
            self.fieldCoilBiasReceived.emit(t, Vcoil)
        else:
            print('Unknown origin', origin)
            
def testHousekeepingSubscriber():
    from PyQt4.QtGui import QApplication, QWidget, QFormLayout, QLineEdit
    app = QApplication([])
    
    widget = QWidget()
    layout = QFormLayout()
    sensorCombo = QLineEdit()
    timeLe = QLineEdit()
    resistanceLe = QLineEdit()
    temperatureLe = QLineEdit()
    powerLe = QLineEdit()
    magnetVLe = QLineEdit()
    layout.addRow('Sensor', sensorCombo)
    layout.addRow('Time', timeLe)
    layout.addRow('Resistance', resistanceLe)
    layout.addRow('Temperature', temperatureLe)
    layout.addRow('Power', powerLe)
    layout.addRow('Magnet V', magnetVLe)
    widget.setLayout(layout)
    widget.show()
    def readingReceived(sensor, t, R, T, P):
        sensorCombo.setText(sensor)
        timeLe.setText(str(t))
        resistanceLe.setText(str(R))
        temperatureLe.setText(str(T))
        powerLe.setText(str(P))

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

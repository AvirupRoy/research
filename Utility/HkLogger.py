# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 17:26:45 2017

@author: wisp10
"""


from PyQt4.QtCore import QObject
from HdfWriter import HdfVectorWriter
import numpy as np

class HkLogger(QObject):
    def __init__(self, hdfRoot, hkSubscriber, items=None):
        sub = hkSubscriber
        if items is None:
            items = ['thermometers','magnet', 'tesBias', 'fieldCoil','diodeThermometers']

        self.hdfRoot = hdfRoot            
        if 'thermometers' in items:
            self.thermometerWriters = {}
            sub.thermometerReadingReceived.connect(self.thermometerReadingReceived)
            
        if 'magnet' in items:
            g = hdfRoot.require_group('Magnet')
            self.magnetWriter = HdfVectorWriter(g, [('t',np.float), ('Vmagnet', np.float), ('ImagnetCoarse', np.float), ('ImagnetFine', np.float)])
            sub.magnetReadingsReceived.connect(self.magnetReadingReceived)
            
        if 'tesBias' in items:
            g = hdfRoot.require_group('TESBias')
            self.tesBiasWriter = HdfVectorWriter(g, [('t',np.float), ('Vbias', np.float)])
            sub.tesBiasReceived.connect(self.tesBiasReceived)

        if 'fieldCoil' in items:
            g = hdfRoot.require_group('FieldCoilBias')
            self.fieldCoilBiasWriter = HdfVectorWriter(g, [('t',np.float), ('Vcoil', np.float)])
            sub.fieldCoilBiasReceived.connect(self.fieldCoilBiasReceived)
            
        if 'diodeThermometers' in items:
            self.diodeThermometerWriters={}
            sub.diodeThermometerTemperatureReceived.connect(self.diodeThermometersReadingReceived)
            
    def thermometerReadingReceived(self, sensor, t, R, T, P, Tbase):
        sensor = str(sensor)
        #print('Sensor', sensor)
        if not sensor in self.thermometerWriters.keys():
            g = self.hdfRoot.require_group(sensor)
            g.attrs['SensorName'] = sensor
            writer = HdfVectorWriter(g, [('t',np.float), ('R',np.float), ('T',np.float), ('P', np.float), ('Tbase', np.float)])
            self.thermometerWriters[sensor] = writer
        self.thermometerWriters[sensor].writeData(t=t, R=R, T=T, P=P, Tbase=Tbase)

    def diodeThermometersReadingReceived(self, thermometerType, t, T, I):
        thermometerName = str(thermometerType)
        #print('Sensor', sensor)
        if not thermometerName in self.diodeThermometerWriters.keys():
            g = self.hdfRoot.require_group(thermometerName)
            g.attrs['ThermometerName'] = thermometerName
            writer = HdfVectorWriter(g, [('t',np.float), ('T',np.float), ('I', np.float)])
            self.diodeThermometerWriters[thermometerName] = writer
        self.diodeThermometerWriters[thermometerName].writeData(t=t, T=T, I=I)

    def magnetReadingReceived(self, t, Vmagnet, ImagnetCoarse, ImagnetFine):
        #print('Magnet')
        self.magnetWriter.writeData(t=t, Vmagnet=Vmagnet, ImagnetCoarse=ImagnetCoarse, ImagnetFine=ImagnetFine)

    def tesBiasReceived(self, t, Vbias):
        #print('TES bias')
        self.tesBiasWriter.writeData(t=t, Vbias=Vbias)

    def fieldCoilBiasReceived(self, t, Vcoil):
        #print('Field coil bias')
        self.fieldCoilBiasWriter.writeData(t=t, Vcoil=Vcoil)
        
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    import h5py as hdf
    
    from Zmq.Subscribers import HousekeepingSubscriber
    hkSub = HousekeepingSubscriber()
    hdfRoot = hdf.File('HKTest_2.h5', 'w')
    logger = HkLogger(hdfRoot, hkSub)
    hkSub.start()
    import time
    for i in range(50):
        time.sleep(1)
        app.processEvents()

    hkSub.stop()        
    hdfRoot.close()
 
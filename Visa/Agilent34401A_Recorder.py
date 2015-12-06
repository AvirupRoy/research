# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 16:34:55 2015

@author: wisp10
"""

from Agilent34401A import Agilent34401A
from Zmq.Subscribers import TemperatureSubscriber
dmm = Agilent34401A('GPIB0::23')
from PyQt4.QtCore import QCoreApplication, QObject

app = QCoreApplication([])

class Receiver(QObject):
    R = float('nan')
    def receive(self, R):
        self.R = R
        
import time
dmm.setFunctionVoltageDc()

receiver = Receiver(app)
subscriber = TemperatureSubscriber(app)
subscriber.adrResistanceReceived.connect(receiver.receive)
subscriber.start()

fileName = 'CoilMonitor.dat'
with open(fileName, 'w') as f:
    f.write("# Agilent34401A_Recorder\n")
    f.write("# Recording coil voltage\n")
    f.write("#t\tV[V]\tR_adr[Ohm]\n")

t = int(time.time())
while True:
    while time.time()-t < 1.:
        app.processEvents()
    t = time.time()
    V = dmm.reading()
    app.processEvents()
    R = receiver.R
    
    with open(fileName, 'a') as f:
        f.write('%.3f\t%f\t%f\n' % (t, V, R))
    print t,V,R

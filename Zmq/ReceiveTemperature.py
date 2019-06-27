# -*- coding: utf-8 -*-
"""
Created on Thu Nov 10 15:50:44 2016

@author: wisp10
"""
from PyQt4.QtGui import QApplication
import time
from Subscribers import TemperatureSubscriber
app = QApplication([])
class Adr:
    def __init__(self):
        self.T = float('nan')
    def receiveTemp(self, T):
        self.T = T

adr = Adr()    
sub = TemperatureSubscriber()
sub.adrTemperatureReceived.connect(adr.receiveTemp)

sub.start()
while True:
    time.sleep(5)
    app.processEvents()
    print adr.T

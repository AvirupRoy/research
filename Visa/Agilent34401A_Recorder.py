# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 16:34:55 2015

@author: wisp10
"""

from Agilent34401A import Agilent34401A
dmm = Agilent34401A('GPIB0::23')
#dmm = Agilent34401A('USB::0x0957::0x0618::SG47000001')
#from PyQt4.QtCore import QCoreApplication, QObject

#app = QCoreApplication([])

#class Receiver(QObject):
#    R = float('nan')
#    def receive(self, R):
#        self.R = R
#        
import time
dmm.setFunctionVoltageDc()

#receiver = Receiver(app)
#hkSub = HousekeepingSubscriber(app)
#hkSub.adrResistanceReceived.connect(receiver.receive)
#hkSub.start()

#fileName = 'DiodeThermometer_Magnet_DT470_20160904.dat'
fileName = 'TES1_VsquidVsTime_20180523.dat'
with open(fileName, 'a') as f:
    f.write("# Agilent34401A_Recorder\n")
    #f.write("# Recording DT470 diode on magnet (I=10uA)\n")
    f.write("# TES1 SQUID output voltage vs time\n")
    f.write("# Rfb=10kOhm, Cfb=15nF\n")
    #f.write("#t\tV[V]\tR_adr[Ohm]\n")
    f.write("#t\tV[V]\tV_squid[V]\n")

t = int(time.time())
while True:
#    while time.time()-t < 1.:
#        pass
#        app.processEvents()
    t = time.time()
    V = dmm.reading()
#    app.processEvents()
#    R = receiver.R
    
    with open(fileName, 'a') as f:
#        f.write('%.3f\t%f\t%f\n' % (t, V, R))
        f.write('%.3f\t%f\n' % (t, V))
    print t,V
    time.sleep(0.5)

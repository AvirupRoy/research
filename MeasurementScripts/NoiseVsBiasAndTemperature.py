# -*- coding: utf-8 -*-
"""
Created on 2017-09-26
@author: Felix Jaeckel
"""
from Zmq.Zmq import RequestReplyRemote
from Zmq.Ports import RequestReply
import time
from AdrTemperatureControlPidRemote import PidControlRemote
from Zmq.Subscribers import TemperatureSubscriber, TemperatureSubscriber_RuOx2005
import numpy as np
from PyQt4.QtGui import QApplication
from OpenSQUID.OpenSquidRemote import OpenSquidRemote
from TES.SineSweepDaqRemote import SineSweepDaqRemote


class Adr:
    def __init__(self):
        self.T = float('nan')
        temperatureSub = TemperatureSubscriber_RuOx2005()
        temperatureSub.adrTemperatureReceived.connect(self._receiveTemp)
        temperatureSub.start()
        self.temperatureSub = temperatureSub

        self.Tremote = PidControlRemote('TemperatureSteps')
        self.clearHistory()
        self.lastUpdate = 0

    def clearHistory(self):
        self.Thistory = np.zeros(15)
        
    def _receiveTemp(self, T):
        self.T = T
        t = time.time()
        if t-self.lastUpdate > 20:
            self.clearHistory()
        self.lastUpdate = t
        self.Thistory[0] = T
        self.Thistory = np.roll(self.Thistory, +1)

    def rampTo(self, T):
        self.Tremote.enableRamp(False)
        self.Tremote.setRampTarget(baseT)
        self.Tremote.enableRamp(True)

    def stabilizeTemperature(self, Tgoal, maxDeltaT=20E-6, timeOut=600):
        logger.info('Stabilizing temperature to %.5f K' % Tgoal)
        t = time.time()
        tTimeOut = t + timeOut
        Tdiff = 1E6
        while True:
            time.sleep(1)
            app.processEvents()
            adrTemperature = self.T
            if (time.time() - self.lastUpdate) > 3:
                logger.warn('No temperature update in last 3s')
                continue
            Tdiff = np.nanmean(self.Thistory) - Tgoal
            Tstd = np.nanstd(self.Thistory)
            logger.info('T=%.5f K, Tdiff=%.5f K, Tstd=%.5f K' % (adrTemperature, Tdiff, Tstd))
            if np.abs(Tdiff) < maxDeltaT and Tstd < maxDeltaT:
                logger.info('Temperature stabilized')
                return True
            if time.time() > tTimeOut:
                logger.warn('Temperature not stable within timeout')
                return False
  
import DAQ.PyDaqMx as daq

class Squid(object):
    def __init__(self, pflId):
        osRemote = OpenSquidRemote(port = 7894)  
        self.sr = osRemote.obtainSquidRemote('TES1')
        
    def setFeedbackR(self, R):
        self.sr.setEnumParameterValue('feedbackR', R)
        
    def setFeedbackC(self, C):
        self.sr.setEnumParameterValue('feedbackC', C)
    
    def reset(self):
        self.sr.resetPfl()
        
    def report(self):
        return self.sr.report()
        
    def setStage1OffsetCurrent(self, I):
        self.sr.setNumericParameter('stage1OffsetCurrent', I/1E-6)
        
    def stage1OffsetCurrent(self):
        return self.sr.queryNumericParameter('stage1OffsetCurrent')*1E-6
        
    def tuneOutputToZero(self, aiChannel):
        task = daq.AiTask('TuneSQUIDOffset')
        task.addChannel(aiChannel)
        fbCoupling = 6E-6

        Is = fbCoupling * np.linspace(0.5, 2.5, 10)
        Im = np.mean(Is)
        self.setStage1OffsetCurrent(Im) # Start in the middle of the range
        time.sleep(0.05)
        self.reset()
        Vs = []
        for I in Is:
            self.setStage1OffsetCurrent(I)
            time.sleep(0.05)
            V = np.mean(task.readData(100)[0,10:])
            Vs.append(V)
        #print('Vs=',Vs, 'Is=',Is)
        fit = np.polyfit(Vs, Is, 1)
        #print(fit)
        I0 = np.polyval(fit, 0)
        #print("I=", I0)
        if I0 < 0:
            logger.warn('Cannot achieve 0 output')
        else:
            self.setStage1OffsetCurrent(I0)
        V = np.mean(task.readData(100)[0,10:])
        return V

import logging
logger = logging.getLogger('')
logger.setLevel(logging.WARN)
#ch = logging.StreamHandler()
#logger.addHandler(ch)
app = QApplication([])

aiChannel = daq.AiChannel('USB6361/ai2', -10,+10)

squid = Squid('TES1')
squid.setFeedbackR(100E3)
squid.setFeedbackC(15E-9)
x = squid.tuneOutputToZero(aiChannel)
print(x)
print(squid.report())
print(squid.stage1OffsetCurrent())
#x = squid.tuneOutputToZero(aiChannel)

adr = Adr()

import numpy as np
Rbias = 1697.5
Ibias = np.asarray([320E-6, 350E-6, 370E-6, 400E-6])
Vbias = Ibias * Rbias

#baseTs = 1E-3* np.asarray( [74.0, 75.778, 77.556, 79.0, 79.333, 81.111, 82.889, 84.5, 84.667] )

baseTs = [0.1085]
baseTs = []

for bias in [0]: #Ibias:
    # set bias
    
    for baseT in baseTs:
        adr.rampTo(baseT)
        adr.stabilizeTemperature(baseT)

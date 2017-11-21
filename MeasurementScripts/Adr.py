# -*- coding: utf-8 -*-
"""
Created on Thu Oct 05 12:44:35 2017

@author: wisp10
"""

from __future__ import print_function
import time
import numpy as np
from AdrTemperatureControlPidRemote import PidControlRemote
from Zmq.Subscribers import HousekeepingSubscriber
import logging

logger = logging.getLogger('Adr')

class Adr:
    def __init__(self, qApp):
        self.qApplication = qApp
        self.T = float('nan')
        hkSub = HousekeepingSubscriber()
        hkSub.adrTemperatureReceived.connect(self._receiveTemp)
        hkSub.start()
        self.hkSub = hkSub

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
        self.Tremote.setRampTarget(T)
        self.Tremote.enableRamp(True)
        
    def setRampRate(self, mKperMin):
        self.Tremote.setRampRate(mKperMin)

    def stabilizeTemperature(self, Tgoal, maxDeltaT=20E-6, timeOut=600):
        logger.info('Stabilizing temperature to %.5f K' % Tgoal)
        t = time.time()
        tTimeOut = t + timeOut
        Tdiff = 1E6
        while True:
            time.sleep(1)
            self.qApplication.processEvents()
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

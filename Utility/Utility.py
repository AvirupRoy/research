# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 14:19:28 2015

@author: wisp10
"""

from PyQt4.QtCore import QObject, QThread, pyqtSignal
import time

import sys
class ExceptionHandler(QObject):

    errorSignal = pyqtSignal()
    silentSignal = pyqtSignal()

    def __init__(self):
	super(ExceptionHandler, self).__init__()

    def handler(self, exctype, value, traceback):
        self.errorSignal.emit()
        print "ERROR CAPTURED", value, traceback
        sys._excepthook(exctype, value, traceback)

class PeriodicMeasurementThread(QThread):
    error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.interval = 1
        self._stopRequested = False

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, seconds):
        self._interval = float(seconds)
        
    def setInterval(self, seconds):
        self.interval = seconds

    def stop(self):
        '''Gracefully end execution of the thread.'''
        self._stopRequested = True

    def sleepPrecise(self, tOld):
        '''Execute a precisely timed sleep.'''
        minSleep = 0.010
        tSleep = int(1E3*(self.interval-time.time()+tOld-minSleep))
        if tSleep>minSleep: # Enough time left to do a real sleep
            self.msleep(tSleep)
        while (time.time()-tOld) < self.interval:  # Spin for the remaining time
            pass
        
    def handleException(self, e):
        print "Exception in thread:", e
        self.error.emit(str(e))

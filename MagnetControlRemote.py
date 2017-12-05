# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 09:38:26 2016

@author: wisp10
"""

from Zmq.Zmq import ZmqBlockingRequestor, ZmqAsyncRequestor, ZmqRequest, ZmqSubscriber
from Zmq.Ports import RequestReply, PubSub
from PyQt4.QtCore import QObject, pyqtSignal

class MagnetControlRemote(QObject):
    '''Remote control of ADR magnet via ZMQ sockets (pub-sub and req-rep).
    Use this class to interface with the ADR magnet from other programs.'''
    error = pyqtSignal(str)
    supplyVoltageReceived = pyqtSignal(float)
    supplyCurrentReceived = pyqtSignal(float)
    magnetVoltageReceived = pyqtSignal(float)
    magnetCurrentReceived = pyqtSignal(float)
    '''Provide time, supply current, supply voltage, and magnet voltage'''
    dIdtReceived = pyqtSignal(float)

    def __init__(self, origin, enableControl=True, host='tcp://127.0.0.1', blocking=True, parent = None):
        super(MagnetControlRemote, self).__init__(parent)
        self.subscriber = ZmqSubscriber(PubSub.MagnetControl, host, parent = self)
        self.subscriber.floatReceived.connect(self._floatReceived)
        self.subscriber.start()

        self.supplyVoltage = float('nan')
        self.supplyCurrent = float('nan')
        self.magnetVoltage = float('nan')
        self.magnetCurrent = float('nan')
        self.dIdt = float('nan')

        if enableControl:
            if blocking:
                self.requestor = ZmqBlockingRequestor(port=RequestReply.MagnetControl, origin=origin)
            else:
                self.requestor = ZmqAsyncRequestor(port=RequestReply.MagnetControl, origin=origin, parent=self)
                self.requestor.start()
                
    def checkConnection(self):
        request = ZmqRequest(target='dIdt', command='query')
        reply = self.requestor.sendRequest(request, maxRetries = 0)
        #print "Reply:", reply
        return reply.ok()
                
    def stop(self):
        '''Call to stop the subscriber (and a possible requestor) thread.'''
        self.subscriber.stop()
        try:
            self.requestor.stop()
        except:
            pass
        
    def wait(self, seconds):
        '''Wait for the threads to be finished'''
        self.subscriber.wait(int(1E3*seconds))
        try:
            self.requestor.wait(int(1E3*seconds))
        except:
            pass
        
    def enableDriftCorrection(self, enable=True):
        '''Enables or disables the dIdt drift correction.'''
        request = ZmqRequest(target='driftCorrection', command='set', parameters=bool(enable))
        reply = self.requestor.sendRequest(request)
        if reply is not None:        
            if reply.ok():
                return True
            else:
                self.error.emit(reply.errorMessage)
                return False
                
    def disableDriftCorrection(self):
        '''Disable the dIdt drift correction.'''
        self.enableDriftCorrection(False)
            
    def changeRampRate(self, A_per_s):
        '''Change the ramp rate of the magnet. Returns True if successful.'''
        request = ZmqRequest(target='ramprate', command='set', parameters=A_per_s)
        reply = self.requestor.sendRequest(request)
        if reply is not None:        
            if reply.ok():
                return True
            else:
                self.error.emit(reply.errorMessage)
                return False

    def _floatReceived(self, origin, item, value, timestamp):
        if origin != 'MagnetControlThread':
            return
        if item == 'Isupply':
            self.supplyCurrent = value
            self.supplyCurrentReceived.emit(value)
        elif item == 'Vsupply':
            self.supplyVoltage = value
            self.supplyVoltageReceived.emit(value)
        elif item == 'Vmagnet':
            self.magnetVoltage = value
            self.magnetVoltageReceived.emit(value)
        elif item == 'Imagnet':
            self.magnetCurrent = value
            self.magnetCurrentReceived.emit(value)
        elif item == 'dIdt':
            self.dIdt = value
            self.dIdtReceived.emit(value)
        else:
            pass


if __name__ == '__main__':
    remote = MagnetControlRemote('Test', enableControl=True)    
    print "Connected:", remote.checkConnection()
    
    
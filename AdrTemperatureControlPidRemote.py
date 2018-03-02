# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 09:25:21 2016

@author: wisp10
"""

from Zmq.Zmq import RequestReplyRemote # ,ZmqReply, ZmqRequestReplyThread
from Zmq.Ports import RequestReply

class PidControlRemote(RequestReplyRemote):
    '''Remote control of ADR temperature PID via ZMQ request-reply socket.
    Use this class to interface with the ADR temperature PID control from other programs.'''
    
    def __init__(self, origin, parent=None):
        super(PidControlRemote, self).__init__(origin=origin, port=RequestReply.AdrPidControl, parent=parent)
        
    def rampRate(self):
        return self._queryValue('rampRate')
        
    def setRampRate(self, rate):
        return self._setValue('rampRate', rate)
        
    def rampTarget(self):
        return self._queryValue('rampTarget')

    def setRampTarget(self, T):
        return self._setValue('rampTarget', T)
        
    def enableRamp(self, enable=True):
        return self._setValue('rampEnable', enable)
        
    def rampEnabled(self):
        return self._queryValue('rampEnable')
    
    def setpoint(self):
        return self._queryValue('setpoint')

    def setSetpoint(self, T):
        return self._setValue('setpoint', T)
        
    def start(self):
        return self._clickButton('start')
        
    def stop(self):
        return self._clickButton('stop')
        
    def isFinished(self):
        return self._isEnabled('start')


if __name__ == '__main__':
    remote = PidControlRemote('test')
    print "Ramp rate:", remote.rampRate()
    print "Ramp target:", remote.rampTarget()
    print "Ramp enabled:", remote.rampEnabled()
    
    print "Setting ramp rate:", remote.setRampRate(2.0)
    print "Setting target:", remote.setRampTarget(0.110)
    print "Enabling ramp:", remote.enableRamp(False)
    print "Enabling ramp:", remote.enableRamp(True)

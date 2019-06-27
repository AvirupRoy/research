# -*- coding: utf-8 -*-
"""
Created on Thu Aug 04 18:17:26 2016

@author: wisp10
"""

from Zmq.Zmq import RequestReplyRemote
from Zmq.Ports import RequestReply

class PiezoControlRemote(RequestReplyRemote):
    '''Remote control of ADR temperature PID via ZMQ request-reply socket.
    Use this class to interface with the ADR temperature PID control from other programs.'''
    
    def __init__(self, origin, parent=None):
        super(PiezoControlRemote, self).__init__(origin=origin, port=RequestReply.PiezoControl, parent=parent)
        
    def rampRate(self):
        return self._queryValue('rampRate')
        
    def setRampRate(self, rate):
        return self._setValue('rampRate', rate)
        
    def rampTarget(self):
        return self._queryValue('rampTarget')

    def setRampTarget(self, V):
        return self._setValue('rampTarget', V)
        
    def startRamp(self, enable=True):
        return self._setValue('go', enable)
        
    def ramping(self):
        return self._queryValue('go')


if __name__ == '__main__':
    piezo = PiezoControlRemote('test')
    print "Ramp target", piezo.rampTarget()
    piezo.setRampTarget(0)
    print "Ramp target", piezo.rampTarget()
    print "Ramp rate", piezo.rampRate()
    piezo.startRamp()
    
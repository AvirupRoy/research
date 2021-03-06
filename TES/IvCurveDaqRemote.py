# -*- coding: utf-8 -*-
"""
Created on Tue May 16 11:18:56 2017

@author: zhouyu and Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
from __future__ import print_function
from Zmq.Zmq import RequestReplyRemote
from Zmq.Ports import RequestReply

class IvCurveDaqRemote(RequestReplyRemote):
    '''Remote control of ADR temperature PID via ZMQ request-reply socket.
    Use this class to interface with the ADR temperature PID control from other programs.'''
    
    def __init__(self, origin, parent=None):
        super(IvCurveDaqRemote, self).__init__(origin=origin, port=RequestReply.IvCurveDaq, parent=parent)
        
    def auxAoVoltage(self):
        return self._queryValue('auxVoltage')
        
    def setAuxAoVoltage(self, V):
        return self._setValue('auxVoltage', V)
        
    def maxDriveVoltage(self):
        return self._queryValue('maxDrive')
        
    def setMaxDriveVoltage(self, V):
        return self._setValue('maxDrive', V)
        
    def slewRate(self):
        return self._queryValue('slewRate')
        
    def setSlewRate(self, VperSecond):
        return self._setValue('slewRate', VperSecond)
        
    def setSampleName(self, name):
        return self._setValue('sampleName', name)
        
    def sampleName(self):
        return self._queryValue('sampleName')
        
    def setComment(self, comment):
        return self._setValue('comment', comment)
        
    def comment(self):
        return self._queryValue('comment')
        
    def fileName(self):
        return self._execute('fileName')

    def enableAuxAo(self, enable=True):
        return self._setValue('auxAoEnable', enable)
        
    def disableAuxAo(self):
        return self.enableAuxAo(False)
        
    def start(self):
        return self._clickButton('start')
        
    def stop(self):
        return self._clickButton('stop')
        
    def isFinished(self):
        return self._isEnabled('start')
        
    def sweepCount(self):
        return self._queryValue('sweepCount')
        
    def restart(self):
        return self._execute('restart')

if __name__ == '__main__':
    import time
    ivRemote = IvCurveDaqRemote('Testing')
    print('File name:', ivRemote.fileName())
    print('Finished:',ivRemote.isFinished())
    print('Sweep count:', ivRemote.sweepCount())
    ivRemote.restart()
    for i in range(10):
        time.sleep(1)
        
    print('Sweep count:', ivRemote.sweepCount())

# -*- coding: utf-8 -*-
"""
Created on Tue Sep 26 19:15:10 2017

@author: wisp10
"""

from Zmq.Zmq import RequestReplyRemote # ,ZmqReply, ZmqRequestReplyThread
from Zmq.Ports import RequestReply


class AiSpectrumAnalyzerRemote(RequestReplyRemote):
    '''Remote control of ADR temperature PID via ZMQ request-reply socket.
    Use this class to interface with the ADR temperature PID control from other programs.'''
    
    def __init__(self, origin, parent=None):
        super(AiSpectrumAnalyzerRemote, self).__init__(origin=origin, port=RequestReply.DaqAiSpectrum, parent=parent)
        
    def sampleRate(self):
        return self._queryValue('sampleRate')
        
    def aiChannel(self):
        return self._queryValue('aiChannel')
        
    def setAiChannel(self, channel):
        return self._setValue('aiChannel', channel)
        
    def setSampleRate(self, rate):
        return self._setValue('sampleRate', rate)
        
    def refreshTime(self):
        return self._queryValue('refreshTime')

    def setRefreshTime(self, t):
        return self._setValue('refreshTime', t)
        
    def maxCount(self):
        return self._queryValue('maxCount')
    
    def setMaxCount(self, count):
        return self._setValue('maxCount', count)
        
    def count(self):
        return self._queryValue('count')
        
    def setName(self, name):
        return self._setValue('name', name)
        
    def name(self):
        return self._queryValue('name')

    def setComment(self, comment):
        return self._setValue('comment', comment)
        
    def comment(self):
        return self._queryValue('comment')
        
    def run(self):
        if not self.isRunning():
            return self._clickButton('run')
        
    def stop(self):
        if self.isRunning():
            return self._clickButton('run')
        
    def isRunning(self):
        return self._queryValue('running')


if __name__ == '__main__':
    remote = AiSpectrumAnalyzerRemote('test')
    print "Sample rate:", remote.sampleRate()
    print "max count:", remote.maxCount()
    print "channel:", remote.aiChannel()
    remote.setName('Test2')
    remote.setMaxCount(25)
    response = remote.setAiChannel('ai7')
    print "set channel:", response
    remote.run()
    
    import time
    while True:
        time.sleep(0.5)
        running = remote.isRunning()
        print("Running:", running)
        if not remote.isRunning():
            break
        
    




# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 14:46:57 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from Zmq.Zmq import RequestReplyRemote
from Zmq.Ports import RequestReply

class SineSweepDaqRemote(RequestReplyRemote):
    '''Remote control of SineSweepDaq (for measuring transfer functions)'''
    
    def __init__(self, origin, parent=None):
        super(SineSweepDaqRemote, self).__init__(origin=origin, port=RequestReply.SineSweepDaq, parent=parent)
        
    def auxAoVoltage(self):
        return self._queryValue('auxAo')
        
    def setAuxAoVoltage(self, V):
        return self._setValue('auxAo', V)
        
    def setSampleName(self, name):
        return self._setValue('sample', name)
        
    def sampleName(self):
        return self._queryValue('sample')
        
    def setComment(self, comment):
        return self._setValue('comment', comment)
        
    def start(self):
        return self._clickButton('start')
        
    def stop(self):
        return self._clickButton('stop')
    
    def setOffsetVoltage(self, V):
        return self._setValue('offset', V)
        
    def offsetVoltage(self):
        return self._queryValue('offset')
    
    def setAmplitude(self, V): 
        return self._setValue('amplitude', V)
        
    def amplitude(self): 
        return self._queryValue('amplitude')
        
    def setStartFrequency(self, f):
        return self._setValue('fStart', f)
    
    def startFrequency(self):
        return self._queryValue('fStart')
        
    def setStopFrequency(self, f):
        return self._setValue('fStop', f)
    
    def stopFrequency(self):
        return self._queryValue('fStop')
        
    def setNumberOfSteps(self, num):
        return self._setValue('fSteps', num)
    
    def numberOfSteps(self):
        return self._queryValue('fSteps')
        
    def isFinished(self):
        return self._isEnabled('start')
        
    def totalTime(self):
        return self._queryValue('totalTime')
        
    def samplingRate(self):
        return self._queryValue('samplingRate')*1E3
        
    def setSamplingRate(self, fs):
        return self._setValue('samplingRate', fs*1E-3)
        
    def fileName(self):
        return self._execute('fileName')

if __name__ == '__main__':
    ssd = SineSweepDaqRemote('JustATest')
    print('Filename:', ssd.fileName())
    ssd.setStopFrequency(123456.)
    ssd.setStartFrequency(15.35)
    ssd.setOffsetVoltage(0.1)
    ssd.setSampleName('NonsenseTest')
    print('fStart=',ssd.startFrequency())
    print('fStop=',ssd.stopFrequency())
    print('fSteps=',ssd.numberOfSteps())
    print('Voffset=',ssd.offsetVoltage())
    print('fs=',ssd.samplingRate())
    print('totalTime=', ssd.totalTime())
    #r.start()
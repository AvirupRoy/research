# -*- coding: utf-8 -*-
"""
Created on Tue May 16 11:18:56 2017

@author: zhouyu and Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
from __future__ import print_function
from Zmq.Zmq import RequestReplyRemote
from Zmq.Ports import RequestReply

class PulseCollectorRemote(RequestReplyRemote):
    '''Remote control of ADR temperature PID via ZMQ request-reply socket.
    Use this class to interface with the ADR temperature PID control from other programs.'''
    
    def __init__(self, origin, parent=None):
        super(PulseCollectorRemote, self).__init__(origin=origin, port=RequestReply.PulseCollector, parent=parent)
        
#    def auxAoVoltage(self):
#        return self._queryValue('auxVoltage')
#        
#    def setAuxAoVoltage(self, V):
#        return self._setValue('auxVoltage', V)
        
    def finalBiasVoltage(self):
        return self._queryValue('biasFinal')
        
    def setFinalBiasVoltage(self, V):
        return self._setValue('biasFinal', V)
        
    def setPulseLowLevel(self, V):
        return self._setValue('pulseLowLevel', V)
        
    def pulseLowLevel(self):
        return self._queryValue('pulseLowLevel')
        
    def testPulseCount(self):
        return self._queryValue('testPulseCount')

    def setTestPulseWidth(self, s):
        us = 1E6*s
        return self._setValue('testPulseWidth', us)

    def testPulseWidth(self):
        return 1E-6*self._queryValue('testPulseWidth')
        
    def setTestHighLevel(self, V):
        return self._setValue('testHighLevel', V)

    def testHighLevel(self):
        return self._queryValue('testHighLevel')
        
    def start(self):
        return self._execute('start')
        
    def stop(self):
        return self._execute('stop')
        
    def setComment(self, string):
        self._setValue('comment', string)
        
    def fileName(self):
        return self._execute('fileName')
        
#    def isFinished(self):
#        return self._isEnabled('start')
        

if __name__ == '__main__':
    import time
    import numpy as np    
    pr = PulseCollectorRemote('Testing')
    print('Test pulse width:', pr.testPulseWidth())
    print('Test pulse high level:', pr.testHighLevel())
    print('Test pulse count:', pr.testPulseCount())

    #pws = np.asarray([0.04, 0.06, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0])*1E-6
    pws = np.arange(0.4, 15, 0.4)*1E-6
    deltaPw = 0.05
    #pws = np.arange(0.05, 0.4+deltaPw, deltaPw)*1E-6
    pws = np.arange(0.025, 0.805, 0.005)*1E-6
    pws = np.arange(0.025, 0.370, 0.025)*1E-6
#    pws = np.arange(0.025, 1.525, 0.025)*1E-6
    #pws = np.arange(0.50, 6.5, 0.5)*1E-6
    pws = np.arange(0.025, 0.5+0.025, 0.025)*1E-6
    pws = np.arange(0.025, 0.550, 0.025)*1E-6
    pws = np.hstack([0.016E-6,pws])
    print(len(pws))

    if False:
        oldCount = -1
        for pw in pws:
            print(pw)
            #pr.setTestPulseWidth(pw)
            while True:
                time.sleep(30)
                count = pr.testPulseCount()
                if count > oldCount+0:
                    oldCount = count
                    break
            print('Changing pulse width to:', pw)
            pr.setTestPulseWidth(pw)
    
    if True:
        oldCount = -1
        while True:
            for pw in np.random.permutation(pws):
                print(pw)
                #pr.setTestPulseWidth(pw)
                while True:
                    time.sleep(30)
                    count = pr.testPulseCount()
                    if count > oldCount+10:
                        oldCount = count
                        break
                print('Changing pulse width to:', pw)
                pr.setTestPulseWidth(pw)

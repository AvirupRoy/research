# -*- coding: utf-8 -*-
"""
Created on Mon Oct 02 14:45:15 2017

@author: wisp10
"""
from __future__ import print_function
import DAQ.PyDaqMx as daq
import numpy as np
import time

        
def tuneStage1OutputToZero(pfl, aiChannel):
    task = daq.AiTask('TuneStage1OffsetCurrent')
    task.addChannel(aiChannel)
    fbCoupling = 6E-6

    Is = fbCoupling * np.linspace(0.5, 2.5, 10)
    Im = np.mean(Is)
    pfl.setStage1OffsetCurrent(Im) # Start in the middle of the range
    time.sleep(0.05)
    pfl.resetPfl()
    Vs = []
    for I in Is:
        pfl.setStage1OffsetCurrent(I)
        time.sleep(0.05)
        V = np.mean(task.readData(100)[0,10:])
        Vs.append(V)
    #print('Vs=',Vs, 'Is=',Is)
    fit = np.polyfit(Vs, Is, 1)
    #print(fit)
    I0 = np.polyval(fit, 0)
    #print("I=", I0)
    if I0 < 0:
        pass
        #logger.warn('Cannot achieve 0 output')
    else:
        pfl.setStage1OffsetCurrent(I0)
    V = np.mean(task.readData(100)[0,10:])
    return V
        
def tuneStage2OutputToZero(pfl, aiChannel):
    pfl.lockStage2()
    task = daq.AiTask('TuneStage2OffsetCurrent')
    task.addChannel(aiChannel)
    fbCoupling = 6E-6

    Is = fbCoupling * np.linspace(0.5, 2.5, 10)
    Im = np.mean(Is)
    pfl.setStage2OffsetCurrent(Im) # Start in the middle of the range
    time.sleep(0.05)
    pfl.resetPfl()
    Vs = []
    for I in Is:
        pfl.setStage2OffsetCurrent(I)
        time.sleep(0.05)
        V = np.mean(task.readData(100)[0,10:])
        Vs.append(V)
    fit = np.polyfit(Vs, Is, 1)
    I0 = np.polyval(fit, 0)
    if I0 < 0:
        pass
        #logger.warn('Cannot achieve 0 output')
    else:
        pfl.setStage2OffsetCurrent(I0)
    V = np.mean(task.readData(100)[0,10:])
    return V

if __name__ == '__main__':
    from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote
    
    osr = OpenSquidRemote(port = 7894)
    pfl = Pfl102Remote(osr, 'TES2')
    print('Feedback capacitor:', pfl.feedbackC()*1E-9, 'nF')
    print('Feedback resistor:', pfl.feedbackR(), 'Ohm')
    print('Stage 1 bias current:', pfl.stage1BiasCurrent()*1E6, 'uA')
    print('Stage 1 flux current:', pfl.stage1OffsetCurrent()*1E6, 'uA')
    print('Stage 2 bias current:', pfl.stage2BiasCurrent()*1E6, 'uA')
    print('Stage 2 offset current:', pfl.stage2OffsetCurrent()*1E6, 'uA')
    print('Stage 2 offset voltage:', pfl.stage2OffsetVoltage()*1E3, 'mV')
    print('Report:', pfl.report())

    print(pfl.lockStage1())
    print(pfl.lockStage2())
    #tuneStage2OutputToZero(pfl, aiChannel)
    print('Stage 1 locked:', pfl.stage1Locked())
    print('Stage 2 locked:', pfl.stage2Locked())
    pfl.setTestInput('SQUID flux')
    pfl.setTestSignal('On')
    print('Test input:', pfl.testInput())
    print('Test signal:', pfl.testSignal())

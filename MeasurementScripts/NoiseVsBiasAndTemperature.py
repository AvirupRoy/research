# -*- coding: utf-8 -*-
"""
Created on 2017-09-26
@author: Felix Jaeckel
"""
from __future__ import print_function
import time
import numpy as np
from PyQt4.QtGui import QApplication
from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote
from SquidHelper import tuneStage1OutputToZero
from Adr import Adr
 
import DAQ.PyDaqMx as daq

class Tes(object):
    def __init__(self, Rbias, biasChannel, fieldChannel=None):
        self.Rbias = Rbias
        self.biasChannel = biasChannel
      
    def setBias(self, Ibias):
        task = daq.AoTask('biasTask')
        task.addChannel(self.biasChannel)
        Vbias = Ibias * self.Rbias
        logger.info('Applying Vbias=%.5f V' % Vbias)
        task.writeData([Vbias], autoStart = True)
        task.stop()
        task.clear()

def wait(seconds):
    t0 = time.time()
    while time.time()-t0 < seconds-2:
        app.processEvents()
        time.sleep(1)
        
    while time.time()-t0 < seconds:
        time.sleep(0.1)

if __name__ == '__main__':
    import logging
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    #ch = logging.StreamHandler()
    #logger.addHandler(ch)
    app = QApplication([])
    
    aiChannel = daq.AiChannel('USB6361/ai7', -10,+10)
    osr = OpenSquidRemote(port=7894, origin='NoiseVsBiasAndTemperature')
    
    device = 'TES2'
    squid = Pfl102Remote(osr, device)
    squid.setFeedbackR(100E3)
    squid.setFeedbackC(15E-9)
    x = tuneStage1OutputToZero(squid, aiChannel)
    print(x)
    print(squid.report())
    print(squid.stage1OffsetCurrent())
            
    adr = Adr(app)
    
    #Rbias = 1697.5 # TES 1
    Rbias = 1601.7 # TES 2
    
    tes = Tes(Rbias, biasChannel = daq.AoChannel('USB6361/ao0',-5,+5))
    Vcoil = -0.167 # For TES2

    coilChannel = daq.AoChannel('USB6361/ao1',-5,+5)
    taskCoil = daq.AoTask('coilTask')
    taskCoil.addChannel(coilChannel)
    logger.info('Applying Vcoil=%.5f V' % Vcoil)
    taskCoil.writeData([Vcoil], autoStart = True)
    taskCoil.stop()
    taskCoil.clear()
        
    from DAQ.AiSpectrumAnalyzerRemote import AiSpectrumAnalyzerRemote
    sa = AiSpectrumAnalyzerRemote('test')
    sa.setSampleRate(2E6)
    sa.setMaxCount(400)
    sa.setRefreshTime(0.1)
    
    Ibiases = np.asarray([0, 100E-6, 200E-6, 300E-6, 320E-6, 350E-6, 370E-6])
    #Ibiases = np.linspace(0, 400, 21)*1E-6
    
    #TES1
    #baseTs = 1E-3* np.asarray( [74.0, 75.778, 77.556, 79.0, 79.333, 81.111, 82.889, 84.5, 84.667, 87.5, 90.0, 92.5, 95.0, 100.0, 105.0, 110.0, 120.0, 150.0, 200.0] )

    #TES2
    baseTs = 1E-3*np.asarray([82.0, 83.444, 84.889, 85.1, 86.2, 86.333, 87.2, 87.316, 87.778, 88.4,88.423, 89.222,89.531,90.639, 90.667, 91.747,92.111, 92.8,92.854, 93.556,93.962, 95, 100, 110, 120, 150, 200, 250, 300])
    baseTs = 1E-3*np.asarray([89.531,90.639, 90.667, 91.747,92.111, 92.8,92.854, 93.556,93.962, 95, 100, 110, 120, 150, 200, 250, 300])
    #baseTs = np.linspace(75, 105, 31)*1E-3
    
    Cfbs = [15E-9] #, 1.5E-9]    
    for baseT in baseTs:
        print('Ramping to %fK' % baseT)
        adr.rampTo(baseT)
        adr.stabilizeTemperature(baseT)
        print('Temperature stabilized. Waiting...')
        wait(45)
        for Ibias in Ibiases:
            for Cfb in Cfbs:
                print('Setting SQUID FB: %.1f nF' % (Cfb*1E9))
                squid.setFeedbackC(Cfb)
                print('Applying bias: %.3fuA' % (Ibias*1E6))
                tes.setBias(Ibias)
                wait(2)        
                print('Zeroing SQUID...',)
                V = tuneStage1OutputToZero(squid, aiChannel)
                print('Done: V=%f V' % V)
                
                sa.setName(device+'_%.1fuA_%.2fmK_C%.1fnF' % (Ibias*1E6, baseT*1E3, Cfb*1E9))
                sa.setComment(str(squid.report()))
        
                for i in range(2):
                    print('Acquiring spectrum %d' % i, end='')
                    sa.run()
                    t = time.time()
                    wait(3)
                    while sa.isRunning():
                        print('.', end='')
                        if time.time() - t > 120:
                            print("Still hasn't finished. Asking it to stop.")
                            sa.stop()
                            wait(3)
                        wait(3)
                    print('Done')
                    squid.resetPfl()
                    wait(1)
            
    #adr.rampTo(0.175)
    #adr.setRampRate(15)

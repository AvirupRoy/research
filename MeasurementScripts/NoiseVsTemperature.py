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
            
    adr = Adr(app)
    
    from DAQ.AiSpectrumAnalyzerRemote import AiSpectrumAnalyzerRemote
    sa = AiSpectrumAnalyzerRemote('test')
    sa.setSampleRate(2E6)
    sa.setMaxCount(400)
    sa.setRefreshTime(0.1)
    
    baseTs = np.logspace(np.log10(0.120), np.log10(0.055), 20)
    
    Cfbs = [15E-9]
    for baseT in baseTs:
        print('Ramping to %fK' % baseT)
        adr.rampTo(baseT)
        adr.stabilizeTemperature(baseT)
        print('Temperature stabilized. Waiting...')
        wait(45)
        for Cfb in Cfbs:
            print('Setting SQUID FB: %.1f nF' % (Cfb*1E9))
            squid.setFeedbackC(Cfb)
            wait(2)        
            print('Zeroing SQUID...',)
            V = tuneStage1OutputToZero(squid, aiChannel)
            print('Done: V=%f V' % V)
            
            sa.setName(device+'_Noise_%.2fmK_C%.1fnF_%s' % (baseT*1E3, Cfb*1E9, time.strftime('%Y%m%d_%H%M%S')))
            sa.setComment(str(squid.report()))
    
            for i in range(3):
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

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
from Utility.HkLogger import HkLogger
import h5py as hdf
from Zmq.Subscribers import HousekeepingSubscriber

def wait(seconds):
    t0 = time.time()
    while time.time()-t0 < seconds-2:
        app.processEvents()
        time.sleep(1)
    app.processEvents()
    while time.time()-t0 < seconds:
        time.sleep(0.1)

if __name__ == '__main__':
    import logging
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    aiChannel = daq.AiChannel('USB6361/ai5', -10,+10)
    baseTs = np.logspace(np.log10(0.055), np.log10(1.300), 71)
    print('Temperatures:', baseTs)
    device = 'TES2'
    Cfbs = [1.5E-9]
    
    origin = 'NoiseVdTemperature'
    app = QApplication([])
    hdfFile = hdf.File('NoiseVsT_%s_20180130.h5' % device)
    hdfFile.attrs['program'] = origin
    hdfFile.attrs['Control'] = 'RuOx2005'
    hdfFile.attrs['Device'] = device
    hdfFile.attrs['aiChannel'] = str(aiChannel.physicalChannel)
    hdfFile.attrs['Ts'] = baseTs
    
    hkGroup = hdfFile.require_group('HK')
    hkSub = HousekeepingSubscriber()
    hkSub.start()        
    hkLogger = HkLogger(hkGroup, hkSub)
    
    osr = OpenSquidRemote(port=7894, origin=origin)
    
    squid = Pfl102Remote(osr, device)
    squid.setFeedbackR(100E3)
    squid.setFeedbackC(1.5E-9)
    x = tuneStage1OutputToZero(squid, aiChannel)
            
    adr = Adr(app)
    
    from DAQ.AiSpectrumAnalyzerRemote import AiSpectrumAnalyzerRemote
    sa = AiSpectrumAnalyzerRemote('test')
    sa.setSampleRate(2E6)
    sa.setMaxCount(300)
    sa.setRefreshTime(0.1)
    
    for baseTindex, baseT in enumerate(baseTs):
        print('Ramping to %fK' % baseT)
        rampRate = min(10,max(0.3, 1E3*abs(adr.T - baseT) / 1.5))
        print('Ramp rate:', rampRate)
        adr.setRampRate(rampRate)
        
        adr.rampTo(baseT)
        adr.stabilizeTemperature(baseT)
        print('Temperature stabilized. Waiting...')
        wait(45)
        g = hdfFile.require_group('BaseT%05d' % baseTindex)
        g.attrs['Tbase'] = baseT
        for CfbIndex, Cfb in enumerate(Cfbs):
            subG = g.require_group('Cfb%03d' % CfbIndex)
            subG.attrs['Cfb'] = Cfb
            print('Setting SQUID FB: %.1f nF' % (Cfb*1E9))
            squid.setFeedbackC(Cfb)
            wait(2)        
            print('Zeroing SQUID...',)
            V = tuneStage1OutputToZero(squid, aiChannel)
            subG.attrs['squidZero'] = V
            print('Done: V=%f V' % V)
            
            name = device+'_Noise_%.2fmK_C%.1fnF_%s' % (baseT*1E3, Cfb*1E9, time.strftime('%Y%m%d_%H%M%S'))
            sa.setName(name)
            subG.attrs['fileName'] = name
            
            sa.setComment(str(squid.report()))
    
            for i in range(3):
                print('Acquiring spectrum %d' % i, end='')
                sa.run()
                t = time.time()
                subG.attrs['start'] = t
                wait(3)
                while sa.isRunning():
                    print('.', end='')
                    if time.time() - t > 120:
                        print("Still hasn't finished. Asking it to stop.")
                        sa.stop()
                        wait(3)
                    wait(3)
                print('Done')
                subG.attrs['stop'] = time.time()
                squid.resetPfl()
                wait(1)
            
    #adr.rampTo(0.175)
    #adr.setRampRate(15)
    hdfFile.attrs['tStop'] = time.time()
    del hkSub
    del hkLogger
    hdfFile.close() 
    print('Done')

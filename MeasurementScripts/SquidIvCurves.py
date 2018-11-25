# -*- coding: utf-8 -*-
"""
Created on Mon Oct 02 14:44:32 2017

@author: wisp10
"""
from __future__ import print_function

import h5py as hdf

def collectIvCurves(device, hdfRoot, offsetCurrents):
    osr = OpenSquidRemote(port = 7894)
    pfl = Pfl102Remote(osr, device)
    pfl.setTestSignal('Off')
    pfl.setTestInput('SQUID bias')
    channel = bytes(pfl.daqDevice()+'/'+pfl.daqChannel())
    refChannel = bytes(pfl.daqDevice()+'/'+pfl.daqReferenceChannel())
    triggerTerminal = bytes(pfl.daqTrigger())
    print('Channel:', channel)
    aiChannel = daq.AiChannel(channel, -10, +10)
    aiChannel.setTerminalConfiguration(daq.AiChannel.TerminalConfiguration.DIFF)

    aiRefChannel = daq.AiChannel(refChannel, -10, +10)
    aiRefChannel.setTerminalConfiguration(daq.AiChannel.TerminalConfiguration.DIFF)
    
    pfl.lockStage2()
    pfl.setStage1BiasCurrent(0)
    tuneStage2OutputToZero(pfl, aiChannel)
    pfl.setTestSignal('On')

    fs = 500E3
    samples = int(fs*0.09)
    timing = daq.Timing(rate=fs)
    timing.setSamplesPerChannel(samples)
    timing.setSampleMode(daq.Timing.SampleMode.FINITE)
        
    g = hdfRoot.create_group('IV_Test')
    g.attrs['device'] = device
    g.attrs['sampleRate'] = timing.rate

    aiTaskR = daq.AiTask('aiRef')
    aiTaskR.addChannel(aiRefChannel)
    aiTaskR.configureTiming(timing)
    aiTaskR.digitalEdgeStartTrigger(triggerTerminal, daq.Edge.RISING)
    rsRef = RunningStats()
    for i in range(10):
        aiTaskR.start()
        while aiTaskR.samplesAvailable() < samples:
            print('.', end='')
            time.sleep(0.05)
        d = aiTaskR.readData(samples)[0]
        aiTaskR.stop()
        rsRef.push(d)
    g.attrs['FgChannel'] = refChannel
    g.create_dataset('FgMean', data=rsRef.mean())
    g.create_dataset('FgStd', data=rsRef.std())
    g.attrs['report'] = str(pfl.report())
    g.attrs['offsetCurrents'] = offsetCurrents

    aiTask = daq.AiTask('aiPfl')
    aiTask.addChannel(aiChannel)
    aiTask.configureTiming(timing)
    aiTask.digitalEdgeStartTrigger(triggerTerminal, daq.Edge.RISING)
    
    #import matplotlib.pyplot as mpl
    
    for offsetCurrent in offsetCurrents:
        print('Current:', offsetCurrent)
        pfl.setStage1OffsetCurrent(offsetCurrent)
        pfl.setTestSignal('Off')
        time.sleep(0.2)
        pfl.resetPfl()
        pfl.setTestSignal('On')
        time.sleep(0.2)
        print('Acquiring', end='')
        rs = RunningStats()
        for i in range(20):
            aiTask.start()
            while aiTask.samplesAvailable() < samples:
                print('.', end='')
                time.sleep(0.05)
            d = aiTask.readData(samples)[0]
            rs.push(d)
            #print(d.shape)
            aiTask.stop()
        #mpl.plot(rs.mean())
        sg = g.create_group('Offset%05.0fnA' % (offsetCurrent*1E9))
        sg.create_dataset('PflMean', data=rs.mean())
        sg.create_dataset('PflStd', data=rs.std())
        sg.attrs['squidFlux'] = pfl.stage1OffsetCurrent()
        sg.attrs['Channel'] = channel
        
    #mpl.show()

def collectVPhiCurves(device, hdfRoot, biasCurrents):
    osr = OpenSquidRemote(port = 7894)
    pfl = Pfl102Remote(osr, device)
    pfl.setTestSignal('Off')
    pfl.setTestInput('SQUID flux')
    channel = bytes(pfl.daqDevice()+'/'+pfl.daqChannel())
    refChannel = bytes(pfl.daqDevice()+'/'+pfl.daqReferenceChannel())
    triggerTerminal = bytes(pfl.daqTrigger())
    print('Channel:', channel)
    aiChannel = daq.AiChannel(channel, -5, +5)
    aiChannel.setTerminalConfiguration(daq.AiChannel.TerminalConfiguration.DIFF)

    aiRefChannel = daq.AiChannel(refChannel, -2, +2)
    aiRefChannel.setTerminalConfiguration(daq.AiChannel.TerminalConfiguration.DIFF)
    
    pfl.lockStage2()
    pfl.setStage1OffsetCurrent(0)
    tuneStage2OutputToZero(pfl, aiChannel)
    pfl.setTestSignal('On')

    fs = 500E3
    samples = int(fs*0.09)
    timing = daq.Timing(rate=fs)
    timing.setSamplesPerChannel(samples)
    timing.setSampleMode(daq.Timing.SampleMode.FINITE)
        
    g = hdfRoot.create_group('V-Phi')
    g.attrs['device'] = device
    g.attrs['sampleRate'] = timing.rate

    aiTaskR = daq.AiTask('aiRef')
    aiTaskR.addChannel(aiRefChannel)
    aiTaskR.configureTiming(timing)
    aiTaskR.digitalEdgeStartTrigger(triggerTerminal, daq.Edge.RISING)
    rsRef = RunningStats()
    for i in range(10):
        aiTaskR.start()
        while aiTaskR.samplesAvailable() < samples:
            print('.', end='')
            time.sleep(0.05)
        d = aiTaskR.readData(samples)[0]
        aiTaskR.stop()
        rsRef.push(d)
    g.attrs['FgChannel'] = refChannel
    g.create_dataset('FgMean', data=rsRef.mean())
    g.create_dataset('FgStd', data=rsRef.std())
    g.attrs['report'] = str(pfl.report())
    g.attrs['biasCurrents'] = biasCurrents

    aiTask = daq.AiTask('aiPfl')
    aiTask.addChannel(aiChannel)
    aiTask.configureTiming(timing)
    aiTask.digitalEdgeStartTrigger(triggerTerminal, daq.Edge.RISING)
    
    #import matplotlib.pyplot as mpl
    pfl.setTestSignal('On')
    
    for biasCurrent in biasCurrents:
        print('Current:', biasCurrent)
        pfl.setStage1BiasCurrent(biasCurrent)
        time.sleep(0.2)
        print('Acquiring', end='')
        rs = RunningStats()
        for i in range(20):
            aiTask.start()
            while aiTask.samplesAvailable() < samples:
                print('.', end='')
                time.sleep(0.05)
            d = aiTask.readData(samples)[0]
            rs.push(d)
            #print(d.shape)
            aiTask.stop()
        #mpl.plot(rs.mean())
        sg = g.create_group('Bias%07.0fuA' % (biasCurrent*1E6))
        sg.create_dataset('PflMean', data=rs.mean())
        sg.create_dataset('PflStd', data=rs.std())
        sg.attrs['biasCurrent'] = pfl.stage1BiasCurrent()
        sg.attrs['Channel'] = channel
        
    #mpl.show()

if __name__ == '__main__':
    import numpy as np
    from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote
    from SquidHelper import tuneStage2OutputToZero
    import DAQ.PyDaqMx as daq
    import time
    #from Utility.RunningStats import RunningStats
    from Utility.RunningStats import RunningStats

    device = 'TES2'
    offsetCurrents = np.linspace(1.30E-6, 7.5E-6, 51)
    biasCurrents = np.linspace(10E-6, 300E-6, 61)
    
    osr = OpenSquidRemote(port = 7894, origin='SquidIvCurves')
    ifc = osr.obtainInterfaceRemote('PCI-1000')
    fg = ifc.functionGenerator()

    with hdf.File('SQUID_%s_075mK_Vac50mV_fac321kHz_%s.h5' % (device,time.strftime('%Y%m%d_%H%M%S')), 'a') as f:
        fg.setAmplitude(3.0)
        collectIvCurves(device, f, offsetCurrents)
        fg.setAmplitude(1.0)
        collectVPhiCurves(device, f, biasCurrents)

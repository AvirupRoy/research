# -*- coding: utf-8 -*-
"""
At a fixed base temperature, measure:
a) IV curve vs a few nearby temperatures (for betaIV)
b) IV curve at base temperature to determine bias points
c) Transfer function for different Vbias from normal all the way to SC
    d) Optionally take noise spectrum at each of these points

Created 2017-11-14
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from __future__ import print_function
import logging
logging.basicConfig(level=logging.WARN)

from Analysis.G4C.MeasurementDatabase import obtainTes
import numpy as np
from PyQt4.QtGui import QApplication
from OpenSQUID.OpenSquidRemote import OpenSquidRemote, Pfl102Remote
from TES.IvCurveDaqRemote import IvCurveDaqRemote
from TES.SineSweepDaqRemote import SineSweepDaqRemote
from DAQ.AiSpectrumAnalyzerRemote import AiSpectrumAnalyzerRemote
from SquidHelper import tuneStage1OutputToZero
from Adr import Adr
from Tes import Tes, FieldCoil
import time
from Utility import wait
import DAQ.PyDaqMx as daq
import h5py as hdf
from MeasurementScripts.IvBiasPointFinder import findBiasPointR

cooldown = 'G4C'
deviceId = 'TES1'
pflChannelId = 'ai2'
acBiasAttenuation = 20.
doNoise = True; nSpectra = 1

tes = obtainTes(cooldown, deviceId)

Tbase = 72E-3
deltaTs = 1E-3*np.asarray([-0.35, -0.25, -0.15, -0.05, 0, +0.05, +0.15, +0.25, +0.35])
#deltaTs = 1E-3*np.asarray([-0.1,0.1])
#deltaTs = np.asarray([])
Rgoals = np.hstack([[0], np.logspace(np.log10(0.05), np.log10(0.90), 31), [1]]) * tes.Rnormal
Rgoals.sort()
Rgoals = Rgoals[::-1]
Vcoils = np.linspace(-0.7,+0.3, 21)

startTimeString = time.strftime('%Y%m%d_%H%M%S')
outputFileName = deviceId + '_TfVsBias_' + startTimeString+ '.h5'
origin = 'Tes_TransferVsBias'

biasChannel = daq.AoChannel('USB6361/%s' % 'ao0', -5, +5)
acBiasChannel = daq.AoChannel('USB6361/%s' % 'ao1', -5, +5)
pflChannel = daq.AiChannel('USB6361/%s' % pflChannelId, -5,+5)
tesDev = Tes(tes.Rbias, biasChannel, fieldChannel = None, pflChannel = pflChannel)

sa = AiSpectrumAnalyzerRemote(origin)
sa.setSampleRate(2E6)
sa.setMaxCount(400)
sa.setRefreshTime(0.1)
sa.setAiChannel(pflChannelId)        

ssd = SineSweepDaqRemote(origin)
ssd.setSampleName(deviceId)

ivRemote = IvCurveDaqRemote(origin)
osr = OpenSquidRemote(port=7894, origin=origin)
squid = Pfl102Remote(osr, deviceId)

app = QApplication([])
adr = Adr(app)

coil = FieldCoil()
coil.rampBias(-5)

def collectIvSweeps(count):
    ivRemote.start()
    print('Recording IV curve', end='')
    wait(10)
    while True:
        wait(1)
        print('.', end='')
        if ivRemote.sweepCount() >= count:
            print('Enough sweeps.')
            break
    ivRemote.stop()
    while True:     # Wait for IV sweep to stop
        wait(1)
        print('.', end='')
        if ivRemote.isFinished():
            print('Done.')
            break
    ivFileName = ivRemote.fileName()
    return ivFileName    
    
def rampAndStabilize(Tgoal):
    rampRate = min(5,max(0.2, 1E3*abs(adr.T - Tbase) / 1.5))
    adr.setRampRate(rampRate)
    adr.rampTo(Tgoal)
    print('Going to %.4f K' % Tgoal)
    adr.stabilizeTemperature(Tgoal)
    wait(60)
    
def killAcBias():
    # Would like to ensure there's no output from modulation terminal
    aoTask = daq.AoTask('acBiasReturnToZero')
    aoTask.addChannel(acBiasChannel)
    aoTask.writeData([0], autoStart=True)
    aoTask.stop()
    aoTask.clear()
    del aoTask

print('Waiting for valid ADR temperature', end='')
while True:
    print('.', end='')
    app.processEvents()
    time.sleep(1)
    T = adr.T
    if T == T:
        print(T, 'K')
        break


for Vcoil in Vcoils:
    print('Vcoil=', Vcoil)
    coil.rampBias(Vcoil)
    outputFileName = deviceId + '_TfVsBias_' + startTimeString+ '.h5'
    
    with hdf.File(outputFileName, mode='a') as f:
        a = f.attrs
        a['program'] = 'Tes_TransferVsBias.py'
        a['time'] = time.time()
        a['localTime'] = startTimeString
        a['TbaseGoal'] = Tbase
        a['Vcoil'] = Vcoil
        a['Rbias'] = tes.Rbias
        a['Rnormal'] = tes.Rnormal
        a['deviceName'] = tes.DeviceName
        a['Rshunt'] = tes.Rshunt
        a['SQUID'] = str(squid.report())
        a['Rgoals'] = Rgoals
        a['deltaTs'] = deltaTs
        
    # Collect IV sweeps around Tbase
    # Switch PFL to low gain
    squid.setFeedbackR(10E3)
    squid.setFeedbackC(15E-9)
    squid.resetPfl()
    
    sweepFileNames = []
    for deltaT in deltaTs:
        Tgoal = Tbase+deltaT
        rampAndStabilize(Tgoal)
        sweepFileName = collectIvSweeps(3)
        sweepFileNames.append(sweepFileName)
        
    with hdf.File(outputFileName, mode='a') as f:
        f.attrs['ivSweepTbases'] = Tbase+deltaTs
        for i, fileName in enumerate(sweepFileNames):
            f.attrs['ivSweepFileName%02d' % i] = fileName
    
    rampAndStabilize(Tbase)
    sweepFileName = collectIvSweeps(4) 
    
    with hdf.File(outputFileName, mode='a') as f:
        f.attrs['ivSweepFileName'] = sweepFileName
    
    Ibiases = np.zeros_like(Rgoals)
    Vbiases = np.zeros_like(Rgoals)
    for iR, Rgoal in enumerate(Rgoals):
        if Rgoal == 0:
            Vbias = 0
        elif Rgoal == tes.Rnormal:
            Vbias = 4.8
        else:
            Vbias = findBiasPointR(sweepFileName, tes, Rfb=squid.feedbackR(), Rgoal=Rgoal)
        Ibias = Vbias/tes.Rbias
        Ibiases[iR] = Ibias
        Vbiases[iR] = Vbias
    
    print(Vbiases)
    
    squid.setFeedbackR(100E3)
    squid.setFeedbackC(1.5E-9)
    squid.resetPfl()
    
    for i, (Ibias, Rgoal) in enumerate(zip(Ibiases, Rgoals)):
        Vbias = Ibias * tes.Rbias
        print('Rgoal=%.5f, Vbias=%.5f' % (Rgoal, Vbias))
        tesDev.rampBias(Ibias)
        wait(2)
        squid.resetPfl()
        tuneStage1OutputToZero(squid, pflChannel)
    
        # Record transfer function
        transferFunctionFileNames = []
        amplitudes = np.asarray([0.002, 0.004])
        for amplitude in amplitudes:
            ssd.setAmplitude(amplitude*acBiasAttenuation)
            ssd.setComment('Tbase=%.4f, Vbias=%.4f, Vcoil=%.4f, Rfb=%.1f' % (Tbase, Vbias, Vcoil, squid.feedbackR()))
            squid.resetPfl()
            wait(1)
            ssd.start()
            print('Recording transfer function', end='')
            while True:
                wait(2)
                print('.', end='')
                if ssd.isFinished():
                    print('Done.')
                    break
            transferFunctionFileNames.append(ssd.fileName())
            killAcBias()
      
        if doNoise:  
            squid.resetPfl()
            # Take noise data
            fileNameNoise = '%s_Noise_%.3fmK_Bias%.4fV_Coil%.4fV_%s' % (deviceId, Tbase*1E3, Vbias, Vcoil, time.strftime('%Y%m%d_%H%M%S')) 
            sa.setName(fileNameNoise)
            sa.setComment(str(squid.report()))
        
            for iSpectrum in range(nSpectra):
                print('Acquiring noise spectrum %d' % iSpectrum, end='')
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
        else:
            fileNameNoise = ''
        
        print('Writing file')
        with hdf.File(outputFileName, mode='a') as f:
            group = f.require_group('Rgoal%03d' % iR)
            group.attrs['Tbase'] = Tbase
            group.attrs['Vbias'] = Vbias
            group.attrs['Vcoil'] = Vcoil
            group.attrs['Ibias'] = Ibias
            group.attrs['Rgoal'] = Rgoal
            group.attrs['TFamplitudes'] = np.asarray(amplitudes)
            group.attrs['noiseFileName'] = fileNameNoise
            for i, fileName in enumerate(transferFunctionFileNames):
                group.attrs['transferFunctionFileName%d' % i] = fileName
    
    squid.setFeedbackR(10E3)
    squid.setFeedbackC(15E-9)
    wait(2)
    squid.resetPfl()
    tuneStage1OutputToZero(squid, pflChannel)
    print('Collecting one more set of IV sweeps')
    sweepFileNameEnd = collectIvSweeps(4) 
    with hdf.File(outputFileName, mode='a') as f:
        f.attrs['ivSweepFileNameEnd'] = sweepFileNameEnd
                
print('Done on cold end!')

adr.setRampRate(4)
adr.rampTo(0.15)

sweepFileNameHot = collectIvSweeps(4) 
with hdf.File(outputFileName, mode='a') as f:
    f.attrs['ivSweepFileNameHot'] = sweepFileNameHot

squid.setFeedbackR(100E3)
squid.setFeedbackC(1.5E-9)
squid.resetPfl()
tuneStage1OutputToZero(squid, pflChannel)

transferFunctionFileNamesHot = []
for amplitude in amplitudes:
    ssd.setAmplitude(amplitude*acBiasAttenuation)
    ssd.setComment('Tbase=%.4f, Vbias=%.4f, Vcoil=%.4f, Rfb=%.1f' % (Tbase, Vbias, Vcoil, squid.feedbackR()))
    squid.resetPfl()
    wait(1)
    ssd.start()
    print('Recording transfer function', end='')
    while True:
        wait(2)
        print('.', end='')
        if ssd.isFinished():
            print('Done.')
            break
    transferFunctionFileNamesHot.append(ssd.fileName())
    killAcBias()

with hdf.File(outputFileName, mode='a') as f:
    group = f.require_group('Hot')
    for i, fileName in enumerate(transferFunctionFileNamesHot):
        group.attrs['transferFunctionFileName%d' % i] = fileName
        
    



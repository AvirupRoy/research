# -*- coding: utf-8 -*-
"""
Go to various bias points and base temperatures and measure:
a) Isquid vs. T to determine beta
b) IV curve to determine alpha
c) Transfer function
d) Noise spectra

Created on Mon Oct 23 21:48:29 2017
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from __future__ import print_function
import logging
logging.basicConfig(level=logging.WARN)

from Analysis.G4C.MeasurementDatabase import obtainTes
#import numpy as np
import pandas as pd
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
import numpy as np

from Analysis.TesIvSweepReader import IvSweepCollection

def findBiasPointR(fileName, tes, Rfb, Rgoal):    
    sweeps = IvSweepCollection(fileName)

    Vteses = []; Iteses = []; Vbiases = []

    for sweep in sweeps:
        #sweep.plotRaw()
        MiOverMfb = tes.MiOverMfb(Rfb)
        #shift = sweep.checkForOffsetShift()
        sweep.subtractSquidOffset()
        sweep.applyCircuitParameters(Rb=tes.Rbias, Rfb=Rfb, Rs=tes.Rshunt, Mfb=1.0, Mi=MiOverMfb)
        Vbias, Ites, Vtes = sweep.findBiasPoint('R', Rgoal)
        
        Iteses.append(Ites)
        Vbiases.append(Vbias)
        Vteses.append(Vtes)
    
    return np.nanmean(Vbiases)
    
def findBiasPointI(fileName, tes, Rfb, Igoal):    
    sweeps = IvSweepCollection(fileName)

    Vteses = []; Iteses = []; Vbiases = []

    for sweep in sweeps:
        #sweep.plotRaw()
        MiOverMfb = tes.MiOverMfb(Rfb)
        #shift = sweep.checkForOffsetShift()
        sweep.subtractSquidOffset()
        sweep.applyCircuitParameters(Rb=tes.Rbias, Rfb=Rfb, Rs=tes.Rshunt, Mfb=1.0, Mi=MiOverMfb)
        Vbias, Ites, Vtes = sweep.findBiasPoint('I', Igoal)
        Iteses.append(Ites)
        Vbiases.append(Vbias)
        Vteses.append(Vtes)
    return np.nanmean(Vbiases)


cooldown = 'G4C'
deviceId = 'TES1'
pflChannelId = 'ai2'
acBiasAttenuation = 20.

#biasPointFileName = '../Analysis/%s/%s_BiasPointsNormalSC.csv' % (cooldown,deviceId)
#biasPointFileName = '../Analysis/%s/%s_BiasPointsVcoil.csv' % (cooldown,deviceId)
#biasPointFileName = '../Analysis/%s/%s_BiasPointsRn6.csv' % (cooldown,deviceId)
#biasPointFileName = '../Analysis/%s/%s_BiasPoints_Vcoil.csv' % (cooldown,deviceId)
biasPointFileName = '../Analysis/%s/%s_BiasPointsRn5.csv' % (cooldown,deviceId)
doNoise = True

startTimeString = time.strftime('%Y%m%d_%H%M%S')

outputFileName = biasPointFileName+'_' + startTimeString+ '.h5'
df = pd.DataFrame.from_csv(biasPointFileName)

#df = df[df.Tbase >= 0.140]
#df = df[df.Tbase > 0.065]
#df = df[(df.Vcoil >= 0.4) | (df.Tbase >= 0.08)]

print(df)
reply = raw_input('Continue?')

origin = 'Tes_MapTransferAndNoise'

biasChannel = daq.AoChannel('USB6361/%s' % 'ao0', -5, +5)
acBiasChannel = daq.AoChannel('USB6361/%s' % 'ao1', -5, +5)
pflChannel = daq.AiChannel('USB6361/%s' % pflChannelId, -5,+5)

tes = obtainTes(cooldown, deviceId)

tesDev = Tes(tes.Rbias, biasChannel, fieldChannel = None, pflChannel = pflChannel)
tesDev.setBias(0)
IbiasNormal = 4.5/tes.Rbias

coil = FieldCoil()

app = QApplication([])
adr = Adr(app)

ivRemote = IvCurveDaqRemote('TesIcVsB')
osr = OpenSquidRemote(port=7894, origin=origin)
squid = Pfl102Remote(osr, deviceId)

with hdf.File(outputFileName, mode='a') as f:
    a = f.attrs
    a['program'] = 'Tes_MapTransferAndNoise.py'
    a['time'] = time.time()
    a['localTime'] = startTimeString
    a['biasPointFileName'] = biasPointFileName
    a['TbaseGoal'] = df.Tbase.values
    a['VbiasGoal'] = df.Vbias.values
    a['PTesGoal'] = df.Ptes.values
    a['doBeta'] = df.betaSweep.values
    a['VcoilGoal'] = df.Vcoil.values
    a['Rbias'] = tes.Rbias
    a['Rnormal'] = tes.Rnormal
    a['deviceName'] = tes.DeviceName
    a['Rshunt'] = tes.Rshunt
    a['SQUID'] = str(squid.report())

sa = AiSpectrumAnalyzerRemote(origin)
sa.setSampleRate(2E6)
sa.setMaxCount(400)
sa.setRefreshTime(0.1)
sa.setAiChannel(pflChannelId)        

ssd = SineSweepDaqRemote(origin)
ssd.setSampleName(deviceId)

print('Waiting for valid ADR temperature', end='')
while True:
    print('.', end='')
    app.processEvents()
    time.sleep(1)
    T = adr.T
    if T == T:
        print(T, 'K')
        break
    
print('Checking all remotes:')
print('ADR:', adr.T)
print('PFL:', squid.feedbackR())
print('Spectrum analyzer:', sa.aiChannel())
print('Sine Sweep DAQ:', ssd.offsetVoltage())
print('IV curve:', ivRemote.auxAoVoltage())

oldT = 0
#coil.rampBias(-5.0)

for i in df.index:
    Tbase = df.Tbase[i]
    Vbias = df.Vbias[i]
    Ptes = df.Ptes[i]
    Rtes = df.Rtes[i]
    Vcoil = df.Vcoil[i]
    doBeta = df.betaSweep[i]
    Ibias = Vbias/tes.Rbias
    
    print('Tbase=%.4f K' % Tbase, 'Vbias=%.4f V' % Vbias, 'Vcoil=%.4f V' % Vcoil)

    coil.rampBias(Vcoil)

    # Switch PFL to low gain
    squid.setFeedbackR(10E3)
    squid.setFeedbackC(15E-9)
    squid.resetPfl()

    rampRate = min(5,max(0.2, 1E3*abs(adr.T - Tbase) / 1.5))
    print('Ramp rate:', rampRate)
    adr.setRampRate(rampRate)
    adr.rampTo(Tbase)
    adr.stabilizeTemperature(Tbase)
    if Tbase != oldT:
        wait(45)
    oldT = Tbase

    ## Take a few IV sweeps at that temperature
    ivRemote.start()
    print('Recording IV curve', end='')
    wait(10)
    while True:
        wait(1)
        print('.', end='')
        if ivRemote.sweepCount() >= 3:
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

    # Find the best possible bias point
    if abs(Ptes) > 5E-13:
        Ites = np.sqrt(Ptes / Rtes)
        print('Ites=', Ites)
        VbiasNew = findBiasPointI(ivFileName, tes, Rfb=squid.feedbackR(), Igoal=Ites)
        Vbias = VbiasNew
        print('Actual bias point:', Vbias)
        Ibias = Vbias/tes.Rbias

    # Record transfer function
    transferFunctionFileNames = []
    if abs(Ptes) > 5E-13:
        amplitudes = np.asarray([0.004,0.008])
    else:
        amplitudes = np.asarray([0.004, 0.008, 0.016])
    for amplitude in amplitudes:
        if abs(Ptes) > 5E-13:
            print('Driving normal.')
            tesDev.rampBias(IbiasNormal)     # Drive normal FIXME: this needs to be changed for negative bias
        else:
            print('Driving superconducting.')
            tesDev.rampBias(0) # Go superconducting
        print('Going to bias point')
        tesDev.rampBias(Ibias) # Go to actual bias point
        wait(5)
        ssd.setAmplitude(amplitude*acBiasAttenuation)
        ssd.setComment('Tbase=%.4f, Vbias=%.4f, Vcoil=%.4f' % (Tbase, Vbias, Vcoil))
        ssd.start()
        print('Recording transfer function', end='')
        while True:
            wait(2)
            print('.', end='')
            if ssd.isFinished():
                print('Done.')
                break
        transferFunctionFileNames.append(ssd.fileName())
        
    # Would like to ensure there's no output from modulation terminal
    aoTask = daq.AoTask('acBiasReturnToZero')
    aoTask.addChannel(acBiasChannel)
    aoTask.writeData([0], autoStart=True)
    aoTask.stop()
    aoTask.clear()
    del aoTask
  
    if doNoise:  
        # Switch PFL to high gain
        squid.setFeedbackR(100E3)
        squid.setFeedbackC(1.5E-9)
    
        if abs(Ptes) > 5E-13:
            print('Driving normal.')
            tesDev.rampBias(IbiasNormal)     # Drive normal FIXME: this needs to be changed for negative bias
        else:
            print('Driving superconducting.')
            tesDev.rampBias(0) # Go superconducting
        print('Going to bias point')
        tesDev.rampBias(Ibias) # Go to actual bias point
        wait(5)
        tuneStage1OutputToZero(squid, pflChannel)
    
        # Take noise data
        fileNameNoise = '%s_Noise_%.3fmK_Bias%.4fV_Coil%.4fV_%s' % (deviceId, Tbase*1E3, Vbias, Vcoil, time.strftime('%Y%m%d_%H%M%S')) 
        sa.setName(fileNameNoise)
        sa.setComment(str(squid.report()))
    
        for iSpectrum in range(2):
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


    tesDev.rampBias(0) # Turn off bias to zero out SQUID (the ramper will ramp it up again)
    
    # Switch PFL to low gain
    squid.setFeedbackR(10E3)
    squid.setFeedbackC(15E-9)
    tuneStage1OutputToZero(squid, pflChannel)

    # Take I vs Tbase data
    if doBeta:
        print('Now doing the Tbase sweep.')
        adr.setRampRate(0.4)
        fileNameBeta = '%s_Beta_%.3fmK_Bias%.4fV_Coil%.4fV_%s.dat' % (deviceId, Tbase*1E3, Vbias, Vcoil, time.strftime('%Y%m%d_%H%M%S'))
        ts, Tadrs, Vbiases, Vsquids = tesDev.measureIvsT(adr, Ibias, Tmid=Tbase, deltaT=1E-3, fileName=fileNameBeta)
    else:
        print('No Tbase sweep.')
        fileNameBeta = None
    
    print('Writing file')
    with hdf.File(outputFileName, mode='a') as f:
        group = f.create_group('BiasPoint%d' % i)
        group.attrs['Tbase'] = Tbase
        group.attrs['Vbias'] = Vbias
        group.attrs['Vcoil'] = Vcoil
        group.attrs['Ibias'] = Ibias
        group.attrs['TFamplitudes'] = np.asarray(amplitudes)
        group.attrs['ivSweepFileName'] = ivFileName
        group.attrs['noiseFileName'] = fileNameNoise
        for i, fileName in enumerate(transferFunctionFileNames):
            group.attrs['transferFunctionFileName%d' % i] = fileName
        if fileNameBeta is not None:
            betaGroup = group.create_group('BetaSweep')
            betaGroup.attrs['fileName'] = fileNameBeta
            betaGroup.attrs['Rfb'] = squid.feedbackR()
            betaGroup.attrs['Cfb'] = squid.feedbackC()
            betaGroup.create_dataset('t', data=ts)
            betaGroup.create_dataset('Tadr', data=Tadrs)
            betaGroup.create_dataset('Vbias', data=Vbiases)
            betaGroup.create_dataset('Vsquid', data=Vsquids)
print('Done!')
#adr.setRampRate(2)
#adr.rampTo(0.15)

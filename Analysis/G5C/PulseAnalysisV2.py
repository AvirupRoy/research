# -*- coding: utf-8 -*-9
"""
Created on Fri Feb 23 15:33:12 2018

@author: wisp10
"""
from __future__ import print_function, division

import h5py as hdf
import numpy as np
from Utility.RunningStats import RunningStats
from Analysis.PulseFileImporter import PulseImporter
        
if __name__ == '__main__':

    eV = 1.60217662E-19

    import matplotlib.pyplot as mpl
    cooldown = 'G5C'
    path = 'D:\\Users\\Runs\\{0}\\IV\\'.format(cooldown)
    fileName = path+'TES2_20180223_010847.h5'
    fileName = path+'TES1_20180226_222300.h5'
    fileName = path+'TES1_20180226_223611.h5'
    #fileName = path+'TES1_20180226_231254.h5' # Not so great
    #fileName = path+'TES1_20180226_233634.h5'
    #fileName = path+'TES1_20180226_235404.h5' # Can resolve single photons here!
    fileName = path+'TES1_20180227_003009.h5' # I think I can get out to n=65 or maybe higher. Drift corrections might be necessary. Several populations of test pulses.
    #fileName = path+'TES1_20180227_021040.h5'

    cal = 11./3.56E-5
    #cal = 11./3.56E-5 / 2.5
    #cal *= 27/20.7 # For 'TES1_20180227_021040.h5'
    
    pulses = PulseImporter(fileName)
    print('Number of pulses:', len(pulses))
    tesId = pulses.tes.tesId
    tesId = 'TES1' # Not correct for the first few files
    from Analysis.G4C.MeasurementDatabase import obtainTes
    tes = obtainTes(cooldown, tesId)
    Rfb = 10E3 # This should be in the file, but currently isn't
    Rsq = tes.Rsquid(Rfb)
    pulses.iv.analyze(Rsq=Rsq, Rb = tes.Rbias, Rs = tes.Rshunt)
    print('TES bias point: Rtes=%.3f mOhm, Ites=%.3f uA, Ptes=%.3f pW' % (pulses.iv.RtesFinal*1E3, pulses.iv.ItesFinal*1E6, pulses.iv.PtesFinal*1E12))


    t0 = pulses.startTime
    fig, ax = mpl.subplots(2,1,sharex=True)    
    ax[0].plot(pulses.pulseEndTimes-t0, pulses.baselines)
    thermo = pulses.hk.thermometers['RuOx2005Thermometer']
    ax[1].plot(thermo.t-t0,thermo.T)
    ax[1].set_xlabel('t (s)')
   
    
#    mpl.figure()
    print('Vsquid final:', pulses.iv.VsquidFinal)
    
#    for i in pulses.iBaseline:
#        pulse = pulses[i]
#        mpl.plot(pulse.Vsquid)

    
    from scipy.integrate import cumtrapz    
    templatePulse = pulses.templatePulseAverage()/Rsq
    t = np.arange(0, len(templatePulse))-pulses.pretriggerSamples * pulses.dt
    fig, ax = mpl.subplots(3,1, sharex=True)
    ax[0].plot(t, templatePulse*1E6)
    ax[0].set_ylabel('$\delta I_{tes}$ ($\\mu$A)')
    ax[1].semilogy(t, -templatePulse*1E6)
    ax[1].set_ylabel('$-\delta I_{tes}$ ($\\mu$A)')
    y1 = tes.Rshunt * (pulses.iv.ItesFinal - pulses.iv.IbiasFinal) * cumtrapz(templatePulse, dx=pulses.dt)
    y2 = tes.Rshunt * cumtrapz(templatePulse**2, dx=pulses.dt)
    ax[2].plot(t[1:], y1/eV, '--r')
    ax[2].plot(t[1:], y2/eV, '--b')
    ax[2].plot(t[1:], (y1+y2)/eV, '--k')
    ax[2].set_ylabel('Pulse integral (eV)')
    ax[-1].set_xlabel('Time')
    #mpl.show()
    
    #from scipy.fftpack import rfft, irfft
    #from numpy import rfft, irfft
    
    nPoints = len(templatePulse)
    window = np.hanning(nPoints)
    windowedTemplate = window*templatePulse
    windowNorm = np.sum(window)
    
    noise = RunningStats()
    for i in pulses.iBaseline:
        pulse = pulses[i]
        y = pulse.Vsquid - pulse.preTriggerBaseline()
        noise.push(abs(np.fft.rfft(window*y))**2)
    noisePsd = noise.mean() #/nPoints**2/windowNorm
    mpl.figure()
    f = (np.arange(0, len(noisePsd)) / (len(noisePsd) * pulses.dt))
    mpl.loglog(f, np.sqrt(noisePsd))
    mpl.ylabel('Noise PSD (V/rtHz)')
    mpl.xlabel('f (Hz)')
    
    psdTemplate = abs(np.fft.rfft(windowedTemplate))**2
    mpl.loglog(f, np.sqrt(psdTemplate))
    mpl.ylabel('Noise PSD (V/rtHz)')
    mpl.xlabel('f (Hz)')
    
    
    templateFft = np.fft.rfft(windowedTemplate) #/ nPoints**2/windowNorm
    
    phFilter_f = templateFft.conjugate() / noisePsd
    
    NEPsq = noisePsd/(templateFft*templateFft.conjugate())
    df = 1./(nPoints*pulses.dt)
    deltaVrms = np.sqrt(np.sum(df/NEPsq))
    
    phFilter_t = np.fft.irfft(phFilter_f,nPoints)
    #phFilter_t = np.roll(phFilter_t, nPoints//2)
    assert(len(phFilter_t) == nPoints)
    
    from scipy.signal import fftconvolve
    
    templatePulseFiltered = fftconvolve(windowedTemplate, phFilter_t, mode='full')
    iMax = np.argmax(templatePulseFiltered)
    templateAmp = templatePulseFiltered[iMax]
    
    print('Filtering all pulses.', end='')
    ophs = []
    for i, pulse in enumerate(pulses):
        if i%10 ==0 :
            print('.', end='')
        y = (pulse.Vsquid-pulse.preTriggerBaseline()) * window
        filteredPulse = fftconvolve(y, phFilter_t, mode='full')
        ph = filteredPulse[iMax]
        ophs.append(ph)
    ophs = np.asarray(ophs)

    print('Done filtering.')
    mpl.figure()    
    mpl.plot(templatePulseFiltered)

        

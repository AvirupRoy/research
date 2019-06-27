# -*- coding: utf-8 -*-9
"""
Created on Fri Feb 23 15:33:12 2018

@author: wisp10
"""
from __future__ import print_function, division

import h5py as hdf
import numpy as np
from Analysis.HkImport import HkImporter
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

        
    #testPulseWidths = np.unique(pulses.ldPulseWidths[pulses.iTest])
    #testPulseHeights = np.unique(pulses.ldPulseHighLevels[pulses.iTest])
    
    #print('Test pulse widths:)
    
    calOphs = cal*ophs
    binSpacing = 0.1
    bins = np.arange(-2, 96, binSpacing)
    mpl.figure(figsize=(8,6))
    mpl.hist(calOphs[pulses.iBaseline], bins=bins, label='baseline ($n=$%d)' % np.count_nonzero(pulses.iBaseline))
    mpl.hist(calOphs[pulses.iTemplate], bins=bins, label='template ($n=$%d, $t_p=$%.3f $\\mu$s, $V_H=$%.3fV)' % (np.count_nonzero(pulses.iTemplate), 1E6*pulses.ldPulser.templatePulseWidth, pulses.ldPulser.templateHighLevel))
    mpl.hist(calOphs[pulses.iTest], bins=bins, label='test ($n=%d$,$t_p=$%.3f $\\mu$s, $V_H=$%.3fV)' % (np.count_nonzero(pulses.iTemplate), 1E6*pulses.ldPulser.testPulseWidth, pulses.ldPulser.testHighLevel))
    mpl.xlabel('# of 3eV photons')
    mpl.ylabel('Counts / %.2f photon bin' % binSpacing)
    title  = 'Pulse histogram for %s/%s %s' % (cooldown, tesId, tes.DeviceName)
    title += '\nRun %s - record length %.1f ms @ %.2f kS/s' % (pulses.startTimeLocal, 1E3*pulses.dt*nPoints, pulses.sampleRate/1E3) 
    title += '\nBias: $V_b=%.3f$ V, $I_b=$%.3f $\\mu$A, $R_0=$%.3f m$\\Omega$, $P_0=$%.3f pW' % (pulses.tes.bias, 1E6*pulses.iv.IbiasFinal, 1E3*pulses.iv.RtesFinal, 1E12*pulses.iv.PtesFinal)
    mpl.title(title)
    mpl.ylim(0, 50)
    mpl.grid()
    mpl.legend(loc='best')
    #mpl.savefig('PulseHistogram.png')
    #mpl.savefig('PulseHistogram.pdf')
    mpl.show()
    
    
    def gaussian(A, mu, sigma, x):
        return A*np.exp(-0.5*((x-mu)/sigma)**2) / (sigma*np.sqrt(2.*np.pi))
    
    import lmfit
    #model = lmfit.Model(gaussian, independent_vars='x')
    model = lmfit.models.GaussianModel()
    #p = model.make_params()
    #p['mu'].value = 0
    #['sigma'].value = 0.25
    #p['A'].value = float(len(pulses.iBaseline))/binSpacing

    binWidth = 0.02
    bins = np.arange(-2, 2+binWidth, binWidth)
    counts, binEdges = np.histogram(calOphs[pulses.iBaseline], bins = bins)
    binCenters = 0.5*(binEdges[0:-1]+binEdges[1:])
    pars = model.guess(counts, x=binCenters)
    fit = model.fit(counts, pars, x=binCenters)
    print(fit.fit_report())
    
    mpl.figure()
    mpl.bar(binCenters, counts, binWidth, edgecolor = 'k')
    center = fit.params['center']
    fwhm = fit.params['fwhm']
    mpl.plot(binCenters, fit.best_fit, 'r-', label='$\mu=%.3f$, FWHM=%.3f$\\pm$%.3f' % (center.value, fwhm.value, fwhm.stderr) )
    mpl.legend()
    mpl.title('Baseline')
    #mpl.savefig('Baseline_Fit.pdf')
    
    
#    mpl.figure()
#    mpl.hist(calOphs[pulses.iBaseline], bins=bins, label='baseline ($n=$%d)' % np.count_nonzero(pulses.iBaseline))
    
    def poisson(l, k):
        '''Returns Poisson probability (e.g. that with average photon rate l we get k photons per time interval)'''
        return np.exp(-l)*np.power(l, k)/np.math.factorial(k)
        
    def poissonGauss(nAvg, sigma, Escale, counts, x):
        total = np.zeros_like(x)
        for n in range(60):
            p = poisson(nAvg, n)
            s = gaussian(p, n*Escale, sigma, x)
            total += s
        return counts*total


    waveLength = 405E-9
    hPlanck = 6.62607004E-34
    speedOfLight = 299792458.
    Ephoton = hPlanck*speedOfLight/waveLength
    print('Photon energy:', Ephoton/eV, 'eV')
    
    binWidth = 0.05
    bins = np.arange(-2, 14+binWidth, binWidth)
    counts, binEdges = np.histogram(calOphs[pulses.iTest], bins = bins)
    binCenters = 0.5*(binEdges[0:-1]+binEdges[1:])
    model = lmfit.Model(poissonGauss, independent_vars='x')
    pars = model.make_params()
    pars['nAvg'].value = 4
    pars['sigma'].value = 0.55/np.sqrt(8*np.log(2))
    pars['Escale'].value = 1; pars['Escale'].vary = False
    pars['counts'].value = len(pulses.iTest)*binWidth; pars['counts'].vary = False
    fit = model.fit(counts, params=pars, x=binCenters)
    mpl.figure()
    mpl.bar(binCenters, counts, binWidth, edgecolor = 'k')
    #center = fit.params['center']
        
    #fwhm = fit.params['fwhm']
    nAvg = fit.params['nAvg']
    fwhm = fit.params['sigma'].value*np.sqrt(8*np.log(2))
    mpl.plot(binCenters, fit.best_fit, 'r-', label='fit: $\\overline{n}=%.2f\\pm%.2f$ photons, FWHM=%.3f' % (nAvg.value, nAvg.stderr, fwhm))
    print(fit.fit_report())
    mpl.legend()
    #mpl.xlabel('Pulse height (eV)')
    mpl.xlabel('Pulse height (photons)')
    mpl.ylabel('Counts')
    mpl.title('Test')
    #mpl.savefig('TestPulses_PoissonFit.pdf')
    

    # Template
    binWidth = 0.1
    bins = np.arange(12, 41+binWidth, binWidth)
    counts, binEdges = np.histogram(calOphs[pulses.iTemplate], bins = bins)
    binCenters = 0.5*(binEdges[0:-1]+binEdges[1:])
    model = lmfit.Model(poissonGauss, independent_vars='x')
    pars = model.make_params()
    pars['nAvg'].value = 27
    pars['sigma'].value = 0.55/np.sqrt(8*np.log(2))
    pars['Escale'].value = 1; pars['Escale'].vary = True
    pars['counts'].value = len(pulses.iTest)*binWidth; pars['counts'].vary = True
    fit = model.fit(counts, params=pars, x=binCenters)
    mpl.figure()
    mpl.bar(binCenters, counts, binWidth, edgecolor = 'k')
    #center = fit.params['center']
        
    #fwhm = fit.params['fwhm']
    nAvg = fit.params['nAvg']
    fwhm = fit.params['sigma'].value*np.sqrt(8*np.log(2))
    mpl.plot(binCenters, fit.best_fit, 'r-', label='fit: $\\overline{n}=%.2f\\pm%.2f$ photons, FWHM=%.3f' % (nAvg.value, nAvg.stderr, fwhm))
    print(fit.fit_report())
    mpl.legend()
    #mpl.xlabel('Pulse height (eV)')
    mpl.xlabel('Pulse height (photons)')
    mpl.ylabel('Counts')
    mpl.title('Template')
    #mpl.savefig('TemplatePulses_PoissonFit.pdf')
    
#    phs = np.asarray([pulse.roughPh() for pulse in pulses])
#    mpl.figure()
#    mpl.hist(phs[pulses.iBaseline], bins=30)
#    mpl.hist(phs[pulses.iTemplate], bins=30)
#    mpl.hist(phs[pulses.iTest], bins=30)
#    mpl.show()

    #np.savez('TES1_20180226_235404_PHs.txt', ofph=ophs, baselines=pulses.baselines, pulseTypes=pulses.pulseTypes, ldPulseWidths=pulses.ldPulseWidths, ldPulseHls=pulses.ldPulseHighLevels)
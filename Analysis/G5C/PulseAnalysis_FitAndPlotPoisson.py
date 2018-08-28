# -*- coding: utf-8 -*-
"""
Load pulse height data from file, fit with Gaussian-broadened Poisson, and plot
Created on Mon Mar 12 15:13:12 2018

@author: wisp10
"""

import matplotlib.pyplot as mpl
    
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
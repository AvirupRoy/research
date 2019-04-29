# -*- coding: utf-8 -*-
"""
Fit multiple TF functions in one go - still only the simplest model
There's now a separate function (fitTransferFunction) that does the fitting
Created on Thu Nov 02 16:02:01 2017

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from __future__ import print_function, division
from Analysis.G4C.MeasurementDatabase import obtainTes
from Analysis.TransferFunction import TesAdmittance, TheveninEquivalentCircuit, AdmittanceModel_Simple
from Analysis.TesIvSweepReader import IvSweepCollection
from Analysis.FileTimeStamps import filesInDateRange
from Analysis.SineSweep import SineSweep

from Analysis.TesModel_Maasilta import HangingModel, ParallelModel
import numpy as np
import lmfit
import ast
from matplotlib.backends.backend_pdf import PdfPages

Rshunt = 257E-6
tesModel = HangingModel(Rshunt = Rshunt)
#tesModel = AdmittanceModel_Simple

def fitFunction(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, f):
#def fitFunction(alphaI, betaI, P, g_tes1, g_tesb, g_1b, Ctes, C1, T, T1, R, betaThermal, f):
    '''Wrapper for complex fits'''
    l = len(f)//2
    omega=2*np.pi*f[:l]
    #print('l=', l)
    #A = AdmittanceModel_Simple(f[:l], tau, L, beta, R0)
    #Z = tesModel.impedance(alphaI, betaI, P, g_tes1, g_tesb, g_1b, Ctes, C1, T, T1, R, betaThermal, omega)
    Z = tesModel.impedance(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega)
    A = 1./Z
    return A.view(dtype=np.float)

def fitTransferFunction(ss, thevenin, Rsq, sweeps, axes=None, fMax=1E5):
    metaData = eval(ss.comment)
    Rfb = metaData['Rfb']
    try:
        Cfb = metaData['Cfb']
    except KeyError:
        Cfb = 0
    Vbias = metaData['Vbias']
    Vcoil = metaData['Vcoil']
    
    print('Sine-sweep amplitudes: SC=', ssSc.amplitude, 'Normal=', ssNormal.amplitude, 'Bias=', ss.amplitude)
    
    tesAdmittance = TesAdmittance(ss, thevenin, Rsq)
    
    
    print('IV sweep comment:', sweeps.info.comment)
    sweep = sweeps[1]
    sweep.subtractSquidOffset(zeros=[1])
    print('IV sweep Rfb=', sweeps.info.pflRfb)
    sweep.findTesBias(tes.Rbias, tes.Rshunt, tes.Rsquid(sweeps.info.pflRfb))
    Tbase = sweep.Tadr
    sweep.applyThermalModel(tes.temperature, Tbase)
    I0, R0, T0, alphaIv = sweep.findAlphaIvCloseTo('Vbias', Vbias, n=10, order=3)
    P0 = I0**2*R0
    print('From IV sweep: R0=', R0*1E3, 'mOhm, I0=', 1E6*I0, 'uA, P0=', P0*1E12, ' pW, T0=', T0*1E3, 'mK')
    
    #R,dRdVb = sweep.fitRtesCloseTo('Vbias', Vbias, n=30, order=3)
    betaI, tau, L = tesAdmittance.guessBetaTauL(R0, fmin=10E3, fmax=100E3)

    G = tes.thermalConductance(Ttes=T0)
    alphaI = L *G*T0/P0
    C = tau * G

    print('Parameter guesses:')
    print('beta=', betaI)
    print('tau=', tau)
    print('L=', L)
    print('G=', G)
    print('C=', C)
    print('alphaI=', alphaI)
    
    acAmplitude = ss.amplitude / 20
    
    f = tesAdmittance.f
    iFit = f < fMax
    
    model = lmfit.Model(fitFunction, independent_vars='f')
    params = model.make_params()

    #alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega
    params['alphaI'].vary = True;  params['alphaI'].value = alphaI;
    params['betaI'].vary  = True;  params['betaI'].value = betaI;
    params['P'].vary      = False; params['P'].value = P0
    params['g_tesb'].vary = True;  params['g_tesb'].value = 0.9*G; params['g_tesb'].min = 0
    params['g_tes1'].vary = True;  params['g_tes1'].value = 0.1*G; params['g_tes1'].min = 0
    #params['g_1b'].vary = True;  params['g_1b'].value = 0.1*G; params['g_1b'].min = 0
    params['Ctes'].vary   = True;  params['Ctes'].value = 0.8*C;  # params['Ctes'].min   = 0
    params['C1'].vary     = True;  params['C1'].value   = 0.2*C;   params['C1'].min     = 0   # Wild guess
    params['T'].vary      = False; params['T'].value = T0
   # params['T1'].vary      = True; params['T1'].value = T0
    params['R'].vary      = False; params['R'].value = R0
    #params['betaThermal'].vary      = False; params['betaThermal'].value = 2.26
    
    
    result = model.fit(data=tesAdmittance.A[iFit].view(dtype=np.float),
                   f=np.hstack([f[iFit], f[iFit]]),
                   params=params )
    print(result.fit_report())
    
#    beta = result.best_values['beta']
#    tau = result.best_values['tau']
#    L = result.best_values['L']
#    R0 = result.best_values['R0']

    alphaI = result.best_values['alphaI']
    betaI = result.best_values['betaI']
    P = result.best_values['P']
    g_tes1 = result.best_values['g_tes1']
    g_tesb = result.best_values['g_tesb']
    #g_1b = result.best_values['g_1b']
    Ctes = result.best_values['Ctes']
    C1 = result.best_values['C1']
    T = result.best_values['T']
    #T1 = result.best_values['T1']
    R = result.best_values['R']
    #betaThermal = result.best_values['betaThermal']
    omega = 2*np.pi*tesAdmittance.f
    
    
#    Zfit = tesModel.impedance(alphaI, betaI, P, g_tes1, g_tesb, g_1b, Ctes, C1, T, T1, R, betaThermal, omega)
    Zfit = tesModel.impedance(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega)

    Afit = 1./Zfit
    
    A = tesAdmittance.A
    
#    print('Tau type:', type(tau))
#    fitResults = dict(betaI=beta.value, L=L.value, tau=tau.value, R0=R0.value,
#                      betaIStd=beta.stderr, LStd=L.stderr, tauStd = tau.stderr, R0Std = R0.stderr,
#                      chired=result.redchi, aic=result.aic, bic=result.bic, alphaI=alphaTf)
#    bias = dict(Vcoil=Vcoil, Vbias=Vbias, I0=I0, P0=P0, T0=T0, Tbase=Tbase, G=G, C=C)
#    results = dict(); results.update(fitResults); results.update(bias); #results.update(hkDict);
    fig = mpl.figure()
    if axes is None:
        gs = gridspec.GridSpec(2, 2, width_ratios=[3,1]) # 2x2
        ax1 = mpl.subplot(gs[0, 0]) # 1x3
        ax2 = mpl.subplot(gs[1, 0]) # 1x3
        ax3 = mpl.subplot(gs[0, 1]) # 1x2
        ax4 = mpl.subplot(gs[1, 1]) # 1x2 for text
        axes = (ax1,ax2,ax3,ax4)
    else:
        ax1,ax2,ax3,ax4 = axes

    # Re(Y), Im(Y)
    if plotType == 'admittance':
        y = A
        yfit = Afit
        yReLabel = '$\\operatorname{Re}(Y)$'
        yImLabel = '$\\operatorname{Im}(Y)$'
        ax1.set_ylabel(u'TES admittance $Y(f)$ (S)')
        ax2.set_ylabel('$Y(f)$ residual (S)')
        ax2.set_ylim(-100, +100)
    elif plotType == 'impedance':
        y = 1./A
        yfit = 1./Afit
        yReLabel = '$\\operatorname{Re}(Z)$'
        yImLabel = '$\\operatorname{Im}(Z)$'
        ax1.set_ylabel(u'TES impedance $Z(f)$ ($\\Omega$)')
        ax2.set_ylabel('$Z(f)$ residual ($\\Omega$)')
        ax2.set_ylim(-3E-4, +3E-4)
    
    ax1.semilogx(f, np.real(yfit), '-k', label='fit')
    ax1.semilogx(f, np.real(y), 'ob', ms=2, label=yReLabel)
    ax1.semilogx(f, np.imag(yfit), '-k')
    ax1.semilogx(f, np.imag(y), 'or', ms=2, label=yImLabel)
    # Resdiuals
    residual = y-yfit
    ax2.semilogx(f, np.real(residual), '.r', ms=2)
    ax2.semilogx(f, np.imag(residual), '.b', ms=2)
    
    ax2.set_xlabel('$f$ (Hz)')
    ax2.grid()

    #ax1.set_ylabel(u'TES admittance $Y(f)$ (S)')
    #ax1.set_xlabel('$f$ (Hz)')
    ax1.legend(loc='best')
    ax1.grid()

    fitText  = u'$R_0$ = %.4g m$\\Omega$ (%.2f%% $R_n$)\n' % (1E3*R0, 100*R0/Rn)
    fitText += u'$P_0$ = %.3f pW\n' % (1E12*P0) # Units used to be incorrect ("nW") -> fixed 2017-12-13
    fitText += u'$I_0$ = %.3f $\\mu$A\n' % (1E6*I0)
    fitText += u'$T_0$ = %.3f mK\n' % (1E3*T0)
    fitText += u'$T_b$ = %.3f mK\n' % (1E3*Tbase)
    #fitText += u'$\\alphaI = %.1f \\pm %.1f$\n' % (alphaI, alphaI.stderr)
    #fitText += u'$\\beta_{I}$ = %.3f $\\pm$ %.3f\n' % (betaI.value, betaI.stderr)
    #fitText += u'$\\mathcal{L} = %.3f \\pm %.3f$\n' % (L.value, L.stderr)
    #fitText += u'$\\tau = %.3f \\pm %.3f$ ms\n' % (1E3*tau.value, 1E3*tau.stderr)
    #fitText += u'$C = %.3f \\pm %.3f$ pJ/K' % (1E12*C, 1E12*tau.stderr/tau.value*C)
    #fitText += u'$C1 = %.3f \\pm %.3f$ pJ/K' % (1E12*C1, 1E12*tau.stderr/tau.value*C1)
    props = dict(boxstyle='square', alpha=0.5, facecolor='w')
    ax4.text(0.02, 0.92, fitText, va='top', bbox=props, transform=ax4.transAxes)
    ax4.axis('off')
    #ax4.axes.get_xaxis().set_visible(False)
    #ax4.axes.get_yaxis().set_visible(False)
    
    bpTitle = '%.2fmK_Vc%.3f_Vb%.3f' % (1E3*Tbase, Vcoil, Vbias)

    # Polar            
#            ax3.plot(np.real(A), np.imag(A), '.')
    norm=colors.LogNorm(vmin=f.min(), vmax=f.max())
    ax3.plot(np.real(yfit), np.imag(yfit), '-k', lw=1.0)
    ax3.scatter(np.real(y), np.imag(y), s=4,c=f, cmap = cmap, norm=norm)
    #ax3.set_yticklabels([]); ax3.tick_params(labelbottom='off')
    ax3.yaxis.tick_right()
    ax3.yaxis.set_label_position('right')
    ax3.set_xlabel(yReLabel)
    ax3.set_ylabel(yImLabel)
    #limits = ax1.get_ylim(); ax3.set_ylim(limits); ax3.set_xlim(limits)
    ax3.set_aspect('equal', adjustable='datalim', anchor='SW')
    ax3.grid()
    import time
    dateStr = time.strftime('%Y%m%d', time.localtime(ss.t[0]))
    fullDateStr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ss.t[0]))
    title  = '%s/%s: %s - %s\n' % (cooldown, deviceId, tes.DeviceName, fullDateStr)
    title += '$V_{coil}$=%+06.4f V, Vbias=%.4fV, AC=%.4f Vp' % (Vcoil, Vbias, acAmplitude)
    fig.suptitle(title)

    plotFileName = '%s_TFFit_%s_A%.0fmV_%s' % (deviceId, bpTitle, 1E3*acAmplitude, dateStr)
    #mpl.savefig(plotFileName+'.png')
    pdf = PdfPages(outputPath+plotFileName+'.pdf')
    pdf.savefig(fig)
    pdf.close()
    
    mpl.show()
    
    return result,axes

if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    from matplotlib import colors, cm
    from matplotlib import gridspec
    cmap = cm.coolwarm
    cooldown = 'G8C'

    pathIv = '/Users/calorim/Documents/ADR3/%s/IV/' % cooldown
    pathTf = '/Users/calorim/Documents/ADR3/%s/TF/' % cooldown
    outputPath = '/Users/calorim/Documents/ADR3/%s/plots/' % cooldown

    if True:
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20190424_185352.h5' #160mV
        tfScFileName = 'TES2_20190424_174157.h5'     #160mV
        ivFileName = 'TES2_IV_20190424_171441.h5'

        Rfb = 10E3
        Rsq = 10502.0685863
        Rn = 10.5531061187E-3 # 120mV, 80 mV
        tfFileNames = ['TES2_20190424_180932.h5','TES2_20190424_180624.h5','TES2_20190424_180401.h5',
                       'TES2_20190424_180116.h5','TES2_20190424_175855.h5','TES2_20190424_175624.h5',
                       'TES2_20190424_175406.h5','TES2_20190424_175110.h5']
    tes = obtainTes(cooldown, deviceId)
    Rsq = tes.Rsquid(Rfb)
    #Rn = tes.Rnormal
    doPlot = True
    
    plotType = 'admittance'
    #plotType = 'impedance'
    
    axes = None
    
    ssSc = SineSweep(pathTf+tfScFileName)
    ssNormal = SineSweep(pathTf+tfNormalFileName)
    #axes = ssSc.plotRPhi()
    #ssNormal.plotRPhi(axes)
    #print('Normal sine-sweep amplitude), ssNormal.amplitude,ss.amplitude,np.mean(ss.Vdc), np.std(ss.Vdc))
    
    thevenin = TheveninEquivalentCircuit(ssNormal, ssSc, Rn, Rsq)
    #axes = thevenin.plot(None)
    
    
    sweeps = IvSweepCollection(pathIv+ivFileName)

    fig = mpl.figure(figsize=(8, 6))
    axes = None
    
    import pandas as pd
    df = pd.DataFrame()
    for tfFileName in tfFileNames:
        ss = SineSweep(pathTf+tfFileName)
        print('Sine sweep comment:', ss.comment)
        result, axes =  fitTransferFunction(ss, thevenin, Rsq, sweeps, axes=axes, fMax=1E4)
        rdict = {}
        rdict.update(result.best_values)
        #rdict['Vbias'] = Vbias
        df = df.append(rdict, ignore_index=True)
    
    #df.to_hdf('TES2_MultibiasTfFit.h5', 'TfFit')
    #mpl.savefig('TES2_MultibiasPoints_TFfits.png')
    #mpl.savefig('TES2_MultibiasPoints_TFfits.pdf')

    df['kappa'] = np.sqrt(df.alphaI.values/(1.+2*df.betaI.values))
    mpl.figure()
    #x = 1E3*df.R0
    x = df.R
    fig, axes = mpl.subplots(4,1,sharex=True)
    axes[0].plot(x, df.alphaI, '.-')
    axes[0].set_ylabel('$\\alpha_{I}$')
    axes[1].plot(x, df.betaI, '.-')
    axes[1].set_ylabel('$\\beta_{I}$')
    
    axes[2].plot(x, df.kappa, '.-')
    axes[2].set_ylabel('$\\kappa \\equiv \\sqrt{\\frac{\\alpha}{1+2\\beta}}$')
    
    axes[3].plot(x, 1E3*df.tau, '.-')
    axes[3].set_ylabel('$\\tau$ (ms)')
    axes[3].set_xlabel('$R_{TES}$ (m$\\Omega$)')
    
    mpl.xlabel('Vbias')
    mpl.show()

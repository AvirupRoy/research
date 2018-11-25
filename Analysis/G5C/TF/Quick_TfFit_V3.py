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

from Analysis.TesModel_Maasilta import HangingModel
import numpy as np
import lmfit
import ast

Rshunt = 257E-6
#tesModel = HangingModel(Rshunt = Rshunt)
tesModel = AdmittanceModel_Simple

def fitFunction(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, f):
    '''Wrapper for complex fits'''
    l = len(f)//2
    omega=2*np.pi*f[:l]
    #print('l=', l)
    #A = AdmittanceModel_Simple(f[:l], tau, L, beta, R0)
    Z = tesModel.impedance(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega)
    A = 1./Z
    return A.view(dtype=np.float)

def fitTransferFunction(ss, thevenin, Rsq, sweeps, axes=None, fMax=1E5):
    metaData = ast.literal_eval(ss.comment)
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
    params['g_tes1'].vary = True;  params['g_tes1'].value = 0.1*G; params['g_tes1'].min = 0   # Wild guess
    params['Ctes'].vary   = True;  params['Ctes'].value = 0.8*C;  # params['Ctes'].min   = 0
    params['C1'].vary     = True;  params['C1'].value   = 0.2*C;  # params['C1'].min     = 0   # Wild guess
    params['T'].vary      = False; params['T'].value = T0
    params['R'].vary      = False; params['R'].value = R0
    
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
    Ctes = result.best_values['Ctes']
    C1 = result.best_values['C1']
    T = result.best_values['T']
    R = result.best_values['R']
    omega = 2*np.pi*tesAdmittance.f
    
    Zfit = tesModel.impedance(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega)
    Afit = 1./Zfit
    
    A = tesAdmittance.A
    
#    print('Tau type:', type(tau))
#    fitResults = dict(betaI=beta.value, L=L.value, tau=tau.value, R0=R0.value,
#                      betaIStd=beta.stderr, LStd=L.stderr, tauStd = tau.stderr, R0Std = R0.stderr,
#                      chired=result.redchi, aic=result.aic, bic=result.bic, alphaI=alphaTf)
#    bias = dict(Vcoil=Vcoil, Vbias=Vbias, I0=I0, P0=P0, T0=T0, Tbase=Tbase, G=G, C=C)
#    results = dict(); results.update(fitResults); results.update(bias); #results.update(hkDict);

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
    #mpl.savefig('Plots\\pdf\\'+plotFileName+'.pdf')
    #mpl.close()
    mpl.show()
    
    return result,axes

if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    from matplotlib import colors, cm
    from matplotlib import gridspec
    cmap = cm.coolwarm
    cooldown = 'G6C'

    pathIv = 'G:/Runs/%s/IV/' % cooldown
    pathTf = 'G:/Runs/%s/TF/' % cooldown

    if False:
        deviceId = 'TES1'
        tfNormalFileName = 'TES1_20180326_213552.h5'
        ivNormalFileName = 'TES1_IV_20180326_213434.h5'
        #tfScFileName = 'TES1_20180326_204354.h5' # 60mK
        tfScFileName = 'TES1_20180326_155444.h5'
        
        ivFileName = 'TES1_IV_20180326_154913.h5' # 55mK
        tfFileName = 'TES1_20180326_154258.h5' # 55mK, Vbias=2.00V
        
        #ivFileName = 'TES1_IV_20180327_181306.h5' # 50mK
        #tfFileName = 'TES1_20180327_182044.h5' # Vbias=2.0 at 50mK
        #tfFileName = 'TES1_20180327_183139.h5' # Vbias=2.1 at 50mK 
        #tfFileName = 'TES1_20180327_183635.h5' # Vbias=1.9 at 50mK
        #tfFileName = 'TES1_20180327_224638.h5' # Vbias=2.0 at 50mK again
        
        #ivFileName = 'TES1_IV_20180327_231807.h5' # 55mK
        #tfFileName = 'TES1_20180327_232115.h5' # Vbias=2.0 at 55mK
        
        #tfFileName = 'TES1_20180326_194736.h5' # 60mK, 1.92V
        
        # 55mK, 1.92V
        tfFileName = 'TES1_20180330_102635.h5' # 55mK, 1.92V
        tfFileName = 'TES1_20180330_094740.h5' # This one looks reasonable (80mV drive)
        tfFileName = 'TES1_20180327_232115.h5' # 2V bias
        tfFileName = 'TES1_20180327_224638.h5' # 2V bias, poor fit?!
        

        ## Three at same bias point (pulser overnight), but different drive amplitude
        ivFileName = 'TES1_IV_20180330_103111.h5'
        ivNormalFileName = 'TES1_IV_20180330_181442.h5' # Not really used here
        if True:    # 55mK, 1.92V, 160mVpp drive
            tfNormalFileName = 'TES1_20180330_180927.h5' # 160mV
            tfScFileName = 'TES1_20180330_173608.h5'# 160mV
            tfFileName = 'TES1_20180330_102635.h5' # 160mV

        if False:  # 55mK, 1.92V, 80mVpp drive
            tfNormalFileName = 'TES1_20180330_180121.h5'
            tfScFileName = 'TES1_20180330_173213.h5'
            tfFileName = 'TES1_20180330_094740.h5'

        if False:   # 55mK, 1.92V, 40mVpp drive
            tfNormalFileName = 'TES1_20180330_175311.h5'
            tfScFileName = 'TES1_20180330_173946.h5'
            tfFileName = 'TES1_20180330_095133.h5' # 40mV amplitude
        
        Rn = 6.6675E-3
        Rfb = 100E3

    if False: # 40mV
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180403_123652.h5' # 40mV
        tfScFileName = 'TES2_20180402_182452.h5' # 40mV
        # Seems I did not record one
        
        
    if False: # 80mV
        deviceId = 'TES2'
        ivNormalFileName = 'TES2_IV_20180403_121838.h5'
        tfNormalFileName = 'TES2_20180403_123209.h5'  # 80mV
        tfScFileName = 'TES2_20180402_182127.h5'

        ivFileName = 'TES2_IV_20180402_182835.h5'
        tfFileName = 'TES2_20180402_185508.h5' # 80mV
        Rn = 6.683496E-3
        Rfb = 100E3
        
    if False: # 160mV
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180403_122923.h5' # 160mV
        tfScFileName = 'TES2_20180402_181836.h5' # 160mV
        ivFileName = 'TES2_IV_20180402_182835.h5'        
        tfFileName = 'TES2_20180402_185756.h5' # Vbias=1.1V, 160mV
        Rn = 6.683496E-3
        Rfb = 100E3
        
    if False: # 80mV  at bias point 55mK, 1.1V, 3.4V (pulses recorded)
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180529_133813.h5'
        tfScFileName = 'TES2_20180526_013427.h5'
        ivFileName = 'TES2_IV_20180526_013252.h5'
        tfFileName = 'TES2_20180526_012813.h5 '
        #Rn = 6.683496E-3
        Rn = 0.006801558
        Rfb = 100E3
        
    if False:
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180530_201055.h5'
        tfScFileName = 'TES2_20180529_230410.h5'
        ivFileName = 'TES2_IV_20180529_230801.h5'
        Rfb = 100E3
        tfFileName = 'TES2_20180529_231509.h5'
        Rn = 0.006801558
    
    if False:
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180611_111210.h5'
        tfScFileName = 'TES2_20180608_191741.h5'
        ivFileName = 'TES2_IV_20180608_191252.h5'
        Rfb = 100E3
        Rn = 6.65034512864E-3
        tfFileNames = ['TES2_20180608_195936.h5', 'TES2_20180608_201002.h5', 
                       'TES2_20180608_201456.h5', 'TES2_20180608_202002.h5', 'TES2_20180608_202453.h5',
                       'TES2_20180608_202955.h5', 'TES2_20180608_203736.h5', 'TES2_20180608_204214.h5',
                       'TES2_20180608_204656.h5', 'TES2_20180608_205142.h5']
                       
    if True:
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180613_000054.h5' # 100kOhm, 15nF, using a different set of frequencies now
        tfScFileName = 'TES2_20180613_010907.h5' # 55mK superconducting
        ivFileName = 'TES2_IV_20180613_010700.h5'
        Rfb = 100E3
        Rn = 6.65034512864E-3
        tfFileNames = ['TES2_20180613_012729.h5', 'TES2_20180613_013427.h5', 'TES2_20180613_014125.h5', 'TES2_20180613_014832.h5', 'TES2_20180613_015540.h5', 'TES2_20180613_020238.h5', 'TES2_20180613_020946.h5', 'TES2_20180613_021643.h5', 'TES2_20180613_022351.h5', 'TES2_20180613_023049.h5', 'TES2_20180613_023757.h5'  ] # 'TES2_20180613_010907.h5'
        
    if True:
        deviceId = 'TES3'
        tfNormalFileName = 'TES3_20181018_193323.h5'
        tfScFileName = 'TES3_20181019_194714.h5'
        ivFileName = 'TES3_IV_20181019_190856.h5'

        Rfb = 10E3
        Rn = 10.502E-3 # 25%, 22.5%, 20%, 17.5%, 15.0%, 12.5%, 10.0%, 7.5%
        tfFileNames = ['TES3_20181019_191903.h5', 'TES3_20181019_192236.h5', 'TES3_20181019_192619.h5', 'TES3_20181019_192950.h5', 
                       'TES3_20181019_193330.h5', 'TES3_20181019_193717.h5', 'TES3_20181019_194034.h5', 'TES3_20181019_194355.h5']
    
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

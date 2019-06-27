# -*- coding: utf-8 -*-
"""
Created on Thu Nov 02 16:02:01 2017

@author: wisp10
"""

from __future__ import print_function, division
from Analysis.G4C.MeasurementDatabase import obtainTes
from Analysis.TransferFunction import TesAdmittance, TheveninEquivalentCircuit, AdmittanceModel_Simple
from Analysis.TesIvSweepReader import IvSweepCollection

from Analysis.SineSweep import SineSweep
import numpy as np
import lmfit
import ast

def fitFunction(f, tau, L, beta, R0):
    '''Wrapper for complex fits'''
    l = len(f)//2
    print('l=', l)
    A = AdmittanceModel_Simple(f[:l], tau, L, beta, R0)
    return A.view(dtype=np.float)

if __name__ == '__main__':
    import matplotlib.pyplot as mpl
    from matplotlib import colors, cm
    from matplotlib import gridspec
    cmap = cm.coolwarm
    cooldown = 'G5C'

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
        
    if True: # 80mV  at bias point 55mK, 1.1V, 3.4V (pulses recorded)
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
    
    thevenin = TheveninEquivalentCircuit(ssNormal, ssSc, Rn, Rsq)
    #axes = thevenin.plot(None)
    
    ss = SineSweep(pathTf+tfFileName)
    print('Sine sweep comment:', ss.comment)

    metaData = ast.literal_eval(ss.comment)
    Rfb = metaData['Rfb']
    Cfb = metaData['Cfb']
    Vbias = metaData['Vbias']
    Vcoil = metaData['Vcoil']
    
    print('Sine-sweep amplitudes: SC=', ssSc.amplitude, 'Normal=', ssNormal.amplitude, 'Bias=', ss.amplitude)
    #print('Normal sine-sweep amplitude), ssNormal.amplitude,ss.amplitude,np.mean(ss.Vdc), np.std(ss.Vdc))
    
    tesAdmittance = TesAdmittance(ss, thevenin, Rsq)
    
    sweeps = IvSweepCollection(pathIv+ivFileName)
    print('IV sweep comment:', sweeps.info.comment)
    sweep = sweeps[1]
    print('IV sweep Rfb=', sweeps.info.pflRfb)
    sweep.findTesBias(tes.Rbias, tes.Rshunt, tes.Rsquid(sweeps.info.pflRfb))
    Tbase = sweep.Tadr
    sweep.applyThermalModel(tes.temperature, Tbase)
    I0, R0, T0, alphaIv = sweep.findAlphaIvCloseTo('Vbias', Vbias, n=10, order=3)
    P0 = I0**2*R0
    print('From IV sweep: R0=', R0*1E3, 'mOhm, I0=', 1E6*I0, 'uA, P0=', P0*1E12, ' pW, T0=', T0*1E3, 'mK')
    
    #R,dRdVb = sweep.fitRtesCloseTo('Vbias', Vbias, n=30, order=3)
    beta, tau, L = tesAdmittance.guessBetaTauL(R0, fmin=10E3, fmax=100E3)
    print('Parameter guesses:')
    print('beta=', beta)
    print('tau=', tau)
    print('L=', L)
    
    acAmplitude = ss.amplitude / 20
    
    f = tesAdmittance.f
    iFit = f < 1E5
    
    model = lmfit.Model(fitFunction, independent_vars='f')
    params = model.make_params()
    
    params['tau'].value = tau; params['beta'].value = beta; params['L'].value = L; params['R0'].value = R0
    params['R0'].vary = False
    result = model.fit(data=tesAdmittance.A[iFit].view(dtype=np.float),
                   f=np.hstack([f[iFit], f[iFit]]),
                   params=params )
    print(result.fit_report())
    beta = result.best_values['beta']
    tau = result.best_values['tau']
    L = result.best_values['L']
    R0 = result.best_values['R0']
    
    Afit = AdmittanceModel_Simple(tesAdmittance.f, tau, L, beta, R0)
       
    A = tesAdmittance.A
    
    #Rn = tes.Rnormal
    beta = result.params['beta']
    L = result.params['L']
    tau = result.params['tau']
    G = tes.thermalConductance(Ttes=T0)
    C = tau.value * G
    alphaTf = L.value*G*T0/P0
    print(T0, R0, alphaIv, alphaTf, beta, tau, L)

    fig = mpl.figure(figsize=(8, 6))
    gs = gridspec.GridSpec(2, 2, width_ratios=[3,1]) # 2x2
    ax1 = mpl.subplot(gs[0, 0]) # 1x3
    ax2 = mpl.subplot(gs[1, 0]) # 1x3
    ax3 = mpl.subplot(gs[0, 1]) # 1x2
    ax4 = mpl.subplot(gs[1, 1]) # 1x2 for text

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
    fitText += u'$\\alpha = %.1f \\pm %.1f$\n' % (alphaTf, L.stderr/L.value * alphaTf)
    fitText += u'$\\beta_{I}$ = %.3f $\\pm$ %.3f\n' % (beta.value, beta.stderr)
    fitText += u'$\\mathcal{L} = %.3f \\pm %.3f$\n' % (L.value, L.stderr)
    fitText += u'$\\tau = %.3f \\pm %.3f$ ms\n' % (1E3*tau.value, 1E3*tau.stderr)
    fitText += u'$C = %.3f \\pm %.3f$ pJ/K' % (1E12*C, 1E12*tau.stderr/tau.value*C)
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
    mpl.savefig(plotFileName+'.png')
    #mpl.savefig('Plots\\pdf\\'+plotFileName+'.pdf')
    #mpl.close()
    mpl.show()
            

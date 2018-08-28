# -*- coding: utf-8 -*-
"""
This is branched form G4C/TF_SanityCheck
Created on Tue Mar 27 15:01:23 2018

@author: wisp10
"""

from __future__ import print_function

def fitRsquid(sweep, tes, Rfb, RsqGuess):        
    # Figure out Rsq (basically could use any sweep)
    Rb = tes.Rbias
    Rs = tes.Rshunt
    RsqGuess = tes.Rsquid(Rfb)
    sweep.findTesBias(Rb, Rs, RsqGuess)
    Ics = sweep.findCriticalCurrents(1E-9)
    VbiasMax = 0.75*Ics[0]*Rb
    slope = sweep.findSlopeAndOffset(VbiasMax, ramp=sweep.iRampUp1)[0]
    Rsq = Rb*slope
    print(Rsq, RsqGuess)
    if abs(1 - Rsq/RsqGuess) > 0.05:
        import warnings
        warnings.warn('Discrepancy in Rsq: guess=%.5f, fit=%.5f', RsqGuess, Rsq)
    return Rsq

def fitNormalResistance(sweeps, tes, Rsq):
    Rnormals = []
    for sweep in sweeps:
        slope = sweep.findSlopeAndOffset(Vmax=1,ramp=sweep.iRampUp1)[0]
        Rb = tes.Rbias; Rs = tes.Rshunt
        Rnormal = Rs*(Rsq/(Rb*slope) - 1)
        Rnormals.append(Rnormal)
    print('Rnormal:', Rnormals)
    return np.mean(Rnormals)


if __name__ == '__main__':
    from Analysis.G4C.MeasurementDatabase import obtainTes
    from Analysis.SineSweep import SineSweep
    from Analysis.TesIvSweepReader import IvSweepCollection

    import matplotlib.pyplot as mpl
    import numpy as np
    cooldown = 'G5C'

    pathIv = 'D:/Users/Runs/%s/IV/' % cooldown
    pathTf = 'D:/Users/Runs/%s/TF/' % cooldown
    pathIv = 'G:/Runs/%s/IV/' % cooldown
    pathTf = 'G:/Runs/%s/TF/' % cooldown
    if False:    
        deviceId = 'TES1'
        tfNormalFileName = 'TES1_20180326_213552.h5'
        ivNormalFileName = 'TES1_IV_20180326_213434.h5'
        tfScFileName = 'TES1_20180326_204354.h5'
        ivScFileName = 'TES1_IV_20180326_154913.h5'
        Rfb = 100E3
        
    if False:
        deviceId = 'TES1'
        tfNormalFileName = 'TES1_20180326_214310.h5'
        tfScFileName = 'TES1_20180326_155140.h5'
        ivNormalFileName = 'TES1_IV_20180326_213211.h5'
        ivScFileName = 'TES1_IV_20180326_154913.h5'
        Rfb = 10E3
        
    if True:
        deviceId = 'TES2'
        ivNormalFileName = 'TES2_IV_20180403_121838.h5'
        tfNormalFileName = 'TES2_20180403_123209.h5'
        ivScFileName = 'TES2_IV_20180402_182835.h5'
        tfScFileName = 'TES2_20180402_185756.h5' # Vbias=1.1V, 160mV
        #tfScFileName = 'TES2_20180402_185508.h5' # Vbias=1.1V, 40mV
        #tfScFileName = 'TES2_20180402_182452.h5' # 40mV SC
        #tfScFileName = 'TES2_20180402_184243.h5' # 40mV
        tfScFileName = 'TES2_20180402_182408.h5' # Incomplete, 40mV
        tfScFileName = 'TES2_20180402_182127.h5' # SC, 80mV
        tfScFileName = 'TES2_20180402_181836.h5' # SC, 160mV
        tfScFileName = 'TES2_20180402_181455.h5' # SC (Vbias=0.69), 160mV
        tfScFileName = 'TES2_20180402_181154.h5' # SC (Vbias=0.69), 80mV
        tfScFileName = 'TES2_20180402_181050.h5' # Inclomplete 0.69V, 80mV
        tfScFileName = 'TES2_20180402_180744.h5' # SC (Vbias=0.69), 40mV
        tfScFileName = 'TES2_20180402_180654.h5' # AI overload
        
        tfScFileName = 'TES1_20180330_180927.h5' # Not sure # This is TES1 and does not belong here?!
        tfScFileName = 'TES1_20180330_180121.h5' # Not sure
        tfScFileName = 'TES1_20180330_175311.h5' # Not sure
        Rfb = 100E3
        
    if False:
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180529_133813.h5'
        tfScFileName = 'TES2_20180526_013427.h5'
        ivNormalFileName = 'TES2_IV_20180529_133353.h5' # Rfb=100k
        ivScFileName = 'TES2_IV_20180526_013252.h5' #Rfb=10k (I think)
        
    if False:
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180530_201055.h5'
        tfScFileName = 'TES2_20180529_230410.h5'
        ivNormalFileName = 'TES2_IV_20180530_200838.h5'
        ivScFileName = 'TES2_IV_20180529_230801.h5'
        
    if True:
        deviceId = 'TES2'
        tfNormalFileName = 'TES2_20180611_111210.h5'
        tfScFileName = 'TES2_20180608_191741.h5'
        ivNormalFileName = 'TES2_IV_20180611_111114.h5' # Rfb=100kOhm
        ivNormalFileName = 'TES2_IV_20180611_110944.h5' # Rfb=10kOhm
        ivScFileName = 'TES2_IV_20180608_191252.h5'
        
        

    tes = obtainTes(cooldown, deviceId)
    Rsq = tes.Rsquid(Rfb)
    #Rsq = MiOverMfb * Rfb
    Rn = tes.Rnormal
    
    tfNormal = SineSweep(pathTf+tfNormalFileName)
    ivNormalSweeps = IvSweepCollection(pathIv+ivNormalFileName)
    ivNormal = ivNormalSweeps[1]
    Tnormal = ivNormal.Tadr
    print('Normal IV sweep temperature:', Tnormal)
    print('Normal TF comment:', tfNormal.comment)
    

    tfSc = SineSweep(pathTf+tfScFileName)
    ivSc = IvSweepCollection(pathIv+ivScFileName)[1]
    Tsc = ivSc.Tadr
    print('SC IV sweep temperature:', Tsc)
    print('SC TF comment:', tfSc.comment)
    f = tfSc.f
    ratio = tfSc.TF / tfNormal.TF
    Tsc = ivSc.Tadr
    
    amplitude = tfSc.amplitude

    #Rsq = fitRsquid(ivSc, tes, Rfb, Rsq)
    print('Rsq:', Rsq)
    Rnormal = fitNormalResistance([ivNormal], tes, Rsq=tes.Rsquid(ivNormalSweeps.info.pflRfb))
    print('Rnormal:', Rnormal)

    def modelTfRatio(f, Rs, Rtes, L):
        omega=2*np.pi*f
        XL = 1j*omega*L
        ScToNormal = (Rs+Rtes+XL)/(Rs+XL)
        return ScToNormal

#    from scipy.optimize import curve_fit
    def fitFunction(f, Rs, Rtes, L):
        '''Wrapper for complex fits'''
        l = len(f)/2
        A = modelTfRatio(f[:l], Rs, Rtes, L)
        return A.view(dtype=np.float)


    axes = tfNormal.plotXY(label='Normal')
    tfSc.plotXY(axes, label='SC')
    axes[0].legend()
    axes[0].set_title('Raw transfer functions')
    
    import lmfit

    iFit = f < 5E6
    
    model = lmfit.Model(fitFunction, independent_vars='f', param_names=['Rs', 'Rtes', 'L'])
    params = model.make_params()
    params['Rs'].value = tes.Rshunt; params['Rs'].vary = False
    params['Rtes'].value = Rnormal; params['Rtes'].vary = False
    params['L'].value = 30E-9
    result = model.fit(data=ratio[iFit].view(dtype=np.float),
                       f=np.hstack([f[iFit], f[iFit]]),
                       params=params )
    print(result.fit_report())
    
    fitY = result.best_fit.view(np.complex)
    
    fig, axes = mpl.subplots(2,1,sharex=True)
    ax = axes[0]
    ax.semilogx(f, np.real(ratio), '.b', label='real')
    ax.semilogx(f[iFit], np.real(fitY), '-k', lw=2)
    ax.semilogx(f, np.imag(ratio), '.r', label='imag')
    ax.semilogx(f[iFit], np.imag(fitY), '-k', lw=2)
    ax.set_ylabel('X, Y')
    ax.legend(loc='best')
    ax = axes[1]
    res = result.residual.view(np.complex)
    ax.semilogx(f, np.real(res), '.b')
    ax.semilogx(f, np.imag(res), '.r')
    ax.set_ylabel('Residuals')
    ax.set_xlabel('f (Hz)')
    L = result.params['L']
    
    import time
    fullDateStr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tfSc.t[0]))
    fnDateStr = time.strftime('%Y%m%d_%H%M', time.localtime(tfSc.t[0]))
    
    title  = u'Superconducting/Normal TFs for %s/%s (%s)\n' % (cooldown, deviceId, fullDateStr)
    title += u'$R_n=%.3f$ m$\\Omega$ at $T_{adr}=%.2f$ mK ($T_{sc}$=%.2f mK)\n' % (1E3*Rnormal, 1E3*Tnormal, 1E3*Tsc)
    title += u'AC amplitude: %.1f mV, fit: L=%.3f $\\pm$ %.3f nH' % (1E3*amplitude, L.value*1E9, 1E9*L.stderr)
    fig.suptitle(title)
    #mpl.savefig('TF_SanityCheck.pdf')
    mpl.savefig('%s_TfRatioCheck_%s.png' % (deviceId, fnDateStr))
    mpl.show()    

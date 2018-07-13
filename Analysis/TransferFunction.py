# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 13:05:13 2017

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
from __future__ import division
import numpy as np
import matplotlib.pyplot as mpl
import matplotlib.cm as cm
import matplotlib.colors as colors
cmap = cm.coolwarm
k_B = 1.3806485279E-23 # Boltzmann constant

class TheveninEquivalentCircuit(object):
    def __init__(self, sineSweepNormal, sineSweepSc, Rn, Rsq):
        '''Compute Thevenin equivalent circuit parameters Rth and Vth from
        normal and superconducting transfer functions. The normal resistance Rn
        of the TES must be known.
        Rsq is the equivalent SQUID resistance, given as Rsq = Mif/Mfb * Rfb'''
        
        identicalFs = np.all(sineSweepNormal.f == sineSweepSc.f)
        assert identicalFs, 'Frequencies do not match!'
        assert np.all(sineSweepNormal.amplitude == sineSweepSc.amplitude), 'Drive amplitudes do not match!'
        Zth = Rn * sineSweepNormal.TF / (sineSweepSc.TF - sineSweepNormal.TF)
        IsqSC = sineSweepSc.TF / Rsq * sineSweepSc.amplitude
        Vth = IsqSC * Zth
        self.Zth = Zth
        self.Vth = Vth
        self.f = sineSweepNormal.f
        
    def plot(self, axes=None):
        if axes is None:
            fig, axes = mpl.subplots(2,1, sharex=True)
        x = self.f
        axes[0].semilogx(x, np.real(self.Vth), label='real')
        axes[0].semilogx(x, np.imag(self.Vth), label='imag')
        axes[0].set_ylabel(u'Thevenin equivalent voltage $V_{th}$ (V)')
        axes[0].legend(loc='best')
        axes[1].semilogx(x, np.real(self.Zth), label='real')
        axes[1].semilogx(x, np.imag(self.Zth), label='imag')
        axes[1].set_ylabel(u'Thevenin equivalent impedance $Z_{th}$ ($\\Omega$)')
        axes[1].set_xlabel('f (Hz)')
        axes[1].legend(loc='best')
        return axes

class TesAdmittance(object):
    def __init__(self, sineSweep, theveninCircuit, Rsq):
        self.f = sineSweep.f
        assert np.all(self.f == theveninCircuit.f)
        Isq = sineSweep.TF * sineSweep.amplitude / Rsq
        self.Z = theveninCircuit.Vth/Isq - theveninCircuit.Zth
        self.A = 1./self.Z
        
    def plot(self, what='admittance'):
        if what in ['A', 'admittance']:
            y = self.A
        elif what in ['Z', 'impedance']:
            y = self.Z
        x = self.f        
        mpl.semilogx(x, np.real(y), label='real')
        mpl.semilogx(x, np.imag(y), label='imag')
        
    def plotPolar(self, what='admittance'):
        if what in ['A', 'admittance']:
            y = self.A; label = 'A'
        elif what in ['Z', 'impedance']:
            y = self.Z; label = 'Z'
        norm=colors.LogNorm(vmin=self.f.min(), vmax=self.f.max())
        mpl.scatter(np.real(y), np.imag(y), s=2,c=self.f, cmap = cmap, norm=norm)
        mpl.plot(np.real(y), np.imag(y), '-')
        mpl.xlabel('Re(%s)' % label)
        mpl.ylabel('Im(%s)' % label)
        
    def guessBetaTauL(self, R, fmin=20E3, fmax=200E3):
        '''Make a guess on beta, tau, and L based on:
        *high frequency limit fmin<f<fmax)->beta=1./(R*Re(Y)) - 1
        *L = (1-(1+beta)*R*Re(Y(0))/ (1+Re(Y(0)) * R)
        *tau = 1./(2pifmax) with fmax = max(Im(Y))
        '''
        A0 = np.real(self.A[np.argmin(self.f)]) # Low frequency limit
        i = (self.f >= fmin) & (self.f <= fmax)
        Ainf = np.mean(self.A[i]) # High frequency limit
        # Maximum in imaginary part at fmaxIm
        i = np.argmax(np.imag(self.A))
        fmaxIm = self.f[i]
        beta = 1./(R*np.real(Ainf)) - 1
        L =(1-(1+beta)*R*A0)/ (1+A0 * R)
        tau = 1./(2*np.pi*fmaxIm)
        return beta, tau, L
        
    def fitSimpleModel(self, beta, tau, L):
        pass
    
    def toHdf(self, hdfGroup):
        hdfGroup.create_dataset('f', data=self.f)
        hdfGroup.create_dataset('A', data=self.A)
        
        
def AdmittanceModel_Simple(f, tau, L, beta, R):
    '''From Dan's chapter, table 5, equation (49)'''
    iomegataup1 = 1j*2.*np.pi*f*tau + 1.
    A = (iomegataup1 - L)/(iomegataup1 * (1.+beta) + L) / R
    return A
    
def AdmittanceModel_Irwin(f, tauI, L, beta, R):
    omega=2*np.pi*f
    Z = R*(1+beta) + R*L/(1-L) * (2+beta)/(1+1j*omega*tauI)
    Y = 1./Z
    return Y
    

class TesModelSimple(object):
    '''TES model with single heat-capacitance and G, following the equations from Dan McCammon's chapter (Table 5)
    All variable dependencies are explicit, except for the (fixed) shunt resistance'''
    def __init__(self, Rshunt):  
        self.Rshunt = Rshunt
        
    def b(self, R):
        '''Return the bias parameter b'''
        return (self.Rshunt - R)/(self.Rshunt + R)

    def K_LI(self, R):
        '''Return the loading factor of the shunt resistance'''
        return R/(self.Rshunt+R)
         
    def b_I(self, betaI, R):
        return self.b(R) / (1+self.K_LI(R)*betaI)
        
    def L_I(self, alphaI, P, G, T):
        '''Return loop gain'''
        return alphaI * P / (G * T)
        
    def K_FI(self, alphaI, betaI, tau, P, G, T, R, omega):
        '''Return feedback factor K_FI (change in gain due to ETF)'''
        iwt = 1j * omega * tau
        LI = self.L_I(alphaI, P, G, T)
        bI = self.b_I(betaI, R)
        K_FI = 1./(1.-bI*LI) * (1+iwt)/(1+iwt/(1.-bI*LI))
        return K_FI
         
    def responsitivity(self, alphaI, betaI, tau, P, G, T, R, omega):
        '''Return the current responsivity of the TES. Equation 48 in McCammon chapter'''
        iwt = 1j * omega * tau
        LI = self.L_I(alphaI, P, G, T)
        V = np.sqrt(P*R)
        K_LI = self.K_LI(R)
        K_FI = self.K_FI(alphaI, betaI, tau, P, G, T, R, omega)
        S_I = -LI / (V*(1 + K_LI * betaI)) * 1./(1.+iwt) * K_LI * K_FI
        return S_I
        
    def admittance(self, alphaI, betaI, tau, P, G, T, R, omega):
        '''Return the admittance of the TES'''
        LI = self.L_I(alphaI, P, G, T)
        iwt = 1j * omega * tau
        A = ((1.+iwt) - LI) / ((1+iwt)*(1+betaI)+LI) * 1./R
        return A
        
    def impedance(self, alphaI, betaI, tau, P, G, T, R, omega):
        '''Return the impedance of the TES'''
        return 1./self.admittance(alphaI, betaI, tau, P, G, T, R, omega)
        
    def TFN(self, alphaI, betaI, tau, P, G, T, R, Tbase, G0, omega):
        '''Return the thermal fluctation noise.'''
        Flink = 1.
        return np.sqrt(4*k_B*Tbase**2*G0*Flink) * (-self.responsitivity(alphaI, betaI, tau, P, G, T, R, omega)) # Note: base temperature in the sqrt
    
    def johnsonNoiseTes(self, alphaI, betaI, tau, P, G, T, R, omega):
        '''Return the Johnson noise of the TES (no non-linear Johnson noise included)'''
        K_LI = self.K_LI(R)
        K_FI = self.K_FI(alphaI, betaI, tau, P, G, T, R, omega)
        return np.sqrt(4*k_B*T/R) * (1./(1+K_LI*betaI)) * K_LI * K_FI
        
    def johnsonNoiseShunt(self, alphaI, betaI, tau, P, G, T, R, Tbase, omega):
        '''Return the Johnson noise of the shunt resistor (at temperature Tbase)'''
        iwt = 1j * omega * tau
        K_LI = self.K_LI(R)
        K_FI = self.K_FI(alphaI, betaI, tau, P, G, T, R, omega)
        Tshunt = Tbase
        LI = self.L_I(alphaI, P, G, T)
        return np.sqrt(4*k_B*Tshunt/self.Rshunt) * self.Rshunt/R * (1. - LI/(1+iwt)) * (1./(1.-K_LI*betaI)) * K_LI * K_FI
        
    def amplifierNoise(self):
        return 0

def FlinkSpecular(beta, T, Tbase):
    t = T/Tbase
    return 0.5*(np.power(t, beta+2) + 1)

def FlinkDiffusive(beta, T, Tbase):
    t = T/Tbase
    return (beta+1)/(2*beta+3) * (np.power(t, 2*beta+3) - 1)/(np.power(t, beta+1)-1)
    
        
Parameters = [('alphaI', 0, 10000, '$\alpha_I$'),
              ('betaI', -100, +100, '$\beta_I$')]
              

    
        
        
        
        

    
    
    

if __name__ == '__main__':
    from SineSweep import SineSweep
    import matplotlib.pyplot as mpl
    from G4C.MeasurementDatabase import obtainTes
    
    deviceId = 'TES1'
    cooldown = 'G4C'
    path = 'D:\\Users\\Runs\\%s\\TF\\' % cooldown
    tes = obtainTes(cooldown, deviceId)

    Rfb = 10E3
    Rsq = tes.MiOverMfb(Rfb) * Rfb
    
    normalFile = path+'TES1_20171030_192245.h5'
    scFile = path+'TES1_20171028_130224.h5'
    Rn = tes.Rnormal
    ssNormal = SineSweep(normalFile)
    ssSc     = SineSweep(scFile)
    ssNormal.plotPolar(label='normal')
    print('Normal offset:', ssNormal.offset)
    print('Normal drive:', ssNormal.amplitude)
    ssSc.plotPolar(label='sc')
    print('Superconducting offset:', ssSc.offset)
    print('Superconducting drive:', ssSc.amplitude)
    mpl.legend()
    
    thevenin = TheveninEquivalentCircuit(ssNormal, ssSc, Rn, Rsq)
    thevenin.plot()
    
    fileName = path+'TES1_20171028_122154.h5'
    ss = SineSweep(fileName)
    tesAdmittance = TesAdmittance(ss, thevenin, Rsq)
    mpl.figure()
    tesAdmittance.plotPolar('admittance')
    mpl.suptitle('TES admittance A')
    mpl.figure()
    tesAdmittance.plot('impedance')
    mpl.show()

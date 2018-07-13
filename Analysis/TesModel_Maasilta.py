# -*- coding: utf-8 -*-
"""
Implements TES models by Illari Maasilta described in AIP Advances 2, 042110 (2012)
Created on Thu Jul 12 13:42:53 2018
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>

"""
from __future__ import division, print_function

import numpy as np

k_B = 1.3806485279E-23 # Boltzmann constant

#def thermalConductance(self, K, beta, T):
#    '''Calculate the thermal conductance at temperature T, given power law exponent beta'''
#    return (beta+1) * K * np.power(T, beta)
    
def scaleConductance(g0, T0, beta, T):
    '''Scale the thermal conductance g0 at temperature T0 to temperature T given power law exponent beta.'''
    g = g0 * np.power(T/T0, beta)
    return g
    
def coldTemperature(gh, Th, beta, P):
    '''Given hot end temperature *Th*, conductance gh, thermal power law exponent beta, and power P, compute the 
    cold end temperature.'''
    x = np.power(Th, beta)*(Th - P*(beta+1)/gh)
    Tbase = np.power(x, 1./(beta+1))
    return Tbase

class MaasiltaModel(object):
    def __init__(self, Rshunt):
        self.Rshunt = Rshunt
        
    def admittance(self, *args, **kwargs):
        return 1./self.impedance(*args, **kwargs)

    def responsivity(self, betaI, P, R, Lsquid, Ztes, omega):
        '''From TES impedance Ztes, calculate responsivity given inductance L, bias point (P, R), and betaI'''
        I = np.sqrt(P/R)
        #Ztes = self.impedance(omega)
        Zcirc = Ztes + self.Rshunt + 1j*omega*Lsquid
        SI = -1./(Zcirc*I) * (Ztes-R*(1+betaI))/(R*(2+betaI)) # Equation (15)
        return SI
        
    def Zcirc(self, Ztes, L, omega):
        Zcirc = Ztes + self.Rshunt + 1j*omega*L
        return Zcirc

    
class HangingModel(MaasiltaModel):
    '''Hanging model formulation following Maasilta 2012. The TES (temperature T, heat capacity Ctes) is connected to the bath through link g_tesb.
    The hanging body (temperature T, heat capacity C1) is connected to the TES through g_tes1.'''
    def modelSpecificParameters(self):
        return [('alphaI', '\\alpha_I', '',     1,    0.1,    1E4, 'Temperature sensitivity'),
                ('betaI',  '\\beta_I',  '',     1,    0,      1E3, 'Current sensitivity'),
                ('g_tes1', 'g_{tes,1}', 'nW/K', 1E-9, 0.001,   10, 'Thermal conductance between hanging body and TES'),
                ('g_tesb', 'g_{tes,b}', 'nW/K', 1E-9, 0.001,   10, 'Thermal conductance between TES and bath'),
                ('Ctes',   'C_{tes}',   'pJ/K', 1E-12, 0.001, 100, 'Heat capacity of TES'),
                ('C1',     'C_{1}',     'pJ/K', 1E-12, 0.001, 100, 'Hanging heat capacity')]

    def impedance(self, alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega):
        iw = 1j*omega
        LH = P*alphaI/((g_tes1+g_tesb)*T) # Equation (5)
        tauI = Ctes / ((g_tes1+g_tesb) * (1-LH)) # Equation (5)
        tau1 = C1 / g_tes1  # Equation (5)
        Z = R*(1+betaI) + LH/(1-LH)*R*(2+betaI) / (1+iw*tauI - g_tes1/((g_tes1+g_tesb)*(1-LH))*1./(1+iw*tau1))  # Equation (6)
        return Z
        
    def noiseComponents(self, alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, betaThermal, Tshunt, omega): # @TODO Remove Tbase (specified via P, g_tesb, and betaThermal)
        '''Returns the squared absolute current noise components in a dictionary.'''
        Ztes = self.impedance(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega)
        absSsq = np.abs(self.responsivity(betaI, P, R, Lsquid, Ztes, omega))**2 
        
        Tbase = coldTemperature(g_tesb, T, betaThermal, P)
        if Tshunt < 0:
            Tshunt = Tbase
            
        # TFN components
        g_tesb_Tbase = scaleConductance(g_tesb, T, betaThermal, Tbase)
        Psq_tesb = 2*k_B*(g_tesb*T**2 + g_tesb_Tbase*Tbase**2) # equation (18) TES to base->different temperatures 
        
        Psq_tes1 = 4*k_B*(g_tes1*T**2) # equation (18) TES and hanging body have same temperature
        
        TFN_TesB = absSsq * Psq_tesb    # equation (17)

        tau1 = C1 / g_tes1  # Equation (5)
        omegaTau1Sq = (omega*tau1)**2
        TFN_Tes1 = absSsq * Psq_tes1 * omegaTau1Sq/(1+omegaTau1Sq)  # equation (17)
        
        # Johnson noise of TES
        VtesSq = 4*k_B*R*T*(1+2*betaI)  #  
        Zcirc = Ztes + self.Rshunt + 1j*omega*Lsquid
        Johnson_Tes = VtesSq / (R*(2+betaI))**2 * abs((Ztes+R)/Zcirc)**2  # equation (20)
        
        # Johnson noise of shunt resistor
        VshuntSq = 4*k_B*self.Rshunt*Tshunt
        Johnson_Shunt = VshuntSq / abs(Zcirc)**2
        return {'TFN_TesB': TFN_TesB, 'TFN_Tes1': TFN_Tes1, 'Johnson_Tes': Johnson_Tes, 'Johnson_Shunt': Johnson_Shunt}
        

class IntermediateModel(MaasiltaModel):
    '''Intermediate model formulation following Maasilta 2012. The intermediate body (temperature T1, heat capacity C1) is connected to the bath through g_1b.
    The TES (temperature T, heat capacity Ctes) is connected to the intermediate body through g_tes,1.
    Since TES and intermediate body are at different temperatures (T and T1), there exists an effective g_eff (measured from IV curves)
    '''
    def impedance(self, alphaI, betaI, P, g_tes1, g_1b, Ctes, C1, T, R, omega):
        iw = 1j*omega
        # Added complication here: need g_tes1 at T0 and T1, but don't even know what T0 and T1 are...
        # For now, assume g_tes1 same at both temperatures
        g_tes1T0 = g_tes1 # @FIXME
        g_tes1T1 = g_tes1 # @FIXME
        
        L_IM = P*alphaI/(g_tes1T0*T) # Equation (9)
        tauI = Ctes / (g_tes1T0 * (1-L_IM)) # Equation (9) 
        tau1 = C1 / (g_tes1T1 + g_1b)  # Equation (9)
        Z = R*(1+betaI) + L_IM/(1-L_IM) * R * (2+betaI) / (1+iw*tauI - g_tes1T1 / ((g_tes1T1+g_1b)*(1-L_IM))*1./(1+iw*tau1))
        return Z
        
    def noiseComponents(self, alphaI, betaI, P, g_tes1, g_1b, Ctes, C1, T, R, Tbase, Tshunt, omega):
        '''Returns the squared absolute current noise components in a dictionary.'''
        Ztes = self.impedance(alphaI, betaI, P, g_tes1, g_1b, Ctes, C1, T, R, omega)
        absSsq = np.abs(self.responsivity(betaI, P, R, Lsquid, Ztes, omega))**2 

        Tbase = coldTemperature(g_tesb, T, betaThermal, P)
        if Tshunt < 0:
            Tshunt = Tbase
            
        # TFN components
        g_tesb_Tbase = scaleConductance(g_tesb, T, betaThermal, Tbase)

        g_tes1T1 = g_tes1  # @FIXME
        g_tes1Tbase = g_tes1  # @FIXME
        
        T1 = T # @FIXME
        
        # TFN components
        Psq_1b = 2*k_B*(g_tesb*T**2 + g_tesb*Tbase**2) # equation (18) TES to base->different temperatures 
        Psq_tes1 = 2*k_B*(g_tes1T1*T1**2 + g_tes1Tbase*Tbase**2) # equation (18) TES and hanging body have same temperature
        
        TFN_TesB = absSsq * Psq_1b * g_tes1T1**2 / (g_tes1T1+g_1b)**2    # equation (23)

        tau1 = C1 / (g_tes1T1 + g_1b)  # Equation (9)
        omegaTau1Sq = (omega*tau1)**2
        TFN_Tes1 = absSsq * Psq_tes1 * (g_1b**2/(g_tes1T1+g_1b)**2 + omegaTau1Sq)/(1+omegaTau1Sq)  # equation (23)
        
        # Johnson noise of TES
        VtesSq = 4*k_B*R*T*(1+2*betaI)
        Zcirc = Ztes + self.Rshunt + 1j*omega*Lsquid
        Johnson_Tes = VtesSq / (R*(2+betaI))**2 * abs((Ztes+R)/Zcirc)**2  # equation (20)
        
        # Johnson noise of shunt resistor
        VshuntSq = 4*k_B*self.Rshunt*Tshunt
        Johnson_Shunt = VshuntSq / abs(Zcirc)**2
        return {'TFN_TesB': TFN_TesB, 'TFN_Tes1': TFN_Tes1, 'Johnson_Tes': Johnson_Tes, 'Johnson_Shunt': Johnson_Shunt}
        
        
class ParallelModel(MaasiltaModel):
    def impedance(self, alphaI, betaI, P, g_tes1, g_tesb, g_1b, Ctes, C1, T, R, omega):
        iw = 1j*omega
        g_tes1T0 = g_tes1 # FIXME
        g_tes1T1 = g_tes1 # FIXME
        LP = P*alphaI/((g_tes1T0+g_tesb)*T)         # Equation (13), same as hanging model
        tauI = Ctes / ((g_tes1T0+g_tesb) * (1-LP))  # Equation (13), same as hanging model
        tau1 = C1 / (g_tes1T1 + g_1b)               # Equation (13), same as intermediate model
        Z = R*(1+betaI) + LP/(1-LP) * R * (2+betaI) / (1+iw*tauI - g_tes1T0*g_tes1T1 / ((g_tes1T0+g_tesb)*(g_tes1T1+g_1b)*(1-LP))*1./(1+iw*tau1))
        return Z
        
class ComplexImpedancePlot(object):
    def __init__(self, var):
        self.fig = mpl.figure(figsize=(8,6))
        self.grid = mpl.GridSpec(2, 4, wspace=0.25, hspace=0.25)
        self.var = var
        
        ax1 = mpl.subplot(self.grid[0, 0:2])
        ax2 = mpl.subplot(self.grid[1, 0:2])
        ax3 = mpl.subplot(self.grid[0:2, 2:4])
        ax1.set_ylabel('Re(%s)' % var)
        ax2.set_ylabel('Im(%s)' % var)
        ax2.set_xlabel('f (Hz)')
        ax3.set_xlabel('Re(%s)' % var)
        ax3.set_ylabel('Im(%s)' % var)
        ax3.set_aspect('equal')
        self.ax1 = ax1
        self.ax2 = ax2
        self.ax3 = ax3
        
    def plot(self, f, Z, label):
        if self.var == 'Y':
            V = 1./Z
        elif self.var == 'Z':
            V = Z
        self.ax1.semilogx(f, np.real(V), '-', label=label)
        self.ax2.semilogx(f, np.imag(V), '-', label=label)
        self.ax3.plot(np.real(V), np.imag(V), '-', label=label)
        

if __name__ == '__main__':
    import matplotlib.pyplot as mpl

    Rshunt = 250E-6 # Not explicitely specified
    model = HangingModel(Rshunt)

    alphaI = 100.    # Not sure    
    betaI = 1. # Specified in Fig. 2
    R = 0.1 # Specified in Fig. 2
    tauTes = 1E-3 # Not spec'd
    Ctes = 1E-12 # Not spec'd
    g_tesb = Ctes/tauTes
    g_tes1 = g_tesb # To make a=0.5 (see Fig. 2)
    a = g_tes1/(g_tes1+g_tesb)
    print('a=', a)
        
    omega = np.logspace(np.log10(0.001), np.log10(500), 500) / tauTes
    
    C1s = np.asarray([0.33, 0.49, 0.73, 1.1, 1.65, 2.48, 3.71, 5.57, 8.35, 12.5]) * Ctes
    L = 1.65 # See Fig. 2
    T = 100E-3 # Not spec'd
    P = L*(g_tesb*T)/alphaI
    
    print('P=', P)
    

    f = omega/(2*np.pi)
    plot = ComplexImpedancePlot('Z')

    for C1 in C1s:    
        Z = model.impedance(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega)
        label = '%.2f' % (C1/Ctes)
        plot.plot(f, Z, label)
        
    plot.ax1.legend(title='$C_{1}/C_{tes}$')
    plot.fig.suptitle('Transfer function (hanging model)')
    
    ## Responsivity
    tauEl = 0.015*tauTes
    Lsquid = tauEl * (Rshunt+R*(1+betaI)) # inductor
    a = 0.9
    g_tes1 = g_tesb / (1/a-1)
    mpl.figure('Responsivity')
    for C1 in C1s:
        Ztes = model.impedance(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, omega)
        S = model.responsivity(betaI, P, R, Lsquid, Ztes, omega)
        mpl.loglog(omega*tauTes, np.abs(S/S[0]), '-', label='%.2f' % (C1/Ctes))

    mpl.grid()
    mpl.legend(loc='best')
    mpl.xlabel('$\\omega \\tau$')
    mpl.ylabel('$|S(\omega)/S(\omega=0)|$')
    mpl.title('Responsivity (hanging model) - see Maasilta 2012 Fig. 3')        
    
    mpl.figure('Noise')
    tauTes = 0.5E-3
    Rshunt = 1E-3 # Figure 4
    I = 10E-6
    P = I**2*R
    print('P=', P)
    print('g_tesb=', g_tesb)
    
    g_tes1 = g_tesb # Leads to a=0.5 (see Fig. 4)
 
    T = 75E-3 # Not specified
    Tbase = coldTemperature(g_tesb, T, 3.5, P)    
    print('Tbase=', Tbase)
    print('T=', T)
    Tshunt = Tbase
    #P = L*(g_tesb*T)/alphaI
    alphaI = L*(g_tesb*T)/P
    print('alphaI=', alphaI)
    tauEl = 0.015*tauTes
    Lsquid = tauEl * (Rshunt+R*(1+betaI)) # inductor
    print('Lsquid=', Lsquid)
    
    model = HangingModel(Rshunt)
    import matplotlib.cm as cm
    lts = {'Johnson_Shunt': ':', 'Johnson_Tes': '-.', 'TFN_TesB': '-', 'TFN_Tes1': '--' }    
    for C1 in C1s:
        noises = model.noiseComponents(alphaI, betaI, P, g_tes1, g_tesb, Ctes, C1, T, R, Tbase, Tshunt, omega)
        nTotal = np.zeros_like(omega)
        x = omega*tauTes
        color = cm.coolwarm((C1-np.min(C1s))/(np.max(C1s)-np.min(C1s)))
        for component in noises.keys():
            n = noises[component]
            nTotal += n
            if C1==C1s[0]:
                label = component
            else:
                label = None
            mpl.semilogx(x, 1E12*np.sqrt(n), lts[component], color=color, label=label)
        if label is not None:
            label = 'total' 
        mpl.semilogx(x, 1E12*np.sqrt(nTotal), '-', color=color, label=label, lw=1.5)
    mpl.ylabel('Current noise (pA/rtHz)')
    mpl.xlabel('$\\omega \\tau$')
    mpl.title('Current noise (hanging model)')
    mpl.grid()
    mpl.legend()
    mpl.show()

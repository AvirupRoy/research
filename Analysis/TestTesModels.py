# -*- coding: utf-8 -*-
"""
Created on Mon Jul 09 17:29:17 2018

@author: wisp10
"""
from __future__ import division, print_function
import numpy as np
import matplotlib.pyplot as mpl
from TransferFunction import TesModelSimple, FlinkSpecular, FlinkDiffusive

Rshunt = 250E-6
model = TesModelSimple(Rshunt)

#Rn = 6E-3



# Some realistic numbers for G5C/TES2/2018-05-26/01:28:18/Vb=1.100V/Vc=3.4000V
alphaI = 203.5
betaI = 6.354
tau = 10.844E-3
R = 1.347E-3
P = 0.885E-12
G = 53.314E-12 # This is G at the warm end
T = 80.132E-3
Tbase = 54.993E-3
thermalK, thermalTtes, thermalBeta = (9.7449268549045635e-09, 0.085014593011416076, 2.5670681840646075)
G0 = (thermalBeta+1) * thermalK * np.power(Tbase, thermalBeta) # G0=G at cold end

f = np.logspace(np.log10(1), np.log10(1E5), 100)
omega = 2*np.pi*f

L_I = model.L_I(alphaI, P, G, T)
print('L_I =', L_I)
A = model.admittance(alphaI, betaI, tau, P, G, T, R, omega)

fig, axes = mpl.subplots(2,1, sharex=True)
ax = axes[0]
ax.semilogx(f, np.real(A), '-b', label='real')
ax.semilogx(f, np.imag(A), '-r', label='imag')
ax.set_ylabel('Admittance (Mohs)')
ax.legend()
ax.grid()

Z = 1./A
ax = axes[1]
ax.semilogx(f, np.real(Z), '-b', label='real')
ax.semilogx(f, np.imag(Z), '-r', label='imag')
ax.grid()
ax.set_ylabel('Impedance (Ohms)')
ax.set_xlabel('f (Hz)')

S = model.responsitivity(alphaI, betaI, tau, P, G, T, R, omega)

fig, axes = mpl.subplots(2,1, sharex=True)
ax = axes[0]
ax.semilogx(f, np.real(S), '-b', label='real')
ax.semilogx(f, np.imag(S), '-r', label='imag')
ax.set_ylabel('Responsivity (A/W)')
#mpl.show()

fig, axes = mpl.subplots(1,1)
ax = axes

TFN        = model.TFN(alphaI, betaI, tau, P, G, T, R, Tbase, G0, omega)
I_nJ_Tes   = model.johnsonNoiseTes(alphaI, betaI, tau, P, G, T, R, omega)
I_nJ_Shunt = model.johnsonNoiseShunt(alphaI, betaI, tau, P, G, T, R, Tbase, omega)
I_n_Total = np.sqrt(I_nJ_Tes**2 + I_nJ_Shunt**2 + TFN**2)
ax.loglog(f, 1E12*I_n_Total, 'k-', label='Total')
ax.loglog(f, 1E12*TFN, 'g-', label='TFN')
ax.loglog(f, 1E12*I_nJ_Tes, 'b-', label='JN TES')
ax.loglog(f, 1E12*I_nJ_Shunt, 'r-', label='JN shunt')
ax.set_ylabel('Noise (pA/$\sqrt{Hz}$)')
ax.legend()
ax.grid()


betas = np.linspace(2, 5)
T = Tbase*1.05
Fspec = FlinkSpecular(betas, T, Tbase)
Fdiff = FlinkDiffusive(betas, T, Tbase)
mpl.figure()
corr = np.power(Tbase/T, betas+1) # This is to account for the different definitions used in McCammon and Irwin chapters
mpl.plot(betas, Fspec*corr, '-', label='specular')
mpl.plot(betas, Fdiff*corr, '-', label='diffusive')
mpl.legend()
mpl.xlabel('$\\beta$')
mpl.ylabel('$F$')
mpl.title('Non-equilibrium TFN factor')
mpl.show()

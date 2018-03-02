# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 15:15:10 2017

@author: wisp10
"""

import numpy as np
class Tes(object):
    DeviceName = ''
    Rbias = 0
    MiOverMfb10k = 0
    MiOverMfb100k = 0
    Rshunt = 0
    Rnormal = 0
    def temperature(self, Tbase, P):
        '''Given base temperature *Tbase* and TES power, compute the TES
        temperature T_TES based on the power law-thermal model.'''
        beta = self.thermalBeta
        Ttes = np.power(np.power(Tbase, beta+1) + P/self.thermalK, 1./(beta+1))
        return Ttes
        
    def thermalConductance(self, Ttes):
        beta = self.thermalBeta
        return (beta+1) * self.thermalK * np.power(Ttes, beta)
        
    def baseTemperature(self, Ttes, P):
        '''Give TES temperature *Ttes* and TES power *P*, compute the 
        base temperature.'''
        #Ttes**(beta+1) = Tbase**(beta+1) + P/thermalK
        beta = self.thermalBeta
        x = np.power(Ttes, beta+1) - P/self.thermalK
        Tbase = np.power(x, 1./(beta+1))
        return Tbase
        
    def Rsquid(self, Rfb):
        return Rfb * self.MiOverMfb(Rfb)
        
    def MiOverMfb(self, Rfb):
        if Rfb == 10E3:
            return self.MiOverMfb10k
        elif Rfb == 100E3:
            return self.MiOverMfb100k
        else:
            raise IndexError()
    
class G4C_Tes1(Tes):
    DeviceName = 'ATH1 C15071Sb128f Bottom #12 (0% perf)'
    CoolDown = 'G4C'
    Rbias = 6.8953E3
    Rshunt = 0.251E-3
    Rnormal = 6.68E-3
    MiOverMfb10k = 1.04898 # For 10kOhm
    MiOverMfb100k = 1.0369862590397567 # For 100kOhm
    thermalK, thermalTtes, thermalBeta = (3.62468112e-08,   8.87960943e-02,   2.64214427)
    
class G4C_Tes2(Tes):
    DeviceName = 'ATH1 C15071Sb128f Bottom #15 (25% perf)'
    coolDown = 'G4C'
    Rbias =  6.8735E3
    Rshunt = 0.257E-3
    Rnormal = 6.9E-3
    MiOverMfb10k = 1.0522909331889936
    MiOverMfb100k = 1.039161565802851 
    thermalK, thermalTtes, thermalBeta = (2.95913929e-08,   8.66501509e-02,   2.64884014) # From 75% of Rn
    
class G5C_Tes1(Tes):
    DeviceName = 'ATH1 C15071Sb128f Top #12 (0% perf)'
    CoolDown = 'G5C'
    Rbias = 6.8953E3 # Should be identical to G4C cooldown
    Rshunt = 0.251E-3 # Should be identical to G4C cooldown
    Rnormal = 6.68E-3 # Unknown
    MiOverMfb10k = 1.04898 # For 10kOhm  # Should be identical to G4C cooldown
    MiOverMfb100k = 1.0369862590397567 # For 100kOhm  # Should be identical to G4C cooldown
    thermalK, thermalTtes, thermalBeta = (3.62468112e-08,   8.87960943e-02,   2.64214427) # Unknown

class G5C_Tes2(Tes):
    DeviceName = 'ATH1 C15071Sb128f Top #15 (75% perf)'
    coolDown = 'G5C'
    Rbias =  6.8735E3
    Rshunt = 0.257E-3
    Rnormal = 6.9E-3 # Unknown
    MiOverMfb10k = 1.0522909331889936
    MiOverMfb100k = 1.039161565802851 
    thermalK, thermalTtes, thermalBeta = (2.95913929e-08,   8.66501509e-02,   2.64884014) # Unknown
    

def obtainTes(cooldown, tesId):
    if cooldown == 'G4C':
        if tesId == 'TES1':
            return G4C_Tes1()
        elif tesId == 'TES2':
            return G4C_Tes2()
    elif cooldown == 'G5C':
        if tesId == 'TES1':
            return G5C_Tes1()
        elif tesId == 'TES2':
            return G5C_Tes2()

if __name__ == '__main__':
    tes = obtainTes('G4C', 'TES1')
    tes
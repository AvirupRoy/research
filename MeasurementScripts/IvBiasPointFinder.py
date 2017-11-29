# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 18:41:01 2017

@author: wisp10
"""

import numpy as np
from Analysis.TesIvSweepReader import IvSweepCollection
def findBiasPointR(fileName, tes, Rfb, Rgoal):    
    sweeps = IvSweepCollection(fileName)

    Vteses = []; Iteses = []; Vbiases = []

    for sweep in sweeps:
        #sweep.plotRaw()
        MiOverMfb = tes.MiOverMfb(Rfb)
        #shift = sweep.checkForOffsetShift()
        sweep.subtractSquidOffset()
        sweep.applyCircuitParameters(Rb=tes.Rbias, Rfb=Rfb, Rs=tes.Rshunt, Mfb=1.0, Mi=MiOverMfb)
        Vbias, Ites, Vtes = sweep.findBiasPoint('R', Rgoal)
        
        Iteses.append(Ites)
        Vbiases.append(Vbias)
        Vteses.append(Vtes)
    
    return np.nanmean(Vbiases)
    
def findBiasPointI(fileName, tes, Rfb, Igoal):    
    sweeps = IvSweepCollection(fileName)

    Vteses = []; Iteses = []; Vbiases = []

    for sweep in sweeps:
        #sweep.plotRaw()
        MiOverMfb = tes.MiOverMfb(Rfb)
        #shift = sweep.checkForOffsetShift()
        sweep.subtractSquidOffset()
        sweep.applyCircuitParameters(Rb=tes.Rbias, Rfb=Rfb, Rs=tes.Rshunt, Mfb=1.0, Mi=MiOverMfb)
        Vbias, Ites, Vtes = sweep.findBiasPoint('I', Igoal)
        Iteses.append(Ites)
        Vbiases.append(Vbias)
        Vteses.append(Vtes)
    return np.nanmean(Vbiases)
    
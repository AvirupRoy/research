# -*- coding: utf-8 -*-
"""
Created on Sat Oct 14 17:49:58 2017

@author: wisp10
"""

import numpy as np

class USP7766(object):
    A,B,C = (1.12877841e-03,2.34200357e-04,8.72346549e-08)
    
    def calculateTemperature(self, R):
        lnR = np.log(R)
        T = 1./(self.A+self.B*lnR+self.C*lnR**3)
        return T

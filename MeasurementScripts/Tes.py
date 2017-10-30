# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 15:32:57 2017

@author: wisp10
"""

import DAQ.PyDaqMx as daq
import numpy as np
from PyQt4.QtGui import QApplication
import time

class Tes(object):
    class States:
        Idle = 0
        RampAboveBias = 1
        RampBias = 2
        WaitForTlow = 3
        HoldLow = 4
        WaitForThigh = 5
        HoldHigh = 6
        WaitForTmid = 7
        HoldTmid = 8
        
    def __init__(self, Rbias, biasChannel, fieldChannel=None, pflChannel = None):
        self.Rbias = Rbias
        self.biasChannel = biasChannel
        self.pflChannel = pflChannel
        self.Vbias = 0
        
    def _makeAoTask(self):
        aoTask = daq.AoTask('biasTask')
        aoTask.addChannel(self.biasChannel)
        return aoTask

    def _makeAiTask(self):
        aiTask = daq.AiTask('pflTask')
        aiTask.addChannel(self.pflChannel)
        return aiTask
      
    def setBias(self, Ibias):
        aoTask = self._makeAoTask()
        Vbias = Ibias * self.Rbias
        #logger.info('Applying Vbias=%.5f V' % Vbias)
        aoTask.writeData([Vbias], autoStart = True)
        self.Vbias = Vbias
        aoTask.stop()
        aoTask.clear()
        
    def rampBias(self, Ibias):
        aoTask = self._makeAoTask()
        Vbias = Ibias * self.Rbias
        step = 0.01 * np.sign(Vbias-self.Vbias)
        Vs = np.arange(self.Vbias, Vbias+step, step)
        for V in Vs:
            aoTask.writeData([V], autoStart = True)
        aoTask.writeData([Vbias], autoStart = True)
        self.Vbias = Vbias
        aoTask.stop()
        aoTask.clear()
        
    def measureIvsT(self, adr, Ibias, Tmid, deltaT, fileName=''):
        assert deltaT > 0
        VbiasTarget = Ibias * self.Rbias
        VbiasTargetAbove = 3.5
        aoTask = self._makeAoTask()
        aiTask = self._makeAiTask()
        state = Tes.States.Idle
        ts = []
        Vsquids = []
        Vbiases = []
        Tadrs = []
        step = 0.02
        nHold = 40
        
        while True:
            time.sleep(0.1)
            QApplication.processEvents()
            Vsquid = np.mean(aiTask.readData(500)[0])
            t = time.time()
            ts.append(time.time())
            Vsquids.append(Vsquid)
            Vbiases.append(self.Vbias)
            T=adr.T
            Tadrs.append(T)
            #print('State=', state, self.Vbias, Vsquid)
            if len(fileName):
                with open(fileName, 'a') as f:
                    f.write('%.3f\t%d\t%.5f\t%.6f\t%.6f\n' % (t, state, self.Vbias, T, Vsquid))
            n = len(Vsquids)
            if state == Tes.States.Idle:
                if n > nHold:
                    state = Tes.States.RampAboveBias
            elif state == Tes.States.RampAboveBias:
                s = step * np.sign(VbiasTargetAbove - self.Vbias)
                Vbias = self.Vbias + s
                if s < 0:
                    Vbias = max(VbiasTargetAbove, Vbias)
                else:
                    Vbias = min(VbiasTargetAbove, Vbias)
                aoTask.writeData([Vbias], autoStart=True)
                self.Vbias = Vbias
                if abs(self.Vbias-VbiasTargetAbove) < 1E-5:
                    state = Tes.States.RampBias
                    nTransition = n
            elif state == Tes.States.RampBias:
                s = step * np.sign(VbiasTarget - self.Vbias)
                Vbias = self.Vbias + s
                if s < 0:
                    Vbias = max(VbiasTarget, Vbias)
                else:
                    Vbias = min(VbiasTarget, Vbias)
                aoTask.writeData([Vbias], autoStart=True)
                self.Vbias = Vbias
                if abs(self.Vbias-VbiasTarget) < 1E-5:
                    adr.rampTo(Tmid-deltaT)
                    state = Tes.States.WaitForTlow
                    nTransition = n
            elif state == Tes.States.WaitForTlow:
                if adr.T <= Tmid - deltaT:
                    state = Tes.States.HoldLow
                    nTransition = n
            elif state == Tes.States.HoldLow:
                if n > nTransition + nHold:
                    state = Tes.States.WaitForThigh
                    adr.rampTo(Tmid + deltaT)
                    nTransition = n
            elif state == Tes.States.WaitForThigh:
                if adr.T >= Tmid + deltaT:
                    state = Tes.States.HoldHigh
                    nTransition = n
            elif state == Tes.States.HoldHigh:
                if n > nTransition + nHold:
                    state = Tes.States.WaitForTmid
                    adr.rampTo(Tmid)
                    nTransition = n
            elif state == Tes.States.WaitForTmid:
                if abs(adr.T - Tmid) < 20E-6:
                    state = Tes.States.HoldTmid
                    nTransition = n
            elif state == Tes.States.HoldTmid:
                if n > nTransition+nHold:
                    break
                
        return np.asarray(ts), np.asarray(Tadrs), np.asarray(Vbiases), np.asarray(Vsquids)
          
if __name__ == '__main__':
#    import matplotlib.pyplot as mpl
    from Adr import Adr
    app = QApplication([])
    adr = Adr(app)
    aiChannelId = 'AI2'
    aoChannelId = 'AO0'
    biasChannel = daq.AoChannel('USB6361/%s' % aoChannelId, -5,+5)
    pflChannel = daq.AiChannel('USB6361/%s' % aiChannelId, -5,+5)
    pflChannel.setTerminalConfiguration(daq.AiChannel.TerminalConfiguration.DIFF)
    tes = Tes(6.0E3, biasChannel, fieldChannel = None, pflChannel = pflChannel)
    tes.setBias(0)
    adr.setRampRate(0.5)
    app.processEvents()
    Tmid = 0.078
    fileName = 'testRamp.txt'
    ts, Tadrs, Vbiases, Vsquids = tes.measureIvsT(adr, 300E-6, Tmid=Tmid, deltaT=0.5E-3, fileName=fileName)    
    np.savez('TestRamp4', ts=ts, Vsquids=Vsquids, Vbiases=Vbiases, Tadrs=Tadrs)
    tes.rampBias(0)
#    mpl.plot(Vbiases,Vsquids)
#    mpl.show()

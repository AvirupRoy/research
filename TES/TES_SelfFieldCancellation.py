# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 16:47:13 2016

@author: wisp10
"""

import LabWidgets.Utilities as ut
ui = ut.compileAndImportUi('TES_SelfFieldCancellation')
ProgramName = 'TES_SelfFieldCancellation'
OrganizationName = 'McCammon X-ray Astrophysics'

import PyQt4.QtGui as gui
from PyQt4.QtCore import pyqtSignal, QThread, QSettings
import DAQ.PyDaqMx as daq

import numpy as np
import time


def limit(V):
    return max(min(V,10),-10)
    
class MsmThread(QThread):
    measurementAvailable = pyqtSignal(float, float, float, float, float, float, float) #(t, Vbias, Vcoil, Vo, Vsq, Ites, Rtes)
    def setFixedParameters(self, Mi, Mfb, Rfb, gCoil, Rcoil, Ap, Rbias, Rs):
        '''Set the circuit parameters that can not be updated during a run.'''
        self.Mi = Mi
        self.Mfb = Mfb
        self.Rfb = Rfb
        self.gCoil = gCoil
        self.Rcoil = Rcoil
        self.Ap = Ap
        self.Rbias = Rbias
        self.Rs = Rs
        
    def setgTes(self, gTes):
        '''Update gTes'''
        self.gTes = gTes
        
    def setBo(self, Bo):
        '''Update Bo'''
        self.Bo = Bo
        
    def setIbias(self, Ibias):
        self._Ibias = Ibias
        
    def setNumberOfSamples(self, nSamples):
        self.nSamples = nSamples
        
    def stop(self):
        self._stopRequested = True
    
    def run(self):
        self._stopRequested = False
        try:
            self.doWork()
        except Exception, e:
            print "Exception:", e
            
    def doWork(self):
        Mi = self.Mi
        Mfb = self.Mfb
        Rfb = self.Rfb
        gCoil = self.gCoil
        Rcoil = self.Rcoil
        Ap = self.Ap
        Rbias = self.Rbias
        Rs = self.Rs

        aiTask = daq.AiTask('SQUID read-out')
        aiChannel = daq.AiChannel('USB6002_B/AI0', -10, +10)
        aiChannel.setTerminalConfiguration(aiChannel.TerminalConfiguration.DIFF)
        aiTask.addChannel(aiChannel)
        aiTask.start()
        
        aoTask = daq.AoTask('Control')
        aoChannel1 = daq.AoChannel('USB6002_B/AO0', -10, +10)
        aoChannel2 = daq.AoChannel('USB6002_B/AO1', -10, +10)
        aoTask.addChannel(aoChannel1)
        aoTask.addChannel(aoChannel2)
        aoTask.start()
        Vo = 0
        Vcoil = 0
        Vbias = limit(Rbias*self._Ibias)
        VoHistory = []
        aoTask.writeData([Vbias, Vcoil])
        while not self._stopRequested:
            Vsq = np.mean(aiTask.readData(self.nSamples)[0])
            if Vbias == 0:
                VoHistory.append(Vsq)
                VoHistory = pruneData(VoHistory)
                Vo = np.mean(VoHistory)
            else:
                VoHistory = []
            t = time.time()
            Ites = (1/Mi)*Mfb*(Vsq-Vo)/Rfb - gCoil*Vcoil*Ap/Rcoil
            Ibias = Vbias/Rbias
            if Ites == 0:
                Rtes = np.nan
            else:
                Rtes = (Ibias-Ites)/Ites * Rs
            self.measurementAvailable.emit(t, Vbias, Vcoil, Vo, Vsq, Ites, Rtes)
            
            # Calculate new target Vcoil and Vbias
            Vcoil = limit(Rcoil/gCoil * (self.Bo - self.gTes*Ites))
            Vbias = limit(Rbias*self._Ibias)
            aoTask.writeData([Vbias, Vcoil])
            self.msleep(10)
        aoTask.writeData([0, 0])
        aoTask.stop()
        aiTask.stop()

from Zmq.Subscribers import HousekeepingSubscriber

from Utility.Math import pruneData

SI_Phi0 = 2.06783375846E-15
SI_uT = 1E-6
SI_A = 1E0
SI_mA = 1E-3
SI_uA = 1E-6
SI_kOhm = 1E3
SI_um = 1E-6
SI_mOhm = 1E-3

import pyqtgraph as pg
class Widget(gui.QWidget, ui.Ui_Form):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)
        self.setupUi(self)
        self.BoSb.setToSiFactor(SI_uT)
        self.gCoilSb.setToSiFactor(SI_uT/SI_mA)
        self.RcoilSb.setToSiFactor(SI_kOhm)
        self.BcoilSb.setToSiFactor(SI_uT)
        self.RfbSb.setToSiFactor(SI_kOhm)
        self.invMiSb.setToSiFactor(SI_uA/SI_Phi0)
        self.invMfbSb.setToSiFactor(SI_uA/SI_Phi0)
        self.ApSb.setToSiFactor(SI_um**2)
        self.RbiasSb.setToSiFactor(SI_kOhm)
        self.gTesSb.setToSiFactor(SI_uT/SI_mA)
        self.RsSb.setToSiFactor(SI_mOhm)
        self.IbiasSb.setToSiFactor(SI_uA)
        self.ItesSb.setToSiFactor(SI_uA)
        self.RtesSb.setToSiFactor(SI_mOhm)
        
        self.setWindowTitle('TES Self-Field Cancellation')
        self.SettingsWidgets = [self.BoSb, self.gCoilSb, self.RcoilSb, self.RfbSb,
                                self.invMiSb, self.invMfbSb, self.ApSb, self.RbiasSb,
                                self.gTesSb, self.IbiasSb, self.nameLe, self.aiSamplesSb]
        self.liveWidgets = [self.BoSb, self.gTesSb, self.IbiasSb]
                                
        self.restoreSettings()
        self.msmThread = None
        self.hkSub = HousekeepingSubscriber(self)
        self.hkSub.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.hkSub.start()
        self.curveVsTime = pg.PlotCurveItem(pen='k')
        self.plotVsTime.addItem(self.curveVsTime)
        self.plotVsTime.plotItem.enableAutoRange(pg.ViewBox.XYAxes, True)
        self.curveVsTemp = pg.PlotCurveItem(pen='k')
        self.plotVsTemp.addItem(self.curveVsTemp)
        self.plotVsTemp.setBackground('w')
        self.plotVsTemp.plotItem.showGrid(x=True, y=True)
        self.plotVsTemp.plotItem.enableAutoRange(pg.ViewBox.XYAxes, True)
        self.clearData()
        self.runPb.clicked.connect(self.run)
        
    def run(self):
        if self.msmThread is not None:
            self.msmThread.stop()
            self.msmThread.wait()
            self.file.close()
            self.msmThread.deleteLater()
            self.msmThread = None
        else:
            Mi = 1./self.invMiSb.valueSi()
            Mfb = 1./self.invMfbSb.valueSi()
            Rfb = self.RfbSb.valueSi()
            gCoil = self.gCoilSb.valueSi()
            self.gCoil = gCoil
            Rcoil = self.RcoilSb.valueSi()
            self.Rcoil = Rcoil
            Ap = self.ApSb.valueSi()
            Rbias = self.RbiasSb.valueSi()
            print "Rbias:", Rbias
            Rs = self.RsSb.valueSi()
            gTes = self.gTesSb.valueSi()
            Bo = self.BoSb.valueSi()
            Ibias = self.IbiasSb.valueSi()
            print "Ibias:", Ibias
            nSamples = self.aiSamplesSb.value()
            
            fileName = '%s_%s.dat' % (self.nameLe.text(), time.strftime('%Y%m%d_%H%M%S'))
            self.file = open(fileName, 'w')
            def writeParameter(name, value):
                self.file.write('#%s=%.6e\n' % (name,value))
            writeParameter('Mi', Mi)
            writeParameter('Mfb', Mfb)
            writeParameter('Rfb', Rfb)
            writeParameter('gCoil', gCoil)
            writeParameter('Rcoil', Rcoil)
            writeParameter('Ap', Ap)
            writeParameter('Rbias', Rbias)
            writeParameter('Rs', Rs)
            writeParameter('gTes', gTes)
            writeParameter('Bo', Bo)
            writeParameter('gTes', gTes)
            writeParameter('Ibias', Ibias)
            self.file.write('#%s\n' % '\t'.join(['t', 'Tadr', 'Vbias', 'Vcoil', 'Vo', 'Vsquid', 'Ites', 'Rtes']) )

            msmThread = MsmThread(parent=self)
            msmThread.setFixedParameters(Mi=Mi, Mfb=Mfb, Rfb=Rfb, gCoil=gCoil,
                                         Rcoil=Rcoil, Ap=Ap, Rbias=Rbias, Rs=Rs)
            msmThread.setgTes(gTes)
            msmThread.setBo(Bo)
            msmThread.setIbias(Ibias)
            msmThread.setNumberOfSamples(nSamples)
            msmThread.finished.connect(self.threadFinished)
            msmThread.measurementAvailable.connect(self.collectData)
            self.gTesSb.valueChangedSi.connect(msmThread.setgTes)
            self.BoSb.valueChangedSi.connect(msmThread.setBo)
            self.IbiasSb.valueChangedSi.connect(msmThread.setIbias)
            self.msmThread = msmThread
            msmThread.start()
            msmThread.started.connect(self.threadStarted)
        
    def clearData(self):
        self.ts = []
        self.T = []
        self.Vbias = []
        self.Vcoil = []
        self.Vo = []
        self.Vsquid = []
        self.Ites = []
        self.Rtes = []
        self.updatePlots()
        
    def collectData(self, t, Vbias, Vcoil, Vo, Vsquid, Ites, Rtes):
        Tadr = self.temperatureSb.value()
        self.ts.append(t)
        self.T.append(Tadr)
        self.Vbias.append(Vbias)
        self.Vcoil.append(Vcoil)
        self.Vo.append(Vo)
        self.Vsquid.append(Vsquid)
        self.Ites.append(Ites)
        self.Rtes.append(Rtes)
        self.file.write('%.3f\t%.5e\t%.5f\t%.5f\t%.5f\t%.5f\t%.5e\t%.5e\n' %  (t, Tadr, Vbias, Vcoil, Vo, Vsquid, Ites, Rtes))

        l = len(self.ts)
        if l % 20 != 0:
            return

        i = min(l, 100)
        if i > 10:
            Dt = t - self.ts[-i]
            rate = float(i)/Dt
            self.loopRateSb.setValue(rate)
        self.lockLostLed.setValue(abs(Vsquid) > 10)

        self.ts = pruneData(self.ts)
        self.T = pruneData(self.T)
        self.Vbias = pruneData(self.Vbias)
        self.Vcoil = pruneData(self.Vcoil)
        self.Vo = pruneData(self.Vo)
        self.Vsquid = pruneData(self.Vsquid)
        self.Ites = pruneData(self.Ites)
        self.Rtes = pruneData(self.Rtes)
        
        self.VbiasSb.setValue(Vbias)
        self.VcoilSb.setValue(Vcoil)
        self.VoSb.setValue(Vo)
        self.VsquidSb.setValue(Vsquid)
        self.ItesSb.setValueSi(Ites)
        self.RtesSb.setValueSi(Rtes)
        Bcoil = self.gCoil * Vcoil / self.Rcoil
        self.BcoilSb.setValueSi(Bcoil)
        self.updatePlots()
        
    def updatePlots(self):
        yAxis = self.yAxisCombo.currentText()
        if yAxis == 'Vbias':
            y = self.Vbias
        elif yAxis == 'Vcoil':
            y = self.Vcoil
        elif yAxis == 'Vo':
            y = self.Vo
        elif yAxis == 'Vsquid':
            y = self.Vsquid
        elif yAxis == 'Ites':
            y = self.Ites
        elif yAxis == 'Rtes':
            y = self.Rtes
        
        if yAxis == 'Ites':
            unit = 'A'
        elif yAxis == 'Rtes':
            unit = 'Ohm'
        else:
            unit = 'V'
        yax = self.plotVsTime.getAxis('left')
        yax.setLabel(yAxis, unit)
        yax = self.plotVsTemp.getAxis('left')
        yax.setLabel(yAxis, unit)
        self.curveVsTime.setData(x=self.ts, y=y)
        self.curveVsTemp.setData(x=self.T, y=y)
            
    def threadStarted(self):
        self.enableControls(False)

    def threadFinished(self):
        self.enableControls(True)
        
    def enableControls(self, enable):
        for w in self.SettingsWidgets:
            if not w in self.liveWidgets:
                w.setEnabled(enable)
        self.runPb.setText('Run' if enable else 'Stop')
        
    def closeEvent(self, event):
        self.saveSettings()
        
    def restoreSettings(self):
        s = QSettings()
        for w in self.SettingsWidgets:
            ut.restoreWidgetFromSettings(s, w)
            
    def saveSettings(self):
        s = QSettings()
        for w in self.SettingsWidgets:
            ut.saveWidgetToSettings(s, w)

if __name__ == '__main__':
    import PyQt4.QtGui as gui    
    app = gui.QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName(ProgramName)
    app.setApplicationVersion('0.1')
    app.setOrganizationName(OrganizationName)
    mw = Widget()
    mw.show()
    app.exec_()
 
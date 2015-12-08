# -*- coding: utf-8 -*-
"""
TES (SQUID readout) version of the IVSweepsDaq.py code.
Collect IV curves by sweeping DAQ output and reading DAQ input.
Detect superconducting to normal transition as the maxima points of the IV characteristic (not robust yet).
Created on Thu Jun 25 17:15:17 2015
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""


from PyQt4.QtGui import QWidget #, QDoubleSpinBox, QSpinBox, QHeaderView
from PyQt4.QtCore import pyqtSignal, QThread, QSettings, QString, QByteArray #, QObject

import time
from Zmq.Subscribers import TemperatureSubscriber
import numpy as np

from Visa.SR830 import SR830

from AnalogSource import  VoltageSourceSR830, VoltageSourceDaq, CurrentSourceKeithley
from AnalogMeter import VoltmeterDaq

print 'Building GUI...',
from PyQt4 import uic
uic.compileUiDir('.')
print ' Done.'
import TES_IVSweepsDaqUi

class IVSweepMeasurement(QThread):
    readingAvailable = pyqtSignal(float,float,float,float,float)
    sweepComplete = pyqtSignal(float, float)
    def __init__(self, ao, ai, parent=None):
        QThread.__init__(self, parent)
        self.ao = ao
        self.ai = ai
        self.paused = False
        self.threshold = 10
        self.bipolar = False
        self.T = np.nan
        self.interSweepDelay = 0
        self.samplesPerPoint = 1
        self.adaptiveSweep = False
        self.adaptiveLower = 0.6
        self.adaptiveUpper = 1.3
        self.reverseSweep = False

    def enableReverseSweep(self, enable=True):
        self.reverseSweep = enable
        
    def enableAdaptiveSweep(self, enable=True):
        self.adaptiveSweep = enable
        
    def setAdaptiveUpper(self, fraction):
        self.adaptiveUpper = fraction
        
    def setAdaptiveLower(self, fraction):
        self.adaptiveLower = fraction

    def setFileName(self, fileName):
        self.fileName = fileName

    def setVoltages(self, voltages):
        self.voltages = voltages

    def enableBipolar(self, enable=True):
        self.bipolar = enable

    def setThreshold(self, threshold):
        self.threshold = threshold

    def setInterSweepDelay(self, delay):
        self.interSweepDelay = delay

    def stop(self):
        self.stopRequested = True

    def pause(self, pause=True):
        self.paused = pause

    def unpause(self):
        self.pause(False)

    def updateTemperature(self, T):
        self.T = T

    def setMaximumVoltage(self, Vmax):
        self.VmaxP = min(abs(Vmax),10.)
        self.VmaxN = self.VmaxP

    def setMinimumVoltage(self, Vmin):
        self.VminP = max(abs(Vmin),0.0)
        self.VminN = self.VminP
        
    def setSteps(self, steps):
        self.steps = steps

    def interruptibleSleep(self, seconds, condition=False):
        t0=time.time()
        while (time.time()-t0 < self.interSweepDelay):
            if self.stopRequested or condition:
                break
            self.msleep(10)


    def run(self):
        self.stopRequested = False
        print "Thread running"
        daqRes = 20./65535.
        bipolarToggle = 1.

        try:
            while not self.stopRequested:
                self.ao.setDcDrive(0)
                self.interruptibleSleep(10.*self.interSweepDelay)
                Vo = self.ai.measureDc()
                print "Offset voltage Vo=", Vo
                if bipolarToggle < 0:
                    Vmax = self.VmaxN
                    Vmin = self.VminN
                else:
                    Vmax = self.VmaxP
                    Vmin = self.VminP
                    
                maxSteps = int((Vmax-Vmin)/daqRes)
                steps = min(self.steps, maxSteps)
                voltages = np.linspace(Vmin, Vmax, steps)
                if self.reverseSweep:
                    voltages = np.append(voltages, voltages[::-1])
                print "Bipolar toggle:", bipolarToggle
                voltages *= bipolarToggle
                self.ao.setDcDrive(voltages[0])
                self.interruptibleSleep(self.interSweepDelay)
                Vmeas = []
                print "Starting sweep from %f to %f V (%d steps)" % (Vmin*bipolarToggle, Vmax*bipolarToggle, steps)
    
                for Vsource in voltages:
                    self.ao.setDcDrive(Vsource)
                    t = time.time()
                    V = self.ai.measureDc()
                    Vmeas.append(V)
                    if len(Vmeas) == 30:
                        fit = np.polyfit(voltages[10:30], Vmeas[10:30], 1)
                        slope = fit[0]
                        offset = fit[1]
                        print "Slope, offset:", slope, offset
                        
                    self.readingAvailable.emit(t,Vsource,V,Vo, self.T)
                    while(self.paused):
                        self.msleep(100)
                    if self.stopRequested:
                        break
                if np.sign(slope) == np.sign(bipolarToggle):
                    iCrit = np.argmax(Vmeas)
                else:
                    iCrit = np.argmin(Vmeas)
                Vcrit = voltages[iCrit]
                Icrit = Vmeas[iCrit] # Not really a current...
                print "iCrit, Vcrit, Icrit:", iCrit, Vcrit, 'V', Icrit, 'V'
                    
                self.ao.setDcDrive(0)
                print "Sweep complete"
                self.sweepComplete.emit(self.T, Icrit)
                    
                if self.adaptiveSweep:
                    Vmin = self.adaptiveLower*abs(Vcrit)
                    Vmax = self.adaptiveUpper*abs(Vcrit)
                    if Vcrit < 0:
                        self.VminN = Vmin
                        self.VmaxN = Vmax
                    else:
                        self.VminP = Vmin
                        self.VmaxP = Vmax

                if self.bipolar:
                    bipolarToggle = -bipolarToggle
    
                if self.stopRequested:
                    break
        except Exception,e:
            print "Exception:", e

        print "Thread finished"


from PyQt4.Qwt5 import Qwt, QwtPlotCurve, QwtPlot
from DAQ import PyDaqMx as daq
from PyQt4 import Qt

import pyqtgraph as pg

class TESIVSweepDaqWidget(TES_IVSweepsDaqUi.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(TESIVSweepDaqWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('TES IV Sweep (DAQ)')

        self.aoDeviceCombo.currentIndexChanged.connect(self.updateDaqChannelsAo)
        self.aiDeviceCombo.currentIndexChanged.connect(self.updateDaqChannelsAi)
        self.populateDaqCombos()
        self.restoreSettings()
        self.msmThread = None
        self.startPb.clicked.connect(self.startPbClicked)
        self.adrTemp = TemperatureSubscriber(self)
        self.adrTemp.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.adrTemp.start()
        self.plotRaw = pg.PlotWidget(title='IV sweeps')
        self.plotLayout.addWidget(self.plotRaw)
        self.curveRaw = pg.PlotCurveItem()
        self.plotRaw.addItem(self.curveRaw)
        
        self.plotCritical = pg.PlotWidget(title='Critical current')
        self.plotLayout.addWidget(self.plotCritical)

        self.plotCritical.addLegend()
        self.criticalCurve1 = pg.PlotCurveItem(name='+', symbol='o', pen='r')
        self.plotCritical.addItem(self.criticalCurve1)

        self.criticalCurve2 = pg.PlotCurveItem(name='o', symbol='o', pen='b')
        self.plotCritical.addItem(self.criticalCurve2)
        
        self.plotRaw.setLabel('bottom', 'Vbias', 'V')
        self.plotRaw.setLabel('left', 'I_TES', 'uA')

        self.plotCritical.setLabel('left', 'I_C', 'uA')
        
        self.clearData()
        self.clearCriticalData()
        
        self.clearPb.clicked.connect(self.clearData)
        self.coilSweepCb.toggled.connect(self.toggleCoilSweep)
        self.clearCriticalPb.clicked.connect(self.clearCriticalData)
        self.samplesPerPointSb.valueChanged.connect(lambda value: self.discardSamplesSb.setMaximum(value-1))
        self.coilEnableCb.toggled.connect(self.toggleCoil)
        self.coilVoltageSb.valueChanged.connect(self.updateCoilVoltage)
        self.toggleCoil(self.coilEnableCb.isChecked())
        self.coilDriverCombo.currentIndexChanged.connect(self.coilDriverChanged)
        self.Vcoil = np.nan

    def coilDriverChanged(self):
        text = self.coilDriverCombo.currentText()
        self.coilVisaLabel.setText('%s VISA' % text)
        self.coilVisaCombo.clear()
        if text == 'SR830':
            suffix = ' V'
            maxDrive = 10
            self.coilDriveLabel.setText('Voltage')
            self.coilVisaCombo.addItem('GPIB0::12')
            self.auxOutChannelSb.setEnabled(True)

        elif text == 'Keithley 6430':
            suffix = ' mA'
            maxDrive = 10
            self.coilDriveLabel.setText('Current')
            self.coilVisaCombo.addItem('GPIB0::24')
            self.auxOutChannelSb.setEnabled(False)

        controls = [self.coilVoltageSb, self.coilSweepMinSb, self.coilSweepMaxSb]
        for control in controls:
            control.setSuffix(suffix)
            control.setMinimum(-maxDrive)
            control.setMaximum(+maxDrive)

    def toggleCoil(self, enabled):
        self.coilDriverCombo.setEnabled(not enabled)
        if enabled:
            drive = self.coilDriverCombo.currentText()
            if drive == 'SR830':
                self.sr830 = SR830(str(self.coilVisaCombo.currentText()))
                self.coilAo = VoltageSourceSR830(self.sr830, self.auxOutChannelSb.value())
            elif drive == 'Keithley 6430':
                self.coilAo = CurrentSourceKeithley(str(self.coilVisaCombo.currentText()), currentRange=10E-3, complianceVoltage=60)
            self.Vcoil = self.coilAo.dcDrive()
            self.coilVoltageSb.setValue(self.Vcoil)
            self.auxOutChannelSb.setEnabled(False)
            self.coilVisaCombo.setEnabled(False)
        else:
            self.coilAo = None
            self.auxOutChannelSb.setEnabled(True)
            self.coilVisaCombo.setEnabled(True)

    def updateCoilVoltage(self, V):
        if self.coilAo is not None:
            self.coilAo.setDcDrive(V)
            self.Vcoil = self.coilAo.dcDrive()

    def updateDaqChannelsAi(self):
        dev = str(self.aiDeviceCombo.currentText())
        self.aiChannelCombo.clear()
        if len(dev):
            device = daq.Device(dev)
            aiChannels = device.findAiChannels()
            for channel in aiChannels:
                self.aiChannelCombo.addItem(channel)

    def updateDaqChannelsAo(self):
        dev = str(self.aoDeviceCombo.currentText())
        self.aoChannelCombo.clear()
        if len(dev):
            device = daq.Device(dev)
            aoChannels = device.findAoChannels()
            for channel in aoChannels:
                self.aoChannelCombo.addItem(channel)

    def populateDaqCombos(self):
        system = daq.System()
        devices = system.findDevices()
        for devName in devices:
            dev = daq.Device(devName)
            if len(dev.findAiChannels()):
                self.aiDeviceCombo.addItem(devName)
            if len(dev.findAoChannels()):
                self.aoDeviceCombo.addItem(devName)

    def clearData(self):
        self.Vdrive = []
        self.Vmeas = []
        self.curveRaw.setData(self.Vdrive, self.Vmeas)

    def clearCriticalData(self):
        self.Vcrit1 = []
        self.Vcrit2 = []
        self.Tcrit1 = []
        self.Tcrit2 = []
        self.VcoilCrit1 = []
        self.VcoilCrit2 = []
        self.updateCriticalPlot()

    def updateRawData(self, t,Vsource,Vmeas, Vo, T):
        string = "%.3f\t%.6f\t%.6f\t%.6f\t%.6f\t%.3f\n" % (t, Vsource, Vmeas, Vo, T, self.Vcoil)
        self.outputFile.write(string)
        self.Vdrive.append(Vsource)
        self.Vmeas.append(Vmeas)
        maxLength = 10000
        if len(self.Vdrive) > int(maxLength*1.1): # Automatically expire old data
            self.Vdrive = self.Vdrive[-maxLength:]
            self.Vmeas = self.Vmeas[-maxLength:]
        self.curveRaw.setData(self.Vdrive, self.Vmeas, connect='finite')

    def toggleCoilSweep(self, checked):
        if checked:
            self.coilVoltages = np.linspace(self.coilSweepMinSb.value(), self.coilSweepMaxSb.value(), self.coilSweepStepsSb.value())
            self.coilVoltages = np.append(self.coilVoltages, self.coilVoltages[::-1])
            self.currentCoilStep = 0
            self.stepCoil()
        else:
            self.coilVoltages = []
            self.currentCoilStep = 0

    def stepCoil(self):
        if self.coilAo is not None:
            self.coilVoltageSb.setValue(self.coilVoltages[self.currentCoilStep])
        self.currentCoilStep += 1
        if self.currentCoilStep >= len(self.coilVoltages): # Start over
            self.currentCoilStep = 0

    def collectSweep(self, T, Vc):
        self.updateRawData(0, np.nan, np.nan, np.nan, np.nan)
        
        if Vc >= 0:
            self.Tcrit1.append(T)
            self.Vcrit1.append(Vc)
            self.VcoilCrit1.append(self.Vcoil)
        else:
            self.Tcrit2.append(T)
            self.Vcrit2.append(-Vc)
            self.VcoilCrit2.append(self.Vcoil)
        self.updateCriticalPlot()

        if self.coilSweepCb.isChecked(): # Move on to next coil voltage
            if self.bipolarCb.isChecked():
                if not len(self.Tcrit2) == len(self.Tcrit1):
                    print "Still need to do negative"
                    return
            self.stepCoil()

    def updateCriticalPlot(self):
        xAxis = self.plotAxisCombo.currentText()
        if xAxis == 'T':
            x1 = self.Tcrit1
            x2 = self.Tcrit2
            self.plotCritical.setLabel('bottom', 'T', 'K')
        elif xAxis == 'Coil V':
            x1 = self.VcoilCrit1
            x2 = self.VcoilCrit2
            self.plotCritical.setLabel('bottom', 'Coil', 'V/A')
        self.criticalCurve1.setData(x1, self.Vcrit1)
        self.criticalCurve2.setData(x2, self.Vcrit2)
        #self.criticalPlot.replot()
        # -1/3.256 +1/2.823
        
    def startPbClicked(self):
        timeString = time.strftime('%Y%m%d-%H%M%S')
        fileName = self.sampleLineEdit.text()+'_%s_IV.dat' % timeString
        self.outputFile = open(fileName, 'a+')
        self.outputFile.write('#Program=TES_IVSweepsDaq.py\n')
        self.outputFile.write('#Date=%s\n' % timeString)
        self.outputFile.write('#Sample=%s\n' % self.sampleLineEdit.text())
        self.outputFile.write('#Source=%s\n' % self.sourceCombo.currentText())
        self.outputFile.write('#Pre-amp gain=%.5g\n' % self.preampGainSb.value())
        self.outputFile.write('#Drive impedance=%.6g\n' % self.dcDriveImpedanceSb.value())
        self.outputFile.write('#Inter-sweep delay=%d\n' % self.interSweepDelaySb.value())
        self.outputFile.write('#Samples per point=%d\n' % self.samplesPerPointSb.value())
        self.outputFile.write('#Discard samples=%d\n' % self.discardSamplesSb.value())
        #self.outputFile.write('#Threshold=%.5g\n' % self.thresholdVoltageSb.value())
        self.outputFile.write('#Bipolar=%d\n' % int(self.bipolarCb.isChecked()))
        self.outputFile.write('#ReverseSweep=%d\n' % int(self.reverseSweepCb.isChecked()))
        if self.coilAo is not None:
            self.outputFile.write('#Coil enabled=1\n')
            self.outputFile.write('#Coil driver=%s\n' % self.coilAo.name())
            self.outputFile.write('#Coil drive=%.3g\n' % self.coilAo.dcDrive())
        else:
            self.outputFile.write('#Coil enabled=0\n')
        if self.coilSweepCb.isChecked():
            self.outputFile.write('#Coil sweep=1\n')
            self.outputFile.write('#Coil min=%.3f\n' % self.coilSweepMinSb.value())
            self.outputFile.write('#Coil max=%.3f\n' % self.coilSweepMaxSb.value())
            self.outputFile.write('#Coil steps=%d\n' % self.coilSweepStepsSb.value())
        else:
            self.outputFile.write('#Coil sweep=0\n')

        self.ao = VoltageSourceDaq(str(self.aoDeviceCombo.currentText()), str(self.aoChannelCombo.currentText()))
        self.ai = VoltmeterDaq(str(self.aiDeviceCombo.currentText()), str(self.aiChannelCombo.currentText()), -10, 10, samples=self.samplesPerPointSb.value(), drop=self.discardSamplesSb.value())
        self.msmThread = IVSweepMeasurement(self.ao, self.ai, self)
        self.msmThread.setFileName(fileName)
        self.msmThread.readingAvailable.connect(self.updateRawData)
        self.msmThread.setMinimumVoltage(self.startVSb.value())
        self.msmThread.setMaximumVoltage(self.stopVSb.value())
        self.msmThread.setSteps(self.stepsSb.value())
        self.msmThread.setInterSweepDelay(self.interSweepDelaySb.value())
        self.msmThread.sweepComplete.connect(self.collectSweep)
        self.msmThread.enableBipolar(self.bipolarCb.isChecked())
        self.msmThread.enableReverseSweep(self.reverseSweepCb.isChecked())
        self.msmThread.setAdaptiveLower(1E-2*self.adaptiveLowerSb.value())
        self.msmThread.setAdaptiveUpper(1E-2*self.adaptiveUpperSb.value())
        self.msmThread.enableAdaptiveSweep(self.adaptiveSweepingGroupBox.isChecked())
        self.adrTemp.adrTemperatureReceived.connect(self.msmThread.updateTemperature)
        self.msmThread.finished.connect(self.finished)
        self.stopPb.clicked.connect(self.msmThread.stop)
        self.reverseSweepCb.toggled.connect(self.msmThread.enableReverseSweep)
        self.adaptiveLowerSb.valueChanged.connect(lambda x:self.msmThread.setAdaptiveLower(1E-2*x))
        self.adaptiveUpperSb.valueChanged.connect(lambda x:self.msmThread.setAdaptiveUpper(1E-2*x))
        self.adaptiveSweepingGroupBox.toggled.connect(self.msmThread.enableAdaptiveSweep)
        
        #self.thresholdVoltageSb.valueChanged.connect(self.msmThread.setThreshold)
        self.outputFile.write('#'+'\t'.join(['time', 'Vdrive', 'Vmeas', 'Vo', 'T', 'Vcoil' ])+'\n')
        self.enableWidgets(False)
        self.msmThread.start()
        print "Thread started"

    def finished(self):
        self.ai.clear()
        self.ao.clear()
        self.outputFile.close()
        self.enableWidgets(True)
        self.msmThread.deleteLater()
#        self.updateStatus('Completed')

    def enableWidgets(self, enable=True):
        self.sampleLineEdit.setEnabled(enable)
        self.startPb.setEnabled(enable)
        self.dcDriveImpedanceSb.setEnabled(enable)
        self.aiChannelCombo.setEnabled(enable)
        self.aiDeviceCombo.setEnabled(enable)
        self.aoChannelCombo.setEnabled(enable)
        self.aoDeviceCombo.setEnabled(enable)
        self.startVSb.setEnabled(enable)
        self.stopVSb.setEnabled(enable)
        self.stepsSb.setEnabled(enable)
        self.interSweepDelaySb.setEnabled(enable)
        self.bipolarCb.setEnabled(enable)

        self.stopPb.setEnabled(not enable)

    def closeEvent(self, e):
        if self.msmThread:
            self.msmThread.stop()
        if self.adrTemp:
            self.adrTemp.stop()
        self.saveSettings()
        super(TESIVSweepDaqWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
        print "Saving settings"
        s.setValue('sampleId', self.sampleLineEdit.text())
        s.setValue('dcDriveImpedance', self.dcDriveImpedanceSb.value() )
        s.setValue('bipolar', self.bipolarCb.isChecked())
        s.setValue('startV', self.startVSb.value())
        s.setValue('stopV', self.stopVSb.value())
        s.setValue('steps', self.stepsSb.value())
        s.setValue('interSweepDelay', self.interSweepDelaySb.value())
        s.setValue('samplesPerPoint', self.samplesPerPointSb.value())
        s.setValue('discardSamples', self.discardSamplesSb.value())

        s.setValue('preampGain', self.preampGainSb.value())
        s.setValue('geometry', self.saveGeometry())
        s.setValue('AI_Device', self.aiDeviceCombo.currentText())
        s.setValue('AO_Device', self.aoDeviceCombo.currentText())
        s.setValue('AI_Channel', self.aiChannelCombo.currentText())
        s.setValue('AO_Channel', self.aoChannelCombo.currentText())
        s.setValue('SourceType', self.sourceCombo.currentText())
        s.setValue('CoilDriver', self.coilDriverCombo.currentText())
        s.setValue('coilVisa', self.coilVisaCombo.currentText())
        s.setValue('CoilAuxOut', self.auxOutChannelSb.value())
        s.setValue('CoilVoltage', self.coilVoltageSb.value())
        s.setValue('CoilSweepEnable', self.coilSweepCb.isChecked())
        s.setValue('CoilSweepSteps', self.coilSweepStepsSb.value())
        s.setValue('CoilSweepMin', self.coilSweepMinSb.value())
        s.setValue('CoilSweepMax', self.coilSweepMaxSb.value())
        s.setValue('adaptiveLower', self.adaptiveLowerSb.value())
        s.setValue('adaptiveUpper', self.adaptiveUpperSb.value())
        s.setValue('adaptiveSweep', self.adaptiveSweepingGroupBox.isChecked())

    def restoreSettings(self):
        s = QSettings()
        print "Restoring settings"
        
        self.sampleLineEdit.setText(s.value('sampleId', '', type=QString))
        self.dcDriveImpedanceSb.setValue(s.value('dcDriveImpedance', 10E3, type=float))
        self.bipolarCb.setChecked(s.value('bipolar', False, type=bool))
        self.startVSb.setValue(s.value('startV', 0, type=float))
        self.stopVSb.setValue(s.value('stopV', 3, type=float))
        self.stepsSb.setValue(s.value('steps', 10, type=int))
        self.preampGainSb.setValue(s.value('preampGain', 1., type=float))
        self.interSweepDelaySb.setValue(s.value('interSweepDelay', 0.5, type=float))
        self.samplesPerPointSb.setValue(s.value('samplesPerPoint', 1, type=int))
        self.discardSamplesSb.setValue(s.value('discardSamples', 0, type=int))
        self.aiDeviceCombo.setCurrentIndex(self.aiDeviceCombo.findText(s.value('AI_Device', '', type=str)))
        self.aoDeviceCombo.setCurrentIndex(self.aoDeviceCombo.findText(s.value('AO_Device', '', type=str)))
        self.aiChannelCombo.setCurrentIndex(self.aiChannelCombo.findText(s.value('AI_Channel', '', type=str)))
        self.aoChannelCombo.setCurrentIndex(self.aoChannelCombo.findText(s.value('AO_Channel', '', type=str)))
        self.sourceCombo.setCurrentIndex(self.sourceCombo.findText(s.value('SourceType', '', type=str)))
        self.coilDriverCombo.setCurrentIndex(self.coilDriverCombo.findText(s.value('CoilDriver', '', type=str)))
        self.coilVisaCombo.setCurrentIndex(self.coilVisaCombo.findText(s.value('coilVisa', '', type=str)))
        self.auxOutChannelSb.setValue(s.value('CoilAuxOut', 1, type=int))
        self.coilVoltageSb.setValue(s.value('CoilVoltage', 0.0, type=float))
        self.coilSweepMinSb.setValue(s.value('CoilSweepMin', -1, type=float))
        self.coilSweepMaxSb.setValue(s.value('CoilSweepMax', 1, type=float))
        self.coilSweepStepsSb.setValue(s.value('CoilSweepSteps', 21, type=float))
        self.coilSweepCb.setChecked(s.value('CoilSweepEnable', True, type=bool))
        self.adaptiveLowerSb.setValue(s.value('adaptiveLower', 75, type=int))
        self.adaptiveUpperSb.setValue(s.value('adaptiveUpper', 130, type=int))
        self.adaptiveSweepingGroupBox.setChecked(s.value('adaptiveSweep', True, type=bool))
        geometry = s.value('geometry', QByteArray(), type=QByteArray)
        self.restoreGeometry(geometry)

def runIvSweepsDaq():
    import sys
    import logging
    from Utility.Utility import ExceptionHandler

    logging.basicConfig(level=logging.WARNING)

    exceptionHandler = ExceptionHandler()
    sys._excepthook = sys.excepthook
    sys.excepthook = exceptionHandler.handler


    from PyQt4.QtGui import QApplication
    #from PyQt4.QtCore import QTimer

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('TES_IVSweepDaq')

    mw = TESIVSweepDaqWidget()
    mw.show()
    app.exec_()


if __name__ == '__main__':
#    from Visa.Keithley6430 import Keithley6430
#    k = Keithley6430('GPIB0::24')
#    print "present:", k.checkPresence()    
#    k.setComplianceVoltage(60)
#    print "Compliance voltage:", k.complianceVoltage()
    runIvSweepsDaq()
#    ao = AnalogOutDaq('USB6002','ao1')
#    ao.setDcDrive(0)

# -*- coding: utf-8 -*-
"""
Collect IV curves by sweeping DAQ output and reading DAQ input. Detect superconducting to normal transition and disable bias.
Created on Thu Jun 25 17:15:17 2015

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""


from PyQt4.QtGui import QWidget #, QDoubleSpinBox, QSpinBox, QHeaderView
from PyQt4.QtCore import pyqtSignal, QThread, QSettings, QString, QByteArray #, QObject

import IVSweepsDaqUi
import time
from Zmq.Subscribers import HousekeepingSubscriber
import numpy as np

from Visa.SR830 import SR830

from AnalogSource import  VoltageSourceSR830, VoltageSourceDaq, CurrentSourceKeithley
from AnalogMeter import VoltmeterDaq
#from Visa.Keithley6430 import Keithley6430

import h5py as hdf

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

    def setFileName(self, fileName):
        self.fileName = fileName

    def setVoltages(self, voltages):
        self.voltages = voltages

    def enableBipolar(self, enable=True):
        self.bipolar = enable

    def setThreshold(self, threshold):
        self.threshold = threshold

    def setInterSweepDelay(self, delay):
        self.interSweepDelay = int(delay)

    def stop(self):
        self.stopRequested = True

    def pause(self, pause=True):
        self.paused = pause

    def unpause(self):
        self.pause(False)

    def updateTemperature(self, T):
        self.T = T

    def setMaximumVoltage(self, Vmax):
        self.Vmax = min(Vmax,10.)

    def setMinimumVoltage(self, Vmin):
        self.Vmin = max(Vmin,0.0)

    def setSteps(self, steps):
        self.steps = steps

    def interruptibleSleep(self, seconds, condition=False):
        t0=time.time()
        while (time.time()-t0 < self.interSweepDelay):
            if self.stopRequested or condition:
                break
            self.sleep(1)


    def run(self):
        self.stopRequested = False
        print "Thread running"
        daqRes = 20./65535.
        bipolarToggle = 1.

        try:
            while not self.stopRequested:
                self.ao.setDcDrive(0)
                Vo = self.ai.measureDc()
                print "Vo", Vo
                maxSteps = int(3.*(self.Vmax-self.Vmin)/daqRes)
                voltages = np.linspace(self.Vmin, self.Vmax, min(self.steps, maxSteps))
                voltages = np.append(voltages, voltages[::-1])
                print "Bipolar toggle:", bipolarToggle
                voltages *= bipolarToggle
                #print "voltages", voltages
                self.ao.setDcDrive(voltages[0])
                self.sleep(1)
                Vmeas = []
                print "Starting sweep"
    
                normal = False
                for Vsource in voltages:
                    #print "Vsource =", Vsource
                    self.ao.setDcDrive(Vsource)
                    self.msleep(5)
                    t = time.time()
                    V = self.ai.measureDc()
                    #print "V=", V
                    Vmeas.append(V)
                    self.readingAvailable.emit(t,Vsource,V,Vo, self.T)
                    if abs(V-Vo) > self.threshold:
                        print "Threshold reached, breaking out"
                        normal = True
                        break
                    while(self.paused):
                        self.msleep(100)
                    if self.stopRequested:
                        break
                if normal:
                    pass
                    #self.setMaximumVoltage(abs(Vsource)*1.5)
                    self.setMinimumVoltage(0)
                    #self.setMinimumVoltage(Vsource/1.5-0.1)
                else:
                    self.setMaximumVoltage(5.0)
                    self.setMinimumVoltage(0.0)
                self.ao.setDcDrive(0)
                print "Sweep complete"
                self.sweepComplete.emit(self.T, Vsource)
                self.interruptibleSleep(self.interSweepDelay)
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

class IVSweepDaqWidget(IVSweepsDaqUi.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(IVSweepDaqWidget, self).__init__(parent)
        self.setupUi(self)

        self.aoDeviceCombo.currentIndexChanged.connect(self.updateDaqChannelsAo)
        self.aiDeviceCombo.currentIndexChanged.connect(self.updateDaqChannelsAi)
        self.populateDaqCombos()
        self.restoreSettings()
        self.msmThread = None
        self.startPb.clicked.connect(self.startPbClicked)
        self.hkSub = HousekeepingSubscriber(self)
        self.hkSub.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.hkSub.start()
        self.rawPlot.setAxisTitle(QwtPlot.yLeft, 'Vmeas')
        self.rawPlot.setAxisTitle(QwtPlot.xBottom, 'Vdrive')
        self.rawCurve = QwtPlotCurve('')
        self.rawCurve.attach(self.rawPlot)
        self.criticalCurve1 = QwtPlotCurve('+')
        self.criticalCurve1.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Cross, Qt.QBrush(), Qt.QPen(Qt.Qt.red), Qt.QSize(5, 5)))
        self.criticalCurve1.attach(self.criticalPlot)
        self.criticalCurve2 = QwtPlotCurve('-')
        self.criticalCurve2.setSymbol(Qwt.QwtSymbol(Qwt.QwtSymbol.Cross, Qt.QBrush(), Qt.QPen(Qt.Qt.blue), Qt.QSize(5, 5)))
        self.criticalCurve2.attach(self.criticalPlot)
        self.criticalPlot.setAxisTitle(QwtPlot.yLeft, 'Vcrit')
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
            self.coilVisaCombo.addItem('GPIB0::12')
            self.auxOutChannelSb.setEnabled(True)

        elif text == 'Keithley 6430':
            suffix = ' mA'
            maxDrive = 50
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
            driver = self.coilDriverCombo.currentText()
            if driver == 'SR830':
                self.sr830 = SR830(str(self.coilVisaCombo.currentText()))
                self.coilAo = VoltageSourceSR830(self.sr830, self.auxOutChannelSb.value())
            elif driver == 'Keithley 6430':
                self.coilAo = CurrentSourceKeithley(str(self.coilVisaCombo.currentText()), currentRange=10E-3)
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
        self.rawCurve.setData(self.Vdrive, self.Vmeas)
        self.rawPlot.replot()

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
        self.Vmeas.append(Vmeas-Vo)
        maxLength = 10000
        if len(self.Vdrive) > int(maxLength*1.1): # Automatically expire old data
            self.Vdrive = self.Vdrive[-maxLength:]
            self.Vmeas = self.Vmeas[-maxLength:]
        self.rawCurve.setData(self.Vdrive, self.Vmeas)
        self.rawPlot.replot()

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
            self.criticalPlot.setAxisTitle(QwtPlot.xBottom, 'T')
        elif xAxis == 'Coil V':
            x1 = self.VcoilCrit1
            x2 = self.VcoilCrit2
            self.criticalPlot.setAxisTitle(QwtPlot.xBottom, 'Coil V')
        self.criticalCurve1.setData(x1, self.Vcrit1)
        self.criticalCurve2.setData(x2, self.Vcrit2)
        self.criticalPlot.replot()

    def startPbClicked(self):
        timeString = time.strftime('%Y%m%d-%H%M%S')
        fileName = self.sampleLineEdit.text()+'_%s_IV.dat' % timeString
        self.outputFile = open(fileName, 'a+')
        self.outputFile.write('#Program=IVSweepsDaq.py\n')
        self.outputFile.write('#Date=%s\n' % timeString)
        self.outputFile.write('#Sample=%s\n' % self.sampleLineEdit.text())
        self.outputFile.write('#Source=%s\n' % self.sourceCombo.currentText())
        self.outputFile.write('#Pre-amp gain=%.5g\n' % self.preampGainSb.value())
        self.outputFile.write('#Drive impedance=%.6g\n' % self.dcDriveImpedanceSb.value())
        self.outputFile.write('#Inter-sweep delay=%d\n' % self.interSweepDelaySb.value())
        self.outputFile.write('#Samples per point=%d\n' % self.samplesPerPointSb.value())
        self.outputFile.write('#Discard samples=%d\n' % self.discardSamplesSb.value())
        self.outputFile.write('#Threshold=%.5g\n' % self.thresholdVoltageSb.value())
        self.outputFile.write('#Bipolar=%d\n' % int(self.bipolarCb.isChecked()))
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
        self.msmThread.setThreshold(self.thresholdVoltageSb.value())
        self.msmThread.readingAvailable.connect(self.updateRawData)
        self.msmThread.setMinimumVoltage(self.startVSb.value())
        self.msmThread.setMaximumVoltage(self.stopVSb.value())
        self.msmThread.setSteps(self.stepsSb.value())
        self.msmThread.setInterSweepDelay(self.interSweepDelaySb.value())
        self.msmThread.sweepComplete.connect(self.collectSweep)
        self.msmThread.enableBipolar(self.bipolarCb.isChecked())
        self.hkSub.adrTemperatureReceived.connect(self.msmThread.updateTemperature)
        self.msmThread.finished.connect(self.finished)
        self.stopPb.clicked.connect(self.msmThread.stop)
        self.thresholdVoltageSb.valueChanged.connect(self.msmThread.setThreshold)
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
        if self.hkSub:
            self.hkSub.stop()
        self.saveSettings()
        super(IVSweepDaqWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
        s.setValue('sampleId', self.sampleLineEdit.text())
        s.setValue('dcDriveImpedance', self.dcDriveImpedanceSb.value() )
        s.setValue('bipolar', self.bipolarCb.isChecked())
        s.setValue('startV', self.startVSb.value())
        s.setValue('stopV', self.stopVSb.value())
        s.setValue('steps', self.stepsSb.value())
        s.setValue('interSweepDelay', self.interSweepDelaySb.value())
        s.setValue('thresholdVoltage', self.thresholdVoltageSb.value())
        s.setValue('samplesPerPoint', self.samplesPerPointSb.value())
        s.setValue('discardSamples', self.discardSamplesSb.value())

        s.setValue('preampGain', self.preampGainSb.value())
        s.setValue('geometry', self.saveGeometry())
        s.setValue('AI_Device', self.aiDeviceCombo.currentText())
        s.setValue('AO_Device', self.aoDeviceCombo.currentText())
        s.setValue('AI_Channel', self.aiChannelCombo.currentText())
        s.setValue('AO_Channel', self.aoChannelCombo.currentText())
        s.setValue('SourceType', self.sourceCombo.currentText())

        s.setValue('coilVisa', self.coilVisaCombo.currentText())
        s.setValue('CoilAuxOut', self.auxOutChannelSb.value())
        s.setValue('CoilVoltage', self.coilVoltageSb.value())

    def restoreSettings(self):
        s = QSettings()
        self.sampleLineEdit.setText(s.value('sampleId', '', type=QString))
        self.dcDriveImpedanceSb.setValue(s.value('dcDriveImpedance', 10E3, type=float))
        self.bipolarCb.setChecked(s.value('bipolar', False, type=bool))
        self.startVSb.setValue(s.value('startV', 0, type=float))
        self.stopVSb.setValue(s.value('stopV', 3, type=float))
        self.stepsSb.setValue(s.value('steps', 10, type=int))
        self.preampGainSb.setValue(s.value('preampGain', 1., type=float))
        self.interSweepDelaySb.setValue(s.value('interSweepDelay', 0, type=int))
        self.thresholdVoltageSb.setValue(s.value('thresholdVoltage', 0.010, type=float))
        self.samplesPerPointSb.setValue(s.value('samplesPerPoint', 1, type=int))
        self.discardSamplesSb.setValue(s.value('discardSamples', 0, type=int))
        self.aiDeviceCombo.setCurrentIndex(self.aiDeviceCombo.findText(s.value('AI_Device', '', type=str)))
        self.aoDeviceCombo.setCurrentIndex(self.aoDeviceCombo.findText(s.value('AO_Device', '', type=str)))
        self.aiChannelCombo.setCurrentIndex(self.aiChannelCombo.findText(s.value('AI_Channel', '', type=str)))
        self.aoChannelCombo.setCurrentIndex(self.aoChannelCombo.findText(s.value('AO_Channel', '', type=str)))
        self.sourceCombo.setCurrentIndex(self.sourceCombo.findText(s.value('SourceType', '', type=str)))
        self.coilVisaCombo.setCurrentIndex(self.coilVisaCombo.findText(s.value('coilVisa', '', type=str)))
        self.auxOutChannelSb.setValue(s.value('CoilAuxOut', 1, type=int))
        self.coilVoltageSb.setValue(s.value('CoilVoltage', 0.0, type=float))
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
    app.setApplicationName('IVSweepDaq')

    mw = IVSweepDaqWidget()
    mw.show()
    app.exec_()


if __name__ == '__main__':
    runIvSweepsDaq()
#    ao = AnalogOutDaq('USB6002','ao1')
#    ao.setDcDrive(0)

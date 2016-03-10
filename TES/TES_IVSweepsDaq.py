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

import h5py as hdf

def limit(x, xMin, xMax):
    return max(min(x, xMax), xMin)
    
import numpy as np

def determineCriticalCurrent(Vdrives, Vmeas):
    nPoints = len(Vdrives)
    ## First, lay out a linear fit starting from smallest Vdrive.
    ## Increase the linear fit span until we see a significant mean absolute
    ## deviation.
    
    stop = min(int(0.05*nPoints), 50)
    increment = int(0.5*stop)
    while stop<nPoints:
        x = Vdrives[:stop]; y = Vmeas[:stop]
        fit = np.polyfit(x, y, 1)
        #print "stop, fit", stop, fit
        sdev = np.sqrt(sum((y - np.polyval(fit, x))**2)/(len(y) - 1)) # Find the standard deviation
        stop2 = min(stop+increment, nPoints)
        nextX = Vdrives[stop:stop2]; nextY = Vmeas[stop:stop2]
        meanDeviation = np.mean(abs(nextY-np.polyval(fit, nextX)))
        if meanDeviation > 2.*sdev:
            break
        else:
            stop = stop2
            increment = int(1.2*increment)
            
    slope = fit[0]; offset = fit[1]
    print "Slope, offset:", slope, offset
    print "Uncertainty:", sdev

    ## Calculate the deviation of all datapoints from the linear fit
    delta = (np.polyval(fit, Vdrives)-Vmeas)
    #sdev = np.sqrt(sum((y - np.polyval(fit, x))**2)/(len(y) - 1)) # Find the standard deviation
    try:
        iOutside = np.where(delta*np.sign(slope)*np.sign(Vdrives)>2.5*sdev)[0]
        spans = clusterIndicesToSpans(iOutside, 2) 
        j = None
        for span in spans: # Find the first continuous span > 50 samples
            if span[1]-span[0] > 50:
                j = span[0]
                break
        if j is not None:
            Vc = Vdrives[j]; Ic = Vmeas[j]
            return Vc, Ic
        else:
            print "No cricital current found!"
            return np.nan, np.nan
    except:
        print "No cricital current found!"
        return np.nan, np.nan
            
def clusterIndicesToSpans(indices, maxDelta):
    clusters = []
    if len(indices) < 1:
        return
    z = indices[0]
    group = [z]
    i = 1
    while i < len(indices):
        znew = indices[i]
        if znew < z+maxDelta:
            group.append(znew)
        else:
            clusters.append((group[0], group[-1]))
            group = [znew]
        z = znew
        i += 1
    clusters.append((group[0], group[-1]))
    return clusters    
    
class IVSweepMeasurement(QThread):
    readingAvailable = pyqtSignal(float,float,float,float,float)
    
    sweepComplete = pyqtSignal(float, float, float, float, float, float, np.ndarray, np.ndarray, np.ndarray)
    '''T, Vo, VcDrive, VcMeas, tStart, tEnd, Vdrives, Vmeas'''
    
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
        self.VmaxP = limit(Vmax, 0, 10)
        self.VmaxN = -self.VmaxP

    def setMinimumVoltage(self, Vmin):
        self.VminP = limit(Vmin, 0, 10)
        self.VminN = -self.VminP
        
    def setPositiveRange(self, Vmin, Vmax):
        self.VmaxP = limit(Vmax, 0, 10)
        self.VminP = limit(Vmin, 0, Vmax)
        
    def setNegativeRange(self, Vmin, Vmax):
        self.VmaxN = -limit(Vmax, 0, 10)
        self.VminN = -limit(Vmin, 0, Vmax)
        
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
        VcritOldP = None        # Keep track of positive and negative critical drive for adaptive sweeping
        VcritOldN = None        
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
                    
                maxSteps = int(abs(Vmax-Vmin)/daqRes)
                steps = min(self.steps, maxSteps)
                Vdrives = np.linspace(Vmin, Vmax, steps)
                if self.reverseSweep:
                    Vdrives = np.append(Vdrives, Vdrives[::-1])
                self.ao.setDcDrive(Vdrives[0])
                self.interruptibleSleep(self.interSweepDelay)
                Vmeas = []
                print "Starting sweep from %f to %f V (%d steps)" % (Vmin, Vmax, steps)
    
                ts = np.ones_like(Vdrives)*np.nan
                Vmeas = np.ones_like(Vdrives)*np.nan
                
                for i, Vdrive in enumerate(Vdrives):
                    self.ao.setDcDrive(Vdrive)
                    t = time.time()
                    V = self.ai.measureDc()
                    Vmeas[i] = V
                    ts[i] = t
                    self.readingAvailable.emit(t,Vdrive,V,Vo, self.T)
                    if self.stopRequested:
                        break
                    
                Vcrit, Icrit = determineCriticalCurrent(Vdrives, Vmeas)
                print "Vcrit, Icrit", Vcrit, Icrit
                #Vcrit = bipolarToggle; Icrit = bipolarToggle
#                if np.sign(slope) == np.sign(bipolarToggle):
#                    iCrit = np.argmax(Vmeas)
#                else:
#                    iCrit = np.argmin(Vmeas)
#                Vcrit = Vdrives[iCrit]
#                Icrit = Vmeas[iCrit] # Not really a current...
                #print "iCrit, Vcrit, Icrit:", iCrit, Vcrit, 'V', Icrit, 'V'
                    
                self.ao.setDcDrive(0)
                print "Sweep complete"
                '''T, VcDrive, VcMeas, tStart, tEnd, Vdrives, Vmeas'''
                self.sweepComplete.emit(self.T, Vo, Vcrit, Icrit, ts[0], ts[-1], np.asarray(Vdrives, dtype=np.float32), np.asarray(Vmeas, dtype=np.float32), np.asarray(ts, dtype=np.float))
                    
                if self.adaptiveSweep and not np.isnan(Vcrit):
                    Vmin = self.adaptiveLower*abs(Vcrit)
                    Vmax = self.adaptiveUpper*abs(Vcrit)
                    if Vcrit < 0:
                        if VcritOldN is not None:
                            error = abs(Vcrit-VcritOldN) / VcritOldN
                        else:
                            error = 0
                        if error < 0.25:
                            VcritOldN = Vcrit
                            self.setNegativeRange(Vmin, Vmax)
                        else:
                            print "Rejected new negative critical drive because the error was too large:", error
                    else:
                        if VcritOldP is not None:
                            error = abs(Vcrit-VcritOldP) / VcritOldP
                        else:
                            error = 0
                        if error < 0.1:
                            VcritOldP = Vcrit
                            self.setPositiveRange(Vmin, Vmax)
                        else:
                            print "Rejected new positive critical drive because the error was too large:", error

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

#from LabWidgets.Utilities import saveWidgetToSettings, restoreWidgetsFromSettings

class TESIVSweepDaqWidget(TES_IVSweepsDaqUi.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(TESIVSweepDaqWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('TES IV Sweep (DAQ)')

        self.aoDeviceCombo.currentIndexChanged.connect(self.updateDaqChannelsAo)
        self.aiDeviceCombo.currentIndexChanged.connect(self.updateDaqChannelsAi)
        self.populateDaqCombos()
        self.msmThread = None
        self.startPb.clicked.connect(self.startPbClicked)
        self.adrTemp = TemperatureSubscriber(self)
        self.adrTemp.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.adrTemp.adrResistanceReceived.connect(self.collectThermometerResistance)
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
        
        self.coilAo = None
        self.clearPb.clicked.connect(self.clearData)
        self.coilSweepCb.toggled.connect(self.toggleCoilSweep)
        self.clearCriticalPb.clicked.connect(self.clearCriticalData)
        self.samplesPerPointSb.valueChanged.connect(lambda value: self.discardSamplesSb.setMaximum(value-1))
        self.coilEnableCb.toggled.connect(self.toggleCoil)
        self.coilVoltageSb.valueChanged.connect(self.updateCoilVoltage)
#        self.toggleCoil(self.coilEnableCb.isChecked())
#        self.toggleCoilSweep(self.coilSweepCb.isChecked())
        self.coilDriverCombo.currentIndexChanged.connect(self.coilDriverChanged)
        self.Vcoil = np.nan
        self.restoreSettings()
        self.Rthermometers = []

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
                self.coilAo = CurrentSourceKeithley(str(self.coilVisaCombo.currentText()), currentRange=10.0E-3, complianceVoltage=20.0)
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
        self.VcritDrive1 = []
        self.VcritDrive2 = []
        self.VcritMeas1 = []
        self.VcritMeas2 = []
        self.Tcrit1 = []
        self.Tcrit2 = []
        self.VcoilCrit1 = []
        self.VcoilCrit2 = []
        self.updateCriticalPlot()

    def updateRawData(self, t,Vdrive,Vmeas, Vo, T):
        #string = "%.3f\t%.6f\t%.6f\t%.6f\t%.6f\t%.3f\n" % (t, Vdrive, Vmeas, Vo, T, self.Vcoil)
        #self.outputFile.write(string)
        self.Vdrive.append(Vdrive)
        self.Vmeas.append(Vmeas)
        maxLength = 10000
        if len(self.Vdrive) > int(maxLength*1.1): # Automatically expire old data
            self.Vdrive = self.Vdrive[-maxLength:]
            self.Vmeas = self.Vmeas[-maxLength:]
        self.curveRaw.setData(self.Vdrive, self.Vmeas, connect='finite')

    def toggleCoilSweep(self, checked):
        if checked:
            print "Making coil voltages"
            self.coilVoltages = np.linspace(self.coilSweepMinSb.value(), self.coilSweepMaxSb.value(), self.coilSweepStepsSb.value())
            if self.coilSweepReverseCb.isChecked():
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
            
    def collectThermometerResistance(self, R):
        self.Rthermometers.append(R)

    def collectSweep(self, T, Vo, VcDrive, VcMeas, tStart, tEnd, Vdrives, Vmeas, t):
        with hdf.File(self.hdfFileName, mode='a') as f:
            grp = f.create_group('Sweeps/%d' % self.sweepNumber)
            self.sweepNumber += 1
            grp.create_dataset('Vdrive', data=Vdrives, compression='gzip')
            grp.create_dataset('Vmeasured', data=Vmeas, compression='gzip')
            grp.create_dataset('t', data=t, compression='gzip')
            grp.attrs['tStart'] = tStart
            grp.attrs['tEnd'] = tEnd
            grp.attrs['Rthermometer'] = np.mean(self.Rthermometers)
            grp.attrs['Vcoil'] = self.Vcoil
            grp.attrs['T'] = T
            grp.attrs['VcritDrive'] = VcDrive
            grp.attrs['VcritMeas'] = VcMeas
            grp.attrs['Vo'] = Vo
        self.Rthermometers = []
            
        self.updateRawData(0, np.nan, np.nan, np.nan, np.nan)
        
        if np.max(VcDrive) >= 0:
            self.Tcrit1.append(T)
            self.VcritDrive1.append(VcDrive)
            self.VcritMeas1.append(VcMeas)
            self.VcoilCrit1.append(self.Vcoil)
        else:
            self.Tcrit2.append(T)
            self.VcritDrive2.append(-VcDrive)
            self.VcritMeas2.append(-VcMeas)
            self.VcoilCrit2.append(self.Vcoil)
        self.updateCriticalPlot()

        if self.coilSweepCb.isChecked(): # Move on to next coil voltage
            if self.bipolarCb.isChecked():
                if not len(self.Tcrit2) == len(self.Tcrit1):
                    print "len(Tcrit2), len(Tcrit1)", len(self.Tcrit2), len(self.Tcrit1)
                    print "Still need to do negative"
                    return
            self.stepCoil()

    def updateCriticalPlot(self):
        xAxis = self.plotXaxisCombo.currentText()
        if xAxis == 'T':
            x1 = self.Tcrit1
            x2 = self.Tcrit2
            self.plotCritical.setLabel('bottom', 'T', 'K')
        elif xAxis == 'Coil V':
            x1 = self.VcoilCrit1
            x2 = self.VcoilCrit2
            self.plotCritical.setLabel('bottom', 'Coil', 'V/A')
        
        yAxis = self.plotYaxisCombo.currentText()
        if yAxis == 'V_c':
            y1 = self.VcritDrive1
            y2 = self.VcritDrive2
        elif yAxis == 'I_c':
            y1 = self.VcritMeas1
            y2 = self.VcritMeas2
        self.criticalCurve1.setData(x1, y1)
        self.criticalCurve2.setData(x2, y2)
        #self.criticalPlot.replot()
        # -1/3.256 +1/2.823
        
    def writeHeader(self, item, value, hdfFile):
        #self.outputFile.write('#%s=%s\n' % (item, value))
        if isinstance(value, QString):
            value = str(value)
        hdfFile.attrs[item] = value
        
    def startPbClicked(self):
        timeString = time.strftime('%Y%m%d-%H%M%S')
        fileName = self.sampleLineEdit.text()+'_%s_IV.dat' % timeString
        self.sweepNumber = 0
#        self.outputFile = open(fileName, 'a+')
        self.hdfFileName = str(self.sampleLineEdit.text()+'_%s_IV.h5' % timeString)
        with hdf.File(self.hdfFileName, mode='w') as f:
            self.writeHeader('Program', 'TES_IVSweepsDaq.py', f)
            self.writeHeader('Date' , timeString, f)
            self.writeHeader('Sample', self.sampleLineEdit.text(), f)
            self.writeHeader('Source', self.sourceCombo.currentText(), f)
            self.writeHeader('Pre-amp gain', self.preampGainSb.value(), f)
            self.writeHeader('Drive impedance', self.dcDriveImpedanceSb.value(), f)
            self.writeHeader('Inter-sweep delay', self.interSweepDelaySb.value(), f)
            self.writeHeader('Samples per point', self.samplesPerPointSb.value(), f)
            self.writeHeader('Discard samples', self.discardSamplesSb.value(), f)
            #self.writeHeader('Threshold', self.thresholdVoltageSb.value(), f)
            self.writeHeader('Bipolar', int(self.bipolarCb.isChecked()), f)
            self.writeHeader('ReverseSweep', int(self.reverseSweepCb.isChecked()), f)
            if self.coilAo is not None:
                self.writeHeader('Coil enabled', 1, f)
                self.writeHeader('Coil driver', self.coilAo.name(), f)
                self.writeHeader('Coil drive', self.coilAo.dcDrive(), f)
            else:
                self.writeHeader('Coil enabled', 0, f)
            if self.coilSweepCb.isChecked():
                self.writeHeader('Coil sweep', 1, f)
                self.writeHeader('Coil min', self.coilSweepMinSb.value(), f)
                self.writeHeader('Coil max', self.coilSweepMaxSb.value(), f)
                self.writeHeader('Coil steps', self.coilSweepStepsSb.value(), f)
            else:
                self.writeHeader('Coil sweep', 0, f)

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
        #self.outputFile.write('#'+'\t'.join(['time', 'Vdrive', 'Vmeas', 'Vo', 'T', 'Vcoil' ])+'\n')
        self.enableWidgets(False)
        self.Rthermometers = []
        
        self.msmThread.start()
        print "Thread started"

    def finished(self):
        self.ai.clear()
        self.ao.clear()
        #self.outputFile.close()
        with hdf.File(self.hdfFileName, mode='a') as f:
            grp = f.create_group('Results/Positive')
            grp.create_dataset('Tcrit', data = self.Tcrit1)
            grp.create_dataset('VcritDrive', data = self.VcritDrive1)
            grp.create_dataset('Vcritmeas', data = self.VcritMeas1)
            grp.create_dataset('Vcoil', data = self.VcoilCrit1)
            grp = f.create_group('Results/Negative')
            grp.create_dataset('Tcrit', data = self.Tcrit2)
            grp.create_dataset('VcritDrive', data = self.VcritDrive2)
            grp.create_dataset('Vcritmeas', data = self.VcritMeas2)
            grp.create_dataset('Vcoil', data = self.VcoilCrit2)
        
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
        #widgets = [self.sampleLineEdit, self.dcDriveImpedanceSb, self.bipolarCb, self.startVSb]
        s = QSettings()
        print "Saving settings"
        s.setValue('sampleId', self.sampleLineEdit.text())
        s.setValue('dcDriveImpedance', self.dcDriveImpedanceSb.value() )
        s.setValue('bipolar', self.bipolarCb.isChecked())
        s.setValue('reverse', self.reverseSweepCb.isChecked())
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
        s.setValue('coilEnable', self.coilEnableCb.isChecked())
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
        self.reverseSweepCb.setChecked(s.value('reverse', False, type=bool))
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
        self.coilEnableCb.setChecked(s.value('coilEnable', False, type=bool))
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
    import faulthandler
    faultFile = open('TES_IVSweepsDaq_Faults.txt','a')
    faultFile.write('TES_IVSweepsDaq starting at %s\n' % time.time())
    faulthandler.enable(faultFile, all_threads=True)
    import sys
    import logging

    logging.basicConfig(level=logging.WARNING)

    #from Utility.Utility import ExceptionHandler
    #exceptionHandler = ExceptionHandler()
    #sys._excepthook = sys.excepthook
    #sys.excepthook = exceptionHandler.handler


    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('TES_IVSweepDaq')

    mw = TESIVSweepDaqWidget()
    mw.show()
    app.exec_()
    faulthandler.disable()
    faultFile.write('TES_IVSweepsDaq ending at %s' % time.time())
    faultFile.close() 

if __name__ == '__main__':
    runIvSweepsDaq()

#    from Visa.Keithley6430 import Keithley6430
#    k = Keithley6430('GPIB0::24')
#    print "present:", k.checkPresence()    
#    k.setComplianceVoltage(60)
#    print "Compliance voltage:", k.complianceVoltage()
#    ao = AnalogOutDaq('USB6002','ao1')
#    ao.setDcDrive(0)

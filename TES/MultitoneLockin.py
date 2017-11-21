# -*- coding: utf-8 -*-
"""
Record sine-sweep transfer functions using a single DAQ device with AO and AI.
Based on IvCurveDaq code
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from __future__ import division, print_function

OrganizationName = 'McCammon Astrophysics'
OrganizationDomain = 'wisp.physics.wisc.edu'
ApplicationName = 'MultitoneLockin'
Copyright = '(c) Felix T. Jaeckel <fxjaeckel@gmail.com'
Version = '0.1'

from LabWidgets.Utilities import compileUi, saveWidgetToSettings, restoreWidgetFromSettings, widgetValue
compileUi('MultiLockinUi')
import MultiLockinUi as ui 
from PyQt4.QtGui import QWidget, QMessageBox, QDoubleSpinBox, QSpinBox, QCheckBox, QHeaderView, QAbstractSpinBox, QAbstractButton, QLineEdit, QComboBox
from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QObject, pyqtSlot, QByteArray
from DecimateFast import DecimatorCascade

import DAQ.PyDaqMx as daq
from Utility.HdfStreamWriter import HdfStreamWriter
import h5py as hdf
import time
import numpy as np
import Queue
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import traceback
import warnings

from Zmq.Subscribers import TemperatureSubscriber


TwoPi = 2.*np.pi
rad2deg = 180./np.pi
deg2rad = np.pi/180.
dtype = np.float32

from Lockin import LockInMkl

class LockIns(QObject):
    chunkAnalyzed = pyqtSignal(int, float)
    resultsAvailable = pyqtSignal(float, float, float, float, float, list) # t, Vmin, Vmax, DC, rms, Zs
    def __init__(self, sampleRate, fRefs, phases, bws, lpfOrders, desiredChunkSize, parent=None):
        QObject.__init__(self, parent)
        self._lias = []
        assert len(fRefs) == len(phases)
        assert len(fRefs) == len(bws)
        self.nRefs = len(fRefs)
        self.nSamples = 0
        decimations = np.asarray(np.power(2, np.round(np.log2(sampleRate/(bws*40)))), dtype=int)
        decimations[decimations<1] = 1
        print("Decimations:",decimations)
        minChunkSize = np.max(decimations)
        print("Min chunk size:", minChunkSize)
        n = int(np.ceil(desiredChunkSize / minChunkSize))
        print("n:",n)
        self.chunkSize = int(n*minChunkSize)
        print("chunksize:",self.chunkSize)
        for i in range(self.nRefs):
            print('sampleRate, fRefs[i], phases[i], decimations[i], bws[i], lpfOrders[i], self.chunkSize', sampleRate, fRefs[i], phases[i], decimations[i], bws[i], lpfOrders[i], self.chunkSize )
            lia = LockInMkl(sampleRate, fRefs[i], phases[i], decimations[i], bws[i], lpfOrders[i], self.chunkSize, dtype=dtype)
            self._lias.append(lia)
        self.chunks = 0
    
    @pyqtSlot(np.ndarray, np.ndarray)
    def integrateData(self, data, stats):
        t = stats[0]        
        Vmin = stats[1]
        Vmax = stats[2]
        dc   = stats[3]
        rms  = stats[4]
        nNew = len(data)
        assert nNew == self.chunkSize
        Zs = []
        data = np.asarray(data, dtype=dtype) # May need conversion to float32 dtype
        for i,lia in enumerate(self._lias):
            Zs.append(lia.integrateData(data))
        self.nSamples += nNew
        self.chunks += 1
        self.chunkAnalyzed.emit(self.chunks, time.time())
        self.resultsAvailable.emit(t, Vmin, Vmax, dc, rms, Zs)

from MultitoneGenerator import MultitoneGeneratorMkl

class DaqThread(QThread):
    error = pyqtSignal(str)
    '''This signal is emitted when an error has been encountered during execution of the thread.'''
    dataReady = pyqtSignal(np.ndarray, np.ndarray)
    '''A new chunk of sampled data is ready.'''
    chunkProduced = pyqtSignal(int, float)
    '''A chunk of data has been written to the AO task. The argument specifies the number of chunks and the time when it was written to the buffer.'''
    inputOverload = pyqtSignal(int)
    '''An input overload has been detected on the AI data (for specified number of samples).'''
    
    def __init__(self, sampleRate, fs, amplitudes, phases, chunkSize, inputDecimation, parent=None):
        assert len(fs) == len(amplitudes)
        assert len(fs) == len(phases)
        self.sampleRate = sampleRate
        self.signals = []
        generator = MultitoneGeneratorMkl(sampleRate, chunkSize)
        for i in range(len(fs)):
            generator.addSineWave(fs[i], amplitudes[i], phases[i])
        self.generator = generator
        self.chunkSize = chunkSize
        QThread.__init__(self, parent)
        self.inputDecimation = inputDecimation
        
    def configureDaq(self, deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig):
        self.deviceName = deviceName
        self.aoChannel = aoChannel
        self.aoRange = aoRange
        self.aiChannel = aiChannel
        self.aiRange = aiRange
        self.aiTerminalConfig = aiTerminalConfig
        self.aiDriveChannel = None

    def stop(self):
        self.stopRequested = True

    def abort(self):
        self.stopRequested = True
        self.abortRequested = True
        
    def setAmplitude(self, i, A):
        self.generator.setAmplitude(i, A)
        
    def setOffset(self, Voff):
        self.generator.setOffset(Voff)
        
    def setRampRate(self, rate):
        rampRate = rate / self.sampleRate # Convert from V/s to V/sample
        self.generator.setRampRate(rampRate)

    def run(self):            
        self.stopRequested = False
        preLoads = 4
        try:
            print("Producer starting")
            d = daq.Device(self.deviceName)
            chunkSize = self.chunkSize
            timing = daq.Timing(rate = self.sampleRate, samplesPerChannel = chunkSize)
            timing.setSampleMode(timing.SampleMode.CONTINUOUS)

            aoChannel = daq.AoChannel('%s/%s' % (self.deviceName, self.aoChannel), self.aoRange.min, self.aoRange.max)
            aiChannel = daq.AiChannel('%s/%s' % (self.deviceName, self.aiChannel), self.aiRange.min, self.aiRange.max)
                
            aoTask = daq.AoTask('AO')
            aoTask.addChannel(aoChannel)
            aoTask.configureTiming(timing)
            aoTask.configureOutputBuffer((preLoads+2)*chunkSize)
            aoTask.disableRegeneration()
            if 'ai/StartTrigger' in d.findTerminals():
                aoTask.digitalEdgeStartTrigger('/%s/ai/StartTrigger' % self.deviceName) # The cheap USB DAQ doesn't support this?!
                print("Configured digital edge start trigger for aoTask")
            
            aiTask = daq.AiTask('AI')
            aiTask.addChannel(aiChannel)
            aiTask.configureInputBuffer(8*chunkSize)
            aiTask.configureTiming(timing)
            aiTask.commit()
            aoTask.commit()
            decimator = DecimatorCascade(self.inputDecimation, self.chunkSize)
            chunkNumber = 0 
            print("Chunk size:", self.chunkSize)
            for i in range(preLoads):
                wave = self.generator.generateSamples()
                aoTask.writeData(wave)
                chunkNumber += 1
                self.chunkProduced.emit(chunkNumber, time.time()+(preLoads-i)*self.chunkSize/self.sampleRate)
            print("Starting aoTask")
            aoTask.start()
            print("Starting aiTask")
            aiTask.start()
            chunkTime = float(chunkSize/self.sampleRate)
            print("Chunk time:", chunkTime)
            
            while not self.stopRequested:
                wave = self.generator.generateSamples()
                aoTask.writeData(wave); chunkNumber += 1
                self.chunkProduced.emit(chunkNumber, time.time()+preLoads*chunkTime)
                data = aiTask.readData(chunkSize); t = time.time() - chunkTime
                nExtra = aiTask.samplesAvailable()
                if nExtra > 0:
                    warnings.warn("Extra samples available: %d" % nExtra)
                d = data[0]
                minimum = np.min(d); maximum = np.max(d); mean = np.sum(d)/d.shape[0]; std = np.std(d)
                overload = maximum > self.aoRange.max or minimum < self.aoRange.min
                if overload:
                    bad = (d>self.aoRange.max) | (d<self.aoRange.min)
                    self.inputOverload.emit(np.count_nonzero(bad))
                samples = decimator.decimate(d)
                self.dataReady.emit(samples, np.asarray([t, minimum, maximum, mean, std]))

        except Exception:
            exceptionString = traceback.format_exc()
            self.error.emit(exceptionString)
        finally:
            del d

class QFloatDisplay(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        QDoubleSpinBox.__init__(self, *args, **kwargs)
        self.setReadOnly(True)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setRange(-1E3,+1E3)
        self.setSpecialValueText('NaN')
        self.setSingleStep(1E-6)
        self.setDecimals(6)

class MultitoneLockinWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(MultitoneLockinWidget, self).__init__(parent)
        self.tableColumns = ['active', 'f', 'A', 'phase', 'bw', 'order', 'X', 'Y', 'R', 'Theta']
        self.setupUi(self)
        self.populateTable()
        self.daqThread = None
        self.liaThread = None
        self.rawWriter = None
        self.hdfFile = None
        self.fMax = 100E6
        
        self.wavePlot.addLegend()
        self.wavePlot.setLabel('left', 'Voltage', units='V')
        self.wavePlot.setLabel('bottom', 'time', units='s')
        self.excitationCurve = pg.PlotDataItem(pen='r', name='Excitation')
        self.wavePlot.addItem(self.excitationCurve)
        self.responseCurve = pg.PlotDataItem(pen='b', name='Response')
        self.wavePlot.addItem(self.responseCurve)
        self.startPb.clicked.connect(self.startMeasurement)
        self.stopPb.clicked.connect(self.stopMeasurement)
        self.settingsWidgets = [self.deviceCombo, self.aoChannelCombo, self.aoRangeCombo,
                                self.aiChannelCombo, self.aiRangeCombo, self.aiTerminalConfigCombo,
                                self.sampleLe, self.commentLe, self.enablePlotCb, 
                                self.sampleRateSb, self.offsetSb, self.rampRateSb, self.inputDecimationCombo,
                                self.saveRawDataCb]
                                
        self.sampleRateSb.valueChanged.connect(self.updateMaximumFrequencies)
        self.deviceCombo.currentIndexChanged.connect(self.updateDevice)
        self.restoreSettings()
        self.adrTemp = TemperatureSubscriber(self)
        self.adrTemp.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.adrTemp.adrResistanceReceived.connect(self.collectAdrResistance)
        self.adrTemp.start()        
        self.curve1 = pg.PlotDataItem(symbol='o', symbolSize=7, pen='b', name='')
        self.curve2 = pg.PlotDataItem(symbol='o', symbolSize=7, pen='r', name='')
        self.plot1.addItem(self.curve1)
        self.plot1.setLogMode(x=True)
        self.plot1.setLabel('bottom', 'f', units='Hz')
        self.plot2.addItem(self.curve2)
        self.plot2.setLogMode(x=True)
        self.plot2.setLabel('bottom', 'f', units='Hz')
        self.plot2.setXLink(self.plot1)
        self.plot1.showGrid(x=True, y=True)
        self.plot2.showGrid(x=True, y=True)
        self.plotxy.setLabel('bottom', 'X', units='')
        self.plotxy.setLabel('left', 'Y', units='')
        self.plotxy.setAspectLocked()
        self.curvexy = pg.PlotDataItem(symbol='o', symbolSize=7, pen='b', name='')
        self.plotxy.addItem(self.curvexy)
        self.plotCombo.currentIndexChanged.connect(self.yAxisChanged)
        self.plotCombo.setCurrentIndex(self.plotCombo.currentIndex())
        self.addRowPb.clicked.connect(self.addTableRow)
        self.deleteRowPb.clicked.connect(self.deleteTableRow)
        self.updateMaximumFrequencies()
        self.sampleRateSb.valueChanged.connect(self.updateMaximumFrequencies)
        self.inputDecimationCombo.currentIndexChanged.connect(self.updateMaximumFrequencies)
        self.saveRawDataCb.toggled.connect(self.toggleRawDataCollection)
        self.enablePlotCb.toggled.connect(self.enablePlotToggled)
    
    def updateMaximumFrequencies(self):
        fs = self.sampleRateSb.value() * 1E3
        self.fMax = 0.5* fs / int(str(self.inputDecimationCombo.currentText()))
        for row in range(self.table.rowCount()):
            self.tableCellWidget(row, 'f').setMaximum(self.fMax)
    
    def populateTable(self):
        t = self.table
        t.setColumnCount(len(self.tableColumns))
        t.setHorizontalHeaderLabels(self.tableColumns)
        t.resizeRowsToContents()
        t.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        t.horizontalHeader().setStretchLastSection(True)
   
    def collectAdrResistance(self, R):
        if self.hdfFile is None:
            return
        
        timeStamp = time.time()
        self.dsTimeStamps.resize((self.dsTimeStamps.shape[0]+1,))
        self.dsTimeStamps[-1] = timeStamp
        
        self.dsAdrResistance.resize((self.dsAdrResistance.shape[0]+1,))
        self.dsAdrResistance[-1] = R

    def populateDevices(self):
        self.deviceCombo.clear()
        system = daq.System()
        devices = system.findDevices()
        for dev in devices:
            self.deviceCombo.addItem(dev)
        
    def updateDevice(self):
        self.aiChannelCombo.clear()
        self.aoChannelCombo.clear()
        self.aiRangeCombo.clear()
        self.aoRangeCombo.clear()
        
        deviceName = str(self.deviceCombo.currentText())
        if len(deviceName) < 1:
            return
        device = daq.Device(deviceName)

        aiChannels = device.findAiChannels()
        for channel in aiChannels:
            self.aiChannelCombo.addItem(channel)
        
        aoChannels = device.findAoChannels()
        for channel in aoChannels:
            self.aoChannelCombo.addItem(channel)
            
        self.aiRanges = device.voltageRangesAi()
        for r in self.aiRanges:
            self.aiRangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))

        self.aoRanges = device.voltageRangesAo()            
        for r in self.aoRanges:
            self.aoRangeCombo.addItem('%+.2f -> %+.2f V' % (r.min, r.max))
        
        if len(aiChannels):
            aiChannel = daq.AiChannel('%s/%s' % (deviceName, aiChannels[0]), self.aiRanges[0].min, self.aiRanges[0].max)
            aiTask = daq.AiTask('TestInputSampleRate')
            aiTask.addChannel(aiChannel)
            aiSampleRate = aiTask.maxSampleClockRate()
        else:
            aiSampleRate = 0

        if len(aoChannels):
            aoChannel = daq.AoChannel('%s/%s' % (deviceName, aoChannels[0]), self.aoRanges[0].min, self.aoRanges[0].max)
            aoTask = daq.AoTask('TestOutputSampleRate')
            aoTask.addChannel(aoChannel)
            aoSampleRate = aoTask.maxSampleClockRate()
        else:
            aoSampleRate = 0
            
        rate = min(aiSampleRate, aoSampleRate)
        self.sampleRateSb.setMaximum(int(1E-3*rate))
        #self.updateInfo()

    def terminalConfiguration(self):
        t = str(self.aiTerminalConfigCombo.currentText())
        tc = daq.AiChannel.TerminalConfiguration
        terminalConfigDict = {'RSE': tc.RSE, 'DIFF': tc.DIFF, 'NRSE': tc.NRSE}
        return terminalConfigDict[t]
        
    def restoreSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        self.populateDevices()
        for w in self.settingsWidgets:
            restoreWidgetFromSettings(s, w)
        geometry = s.value('geometry', QByteArray(), type=QByteArray)
        self.restoreGeometry(geometry)

        g = s.value('splitter1State')
        if g is not None:
            self.splitter1.restoreState(g)
        g = s.value('splitter2State')
        if g is not None:
            self.splitter2.restoreState(g)

        rows = s.beginReadArray('frequencyTable')
        print("Rows:", rows)
        for row in range(rows):
            print("Restoring row:", row)
            s.setArrayIndex(row)
            enabled = s.value('active', True, type=bool)
            f = s.value('f', 10*(3**row), type=float)
            A = s.value('A', 0.1, type=float)
            phase = s.value('phase', 0, type=float)
            bw = s.value('bw', 5, type=float)
            order = s.value('order', 8, type=int)
            self.addTableRow(row, enabled, f, A, phase, bw, order)
        s.endArray()
        
    def tableCellWidget(self, row, item):
        return self.table.cellWidget(row, self.tableColumns.index(item))
        
    def setTableCellWidget(self, row, item, widget):
        self.table.setCellWidget(row, self.tableColumns.index(item), widget)
        
    def enablePlotToggled(self, checked):
        print("Plot toggled")
        if self.daqThread is None:
            return
        if checked:
            self.daqThread.dataReady.connect(self.showWaveform)
        else:
            self.daqThread.dataReady.disconnect(self.showWaveform)
            
        
        
    def addTableRow(self, row=None, enabled=True, f=10, A=0.1, phase=0.0, bw=5, order=8):
        table = self.table
        if row == None:
            row = table.rowCount()
        if row < 1:
            row = 0
        table.insertRow(row)
        cb = QCheckBox()
        cb.setChecked(enabled)
        self.setTableCellWidget(row, 'active', cb)
        
        frequencySb = QDoubleSpinBox()
        frequencySb.setMinimum(1.0)
        frequencySb.setMaximum(self.fMax)
        frequencySb.setSingleStep(0.01)
        frequencySb.setDecimals(2)
        frequencySb.setValue(f)
        self.setTableCellWidget(row, 'f', frequencySb)
        
        amplitudeSb = QDoubleSpinBox()
        amplitudeSb.setMinimum(0.000)
        amplitudeSb.setSingleStep(0.0001)
        amplitudeSb.setDecimals(4)
        amplitudeSb.setMaximum(5)
        amplitudeSb.setValue(A)
        amplitudeSb.valueChanged.connect(lambda v: self.amplitudeChanged(row, v))
        self.setTableCellWidget(row, 'A', amplitudeSb)
        
        phaseSb = QDoubleSpinBox()
        phaseSb.setMinimum(0)
        phaseSb.setDecimals(2)
        phaseSb.setSingleStep(0.01)
        phaseSb.setMaximum(360)
        phaseSb.setWrapping(True)
        phaseSb.setValue(phase)
        self.setTableCellWidget(row, 'phase', phaseSb)
        
        bwSb = QDoubleSpinBox()
        bwSb.setMinimum(0.1)
        bwSb.setMaximum(1000)
        bwSb.setValue(bw)
        bwSb.setSuffix(' Hz')
        self.setTableCellWidget(row, 'bw', bwSb)

        orderSb = QSpinBox()
        orderSb.setMinimum(1)
        orderSb.setMaximum(10)
        orderSb.setValue(order)
        self.setTableCellWidget(row, 'order', orderSb)
        
        self.setTableCellWidget(row, 'X', QFloatDisplay())
        self.setTableCellWidget(row, 'Y', QFloatDisplay())
        self.setTableCellWidget(row, 'R', QFloatDisplay())
        self.setTableCellWidget(row, 'Theta', QFloatDisplay())
        
    def amplitudeChanged(self, row, value):
        if self.daqThread is None:
            return
        if not row in self.activeRows:
            return
        i = np.where(row==self.activeRows)[0][0]
        self.daqThread.setAmplitude(i, value)
    
    def deleteTableRow(self):
        table = self.table
        row = table.currentRow()
        table.removeRow(row)
        
    def saveSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        #s.setValue('geometry', self.win)
        for w in self.settingsWidgets:
            saveWidgetToSettings(s, w)

        s.setValue('splitter1State', self.splitter1.saveState())
        s.setValue('splitter2State', self.splitter2.saveState())
        
        table = self.table
        nRows = table.rowCount()
        s.beginWriteArray('frequencyTable', nRows)
        w = self.tableCellWidget
        for row in range(nRows):
            print ("Saving row:", row)
            s.setArrayIndex(row)
            s.setValue('active', w(row,'active').isChecked())
            s.setValue('f', w(row,'f').value())
            s.setValue('A', w(row,'A').value())
            s.setValue('phase', w(row,'phase').value())
            s.setValue('bw', w(row, 'bw').value())
            s.setValue('rollOff', w(row, 'order').value())
        s.endArray()
        
    def closeEvent(self, event):
        if self.daqThread is not None:
            r = QMessageBox.warning(self, ApplicationName, 'The measurement is still running. Do you really want to quit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if r==QMessageBox.No:
                event.ignore()
                return
        self.saveSettings()
        super(MultitoneLockinWidget, self).closeEvent(event)
        
    def tableColumnValues(self, columnId):
        t = self.table
        values = []
        for row in range(t.rowCount()):
            widget = self.tableCellWidget(row, columnId)
            v = widgetValue(widget)
            values.append(v)
        return np.array(values)
                
    def startMeasurement(self):
        self.tProduce = {}
        sampleRate = int(self.sampleRateSb.value()*1E3)
        deviceName = str(self.deviceCombo.currentText())
        aoChannel = str(self.aoChannelCombo.currentText())
        aiChannel = str(self.aiChannelCombo.currentText())
        aiTerminalConfig = self.terminalConfiguration()
        aiRange = self.aiRanges[self.aiRangeCombo.currentIndex()]
        aoRange = self.aoRanges[self.aoRangeCombo.currentIndex()]
        offset = self.offsetSb.value()
        
        active = self.tableColumnValues('active')
        activeRows = np.where(active)[0]
        self.activeRows = activeRows
        fRefs = self.tableColumnValues('f')[activeRows]
        As = self.tableColumnValues('A')[activeRows]
        phases = self.tableColumnValues('phase')[activeRows]*deg2rad
        bws = self.tableColumnValues('bw')[activeRows]
        orders = self.tableColumnValues('order')[activeRows]
        print('fRefs:', fRefs)
        
        fileName = '%s_%s.h5' % (self.sampleLe.text(), time.strftime('%Y%m%d_%H%M%S'))
        hdfFile = hdf.File(fileName, mode='w')
        hdfFile.attrs['Program'] = ApplicationName
        hdfFile.attrs['Copyright'] = Copyright
        hdfFile.attrs['Version'] = Version
        hdfFile.attrs['Sample'] = str(self.sampleLe.text())
        hdfFile.attrs['Comment'] = str(self.commentLe.text())
        hdfFile.attrs['StartTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S')
        hdfFile.attrs['StartTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())
        hdfFile.attrs['sampleRate'] = sampleRate
        hdfFile.attrs['offset'] = offset
        hdfFile.attrs['deviceName'] = deviceName
        hdfFile.attrs['aoChannel'] = aoChannel
        hdfFile.attrs['aoRangeMin'] = aoRange.min; hdfFile.attrs['aoRangeMax'] = aoRange.max
        hdfFile.attrs['aiChannel'] = aiChannel
        hdfFile.attrs['aiRangeMin'] = aiRange.min; hdfFile.attrs['aiRangeMax'] = aiRange.max
        hdfFile.attrs['aiTerminalConfig'] = str(self.aiTerminalConfigCombo.currentText())
        hdfFile.attrs['excitationFrequencies'] = fRefs
        hdfFile.attrs['lockinFilterBandwidths'] = bws
        hdfFile.attrs['excitationAmplitudes'] = As
        hdfFile.attrs['excitationPhases'] = phases
        hdfFile.attrs['lockinFilterOrders'] = orders
        hdfFile.attrs['rawCount']  = 0
        hdfFile.attrs['rampRate'] = self.rampRateSb.value()
        
        self.liaStreamWriters = []
        for i,f in enumerate(fRefs):
            grp = hdfFile.create_group('F_%02d' % i)
            grp.attrs['fRef'] = f
            streamWriter = HdfStreamWriter(grp, dtype=np.complex64, scalarFields=[('t', np.float64)], metaData={}, parent=self)
            self.liaStreamWriters.append(streamWriter)
        self.fs = fRefs
        
        self.dsTimeStamps = hdfFile.create_dataset('AdrResistance_TimeStamps', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsTimeStamps.attrs['units'] = 's'
        self.dsAdrResistance = hdfFile.create_dataset('AdrResistance', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsAdrResistance.attrs['units'] = 'Ohms'
        
        self.hdfFile = hdfFile
        
        inputDecimation = int(str(self.inputDecimationCombo.currentText()))
        print("Input decimation", inputDecimation)
        sampleRateDecimated = sampleRate/inputDecimation
        print("Decimated sample rate", sampleRateDecimated)
        desiredChunkSize = int(min(0.5*sampleRateDecimated, 2**18)) # Update at least once/second
            
        # Compute phase delays due to the pre-lockin FIR halfband decimator cascade
        dec = DecimatorCascade(inputDecimation, desiredChunkSize)
        phaseDelays = TwoPi*fRefs/sampleRate*(dec.sampleDelay()+1.0)
        print("Phase delays:", phaseDelays*rad2deg,'deg')
        phaseDelays = np.mod(phaseDelays, TwoPi)
        lias = LockIns(sampleRateDecimated, fRefs, phases-phaseDelays, bws, orders, desiredChunkSize=desiredChunkSize); self.lias = lias
        lias.chunkAnalyzed.connect(self.chunkAnalyzed)
        chunkSize = lias.chunkSize
        print("Lias chunk size:", chunkSize)

        self.t = np.linspace(0, chunkSize/sampleRateDecimated, chunkSize)
        self.wavePlot.setXRange(0,self.t[-1])

        daqThread = DaqThread(sampleRate, fRefs, As, phases, chunkSize*inputDecimation, inputDecimation); self.daqThread = daqThread
        daqThread.setRampRate(self.rampRateSb.value())
        daqThread.setOffset(self.offsetSb.value())
        self.rampRateSb.valueChanged.connect(daqThread.setRampRate)
        daqThread.configureDaq(deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig)
        daqThread.chunkProduced.connect(self.chunkProduced)
        daqThread.inputOverload.connect(self.overloadLed.flashOnce)
        daqThread.error.connect(self.reportError)
        self.offsetSb.valueChanged.connect(self.daqThread.setOffset)
        
        if self.enablePlotCb.isChecked():
            daqThread.dataReady.connect(self.showWaveform)
        
        if self.saveRawDataCb.isChecked():
            self.toggleRawDataCollection(True)
        
        self.resultsCollected = 0
        self.chunksProduced = None
        liaThread = QThread(); self.liaThread = liaThread
        lias.moveToThread(liaThread)
        daqThread.dataReady.connect(lias.integrateData)
        lias.resultsAvailable.connect(self.collectLockinResults)
        liaThread.started.connect(lambda: daqThread.start(QThread.HighestPriority))
        liaThread.started.connect(lambda: self.enableWidgets(False))
        liaThread.finished.connect(self.liaThreadFinished)
        liaThread.start() # Start lock-in amplifier(s)
        
#    def showOverload(self, p):
#        self.overloadLed.flashOnce()
        
        
    def toggleRawDataCollection(self, enabled):
        if self.hdfFile is None: return
        if enabled:
            rawCount = self.hdfFile.attrs['rawCount']
            grp = self.hdfFile.create_group('RAW_%06d' % rawCount) # Need to make a new group
            self.hdfFile.attrs['rawCount'] = rawCount+1
            self.rawWriter = HdfStreamWriter(grp, dtype=np.float32, scalarFields=[('t', np.float64), ('Vmin', np.float64), ('Vmax', np.float64), ('Vmean', np.float64), ('Vrms', np.float64)], metaData={}, parent=self)
            self.daqThread.dataReady.connect(self.rawWriter.writeData)
        else:
            if self.rawWriter is not None:
                self.rawWriter.deleteLater()
                self.rawWriter = None
        
    def chunkProduced(self, n, t):
        self.tProduce[n] = t
        self.generatingLed.flashOnce()
        
    def chunkAnalyzed(self, n, t):
        elapsedTime = t - self.tProduce.pop(n)
        self.delayLe.setText('%.3f s' % elapsedTime)
        
    def collectLockinResults(self, t, Vmin, Vmax, dc, rms, Zs):
        self.dcIndicator.setText('%+7.5f V' % dc)
        self.rmsIndicator.setText('%+7.5f Vrms' % rms)
        zs = np.empty((len(Zs),), dtype=np.complex64)
        for i, Z in enumerate(Zs):
            w = self.liaStreamWriters[i]
            if w is not None:
                w.writeData(Z, [t])
            z = np.mean(Z)
            zs[i] = z
            row = self.activeRows[i]
            self.tableCellWidget(row, 'X').setValue(np.real(z))
            self.tableCellWidget(row, 'Y').setValue(np.imag(z))
            self.tableCellWidget(row, 'R').setValue(np.abs(z))
            self.tableCellWidget(row, 'Theta').setValue(np.angle(z)*rad2deg)
        self.zs = zs
        self.updatePlot()
                
    def reportError(self, message):
        QMessageBox.critical(self, 'Exception encountered!', message)

    def stopMeasurement(self):
        if self.daqThread is None:
            return
        if self.stopPb.text() == 'Stop':
            self.daqThread.stop()
            self.stopPb.setText('Abort')
            self.measurementFinished()
        else:
            self.daqThread.abort()
            self.daqThread.wait(1000)
            self.measurementFinished()

    def daqThreadFinished(self):
        print("DAQ thread finished")
        del self.daqThread
        self.daqThread = None
        
    def liaThreadFinished(self):
        print("LIA thread finished")
        self.liaThread.deleteLater()
        self.liaThread = None
        self.lias.deleteLater()
        self.lias = None
        #del self.liaThread; self.liaThread = None
        #del self.lias; self.lias = None
        
    def measurementFinished(self):
        if self.liaThread is not None:
            self.liaThread.quit()
            self.liaThread.wait(2000)
#        self.sweep.toHdf(grp)
        self.closeFile()
        self.stopPb.setText('Stop')
        self.enableWidgets(True)
        
    def closeFile(self):
        if self.hdfFile is not None:
            t = time.time()
            self.hdfFile.attrs['StopTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
            self.hdfFile.attrs['StopTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(t))
            self.hdfFile.close()
            del self.hdfFile
            self.hdfFile = None
            
    def enableWidgets(self, enable):
        self.driveGroupBox.setEnabled(enable)
        self.inputGroupBox.setEnabled(enable)
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)
        
        table = self.table
        for item in ['f', 'phase', 'active', 'bw', 'order']:
            col = self.tableColumns.index(item)
            for row in range(table.rowCount()):
                w = table.cellWidget(row, col)
                if isinstance(w, QAbstractSpinBox) or isinstance(w, QLineEdit):
                    w.setReadOnly(not enable)
                    if enable:
                        w.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
                    else:
                        w.setButtonSymbols(QAbstractSpinBox.NoButtons)
                elif isinstance(w, QAbstractButton) or isinstance(w, QComboBox):
                    w.setEnabled(enable)
        
    def showWaveform(self, samples, stats):
        self.responseCurve.setData(self.t, samples)
            
    def yAxisChanged(self):
        yAxis = str(self.plotCombo.currentText())
        if yAxis=='X/Y':
            self.plot1.setLabel('left', 'X', units='')
            self.plot2.setLabel('left', 'Y', units='')
        elif yAxis=='R/Phi':
            self.plot1.setLabel('left', 'R', units='')
            self.plot2.setLabel('left', 'Phi', units='deg')
        elif yAxis=='Vmax/Vmin':
            self.plot1.setLabel('left', 'Vmax', units='V')
            self.plot2.setLabel('left', 'Vmin', units='V')
        elif yAxis=='R/Vdc':
            self.plot1.setLabel('left', 'R', units='')
            self.plot2.setLabel('left', 'Vdc', units='V')
        ylog = (yAxis[0] == 'R') and self.logscaleCb.isChecked()
        self.plot1.setLogMode(x=True, y=ylog)
        self.updatePlot()

    def updatePlot(self):
        yAxis = str(self.plotCombo.currentText())
        i = np.argsort(self.fs)
        f = self.fs[i]; z = self.zs[i]
        X = np.real(z)
        Y = np.imag(z)
        if yAxis=='X/Y':
            y1 = X
            y2 = Y
        elif yAxis=='R/Phi':
            y1 = np.abs(z)
            y2 = rad2deg*np.angle(z)
        else:
            warnings.warn("Unsupported y-axis: %s" % yAxis)
            return
        self.curve1.setData(f,y1)
        self.curve2.setData(f,y2)
        self.curvexy.setData(X, Y)

if __name__ == '__main__':
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARN)
    #logging.getLogger('Zmq.Zmq').setLevel(logging.WARN)
   
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ApplicationName)    

#    import psutil, os
#    p = psutil.Process(os.getpid())
#    p.set_nice(psutil.HIGH_PRIORITY_CLASS)
    
    from PyQt4.QtGui import QApplication #, QIcon
    app = QApplication([])
    app.setOrganizationDomain(OrganizationDomain)
    app.setApplicationName(ApplicationName)
    app.setApplicationVersion(Version)
    app.setOrganizationName(OrganizationName)
    #app.setWindowIcon(QIcon('../Icons/LegacyDaqStreaming.png'))
    widget = MultitoneLockinWidget()
    widget.setWindowTitle('%s (%s)' % (ApplicationName, Version))
    widget.show()
    app.exec_()

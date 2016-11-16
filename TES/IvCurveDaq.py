# -*- coding: utf-8 -*-
"""
Record TES I-V curves using a single DAQ device with AO and AI.
Produces triangular sweeps (up and down) and records data to HDF5 file.
New code started at Tsinghua October/November 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

OrganizationName = 'McCammon Astrophysics'
OrganizationDomain = 'wisp.physics.wisc.edu'
ApplicationName = 'IvCurveDaq'
Version = '0.1'

from LabWidgets.Utilities import compileUi, saveWidgetToSettings, restoreWidgetFromSettings
compileUi('IvCurveDaqUi')
import IvCurveDaqUi as ui 
from PyQt4.QtGui import QWidget, QMessageBox
from PyQt4.QtCore import QThread, QSettings, pyqtSignal

import DAQ.PyDaqMx as daq
import time
import numpy as np
import scipy.signal as signal
import pyqtgraph as pg
import traceback

from Zmq.Subscribers import TemperatureSubscriber


def decimate(y, factor):
    ynew = y
    while factor > 8:
        ynew = signal.decimate(ynew, 8, ftype='iir') #, zero_phase=True)
        factor /= 8
    ynew = signal.decimate(ynew, factor, ftype='iir') #, zero_phase=True)
    return ynew


class DaqThread(QThread):
    error = pyqtSignal(str)
    dataReady = pyqtSignal(float, float, np.ndarray)

    def __init__(self, deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig, parent=None):
        super(DaqThread, self).__init__(parent)
        self.deviceName = deviceName
        self.aoChannel = aoChannel
        self.aoRange = aoRange
        self.aiChannel = aiChannel
        self.aiRange = aiRange
        self.aiTerminalConfig = aiTerminalConfig
        
    def setWave(self, wave):
        self.wave = wave
        
    def setSampleRate(self, rate):
        self.sampleRate = rate

    def stop(self):
        self.stopRequested = True
        
    def abort(self):
        self.stopRequested = True
        self.abortRequested = True
        
    def sweepCount(self):
        return self.sweepCount

    def run(self):
        self.sweepCount = 0
        self.stopRequested = False
        self.abortRequested = False
        try:
            d = daq.Device(self.deviceName)
            aiChannel = daq.AiChannel('%s/%s' % (self.deviceName, self.aiChannel), self.aiRange.min, self.aiRange.max)
            aiTask = daq.AiTask('AI')
            aiTask.addChannel(aiChannel)
            nSamples = len(self.wave)
            timing = daq.Timing(rate = self.sampleRate, samplesPerChannel = nSamples)
            timing.setSampleMode(timing.SampleMode.FINITE)
            aiTask.configureTiming(timing)
            
            aoChannel = daq.AoChannel('%s/%s' % (self.deviceName, self.aoChannel), self.aoRange.min, self.aoRange.max)
            aoTask = daq.AoTask('AO')
            aoTask.addChannel(aoChannel)
            aoTask.configureTiming(timing)
            aoTask.configureOutputBuffer(2*len(self.wave))
            #aoTask.digitalEdgeStartTrigger('/%s/ai/StartTrigger' % self.deviceName) # The cheap USB DAQ doesn't support this?!
            dt = 1./self.sampleRate
            print "Samples:", len(self.wave)
            while not self.stopRequested:
                aoTask.writeData(self.wave)
                aoTask.start()    
                aiTask.start()
                t = time.time() # Time of the start of the sweep
                while aiTask.samplesAvailable() < nSamples and not self.abortRequested:
                    self.msleep(10)
                    
                data = aiTask.readData(nSamples)
                self.dataReady.emit(t, dt, data[0])
                self.sweepCount += 1
                aiTask.stop()
                try:
                    aoTask.stop()
                except:
                    pass

        except Exception, e:
            exceptionString = traceback.format_exc()
            self.error.emit(exceptionString)
        finally:
            del d
import h5py as hdf

#from Zmq.Zmq import ZmqPublisher
#from Zmq.Ports import PubSub
#from OpenSQUID.OpenSquidRemote import OpenSquidRemote#, SquidRemote
class DaqStreamingWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(DaqStreamingWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = None
        self.hdfFile = None
        self.plot.addLegend()
        self.plot.setLabel('left', 'SQUID response', units='V')
        self.plot.setLabel('bottom', 'bias voltage', units='s')
        self.curves = []
        self.startPb.clicked.connect(self.startMeasurement)
        self.stopPb.clicked.connect(self.stopMeasurement)
#        self.publisher = ZmqPublisher('LegacyDaqStreaming', port=PubSub.LegacyDaqStreaming)
        self.settingsWidgets = [self.deviceCombo, self.aoChannelCombo, self.aoRangeCombo, self.aiChannelCombo, self.aiRangeCombo, self.aiTerminalConfigCombo, self.maxDriveSb, self.slewRateSb, self.zeroHoldTimeSb, self.peakHoldTimeSb, self.betweenHoldTimeSb, self.decimateCombo, self.sampleRateSb, self.sampleLe, self.commentLe, self.enablePlotCb]
        self.deviceCombo.currentIndexChanged.connect(self.updateDevice)
        for w in [self.maxDriveSb, self.slewRateSb, self.zeroHoldTimeSb, self.peakHoldTimeSb, self.betweenHoldTimeSb, self.sampleRateSb]:
            w.valueChanged.connect(self.updateInfo)
        self.decimateCombo.currentIndexChanged.connect(self.updateInfo)
        self.restoreSettings()
        self.adrTemp = TemperatureSubscriber(self)
        self.adrTemp.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.adrTemp.adrResistanceReceived.connect(self.collectAdrResistance)
        self.adrTemp.start()        
 
        pens = 'rgbc'
        for i in range(4):
            curve = pg.PlotDataItem(pen=pens[i], name='Curve %d' % i)
            self.plot.addItem(curve)
            self.curves.append(curve)
            
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
        self.updateInfo()

    def terminalConfiguration(self):
        t = str(self.aiTerminalConfigCombo.currentText())
        tc = daq.AiChannel.TerminalConfiguration
        terminalConfigDict = {'RSE': tc.RSE, 'DIFF': tc.DIFF, 'NRSE': tc.NRSE}
        return terminalConfigDict[t]
            
    def updateInfo(self):
        tz = self.zeroHoldTimeSb.value()
        tr = self.maxDriveSb.value() / self.slewRateSb.value()
        tp = self.peakHoldTimeSb.value()
        tb = self.betweenHoldTimeSb.value()
        f = self.sampleRateSb.value()*1E3
        ttotal = 2*tz+4*tr+2*tp+tb
        self.ttotal = ttotal
        self.totalTimeSb.setValue(ttotal)
        samplesPerSweep = int(np.ceil(ttotal*f/float(self.decimateCombo.currentText())))
        self.samplesPerSweepSb.setValue(samplesPerSweep)
        
    def restoreSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        self.populateDevices()
        for w in self.settingsWidgets:
            restoreWidgetFromSettings(s, w)
        
    def saveSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        for w in self.settingsWidgets:
            saveWidgetToSettings(s, w)
        
    def closeEvent(self, event):
        if self.thread is not None:
            event.ignore()
            return
        self.saveSettings()
        super(DaqStreamingWidget, self).closeEvent(event)
                
    def removeAllCurves(self):
        for curve in self.curves:
            curve.setData([],[])
        self.nSweeps = 0
        self.sweepCountSb.setValue(self.nSweeps)

    def startMeasurement(self):
        self.removeAllCurves()
        f = self.sampleRateSb.value()*1E3
        Vmax = self.maxDriveSb.value()
        wz = np.zeros((int(self.zeroHoldTimeSb.value()*f),), dtype=float)
        wr = np.linspace(0,Vmax, int(Vmax/self.slewRateSb.value()*f) )
        wp = np.ones((int(self.peakHoldTimeSb.value()*f),), dtype=float) * Vmax
        wb = np.zeros((int(self.betweenHoldTimeSb.value()*f),), dtype=float)
        wave = np.hstack([wz, wr, wp, wr[::-1], wb, -wr, -wp, -wr[::-1], wz])
        
        self.decimation = int(self.decimateCombo.currentText())
        self.x = decimate(wave, self.decimation)

        deviceName = str(self.deviceCombo.currentText())
        aoChannel = str(self.aoChannelCombo.currentText())
        aiChannel = str(self.aiChannelCombo.currentText())
        aiTerminalConfig = self.terminalConfiguration()
        aiRange = self.aiRanges[self.aiRangeCombo.currentIndex()]
        aoRange = self.aoRanges[self.aoRangeCombo.currentIndex()]

        fileName = '%s_%s.h5' % (self.sampleLe.text(), time.strftime('%Y%m%d_%H%M%S'))
        hdfFile = hdf.File(fileName, mode='w')
        hdfFile.attrs['Program'] = ApplicationName
        hdfFile.attrs['Version'] = Version
        hdfFile.attrs['Sample'] = str(self.sampleLe.text())
        hdfFile.attrs['Comment'] = str(self.commentLe.text())
        hdfFile.attrs['StartTimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S')
        hdfFile.attrs['StartTimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())
        hdfFile.attrs['Vmax'] = Vmax
        hdfFile.attrs['sampleRate'] = f
        hdfFile.attrs['decimation'] = self.decimation
        hdfFile.attrs['deviceName'] = deviceName
        hdfFile.attrs['aoChannel'] = aoChannel
        hdfFile.attrs['aoRangeMin'] = aoRange.min; hdfFile.attrs['aoRangeMax'] = aoRange.max
        hdfFile.attrs['aiChannel'] = aiChannel
        hdfFile.attrs['aiRangeMin'] = aiRange.min; hdfFile.attrs['aiRangeMax'] = aiRange.max
        hdfFile.attrs['aiTerminalConfig'] = str(self.aiTerminalConfigCombo.currentText())
        hdfFile.attrs['zeroHoldTime'] = self.zeroHoldTimeSb.value()
        hdfFile.attrs['peakHoldTime'] = self.peakHoldTimeSb.value()
        hdfFile.attrs['betweenHoldTime'] = self.betweenHoldTimeSb.value()
        hdfFile.attrs['slewRate'] = self.slewRateSb.value()
        ds = hdfFile.create_dataset('excitationWave', data=wave, compression='lzf', shuffle=True, fletcher32=True); ds.attrs['units'] = 'V'
        ds = hdfFile.create_dataset('excitationWave_decimated', data=self.x, compression='lzf', shuffle=True, fletcher32=True); ds.attrs['units'] = 'V'
        self.dsTimeStamps = hdfFile.create_dataset('AdrResistance_TimeStamps', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsTimeStamps.attrs['units'] = 's'
        self.dsAdrResistance = hdfFile.create_dataset('AdrResistance', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsAdrResistance.attrs['units'] = 'Ohms'
        self.hdfFile = hdfFile
        
        thread = DaqThread(deviceName, aoChannel, aoRange, aiChannel, aiRange, aiTerminalConfig, parent=self)
        thread.setWave(wave)
        self.wave = wave
        thread.setSampleRate(f)
        thread.dataReady.connect(self.collectData)
        thread.error.connect(self.reportError)
        self.enableWidgets(False)
        self.thread = thread
        self.t0 = None
        thread.start()
        thread.finished.connect(self.threadFinished)
        
    def reportError(self, message):
        QMessageBox.critical(self, 'Exception encountered!', message)

    def stopMeasurement(self):
        if self.thread is None:
            return
        if self.stopPb.text() == 'Stop':
            self.thread.stop()
            self.stopPb.setText('Abort')
        else:
            self.thread.abort()

    def threadFinished(self):
        self.closeFile()
        self.thread = None
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

    def collectData(self, timeStamp, dt, data):
        Tadr = self.temperatureSb.value()
        if self.t0 is None:
            self.t0 = timeStamp
        data = decimate(data, self.decimation)
        
        currentSweep = self.nSweeps; self.nSweeps += 1
        self.sweepCountSb.setValue(self.nSweeps)

        grp = self.hdfFile.create_group('Sweep_%06d' % currentSweep)
        grp.attrs['Time'] = timeStamp
        grp.attrs['TimeLocal'] =  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeStamp))
        grp.attrs['TimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(timeStamp))
        grp.attrs['Tadr'] = Tadr
        ds = grp.create_dataset('Vsquid', data=data, compression='lzf', shuffle=True, fletcher32=True)
        ds.attrs['units'] = 'V'
        if self.enablePlotCb.isChecked():
            self.curves[currentSweep % len(self.curves)].setData(self.x, data)


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
    
    from PyQt4.QtGui import QApplication, QIcon
    app = QApplication([])
    app.setOrganizationDomain(OrganizationDomain)
    app.setApplicationName(ApplicationName)
    app.setApplicationVersion(Version)
    app.setOrganizationName(OrganizationName)
    #app.setWindowIcon(QIcon('../Icons/LegacyDaqStreaming.png'))
    widget = DaqStreamingWidget()
    widget.setWindowTitle('%s (%s)' % (ApplicationName, Version))
    widget.show()
    app.exec_()

# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 12:30:54 2016

@author: wisp10
"""

import PyDaqMx as daq
from PyQt4 import QtGui
from PyQt4.QtCore import QSettings, QThread, pyqtSignal
from PyQt4 import uic
import pyqtgraph as pg
import numpy as np
import time
import os
import datetime
with open('PyDaqMx_AiDemoUi.py', 'w')  as of:
    uic.compileUi('PyDaqMx_AiDemoUi.ui', of)

import matplotlib.mlab as mlab
import h5py as hdf
import PyDaqMx_AiDemoUi as ui
from PyDaqMxGui import AiConfigLayout

class AiThread(QThread):
    samplesAvailable = pyqtSignal(float, np.ndarray)
    
    def setTask(self, task, samplesPerChunk):
        self.task = task
        self.samplesPerChunk = samplesPerChunk
        print "Samples per chunk:", samplesPerChunk
        
    def setMaxCount(self, maxCount):
        self.maxCount = maxCount
        
    def stop(self):
        self.stopRequested = True
        
    def run(self):
        self.stopRequested = False
        try:
            self.task.start()
            count = 0
            while not self.stopRequested and count < self.maxCount:
                if self.task.samplesAvailable() >= self.samplesPerChunk:
                    count += 1
                    data = self.task.readData(samplesPerChannel = self.samplesPerChunk)[0]
                    t = time.time()
                    self.samplesAvailable.emit(t, data)
                else:
                    self.msleep(20)
        except Exception, e:
            print e
        finally:
            self.task.stop()
            self.task.clear()
        
class DaqWidget(ui.Ui_Form, QtGui.QWidget):
    def __init__(self):
        super(DaqWidget, self).__init__()
        self.setupUi(self)
        self.aiConfigLayout = AiConfigLayout(parent=self.aiChannelGroupBox)
        self.runPb.clicked.connect(self.run)
        self.savePb.clicked.connect(self.save)                
        self.curve = pg.PlotCurveItem()
        self.plot.addItem(self.curve)
        self.plot.setLabel('left', 'voltage', units='V')
        self.plot.setLabel('bottom', 'time', units='s')
        
        self.curveSpectrum = pg.PlotCurveItem()
        self.spectrumPlot.addItem(self.curveSpectrum)
        self.spectrumPlot.setLabel('left', 'Noise', units='V/rtHz')
        self.spectrumPlot.setLabel('bottom', 'f', units='Hz')
        self.spectrumPlot.setLogMode(x=True, y=True)
        self.sampleRateSb.setMaximum(2E6)
        self.aiThread = None
        self.restoreSettings()
        self.ts = []
        self.f = None
        self.resetPb.clicked.connect(self.reset)
        
    def run(self):
        if self.runPb.text() == 'stop':
            self.aiThread.stop()
            self.aiThread.wait(1000)
            return
            
        self.runPb.setText('stop')
        task = daq.AiTask('AI')
        dev = self.aiConfigLayout.device()
        ch = self.aiConfigLayout.channel()
        range_ = self.aiConfigLayout.voltageRange()
        channelId = '%s/%s' % (dev, ch)
        channel = daq.AiChannel(channelId, range_.min, range_.max)
        channel.setTerminalConfiguration(self.aiConfigLayout.terminalConfiguration())
        task.addChannel(channel)
        print('USB transfer request size:', task.usbTransferRequestSize(channelId))
        task.setUsbTransferRequestSize(channelId, 4*65536L)
        
        sampleRate = self.sampleRateSb.value()
        print "Sample rate:", sampleRate
        
        refreshTime = self.refreshTimeSb.value()
        samplesPerChunk = int(sampleRate*refreshTime)

        timing = daq.Timing(rate=sampleRate, samplesPerChannel=50*samplesPerChunk)   
        timing.setSampleMode(daq.Timing.SampleMode.CONTINUOUS)
        task.configureTiming(timing)
        self.sampleRate = sampleRate
        self.samplesPerChunk = samplesPerChunk
        
        self.aiThread = AiThread(parent=self)
        self.aiThread.setMaxCount(self.maxCountSb.value())
        self.aiThread.setTask(task, samplesPerChunk)
        self.aiThread.finished.connect(self.taskFinished)
        self.aiThread.samplesAvailable.connect(self.collectData)
        self.aiThread.start()
        
    def save(self):
        print('save')        
        print(self.f)
        print(np.sqrt(self.averagePsd))
        fname = r'./PSD Saves/'+'{:%Y%b%d %H%M%S}'.format(datetime.datetime.now())
        os.mkdir(fname)
        np.savetxt(fname + r'/freq.txt',self.f)        
        np.savetxt(fname + r'/psd.txt',np.sqrt(self.averagePsd))
        
        
    def taskFinished(self):
        del self.aiThread
        self.aiThread = None
        self.runPb.setText('run')
        if self.runContinuouslyCb.isChecked():
            self.saveClicked()
            self.reset()
            self.run()
            
    def saveClicked(self):
        print "Saving data"
        
        pass
    
    def writeSpectrum(self):      
        with hdf.File(self.fileName, mode='a') as f:
            grp = f.create_group('Data%06i' % self.count)
            self.count += 1
            grp.attrs['tStart'] = np.min(self.ts)
            grp.attrs['tStop'] = np.max(self.ts)
            grp.attrs['Tmean'] = np.mean(self.Ts)
            grp.attrs['Rmean'] = np.mean(self.Rs)
            grp.attrs['Vmin'] = np.min(self.Vmin)
            grp.attrs['Vmax'] = np.max(self.Vmax)
            grp.attrs['Vstd'] = np.mean(self.Vstd)
            grp.create_dataset('PSD', data = self.averagePsd)
            grp.create_dataset('Frequency', data = self.f)
            grp.create_dataset('Thermometer_R', data=self.Rs)
            grp.create_dataset('Times', data=self.ts)
            grp.create_dataset('Temperatures', data = self.Ts)
            grp.create_dataset('Vmin', data=self.Vmin)
            grp.create_dataset('Vmax', data=self.Vmax)
            grp.create_dataset('Vmean', data=self.Vmean)
            grp.create_dataset('Vstd', data=self.Vstd)
            grp.create_dataset('Psd_Stdev', data = np.std(self.specMatrix, axis=0))
            self.Ts = []
            self.Rs = []
            self.ts = []
            self.Vmin = []
            self.Vmax = []
            self.Vmean = []
            self.Vstd = []
    
                
    def collectData(self, t, samples):
        dt = 1./self.sampleRate
        self.curve.setData(x=np.arange(0, len(samples)*dt, dt),y=samples)
        rms = np.std(samples)
        self.rmsSb.setValue(rms*1E3)
        
        sampleCount = self.maxCountSb.value()

        #nfft = min(self.resolution, len(samples))
        
        nfft = len(samples)
        self.window = mlab.window_hanning
        (psd, f) = mlab.psd(samples, NFFT=nfft, Fs = self.sampleRate, window=self.window, noverlap=3*nfft/4, detrend=mlab.detrend_mean)
        #psd = psd[0]
        
        if self.f is not None and f.shape == self.f.shape and np.all(f == self.f):
            self.averagePsd = (self.psdCount*self.averagePsd + psd)/(self.psdCount+1)
        else:
            self.psdCount = 0
            self.averagePsd = psd
            self.f = f

        if self.psdCount == 0:
            self.specMatrix = np.zeros((sampleCount, len(psd)), dtype=float)
            print "Made specMatrix", self.specMatrix.shape
            
        print "PSD:", psd.shape

        self.ts.append(t)            
        self.specMatrix[self.psdCount, :] = psd.transpose()
        self.psdCount += 1
        
        self.averagePsd = np.mean(self.specMatrix[:self.psdCount], axis = 0)
        self.curveSpectrum.setData(x=np.log10(f[1:]), y=np.log10(np.sqrt(self.averagePsd[1:])))
        self.countSb.setValue(self.psdCount)

        if self.psdCount >= sampleCount:
            self.writeSpectrum()
            self.reset()
        
    def reset(self):
        self.f = None
        self.ts = []

    def closeEvent(self, e):
        if self.aiThread is not None:
            self.aiThread.stop()
            self.aiThread.wait(1000)
        self.saveSettings()
        super(DaqWidget, self).closeEvent(e)
        
    def saveSettings(self):
        s = QSettings()
        self.aiConfigLayout.saveSettings(s)
        s.setValue('sampleRate', self.sampleRateSb.value())
        s.setValue('refreshTime', self.refreshTimeSb.value())
        
    def restoreSettings(self):
        s = QSettings()
        self.aiConfigLayout.restoreSettings(s)
        self.sampleRateSb.setValue(s.value('sampleRate', 1000, type=float))
        self.refreshTimeSb.setValue(s.value('refreshTime', 0.2, type=float))

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('DAQmx AI Demo')
    app.setApplicationVersion('0.2')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = DaqWidget()
    widget.show()
    app.exec_()
        
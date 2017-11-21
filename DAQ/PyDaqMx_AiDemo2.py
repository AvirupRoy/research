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
  
import PyDaqMx_AiDemoUi as ui
from PyDaqMxGui import AiConfigLayout

class AiThread(QThread):
    samplesAvailable = pyqtSignal(float, np.ndarray)
    
    def setTask(self, task, samplesPerChunk):
        self.task = task
        self.samplesPerChunk = samplesPerChunk
        print "Samples per chunk:", samplesPerChunk
        
    def stop(self):
        self.stopRequested = True
        
    def run(self):
        self.stopRequested = False
        try:
            self.task.start()
            while not self.stopRequested:
                if self.task.samplesAvailable() >= self.samplesPerChunk:
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
        channel = daq.AiChannel('%s/%s' % (dev, ch), range_.min, range_.max)
        channel.setTerminalConfiguration(self.aiConfigLayout.terminalConfiguration())
        task.addChannel(channel)
        
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
                
    def collectData(self, t, samples):
        print "Time:", t
        dt = 1./self.sampleRate
        t = np.arange(0, len(samples)*dt, dt)
        self.curve.setData(x=t,y=samples)
        std = np.std(samples)
        self.rmsSb.setValue(std*1E3)

        #nfft = min(self.resolution, len(samples))
        nfft = len(samples)
        self.window = mlab.window_hanning
        (psd, f) = mlab.psd(samples, NFFT=nfft, Fs = self.sampleRate, window=self.window, noverlap=3*nfft/4, detrend=mlab.detrend_mean)
        if self.f is not None and f.shape == self.f.shape and np.all(f == self.f):
            self.averagePsd = (self.psdCount*self.averagePsd + psd)/(self.psdCount+1)
        else:
            self.psdCount = 0
            self.averagePsd = psd
            self.f = f
            
        self.psdCount += 1
        self.curveSpectrum.setData(x=np.log10(f[1:]), y=np.log10(np.sqrt(self.averagePsd[1:,0])))
        #self.spectrumPlot.setRange(xRange=[0.1,fmax])
    def reset(self):
        self.f = None

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
        
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 12:30:54 2016

@author: wisp10
"""

from __future__ import print_function, division

from LabWidgets.Utilities import compileUi
compileUi('PyDaqMx_AiSpectrumAnalyzerUi')


import PyDaqMx as daq
from PyQt4 import QtGui
from PyQt4.QtCore import QSettings, QThread, pyqtSignal
import pyqtgraph as pg
import numpy as np
import time
import matplotlib.mlab as mlab
import h5py as hdf
import PyDaqMx_AiSpectrumAnalyzerUi as ui
from PyDaqMxGui import AiConfigLayout
from Zmq.Zmq import RequestReplyThreadWithBindings
from Zmq.Ports import RequestReply

class AiThread(QThread):
    samplesAvailable = pyqtSignal(float, np.ndarray)
    
    def setTask(self, task, samplesPerChunk):
        self.task = task
        self.samplesPerChunk = samplesPerChunk
        logger.info(u"Samples per chunk: %d", samplesPerChunk)
        
    def setMaxCount(self, maxCount):
        self.maxCount = maxCount
        
    def stop(self):
        self.stopRequested = True
        
    def run(self):
        self.stopRequested = False
        try:
            logger.debug(u"AiThread: Starting")
            self.task.configureInputBuffer(samplesPerChannel = self.samplesPerChunk*4)
            self.task.start()
            count = 0
            while not self.task.isDone() and not self.stopRequested and count < self.maxCount:
                if self.task.samplesAvailable() >= self.samplesPerChunk:
                    count += 1
                    data = self.task.readData(samplesPerChannel = self.samplesPerChunk)[0]
                    t = time.time()
                    logger.debug(u"AiThread: samples acquired")
                    self.samplesAvailable.emit(t, data)
                    logger.debug('AiThread: Back from signal')                    
                else:
                    self.msleep(20)
            logger.debug('AiThread: done with work.')                    
        except Exception, e:
            logger.warn(u"AiThread: Exception encountered: %s", e)
        finally:
            logger.debug(u"AiThread: Stopping task")
            self.task.stop()
            logger.debug(u"AiThread: Clearing task")
            self.task.clear()
            logger.debug(u"AiThread: Task cleared")

from Utility.RunningStats import RunningStatsWithKurtosis

from scipy import signal
        
class DaqWidget(ui.Ui_Form, QtGui.QWidget):
    WindowFunctions = {'Hanning': signal.hann, 'Blackman': signal.blackman, 'Hamming':signal.hamming, 'Bartlett': signal.bartlett, 'Blackman-Harris': signal.blackmanharris}
    DetrendFunctions = {'Mean': mlab.detrend_mean, 'None': mlab.detrend_none, 'Linear': mlab.detrend_linear}

    def __init__(self):
        super(DaqWidget, self).__init__()
        self.setupUi(self)
        self.windowCombo.addItems(self.WindowFunctions.keys())
        self.detrendCombo.addItems(self.DetrendFunctions.keys())
        self.detrendCombo.setCurrentIndex(self.detrendCombo.findText('Mean'))
        
        self.aiConfigLayout = AiConfigLayout(parent=self.aiChannelGroupBox)
        self.runPb.clicked.connect(self.run)
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
        self.startServerThread()

    def startServerThread(self):
        self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.DaqAiSpectrum, parent=self)
        boundWidgets = {'sampleRate': self.sampleRateSb, 'refreshTime': self.refreshTimeSb,
                        'maxCount': self.maxCountSb, 'name': self.nameLe, 'comment': self.commentLe,
                        'run': self.runPb, 'count': self.countSb, 'running': self.runningLed,
                        'aiChannel':self.aiConfigLayout.channelCombo}
        
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        logger.info('Starting server thread')
        self.serverThread.start()
        
        
    def run(self):
        if self.runPb.text() == 'Stop': # 
            self.stop()
            return
            
        self.windowFunction = self.WindowFunctions[str(self.windowCombo.currentText())]
        self.window = None
        self.detrendFunction = self.DetrendFunctions[str(self.detrendCombo.currentText())]
        self.reset()
        if len(self.nameLe.text()) > 0:
            self.fileName = str(self.nameLe.text()) + '.h5'            
        else:
            self.fileName = ''
        try:
            self.task = daq.AiTask('AI_SpectrumAnalyzer')
        except daq.Error as e:
            logger.warn('Unable to create new task. Deleting old. Error was: %s' % str(e))
            self.task.clear()
            return
        dev = self.aiConfigLayout.device()
        ch = self.aiConfigLayout.channel()
        range_ = self.aiConfigLayout.voltageRange()
        channel = daq.AiChannel('%s/%s' % (dev, ch), range_.min, range_.max)
        channel.setTerminalConfiguration(self.aiConfigLayout.terminalConfiguration())
        self.task.addChannel(channel)

        self.deviceStr = str(dev)
        self.channelStr = str(ch)
        self.rangeStr = '%s - %s' % (range_.min, range_.max)
        self.couplingStr = ''
        self.terminalConfigStr = str(self.aiConfigLayout.terminalConfiguration())
        
        sampleRate = self.sampleRateSb.value()
        logger.info("Sample rate: %d", sampleRate)
        
        refreshTime = self.refreshTimeSb.value()
        samplesPerChunk = int(sampleRate*refreshTime)
        updateRate = 1. # per second
        refreshRate = 1./refreshTime
        self.plotUpdateDivider = int(refreshRate / updateRate)

        timing = daq.Timing(rate=sampleRate, samplesPerChannel=50*samplesPerChunk)   
        timing.setSampleMode(daq.Timing.SampleMode.CONTINUOUS)
        self.task.configureTiming(timing)
        self.sampleRate = sampleRate
        self.samplesPerChunk = samplesPerChunk
        
        self.aiThread = AiThread(parent=self)
        self.aiThread.setMaxCount(self.maxCountSb.value())
        self.aiThread.setTask(self.task, samplesPerChunk)
        self.aiThread.finished.connect(self.taskFinished)
        self.aiThread.samplesAvailable.connect(self.collectData)
        self.aiThread.started.connect(self.started)        
        self.aiThread.start()
        
    def started(self):
        self.runningLed.turnOn()        
        self.runPb.setText('Stop')
        #self.aiChannelGroupBox.setEnabled(False)
        #self.sampleRate
        
    def stop(self):
        self.runContinuouslyCb.setChecked(False)
        logger.debug(u"Asking thread to stop")
        self.aiThread.stop()
        #logger.debug(u"Waiting for thread to end")
        #finished = self.aiThread.wait()
        #logger.debug(u"Thread has finished: %s" % str(finished))
        
    def taskFinished(self):
#        del self.aiThread
        #del self.task
 #       self.aiThread = None
        logger.debug(u"Finished signal received")
        self.runPb.setText('Run')
        self.runningLed.turnOff()
        
        if self.runContinuouslyCb.isChecked():
            self.reset()
            self.run()
    
    def writeSpectrum(self):
        if len(self.fileName) == 0:
            return
        with hdf.File(self.fileName, mode='a') as f:
            f.attrs['program'] = 'PyDaqmx_AiSpectrumAnalyzer.py'
            f.attrs['name'] = str(self.nameLe.text())
            n = len(f.keys())
            grp = f.create_group('Data%06i' % n)
            grp.attrs['comment'] = str(self.commentLe.text())
            grp.attrs['device'] = self.deviceStr
            grp.attrs['channel'] = self.channelStr
            grp.attrs['range'] = self.rangeStr
            #grp.attrs['coupling'] = self.couplingStr
            grp.attrs['terminalConfig'] = self.terminalConfigStr
            grp.attrs['detrend'] = str(self.detrendCombo.currentText())
            grp.attrs['window'] = str(self.windowCombo.currentText())
            grp.attrs['sampleRate'] = self.sampleRate
            grp.attrs['tStart'] = np.min(self.ts)
            grp.attrs['tStop'] = np.max(self.ts)
            grp.attrs['Vmin'] = np.min(self.Vmin)
            grp.attrs['Vmax'] = np.max(self.Vmax)
            grp.attrs['Vstd'] = np.mean(self.Vstd)
            grp.attrs['count'] = self.rs.n
            grp.attrs['maxCount'] = self.maxCountSb.value()
            opts = {'compression':'lzf', 'shuffle':True, 'fletcher32':True}
            grp.create_dataset('PSD', data = np.asarray(self.rs.mean(), dtype=np.float32), **opts)
            grp.create_dataset('PSD_std', data = np.asarray(self.rs.std(), dtype=np.float32), **opts)
            grp.create_dataset('PSD_skew', data = np.asarray(self.rs.skew(), dtype=np.float32), **opts)
            grp.create_dataset('PSD_kurtosis', data = np.asarray(self.rs.kurtosis(), dtype=np.float32), **opts)
            grp.create_dataset('Frequency', data = np.asarray(self.f, dtype=np.float32), **opts)
            grp.create_dataset('Times', data=self.ts)
            grp.create_dataset('Vmin', data=self.Vmin)
            grp.create_dataset('Vmax', data=self.Vmax)
            grp.create_dataset('Vmean', data=self.Vmean)
            grp.create_dataset('Vstd', data=self.Vstd)
                
    def collectData(self, t, samples):
        dt = 1./self.sampleRate

        rms = np.std(samples)
        self.rmsSb.setValue(rms*1E3)

        # Store some statistics over data
        self.Vmax.append(np.max(samples))
        self.Vmin.append(np.min(samples))
        self.Vmean.append(np.mean(samples))
        self.Vstd.append(rms)
        self.ts.append(t)            
        
        maxCount = self.maxCountSb.value()

        #nfft = min(self.resolution, len(samples))
        
        nfft = len(samples)
        if self.window is None:
            logger.debug('Making window %s...' % str(self.windowFunction))
            self.window = self.windowFunction(nfft)
        (psd, f) = mlab.psd(samples, NFFT=nfft, Fs = self.sampleRate, window=self.window, noverlap=3*nfft/4, detrend=self.detrendFunction)
        #psd = psd[:,0]
        
        if self.f is None or f.shape != self.f.shape or np.any(f != self.f):
            self.rs.clear()
            self.f = f
            self.averagePsd = None
        
        self.rs.push(psd)
        
        if self.averagingCombo.currentText() == u'Linear':
            self.averagePsd = self.rs.mean()
        else: # Exponential averaging
             if self.averagePsd is not None:
                 alpha = 1./maxCount
                 self.averagePsd = alpha*psd + (1-alpha)*self.averagePsd 
             else:
                 self.averagePsd = psd

        n = self.rs.n
        if n >= maxCount:
            self.writeSpectrum()
            self.reset()

        self.countSb.setValue(n)

        if n % self.plotUpdateDivider == 1 or n == maxCount:
            logger.debug('Updating plot on iteration %d' % n)
            self.curve.setData(x=np.arange(0, len(samples)*dt, dt),y=samples)
            self.curveSpectrum.setData(x=np.log10(f[1:]), y=np.log10(np.sqrt(self.averagePsd[1:])))
        

        
    def reset(self):
        self.f = None
        self.rs = RunningStatsWithKurtosis()
        self.ts = []
        self.Vmin = []
        self.Vmax = []
        self.Vmean = []
        self.Vstd = []

    def closeEvent(self, e):
        if self.aiThread is not None:
            self.aiThread.stop()
            self.aiThread.wait()
        self.saveSettings()
        self.serverThread.stop()
        self.serverThread.wait()
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
    import logging
    logging.basicConfig(filename='PyDaqMx_AiSpectrumAnalyzer.log', 
                        level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M:%S', filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logger = logging.getLogger(__name__)

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('DAQmx AI Demo')
    app.setApplicationVersion('0.2')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = DaqWidget()
    widget.setWindowTitle('AI Spectrum Analyzer')
    widget.show()
    app.exec_()

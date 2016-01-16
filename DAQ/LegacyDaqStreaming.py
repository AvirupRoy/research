# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 17:20:42 2016

@author: wisp10
"""

from PyQt4 import uic
#uic.compileUiDir('.')
with open('LegacyDaqStreamingUi.py', 'w') as f:
    uic.compileUi('LegacyDaqStreamingUi.ui', f)
    print "Done compiling UI"

from PyQt4.QtGui import QWidget


import LegacyDaqStreamingUi
import numpy as np
import pyqtgraph as pg
import PyNiLegacyDaq as daq
import time

from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QString
from SignalProcessing import IIRFilter

class DaqThread(QThread):
    error = pyqtSignal(QString)
    dataReady = pyqtSignal(float, float, float, np.ndarray)

    def __init__(self, channels, gains, rate, parent=None):
        super(DaqThread, self).__init__(parent)
        self.channels = channels
        self.gains = gains
        self.rate = rate

    def stop(self):
        self.stopRequested = True


    def run(self):
        try:
            self.stopRequested = False
            d = daq.Device(1)
            d.configureTimeout(0.1)
            self.rate = d.setAiClock(self.rate)
            print "Actual data rate:", self.rate
            dt = 1./self.rate
            scale = 10. / 65536
            d.enableDoubleBuffering(True)
            print "Starting"
            d.scanSetup(self.channels, self.gains)
            count = int(0.5*self.rate)
            buffer = d.scanStart(samplesPerChannel = count)
            t = time.time()
            complete = False
            while not (self.stopRequested or complete):
                ready,complete = d.halfReady()
                if ready:
                    data = np.right_shift(d.retrieveBufferedData(), 16).astype(np.int16)
                    self.dataReady.emit(t, dt, scale, data)
                    #print "New samples:", t, data.shape[-1]
                    t += data.shape[-1] / self.rate
                self.msleep(100)
            
        except Exception, e:
            print "Exception", e
        finally:
            del d
import h5py as hdf
import pyqtgraph as pg

class DaqStreamingWidget(LegacyDaqStreamingUi.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(DaqStreamingWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = None
        self.hdfFile = None

        plot = pg.PlotWidget(parent=self)
        plot.addLegend()
        self.hLayout.addWidget(plot)
        plot.setLabel('left', 'voltage', units='V')
        plot.setLabel('bottom', 'time', units='s')
        self.plot = plot
        self.curves = []
        self.restoreSettings()
        self.runPb.clicked.connect(self.runPbClicked)
        self.bFilter = []
        self.aFilter = []

    def restoreSettings(self):
        s = QSettings()
#        self.amplitudeSb.setValue(s.value('amplitude', 1.0, type=float))

    def saveSettings(self):
        s = QSettings()
        #s.setValue('amplitude', self.amplitudeSb.value())

    def closeEvent(self, e):
        if self.thread is not None:
            self.endThread()
        self.saveSettings()
        super(DaqStreamingWidget, self).closeEvent(e)
        
    def endThread(self):
        self.thread.stop()
        self.thread.wait(2000)
        if self.hdfFile is not None:
            self.hdfFile.close()
            self.hdfFile = None
        self.thread = None
        

    def runPbClicked(self):
        if self.thread:
            self.endThread()
        else:
            channels = [0, 1, 2, 3]
            for i in self.curves:
                self.plot.removeItem(i)
            self.curves = []
            pens = 'rgbc'
            for i in channels:
                curve = pg.PlotDataItem(pen=pens[i], name='Channel %d' % i)
                self.plot.addItem(curve)
                self.curves.append(curve)
            thread = DaqThread(channels=channels, gains=[0,0,20,40], rate=200000, parent=self)
            thread.dataReady.connect(self.collectData)
            self.enableControls(False)
            self.thread = thread
            hdfFile = hdf.File('test.h5', mode='w')
            nChannels = len(channels)
            self.dset = hdfFile.create_dataset("rawData", (nChannels,0), maxshape=(nChannels, None), chunks=(nChannels, 8192), dtype=np.int16, compression='lzf', shuffle=True, fletcher32=True)
            self.hdfFile = hdfFile
            self.makeFilters()
            thread.start()
            thread.finished.connect(self.threadFinished)
        
            
            #thread.error.connect(self.errorLog.append)
#            thread.packetGenerated.connect(self.chunkCounter.display)
#            self.stopPb.clicked.connect(thread.stop)
#
#            self.thread = thread
#            self.updateWaveform()
#            thread.start()
#            self.enableControls(False)

            
    def makeFilters(self):
        order = 8
        fc = 10E3
        fs = 200E3
        channels = [0, 1, 2, 3]
        for i,channel in enumerate(channels):
            lpf = IIRFilter.lowpass(order, fc, fs)
            self.filters.append(lpf)
            

    def threadFinished(self):
        self.enableControls(True)

    def enableControls(self, enable = True):
        if enable:
            self.runPb.setText('Run')
        else:
            self.runPb.setText('Stop')

    def collectData(self, timeStamp, dt, scale, data):
        
        nChannels = data.shape[0]
        nSamples  = data.shape[-1]
        oldShape = self.dset.shape
        self.dset.resize(oldShape[1]+nSamples, axis=1)
        self.dset[:, -nSamples:] = data

            
        t = np.arange(0, nSamples)*dt
        for channel in range(nChannels):
            y = np.asarray(data[channel], dtype=np.float32) * scale        
            self.curves[channel].setData(t, y)
        self.nSamplesLe.setText("{:,}".format(self.dset.shape[-1]))
        self.elapsedTimeLe.setText('%d' % timeStamp)

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('legacy DAQ Streaming')
    app.setApplicationVersion('0.1')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = DaqStreamingWidget()
    widget.show()
    app.exec_()

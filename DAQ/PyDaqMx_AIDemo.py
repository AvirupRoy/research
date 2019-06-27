# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 12:30:54 2016

@author: wisp10
"""

import PyDaqMx as daq
from PyQt4 import QtGui
from PyQt4.QtCore import QTimer
from PyQt4 import uic
import pyqtgraph as pg
import numpy as np
with open('PyDaqMx_AiDemoUi.py', 'w')  as of:
    uic.compileUi('PyDaqMx_AiDemoUi.ui', of)
    
import PyDaqMx_AiDemoUi as ui
from PyDaqMxGui import AiConfigLayout 
class DaqWidget(ui.Ui_Form, QtGui.QWidget):
    def __init__(self):
        super(DaqWidget, self).__init__()
        self.setupUi(self)
        self.aiConfigLayout = AiConfigLayout(parent=self.aiChannelGroupBox)
        self.runPb.clicked.connect(self.run)
        self.curve = pg.PlotCurveItem()
        self.plot.addItem(self.curve)
        
    def run(self):
        if self.runPb.text() == 'stop':
            self.timer.stop()
            self.task.stop()
            del self.task
            self.runPb.setText('run')
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

        timing = daq.Timing(rate=sampleRate, samplesPerChannel=10*samplesPerChunk)   
        timing.setSampleMode(daq.Timing.SampleMode.CONTINUOUS)
        task.configureTiming(timing)
        self.task = task
        self.sampleRate = sampleRate
        self.samplesPerChunk = samplesPerChunk
        
        timer = QTimer(self)
        ms = int(refreshTime*1000)
        timer.setInterval(ms)
        timer.timeout.connect(self.collectData)
        self.timer = timer
        timer.start()
        task.start()
                
    def collectData(self):
        while self.task.samplesAvailable() < self.samplesPerChunk:
            pass
        data = self.task.readData()[0]
        y = data[:self.samplesPerChunk]
#        data = self.task.readData(samplesPerChannel = self.samplesPerChunk)[0]
        dt = 1./self.sampleRate
        t = np.arange(0, len(y)*dt, dt)
        self.curve.setData(x=t,y=y)
        

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('DAQmx AI Demo')
    app.setApplicationVersion('0.1')
    app.setOrganizationName('McCammon X-ray Astro Physics')
    widget = DaqWidget()
    widget.show()
    app.exec_()
        
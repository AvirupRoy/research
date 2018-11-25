# -*- coding: utf-8 -*-
"""
Readout of AVS47 resistance bridge in single channel mode for simplicity
Created on Fri Dec 04 12:49:18 2015

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

import time, warnings
from LabWidgets.Utilities import connectAndUpdate, saveWidgetToSettings, restoreWidgetFromSettings, compileUi
compileUi('Avs47Ui')
import Avs47Ui as Ui

from Zmq.Zmq import ZmqPublisher
from Zmq.Ports import PubSub #,RequestReply

from PyQt4.QtGui import QWidget
from PyQt4.QtCore import QSettings, pyqtSignal
import pyqtgraph as pg
from PyQt4.Qt import Qt


import logging
logging.basicConfig(level=logging.WARN)

import os.path

from Visa.AVS47 import Avs47
from Visa.Agilent34401A import Agilent34401A

from Calibration.RuOx import RuOx600, RuOxBus, RuOx2005
#ruOxCalibration = RuOx600() # From breakpoint table
#ruOxCalibration = RuOx2005() # Equation
ruOxCalibration = RuOxBus() # Shuo's calibration (works decently below 200mK or so)

from Utility.Utility import PeriodicMeasurementThread

import numpy as np
def pruneData(y, maxLength=20000, fraction=0.3):
    if len(y) < maxLength:
        return y
    start = int(fraction*maxLength)
    firstSection = 0.5*(np.asarray(y[0:start:2])+np.asarray(y[1:start+1:2]))
    return np.hstack( (firstSection, y[start+1:]) ).tolist()

class WorkerThread(PeriodicMeasurementThread):
    readingAvailable = pyqtSignal(float, float)
    '''Signal emitted when a new resistance measurement is available. First parameter is resistance, second is time.'''
    
    def __init__(self, parent=None):
        super(WorkerThread, self).__init__(parent)
        self.dmm = None
    
    def setBridge(self, avs):
        self.avs = avs
        
    def setDmm(self, dmm):
        self.dmm = dmm
        
    def setAutoRangeUp(self, level):
        self.rangeUpLevel = level
        
    def setAutoRangeDown(self, level):
        self.rangeDownLevel = level
        
    def enableAutoRange(self, enable):
        self._autoRangeEnabled = enable

    def takeDmmReading(self):
        for i in range(10):
            try:
                t = time.time()
                V = self.dmm.reading()
                return t,V
            except Exception as e:
                warnings.warn("Having trouble getting DMM reading:", e)
                warnings.warn("Retrying...")
                pass
        warnings.warn("Unable to get a reading from DMM after 10 tries!")
        return t, float('nan')
            
    def run(self):
        try:
            avs = self.avs
            dmm = self.dmm
            avs.checkPresence()
            channel = avs.muxChannel.value
            excitation = avs.excitation.value
            Range = avs.range.value
            #print "Range:", Range
            avs.remote.enabled = True
            
            while not self._stopRequested:
                Range = avs.range.value
                if dmm is not None:
                    t,V = self.takeDmmReading()
                    R = Range * V / 2.0
                else:
                    t = time.time()
                    avs.sample()
                    self.msleep(400)
                    R = avs.resistanceReading()
                self.readingAvailable.emit(R, t)
                if self._autoRangeEnabled:
                    if R > 1E-2*self.rangeUpLevel*Range:
                        try:
                            avs.range.code += 1
                            #print "Range increase"
                            t = t + 4
                        except:
                            pass
                            #print "At maximum range"
                    elif R < 1E-2*self.rangeDownLevel*Range:
                        try:
                            avs.range.code -= 1
                            #print "Range decrease"
                            t = t + 4
                        except:
                            #print "At minimum range"
                            pass
                self.sleepPrecise(t)
            avs.remote.enabled = False
                
        except Exception as e:
            self.handleException(e)

from DAQ.SignalProcessing import IIRFilter

class Avs47SingleChannelWidget(Ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(Avs47SingleChannelWidget, self).__init__(parent)
        self.dmm = None
        self.avs = None
        self.buffer = ''
        self.workerThread = None
        self.setupUi(self)
        self.setWindowTitle('AVS47 Single Channel')
        self.outputFile = None
        self.yaxisCombo.currentIndexChanged.connect(self.switchPlotAxis)
        self.temperatureIndicator.setPrecision(5)
        
        combo = self.calibrationCombo
        combo.addItem('RuOx 600')
        combo.addItem('RuOx 2005')
        combo.addItem('RuOx Bus (Shuo)')
        combo.setItemData(0, 'Nominal sensor calibration for RuOx 600 series', Qt.ToolTipRole)
        combo.setItemData(1, 'Calibration for RuOx sensor #2005 series', Qt.ToolTipRole)
        combo.setItemData(2, 'Cross-calibration against RuOx #2005 by Shuo (not so good above ~300mK)', Qt.ToolTipRole)
        combo.currentIndexChanged.connect(self.selectCalibration)

        axis = pg.DateAxisItem(orientation='bottom')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis})
        self.plot.addLegend()
        self.verticalLayout.addWidget(self.plot)
        self.curve = pg.PlotCurveItem(name='Actual', symbol='o', pen='g')
        self.plot.addItem(self.curve)
        self.clearData()

        self.runPb.clicked.connect(self.runPbClicked)

        self.widgetsForSettings = [self.readoutInternalRadio, self.readoutDmmRadio, self.readoutZmqRadio, self.bridgeCombo, self.dmmCombo, self.autoRangeCb, self.rangeUpSb, self.rangeDownSb, self.yaxisCombo, self.intervalSb, self.calibrationCombo]
        self.restoreSettings()
        self.selectCalibration()
        #self.makeFilters()
        
        self.publisher = ZmqPublisher('Avs47SingleChannel', PubSub.AdrTemperature)

        #self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.AdrPidControl, parent=self)
        #boundWidgets = {'rampRate':self.rampRateSb, 'rampTarget':self.rampTargetSb, 'rampEnable':self.rampEnableCb, 'setpoint':self.setpointSb}
        #for name in boundWidgets:
            #self.serverThread.bindToWidget(name, boundWidgets[name])
        #self.serverThread.start()

    def makeFilters(self):
        fs = 10
        fc = 0.5
        order = 3
        self.lpfR = IIRFilter.lowpass(order=order, fc=fc, fs=fs)
        self.lpfT = IIRFilter.lowpass(order=order, fc=fc, fs=fs)
        self.lpfR.initializeFilterFlatHistory(self.Rs[-1])
        self.lpfT.initializeFilterFlatHistory(self.Ts[-1])
        Rfilt = self.lpfR.filterCausal(R)
        Tfilt = self.lpfT.filterCausal(T)

    def selectCalibration(self):
        cal = self.calibrationCombo.currentText()
        if cal == 'RuOx 600':
            self.calibration = RuOx600()
        elif cal == 'RuOx 2005':
            self.calibration = RuOx2005()
        elif cal == 'RuOx Bus (Shuo)':
            self.calibration = RuOxBus()
        else:
            warnings.warn('Unknown calibration selected:', cal)

    def switchPlotAxis(self):
        yaxis = self.yaxisCombo.currentText()
        if yaxis == 'R':
            self.plot.getAxis('left').setLabel('R', 'Ohm')
        elif yaxis == 'T':
            self.plot.getAxis('left').setLabel('T', 'K')
        self.updatePlot()
        
    def runPbClicked(self):
        if self.workerThread is not None:
            self.workerThread.stop()
            return
        self.avs = Avs47(self.bridgeCombo.visaResource())
        self.avs.range.bindToEnumComboBox(self.rangeCombo)
        self.avs.muxChannel.bindToSpinBox(self.channelSb)
        #self.channelSb.setValue(self.avs.muxChannel.value)
        self.avs.excitation.bindToEnumComboBox(self.excitationCombo)
        self.avs.range.caching = True
        self.avs.excitation.caching = True
        self.avs.muxChannel.caching = True
        
        thread = WorkerThread()
        thread.setBridge(self.avs)
        if self.readoutDmmRadio.isChecked():
            self.dmm = Agilent34401A(self.dmmCombo.visaResource())
            thread.setDmm(self.dmm)
        
        connectAndUpdate(self.rangeUpSb, thread.setAutoRangeUp)
        connectAndUpdate(self.rangeDownSb, thread.setAutoRangeDown)
        connectAndUpdate(self.autoRangeCb, thread.enableAutoRange)
        
        thread.finished.connect(self.threadFinished)
        thread.readingAvailable.connect(self.collectReading)
        self.intervalSb.valueChanged.connect(thread.setInterval)        
        self.workerThread = thread
        self.t0 = time.time()
        thread.start()
        self.enableControls(False)
        self.runPb.setText('Stop')

    def threadFinished(self):
        self.workerThread.deleteLater()
        self.workerThread = None
        self.flushBuffer()
        self.runPb.setText('Start')
        self.enableControls(True)
        
    def appendErrorMessage(self, message):
        self.errorTextEdit.append(message)        

    def enableControls(self, enable):
        self.readoutGroupBox.setEnabled(enable)
        self.bridgeCombo.setEnabled(enable)

    def restoreSettings(self):
        settings = QSettings()
        for widget in self.widgetsForSettings:
            restoreWidgetFromSettings(settings, widget)

    def saveSettings(self):
        settings = QSettings()
        for widget in self.widgetsForSettings:
            saveWidgetToSettings(settings, widget)

    def clearData(self):
        self.ts = []
        self.Rs = []
        self.Ts = []
        self.updatePlot()

    def collectReading(self, R, t):

        channel = self.avs.muxChannel.value
        excitation = self.avs.excitation.code
        Range = self.avs.range.code
        
        V = self.avs.excitation.value
        
        try:
            P = V**2/R
        except ZeroDivisionError:
            P = np.nan
        
        try:
            T = self.calibration.calculateTemperature([R])[0] # @todo This is really a crutch
        except Exception as e:
            self.appendErrorMessage(e)
            T = 0

        self.ts.append(t)
        self.Rs.append(R)
        self.Ts.append(T)

        string = "%.3f\t%d\t%d\t%d\t%.6g\n" % (t, channel, excitation, Range, R)
        self.buffer += string
        if len(self.buffer) > 2048:
            self.flushBuffer()


        Sensors = {0: 'FAA', 1:'GGG'}
        if self.publisher is not None:
            if Sensors.has_key(channel):
                sensorName = Sensors[channel]
                self.publisher.publishDict(sensorName, {'t': t, 'R': R, 'T': T, 'P': P})
            
        
        maxLength = 20000
        self.ts = pruneData(self.ts, maxLength)
        self.Rs = pruneData(self.Rs, maxLength)
        self.Ts = pruneData(self.Ts, maxLength)
            
        self.resistanceIndicator.setValue(R)
        self.temperatureIndicator.setKelvin(T)
        self.updatePlot()
        
            
    def flushBuffer(self):
        t = time.time()
        timeString = time.strftime('%Y%m%d', time.localtime(t))
        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))
        fileName = os.path.join(path,'AVSBridge_%s.dat' % timeString)
        
        if not os.path.isfile(fileName): # Maybe create new file
            x = '#Avs47SingleChannel.py\n'
            x+= '#Date=%s\n' % timeString
            x+= '#AVS-47=%s\n' % self.avs.visaId()
            if self.dmm is not None:
                x+= '#Readout=DMM\n'
                x+= '#DMM=%s\n' % self.dmm.visaId()
            else:
                x+= '#Readout=AVS-47\n'
            x+= '#'+'\t'.join(['time', 'channel', 'excitation', 'range', 'R'])+'\n'
            self.buffer = x+self.buffer

        try:
            with open(fileName, 'a') as f:
                f.write(self.buffer)
            self.buffer = ''
        except Exception as e:
            warnings.warn('Unable to write buffer to log file: %s' % e)
        
    def updatePlot(self):
        yaxis = self.yaxisCombo.currentText()
        if yaxis == 'R':
            self.curve.setData(self.ts, self.Rs)
        elif yaxis == 'T':
            self.curve.setData(self.ts, self.Ts)

    def closeEvent(self, e):
        if self.workerThread is not None:
            self.workerThread.stop()
            self.workerThread.wait(2000)
        self.saveSettings()


if __name__ == "__main__":
    import sys
    from PyQt4.QtGui import QApplication, QIcon
    import faulthandler
    with open('Avs47SingleChannel.log','a') as faultFile:
        faultFile.write('Avs47SingleChannel starting at %s\n' % time.time())
        faulthandler.enable(faultFile, all_threads=True)

        import ctypes
        myappid = u'WISCXRAYASTRO.ADR3.AVS47SINGLECHANNEL.1' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        app = QApplication(sys.argv)
        app.setApplicationName('Avs47SingleChannel')
        app.setOrganizationName('WiscXrayAstro')
        app.setOrganizationDomain('wisp.physics.wisc.edu')
        app.setApplicationVersion('0.2')
        app.setWindowIcon(QIcon('icons/thermometer_icon.jpg'))
    
        mw = Avs47SingleChannelWidget()
        mw.show()
        sys.exit(app.exec_())
        faultFile.write('Avs47SingleChannel ending at %s\n' % time.time())

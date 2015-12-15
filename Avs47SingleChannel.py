# -*- coding: utf-8 -*-
"""
Readout of AVS47 resistance bridge in single channel mode for simplicity
Created on Fri Dec 04 12:49:18 2015

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

import time
import datetime

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

from math import isnan

import Avs47Ui as Ui

#from Zmq.Zmq import ZmqRequestReplyThread, ZmqReply
#from Zmq.Zmq import RequestReplyThreadWithBindings
from Zmq.Zmq import ZmqPublisher
from Zmq.Ports import PubSub #,RequestReply

from LabWidgets.Utilities import connectAndUpdate, saveWidgetToSettings, restoreWidgetFromSettings
import pyqtgraph as pg
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import QSettings, pyqtSignal


import logging
logging.basicConfig(level=logging.WARN)


from Visa.AVS47 import Avs47
from Visa.Agilent34401A import Agilent34401A

from Calibration.RuOx600 import RuOx600
ruOx600 = RuOx600()

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
            except Exception,e:
                print "Having trouble getting DMM reading:", e
                print "Retrying..."
                pass
        print "Unable to get a reading from DMM after 10 tries!"
        return t, float('nan')
            
    def run(self):
        try:
            avs = self.avs
            dmm = self.dmm
            avs.checkPresence()
            channel = avs.muxChannel.value
            excitation = avs.excitation.value
            Range = avs.range.value
            print "Range:", Range
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
                            print "Range increase"
                            t = t + 4
                        except:
                            print "At maximum range"
                    elif R < 1E-2*self.rangeDownLevel*Range:
                        try:
                            avs.range.code -= 1
                            print "Range decrease"
                            t = t + 4
                        except:
                            print "At minimum range"
                self.sleepPrecise(t)
            avs.remote.enabled = False
                
        except Exception, e:
            self.handleException(e)

class Avs47SingleChannelWidget(Ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(Avs47SingleChannelWidget, self).__init__(parent)
        self.workerThread = None
        self.setupUi(self)
        self.outputFile = None
        self.yaxisCombo.currentIndexChanged.connect(self.switchPlotAxis)
        

        axis = pg.DateAxisItem(orientation='bottom')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis})
        self.plot.addLegend()
        self.verticalLayout.addWidget(self.plot)
        self.curve = pg.PlotCurveItem(name='Actual', symbol='o', pen='g')
        self.plot.addItem(self.curve)
        self.clearData()

        self.runPb.clicked.connect(self.runPbClicked)

        self.widgetsForSettings = [self.readoutInternalRadio, self.readoutDmmRadio, self.readoutZmqRadio, self.bridgeCombo, self.dmmCombo, self.autoRangeCb, self.rangeUpSb, self.rangeDownSb, self.yaxisCombo, self.intervalSb]
        self.restoreSettings()
        
        self.publisher = ZmqPublisher('Avs47SingleChannel', port = PubSub.AdrTemperature)

        #self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.AdrPidControl, parent=self)
        #boundWidgets = {'rampRate':self.rampRateSb, 'rampTarget':self.rampTargetSb, 'rampEnable':self.rampEnableCb, 'setpoint':self.setpointSb}
        #for name in boundWidgets:
            #self.serverThread.bindToWidget(name, boundWidgets[name])
        #self.serverThread.start()

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
        self.workerThread = thread
        self.t0 = time.time()
        thread.start()
        self.enableControls(False)
        self.runPb.setText('Stop')

    def threadFinished(self):
        self.workerThread.deleteLater()
        self.workerThread = None
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
        self.ts.append(t)
        self.Rs.append(R)
        
        T = ruOx600.calculateTemperature([R])[0] # @todo This is really a crutch
        self.publisher.publish('ADR_Sensor_R', R)
        self.publisher.publish('ADR_Temperature', T)
        
        self.Ts.append(T)
        
        maxLength = 20000
        self.ts = pruneData(self.ts, maxLength)
        self.Rs = pruneData(self.Rs, maxLength)
        self.Ts = pruneData(self.Ts, maxLength)
            
        self.resistanceIndicator.setValue(R)
        self.temperatureIndicator.setKelvin(T)
        self.updatePlot()

        channel = self.avs.muxChannel.value
        excitation = self.avs.excitation.code
        Range = self.avs.range.code
        
        string = "%.3f\t%d\t%d\t%d\t%.6g\n" % (t, channel, excitation, Range, R)
        import os.path
        timeString = time.strftime('%Y%m%d', time.localtime(t))
        fileName = 'AVSBridge_%s.dat' % timeString
        if not os.path.isfile(fileName): # Maybe create new file1
            with open(fileName, 'a+') as f:
                f.write('#Avs47SingleChannel.py\n')
                f.write('#Date=%s\n' % timeString)
                f.write('#AVS-47=%s\n' % self.avs.visaId())
                f.write('#Readout=DMM\n')
                f.write('#DMM=%s\n' % self.dmm.visaId())
                f.write('#'+'\t'.join(['time', 'channel', 'excitation', 'range', 'R'])+'\n')

        with open(fileName, 'a') as f:
            f.write(string)
        
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
    from PyQt4.QtGui import QApplication
    import faulthandler
    with open('Avs47SingleChannel.log','a') as faultFile:
        faultFile.write('Avs47SingleChannel starting at %s\n' % time.time())
        faulthandler.enable(faultFile, all_threads=True)

        app = QApplication(sys.argv)
        app.setApplicationName('Avs47SingleChannel')
        app.setOrganizationName('WiscXrayAstro')
        app.setOrganizationDomain('wisp.physics.wisc.edu')
        app.setApplicationVersion('0.1')
    
        mw = Avs47SingleChannelWidget()
        mw.show()
        sys.exit(app.exec_())
        faultFile.write('Avs47SingleChannel ending at %s\n' % time.time())

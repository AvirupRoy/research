# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 13:10:58 2015

@author: wisp10
"""

from PyQt4 import QtGui
from PyQt4.QtCore import QThread,QSettings,pyqtSignal
import numpy as np
import time
import LabWidgets.Utilities as ut
ut.compileUi('Ni4351_SingleChannel')
import Ni4351_SingleChannelUi as ui

try:
    from PyNi435x import Ni435x
except WindowsError, e:
    text = ("Windows was unable to load the NI-DAQ DLL: %s\n"
            "This could be because another program is using it. "
            "It is a single-process DLL therefore only one program may use it at a time.\n"
            "The work-around is to put all programs that need to use it into a single process. "
            "Try running from PyLegacyDaq_Combined.py instead!") % e
    print text
    app = QtGui.QApplication([])
    QtGui.QMessageBox.critical(None, "Unable to load NI-DAQ DLL", text)
    app.exec_()
    import sys
    sys.exit(1)

OrganizationName = 'McCammon X-ray Astro Physics'
ProgramName = 'PXI-4351 Single Channel'

class MeasurementThread(QThread):
    #dataAvailable = pyqtSignal(np.ndarray, np.ndarray)    
    dataAvailable = pyqtSignal(float, float)
    
    def setDaqDevice(self, deviceId, channel, rate, inputRange, groundRefEnable, plf=60):
        self.deviceId = deviceId
        self.channel = channel
        self.readingRate = rate
        self.range = inputRange
        self.groundRefEnabled = groundRefEnable
        self.plf = plf
        
    def stop(self):
        self._stopRequested = True
    
    def run(self):
        try:
            self._stopRequested = False
            daq = Ni435x(self.deviceId)        
            daq.setScanList([self.channel])
            if self.plf == 60:
                daq.setPowerLineFrequency(daq.PowerlineFrequency.F60Hz)
            elif self.plf == 50:
                daq.setPowerLineFrequency(daq.PowerlineFrequency.F50Hz)
            else:
                print "Unsupported power line frequency"
            if self.readingRate.upper() == 'FAST':
                rate = daq.ReadingRate.FAST
                samplesPerSecond = float(self.plf)
            else:
                rate = daq.ReadingRate.SLOW
                samplesPerSecond = 10.

            dt = 1./samplesPerSecond
                
            daq.enableGroundReference([self.channel], self.groundRefEnabled)
            daq.setReadingRate(rate)
            daq.setRange(-self.range, +self.range)
            daq.startAcquisition()
            t = time.time()
            sleep = 50
            
            while not self._stopRequested:
                d = daq.checkAndRead(timeOut=0)
                l = d.shape[1]
                if l > 0:
                    for i in range(l):
                        self.dataAvailable.emit(t, d[0][i])
                        t += dt
                self.msleep(sleep)
            daq.stopAcquisition()
        except:
            pass
        finally:
            del daq

import pyqtgraph as pg
        
class Ni4351SingleChannelWidget(QtGui.QWidget, ui.Ui_Form):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.populateUi()
        self.settingsWidgets = [self.deviceCombo, self.plfCombo, self.channelSb, self.rangeCombo, self.speedCombo, self.groundReferenceCb]
        self.restoreSettings()
        self.msmThread = None
        self.curve = pg.PlotCurveItem(name='', symbol='o', pen='k')
        self.plot.addItem(self.curve)
        self.clearData()
        self.startPb.clicked.connect(self.startMeasurement)
        self.clearPb.clicked.connect(self.clearData)
        self.savePb.clicked.connect(self.save)
        self.selectFilePb.clicked.connect(self.selectFile)
        self.loggingEnableCb.toggled.connect(self.loggingToggled)
        
    def populateUi(self):
#        import DAQ.PyNiLegacyDaq as ldaq
        
        deviceList = []        
#        for i in range(1, 10):
#            try:
#                dev = ldaq.Device(i)
#                model = dev.model
#                if model == 'PXI-4351':
#                    deviceList.append('DAQ::%d' % i)
#                del dev
#            except ldaq.LegacyDaqException:
#                break 
            
#        del ldaq
        deviceList.append('DAQ::2')
            
        self.deviceCombo.clear()
        self.deviceCombo.addItems(deviceList)
        
        ranges = [0.625, 1.25, 2.50, 3.75, 7.50, 15.00]
        self.rangeCombo.clear()
        for r in ranges:
            self.rangeCombo.addItem(u'±%5.3f V' % r, userData=r)

    def closeEvent(self, e):
        if self.msmThread is not None:
            self.msmThread.stop()
            self.msmThread.wait(2000)
            self.msmThread.deleteLater()
        self.saveSettings()
        super(Ni4351SingleChannelWidget, self).closeEvent(e)
        
    def restoreSettings(self):
        s = QSettings(OrganizationName, ProgramName)
        for w in self.settingsWidgets:
            ut.saveWidgetToSettings(s, w)
    
    def saveSettings(self):
        s = QSettings(OrganizationName, ProgramName)
        for w in self.settingsWidgets:
            ut.restoreWidgetFromSettings(s, w)
            
    def startMeasurement(self):
        dev = str(self.deviceCombo.currentText())
        plf = int(self.plfCombo.currentText()[0:2])
        self.channel = self.channelSb.value()
        inputRange,ok = self.rangeCombo.itemData(self.rangeCombo.currentIndex()).toFloat()
        gndRef = self.groundReferenceCb.isChecked()
        speed = str(self.speedCombo.currentText())
        self.msmThread = MeasurementThread(parent=self)
        self.msmThread.setDaqDevice(deviceId=dev, channel=self.channel, rate=speed, inputRange=inputRange, groundRefEnable=gndRef, plf=plf)
        self.msmThread.started.connect(self.disableGuiElements)
        self.msmThread.finished.connect(self.measurementStopped)
        self.msmThread.dataAvailable.connect(self.collectData)
        self.stopPb.clicked.connect(self.msmThread.stop)
        self.msmThread.start()
        
    def save(self):
        s = QSettings(OrganizationName, ProgramName)
        import os
        directory = s.value('dataDirectory', os.path.curdir, type=str)
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save data", directory, "TSV (*.dat);;CSV (*.csv);;Numpy (*.npz);;")
        fileName = str(fileName)
        if len(fileName) == 0:
            return
        extension =  os.path.basename(fileName).split('.')[-1].upper()
        directory = os.path.dirname(fileName)
        s.setValue('dataDirectory', directory)
        if extension in ['NPZ']:
            np.savez(fileName, t=self.ts, V=self.Vs)
        else:
            if extension in ['CSV']:
                delimiter = ','
            else:
                delimiter = '\t'
            np.savetxt(fileName, (self.ts, self.Vs), delimiter=delimiter, comments='#NI4351_SingleChannel\n#Channel=%d\n#' % self.channel)
            
    def selectFile(self):
        s = QSettings(OrganizationName, ProgramName)
        import os
        directory = s.value('dataDirectory', os.path.curdir, type=str)
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Select filename for logging", directory, "HDF5 (*.h5)")
        fileName = str(fileName)
        if len(fileName) == 0:
            return
        directory = os.path.dirname(fileName)
        s.setValue('dataDirectory', directory)
        self.fileNameLe.setText(fileName)
        
    def loggingToggled(self, checked):
        pass
#        if checked:
#            fileName = self.fileNameLe.text()
#            open(fileName, )
        

    def clearData(self):
        self.ts = []        
        self.Vs = []
        self.curve.setData(self.ts, self.Vs)
        
    def collectData(self, t, V):
        l = min(100, len(self.ts))
        if l > 0:
            DeltaTime = t - self.ts[-l]
            dt = DeltaTime/l
            rate = 1./dt
            self.rateSb.setValue(rate)
        self.ts.append(t)
        self.Vs.append(V)
        self.readingSb.setValue(V)
        self.curve.setData(self.ts, self.Vs)

    def disableGuiElements(self):
        self.enableGuiElements(False)
        
    def enableGuiElements(self, enable = True):
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(~enable)
        self.deviceGroupBox.setEnabled(enable)
        
    def measurementStopped(self):
        print "Done"
        self.msmThread.deleteLater()
        self.msmThread = None
        self.enableGuiElements(True)
            

if __name__ == '__main__':
    app = QtGui.QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName(ProgramName)
    app.setApplicationVersion('0.1')
    app.setOrganizationName(OrganizationName)
    mw = Ni4351SingleChannelWidget()
    mw.setWindowTitle('PXI-4351 Single Channel')
    mw.show()
    app.exec_()

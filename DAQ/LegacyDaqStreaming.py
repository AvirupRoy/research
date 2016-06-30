# -*- coding: utf-8 -*-
"""
Created on Thu Jan 14 17:20:42 2016

@author: wisp10
"""

OrganizationName = 'McCammon X-ray Astro Physics'
ApplicationName = 'legacy DAQ Streaming'
Version = '0.2'

from PyQt4 import uic
#uic.compileUiDir('.')
with open('LegacyDaqStreamingUi.py', 'w') as f:
    uic.compileUi('LegacyDaqStreamingUi.ui', f)
    print "Done compiling UI"

from PyQt4.QtGui import QWidget, QCheckBox, QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox

import LegacyDaqStreamingUi as Ui
import numpy as np
import pyqtgraph as pg
try:
    import PyNiLegacyDaq as daq
except WindowsError, e:
    text = ("Windows was unable to load the NI-DAQ DLL: %s\n"
            "This could be because another program is using it. "
            "It is a single-process DLL therefore only one program may use it at a time.\n"
            "The work-around is to put all programs that need to use it into a single process. "
            "Try running from PyLegacyDaq_Combined.py instead!") % e
    print text
    from PyQt4.QtGui import QApplication, QMessageBox
    app = QApplication([])
    QMessageBox.critical(None, "Unable to load NI-DAQ DLL", text)
    import sys
    sys.exit(1)
    
import time

from PyQt4.QtCore import QThread, QSettings, pyqtSignal, QString
from SignalProcessing import IIRFilter

class DaqThread(QThread):
    error = pyqtSignal(QString)
    dataReady = pyqtSignal(float, float, np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, channels, couplings, gains, rate, chunkTime, parent=None):
        super(DaqThread, self).__init__(parent)
        self.channels = channels
        self.couplings = couplings
        self.gains = gains
        self.sampleRate = rate
        self.chunkTime = chunkTime

    def stop(self):
        self.stopRequested = True

    def run(self):
        try:
            self.stopRequested = False
            d = daq.Device(1)
            d.configureTimeout(0.1)
            self.sampleRate = d.setAiClock(self.sampleRate)
            print "Actual data rate:", self.sampleRate
            dt = 1./self.sampleRate
            d.enableDoubleBuffering(True)
            print "Starting"
            for channel,coupling in zip(self.channels, self.couplings):
                d.setAiCoupling(channel, coupling=coupling)
            d.scanSetup(self.channels, self.gains)
            scales = np.asarray(d.aiScales())
            count = int(self.chunkTime*self.sampleRate)
            d.scanStart(samplesPerChannel = count)
            complete = False
            while not (self.stopRequested or complete):
                ready,complete = d.halfReady()
                if ready:
                    t = time.time()
                    data,rawData = d.data(raw=True)
                    self.dataReady.emit(t, dt, scales, data, rawData)
                self.msleep(100)
            
        except Exception, e:
            print "Exception", e
        finally:
            del d
import h5py as hdf

from Zmq.Zmq import ZmqPublisher
from Zmq.Ports import PubSub
from OpenSQUID.OpenSquidRemote import OpenSquidRemote, SquidRemote
class DaqStreamingWidget(Ui.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(DaqStreamingWidget, self).__init__(parent)
        self.setupUi(self)
        self.thread = None
        self.hdfFile = None
        self.columns = {'enabled':0, 'save': 1, 'coupling':2, 'mode':3, 'gain':4, 'squid':5, 'reset':6, 'label':7}
        self.plot.addLegend()
        self.plot.setLabel('left', 'voltage', units='V')
        self.plot.setLabel('bottom', 'time', units='s')
        self.curves = []
        self.runPb.clicked.connect(self.runPbClicked)
        self.bFilter = []
        self.aFilter = []
        self.populateUi()
        self.publisher = ZmqPublisher('LegacyDaqStreaming', port=PubSub.LegacyDaqStreaming)
        self.writeDataPb.toggled.connect(self.writeDataToggled)
        
    def populateUi(self):
        s = QSettings(OrganizationName, ApplicationName)
        d = daq.Device(1)
        gains = d.aiGains()
        ranges = [d.rangeForAiGain(gain) for gain in gains]
        nChannels = d.aiChannels
        fMin = d.sampleRateSpan[0]
        fMax = d.sampleRateSpan[1]
        del d
        self.sampleRateSb.setMinimum(fMin/1E3)
        self.sampleRateSb.setMaximum(fMax/1E3)
        self.sampleRateSb.setValue(s.value('sampleRate', 10E3, type=float))
        self.chunkTimeSb.setValue(s.value('chunkTime', 0.5, type=float))
        self.nameLe.setText(s.value('name', '', type=str))
        self.commentLe.setText(s.value('comment', '', type=str))
        self.lpfOrderSb.setValue(s.value('lpfOrder', 0, type=int))
        self.lpfFrequencySb.setValue(s.value('lpfFrequency', 0.1*fMax/1E3, type=float))
        self.resampleRateSb.setValue(s.value('resampleRateSb', 0.2*fMax/1E3, type=float))
        self.enablePlottingCb.setChecked(s.value('enablePlotting', True, type=bool))

        try:
            self.remote = OpenSquidRemote(port = 7894)
            squids = self.remote.findSquids()
            if squids is None:
                squids = []
        except Exception, e:
            print "OpenSQUID remote failed:", e
            squids = []
        
         
        table = self.channelTable
        table.setRowCount(nChannels)
        table.setVerticalHeaderLabels(['CH%d' % ch for ch in range(nChannels)])
        s.beginReadArray('ChannelSettings')
        for ch in range(nChannels):
            s.setArrayIndex(ch)
            gainCombo = QComboBox()
            for gain, fs in zip(gains, ranges):
                gainCombo.addItem(u'%+2ddB (±%.3f V)' % (gain, fs), userData=gain)
            gainCombo.setCurrentIndex(gainCombo.findData(s.value('gain', 0, type=int)))
            
            squidCombo = QComboBox()
            squidCombo.addItem('None')
            squidCombo.addItems(squids)
            squidCombo.setCurrentIndex(squidCombo.findText(s.value('squid', 'None', type=QString)))
            
            resetSb = QDoubleSpinBox()
            resetSb.setMinimum(0)
            resetSb.setMaximum(10)
            resetSb.setDecimals(2)
            resetSb.setSingleStep(0.01)
            resetSb.setAccelerated(True)
            resetSb.setValue(s.value('reset', 0, type=float))
 
            modeCombo = QComboBox()
            modeCombo.addItem('SE')
            modeCombo.addItem('DIFF')
            modeCombo.setCurrentIndex(modeCombo.findText(s.value('mode', 'SE', type=QString)))
            modeCombo.setToolTip('Select single-ended (SE) or differential (DIFF) input coupling via the switches on the break-out box. This setting is for informational purposes only.')
            
            couplingCombo = QComboBox()                
            couplingCombo.addItem('AC')
            couplingCombo.addItem('DC')
            couplingCombo.setCurrentIndex(couplingCombo.findText(s.value('coupling', 'AC', type=QString)))
            
            enabledCb = QCheckBox()
            enabledCb.setChecked(s.value('enabled', False, type=bool))
            saveCb = QCheckBox()
            saveCb.setChecked(s.value('save', False, type=bool))
            lpfSb = QDoubleSpinBox()
            lpfSb.setMinimum(0.1*fMax/1E3)
            lpfSb.setMaximum(0.5*fMax/1E3)
            lpfSb.setSuffix(' kHz')
            lpfSb.setValue(s.value('lpCutOffFrequency', 0, type=float))
            lpfOrderSb = QSpinBox()
            lpfOrderSb.setMinimum(0)
            lpfOrderSb.setMaximum(6)
            lpfOrderSb.setSpecialValueText('Off')
            lpfOrderSb.setValue(s.value('lpfOrder', 0, type=int))
            labelLe = QLineEdit()
            table.setCellWidget(ch, self.columns['enabled'], enabledCb)
            table.setCellWidget(ch, self.columns['save'], saveCb)
            table.setCellWidget(ch, self.columns['gain'], gainCombo)
            table.setCellWidget(ch, self.columns['mode'], modeCombo)
            table.setCellWidget(ch, self.columns['coupling'], couplingCombo)
            table.setCellWidget(ch, self.columns['squid'], squidCombo)
            table.setCellWidget(ch, self.columns['reset'], resetSb)
            table.setCellWidget(ch, self.columns['label'], labelLe)
        s.endArray()
        table.resizeColumnsToContents()
        
    def saveSettings(self):
        s = QSettings(OrganizationName, ApplicationName)
        s.beginWriteArray('ChannelSettings')
        t = self.channelTable
        for ch in range( t.rowCount() ) :
            s.setArrayIndex(ch)
            gainCombo = t.cellWidget(ch, self.columns['gain'])
            couplingCombo = t.cellWidget(ch, self.columns['coupling'])
            modeCombo = t.cellWidget(ch, self.columns['mode'])
            squidCombo = t.cellWidget(ch, self.columns['squid'])
            s.setValue('enabled', t.cellWidget(ch, self.columns['enabled']).isChecked())
            s.setValue('save', t.cellWidget(ch, self.columns['save']).isChecked())
            s.setValue('coupling', couplingCombo.currentText())
            s.setValue('mode', modeCombo.currentText())
            s.setValue('gain', gainCombo.itemData(gainCombo.currentIndex()))
            s.setValue('squid', squidCombo.currentText())
            s.setValue('reset', t.cellWidget(ch, self.columns['reset']).value())
            s.setValue('label', t.cellWidget(ch, self.columns['label']).text())
        s.endArray()            
        s.setValue('sampleRate', self.sampleRateSb.value())
        s.setValue('chunkTime', self.chunkTimeSb.value())
        s.setValue('name', self.nameLe.text())
        s.setValue('comment', self.commentLe.text())
        s.setValue('lpfOrder', self.lpfOrderSb.value())
        s.setValue('lpfFrequency', self.lpfFrequencySb.value())
        s.setValue('resampleRateSb', self.resampleRateSb.value())
        

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
        
    def removeAllCurves(self):
        for curve in self.curves:
            self.plot.removeItem(curve)
            del curve
        self.curves = []
        self.plot.plotItem.legend.items = []
        

    def runPbClicked(self):
        if self.thread:
            self.endThread()
        else:
            table = self.channelTable
            channels = []
            gains = []
            couplings = []
            modes = []
            labels = []
            squids = []
            resets = []
            self.saveChannels = []
            for ch in range(table.rowCount()):
                if not table.cellWidget(ch, self.columns['enabled']).isChecked():
                    continue
                channels.append(ch)
                gainCombo = table.cellWidget(ch, self.columns['gain'])
                gains.append(gainCombo.itemData(gainCombo.currentIndex()).toInt()[0])
                couplings.append(str(table.cellWidget(ch, self.columns['coupling']).currentText()))
                modes.append(str(table.cellWidget(ch, self.columns['mode']).currentText()))
                labels.append(str(table.cellWidget(ch, self.columns['label']).text()))
                squids.append(str(table.cellWidget(ch, self.columns['squid']).currentText()))
                resets.append(table.cellWidget(ch, self.columns['reset']).value())
                if table.cellWidget(ch, self.columns['save']).isChecked():
                    self.saveChannels.append(ch)
                    
            self.squids = squids
            self.resets = resets
            self.channels = channels
            self.removeAllCurves()                
            pens = 'rgbc'
            for ch in channels:
                curve = pg.PlotDataItem(pen=pens[ch], name='Channel %d' % ch)
                self.plot.addItem(curve)
                self.curves.append(curve)
            sampleRate = self.sampleRateSb.value()*1E3
            chunkTime = self.chunkTimeSb.value()
            thread = DaqThread(channels=channels, gains=gains, couplings=couplings, rate=sampleRate, chunkTime=chunkTime, parent=self)
            thread.dataReady.connect(self.collectData)
            self.enableWidgets(False)
            self.thread = thread
            self.makeFilters()
            self.t0 = None
            self.channelTable.setEnabled(False)
            thread.start()
            thread.finished.connect(self.threadFinished)

    def threadFinished(self):
        self.closeFile()
        self.enableWidgets(True)
            
    def createFile(self):
        fileName = '%s_%s.h5' % (self.nameLe.text(), time.strftime('%Y%m%d_%H%M%S'))
        hdfFile = hdf.File(fileName, mode='w')
        hdfFile.attrs['Program'] = ApplicationName
        hdfFile.attrs['Version'] = Version
        hdfFile.attrs['TimeLocal'] = time.strftime('%Y-%m-%d %H:%M:%S')
        hdfFile.attrs['TimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())
        self.hdfFile = hdfFile
        self.dset = None
        
    def closeFile(self):
        if self.hdfFile is not None:
            self.hdfFile.close()
            del self.hdfFile
            self.hdfFile = None
            self.dset = None
        
    def makeDataset(self):
        count = 0
        for group in self.hdfFile.keys(): # Figure out the highest group number we have
            try:
                x = int(group)
                if x > count:
                    count = x
            except:
                pass

        table = self.channelTable
        activeLabels = []
        activeModes = []
        for ch in range(table.rowCount()):
            if not table.cellWidget(ch, self.columns['enabled']).isChecked():
                continue
            activeLabels.append(str(table.cellWidget(ch, self.columns['label']).text()))
            activeModes.append(str(table.cellWidget(ch, self.columns['mode']).currentText()))

        grp = self.hdfFile.create_group('%04d' % (count+1))
        grp.attrs['TimeLocal'] =  time.strftime('%Y-%m-%d %H:%M:%S')
        grp.attrs['TimeUTC'] =  time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())
        grp.attrs['Channels'] = self.saveChannels
        grp.attrs['Gains'] = self.thread.gains
        grp.attrs['Couplings'] = self.thread.couplings
        grp.attrs['Modes'] = activeModes
        grp.attrs['SampleRate'] = self.thread.sampleRate
        grp.attrs['ChunkTime'] = self.thread.chunkTime
        grp.attrs['Labels'] = activeLabels
        nChannels = len(self.saveChannels)
        self.dset = grp.create_dataset("rawData", (nChannels,0), maxshape=(nChannels, None), chunks=(nChannels, 8192), dtype=np.int16, compression='lzf', shuffle=True, fletcher32=True)
        self.dset.attrs['units'] = 'ADC counts'
        self.dsetTimeStamps = grp.create_dataset('timeStamps', (0,), maxshape=(None,), chunks=(500,), dtype=np.float64)
        self.dsetTimeStamps.attrs['units'] = 's'
            
    def enableWidgets(self, enable):
        self.channelTable.setEnabled(enable)
        self.samplingGroupBox.setEnabled(enable)
        self.lpfGroupBox.setEnabled(enable)
        if enable:
            self.runPb.setText('Run')
        else:
            self.runPb.setText('Stop')
                        
    def makeFilters(self):
        order = self.lpfOrderSb.value()
        self.filters = []
        if order == 0:
            return
        fc = self.lpfFrequencySb.value()*1E3
        fs = self.sampleRateSb.value()*1E3
        for i in range(self.channels):
            lpf = IIRFilter.lowpass(order, fc, fs)
            self.filters.append(lpf)
            
    def writeDataToggled(self, checked):
        print "Toggled:", checked

    def collectData(self, timeStamp, dt, scales, data, rawData):
        if self.t0 is None:
            self.t0 = timeStamp
        nChannels = data.shape[0]
        nSamples  = data.shape[-1] # New samples in this chunk

        if self.writeDataPb.isChecked() and len(self.saveChannels)>0:
            if self.hdfFile is None:
                self.createFile()       # Make file if we don't have one
            if self.dset is None:
                self.makeDataset()      # Make dataset if we don't have one
            elif self.dset.shape[-1] >= (2**31 - nSamples):
                self.makeDataset()      # Start a new dataset if we reach or exceed 2 GSamples
            # Write the data
            oldShape = self.dset.shape
            self.dset.resize(oldShape[1]+nSamples, axis=1)
            saveChannels = [x in self.saveChannels for x in self.channels] # True/False vector to extract the channels we'd like to save
            saveChannels = np.where(saveChannels)[0] # Now get the indices of those channels
            self.dset[:, -nSamples:] = rawData[saveChannels,:]
            samplesInDataset = self.dset.shape[-1]
            self.dsetTimeStamps.resize((self.dsetTimeStamps.shape[0]+1,))
            self.dsetTimeStamps[-1] = timeStamp
        else:
            self.dset = None # Finished with the current dataset
            samplesInDataset = 0

        t = np.arange(0, nSamples)*dt
        plotting = self.enablePlottingCb.isChecked()
        for i in range(nChannels):
            y = data[i]
            squidId = self.squids[i]
            reset = self.resets[i]
            if squidId != 'None' and reset > 0:
                if np.abs(np.mean(y)) > reset:
                    remote = self.remote.obtainSquidRemote(squidId)
                    result = remote.resetPfl()
                    print "Reset SQUID:", squidId
            if plotting:
                self.curves[i].setData(t, y)
            dataSet = {'t': timeStamp, 'dt': dt}
            channel = 'Channel%d' % self.channels[i]
            self.publisher.publish(channel, dataSet, arrays={channel: y})
        self.nSamplesLe.setText("{:,}".format(samplesInDataset))
        self.elapsedTimeLe.setText('%.3f s' % (timeStamp-self.t0))


if __name__ == '__main__':
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARN)
    logging.getLogger('Zmq.Zmq').setLevel(logging.WARN)
   
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ApplicationName)    

    import psutil, os
    p = psutil.Process(os.getpid())
    p.set_nice(psutil.HIGH_PRIORITY_CLASS)
    
    from PyQt4.QtGui import QApplication, QIcon
    app = QApplication([])
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName(ApplicationName)
    app.setApplicationVersion(Version)
    app.setOrganizationName(OrganizationName)
    app.setWindowIcon(QIcon('../Icons/LegacyDaqStreaming.png'))
    widget = DaqStreamingWidget()
    widget.setWindowTitle('%s (%s)' % (ApplicationName, Version))
    widget.show()
    app.exec_()

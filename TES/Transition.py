# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 13:27:43 2015

@author: wisp10
"""

# -*- coding: utf-8 -*-
"""
Created on Fri May 22 13:03:06 2015

@author: wisp10
"""

from LabWidgets.Utilities import compileUi
compileUi('TransitionUi')
import TransitionUi as ui

from PyQt4.QtGui import QWidget, QDoubleSpinBox, QSpinBox, QHeaderView
from PyQt4.QtCore import QObject, pyqtSignal, QThread, QSettings, QString, QByteArray


from Visa.Agilent34401A import Agilent34401A
from Visa.SR830 import SR830
from Zmq.Subscribers import HousekeepingSubscriber
from Zmq.Zmq import ZmqBlockingRequestor, ZmqRequest

from AnalogSource import VoltageSourceSR830, VoltageSourceDaq
from AnalogMeter import VoltmeterSR830, VoltmeterDmm, VoltmeterDaq

import numpy as np
import time

class TransitionMeasurement(QThread):
    class State:
        RAMP_TO_START = 2
        RAMP_DOWN = 3
        RAMP_UP = 4
        FINISHED = 5

    class RampSpeed:
        HOLD = 0
        SLOW = 1
        FAST = 2

    class RampDirection:
        UP = 1
        DOWN = 2
    # t, T, Vdc, f, X, Y, state, driveEnabled
    measurementReady = pyqtSignal(float, float, float, float, float, float, int, bool)
    error = pyqtSignal(str)

    def __init__(self, dcSource, dcMeter, acSource, acMeter, parent=None):
        QThread.__init__(self, parent)
        self.dcSource = dcSource
        self.dcMeter = dcMeter
        self.acSource = acSource
        self.acMeter = acMeter
        self.paused = False
        self.requestor = ZmqBlockingRequestor(port=7000, origin='Transition2')
        self.T = np.nan
        self.cycles = 1
        self.driveEnabled = False

    def togglePause(self):
        self.paused = not self.paused

    def announce(self, string):
        self.error.emit('Cycle %d: %s' % (self.cycleCount, string))

    def setTemperatureRange(self, Tmin, Tmax):
        self.Tmin = Tmin
        self.Tmax = Tmax

    def setRampRate(self, rateSlow, rateFast=None):
        self.rateSlow = rateSlow
        if rateFast is None:
            self.rateFast = 5*rateSlow
        else:
            self.rateFast = rateFast

    def setCycles(self, cycles):
        self.cycles = cycles

    def setExcitationParameters(self, f, Vac, Vdc):
        self.f = f
        self.acDrive = Vac
        self.dcDrive = Vdc

    def stop(self):
        self.stopRequested = True
        print "Stop requested:", self.stopRequested

    def pause(self, pause=True):
        self.paused = pause

    def unpause(self):
        self.pause(False)

    def updateTemperature(self, T):
        self.T = T

    def measure(self):
        t = time.time()
        if self.dcMeter is not None:
            Vdc = self.dcMeter.measureDc()
        else:
            Vdc = np.nan
        if self.acMeter is not None:
            X,Y,f = self.acMeter.measureAc()
        else:
            X,Y,f = [np.nan, np.nan, np.nan]
        self.measurementReady.emit(t, self.T, Vdc, f, X, Y, self.state, self.driveEnabled)

    def requestRampRate(self, direction, speed):
        if speed == self.RampSpeed.SLOW:
            rate = self.rateSlow
        elif speed == self.RampSpeed.FAST:
            rate = self.rateFast
        elif speed == self.RampSpeed.HOLD:
            rate = 0.

        if direction == self.RampDirection.UP:
            rate = 1.0*rate
        elif direction == self.RampDirection.DOWN:
            rate = -1.0*rate
        elif direction == self.RampDirection.HOLD:
            rate = 0

        request = ZmqRequest('RAMPRATE %f' % rate)
        try:
            reply = self.requestor.request(request.query)
            if reply != 'OK':
                self.error.emit('Unable to change ramp rate. Response was:%s' % reply)
        except Exception, e:
            self.error.emit(str(e))
        self.announce('New ramp rate: %.1f' % rate)

    def rampToStart(self):
        self.announce('Ramping to start')
        deltaT = self.T - self.Tmax
        speed = self.RampSpeed.FAST if abs(deltaT) > 0.05 else self.RampSpeed.SLOW
        direction = self.RampDirection.UP if deltaT < 0.02 else self.RampDirection.DOWN
        self.state = self.State.RAMP_TO_START
        self.requestRampRate(direction, speed)

    def rampDown(self):
        self.announce('Ramping down')
        self.state = self.State.RAMP_DOWN
        self.requestRampRate(self.RampDirection.DOWN, self.RampSpeed.SLOW)

    def rampUp(self):
        self.announce('Ramping up')
        self.state = self.State.RAMP_UP
        self.requestRampRate(self.RampDirection.UP, self.RampSpeed.SLOW)

    def hold(self):
        self.announce('Holding')
        self.requestRampRate(self.RampDirection.UP, self.RampSpeed.HOLD)

    def handleTemperatureRamp(self):
        if self.state == self.State.RAMP_TO_START:
            deltaT = self.T - self.Tmax
            if deltaT > 0 and deltaT < 0.02:
                self.hold()
                self.measureZero()
                self.enableDrive()
                self.mySleep(3)
                if self.acMeter is not None:
                    self.announce('Auto gain')
                    self.acMeter.autoGain()
                    self.mySleep(5)
                self.rampDown()
        elif self.state == self.State.RAMP_DOWN:
            deltaT = self.T - self.Tmin
            if deltaT < 0:
                self.hold()
                self.measureZero()
                self.enableDrive()
                self.rampUp()
        elif self.state == self.State.RAMP_UP:
            deltaT = self.T - self.Tmax
            if deltaT > 0:
                self.hold()
                self.measureZero()
                self.cycleCount += 1
                if self.cycleCount < self.cycles:
                    self.announce('Finished, cycling again.')
                    self.rampToStart()
                else:
                    self.announce('Finished')
                    self.state = self.State.FINISHED

    def measureZero(self):
        self.enableDrive(False)
        self.mySleep(5)
        self.announce('Measuring zero')
        self.measure()

    def enableDrive(self, enable = True):
        if self.dcSource is not None:
            if enable:
                self.dcSource.setDcDrive(self.dcDrive)
                self.announce('Enabling DC drive')
            else:
                self.dcSource.setDcDrive(0)
                self.announce('Disabling DC drive')

        if self.acSource is not None:
            if enable:
                self.acSource.setAcDrive(self.f, self.acDrive)
                self.announce('Enabling AC drive')
            else:
                self.acSource.setAcDrive(self.f, 0.004)
                self.announce('Disabling AC drive')
        self.driveEnabled = enable
        self.mySleep(2)

    def mySleep(self, time):
        for i in range(int(2*time)):
            if self.stopRequested:
                break
            self.msleep(500)

    def run(self):
        try:
            self.stopRequested = False
            i = 0
            while np.isnan(self.T):
                self.mySleep(1)
                i += 1
                if i > 20:
                    self.error('No valid temperature reading received.')
                    return
            print "Thread running"

            self.cycleCount = 0

            self.rampToStart()

            self.enableDrive(False)
            self.measure()
            self.enableDrive(True)

            while not (self.state == self.State.FINISHED or self.stopRequested):
                self.handleTemperatureRamp()
                self.measure()
                self.sleep(1)
                while self.paused and not self.stopRequested:
                    self.mySleep(1)
            self.enableDrive(False)
            if self.stopRequested:
                print "Stopping"

        except Exception, e:
            self.error.emit(str(e))
        print "Thread done"


class FrequencySpinBox(QDoubleSpinBox):
    def __init__(self, value=333.8, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setMaximum(10E3)
        self.setMinimum(0.1)
        self.setDecimals(3)
        self.setSuffix(' Hz')
        self.setSingleStep(0.1)
        self.setValue(value)

class DcDriveSpinBox(QDoubleSpinBox):
    def __init__(self, value=0.1, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setMaximum(+10.)
        self.setMinimum(-10.)
        self.setDecimals(3)
        self.setSuffix(' V')
        self.setSingleStep(0.001)
        self.setValue(value)

class AcDriveSpinBox(QDoubleSpinBox):
    def __init__(self, value=0.1, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setMaximum(+5.)
        self.setMinimum(0.004)
        self.setDecimals(3)
        self.setSuffix(' V')
        self.setSingleStep(0.002)
        self.setValue(value)

from DAQ.PyDaqMxGui import AoConfigLayout, AiConfigLayout

def saveCombo(combo, settings):
    settings.setValue(combo.objectName(), combo.currentText())

def restoreCombo(combo, settings):
    i = combo.findText(settings.value(combo.objectName(), '', type=str))
    combo.setCurrentIndex(i)

def killInstrument(instrument):
    if instrument is not None:
        instrument.clear()

import pyqtgraph as pg

from scipy.signal import butter, filtfilt

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filtfilt(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def smooth(data):
    return butter_lowpass_filtfilt(data, 0.1, 1, order=4)

def instrumentVisaId(instrument):
    if instrument is None:
        return "None"
    else:
        return instrument.visaId()

class TransitionWidget(ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(TransitionWidget, self).__init__(parent)
        self.sr830 = None
        self.setupUi(self)
        self.outputFile = None
        self.runningRow = None

        self.plot.addLegend()
        self.curveDc = pg.PlotCurveItem(name='DC', symbol='o', pen='g', )
        self.curveAcX = pg.PlotCurveItem(name='X', symbol='o', pen='r')
        self.curveAcY = pg.PlotCurveItem(name='Y', symbol='o', pen='b', )
        #self.curveT = pg.PlotCurveItem(name='T', pen='k')
        self.plot.addItem(self.curveDc)
        self.plot.addItem(self.curveAcX)
        self.plot.addItem(self.curveAcY)
        #self.plot.addItem(self.curveT)

        self.VdcZero = 0
        self.clearData()

        self.nextBiasPointSb.setValue(1)
        self.msmThread = None
        self.aiConfig = AiConfigLayout(parent=self.aiGroupBox)
        self.aoConfig = AoConfigLayout(parent=self.aoGroupBox)
        self.restoreSettings()
        #self.plot = self.plotWidget.canvas.ax.plot([], 'o', label='')
        self.startPb.clicked.connect(self.startPbClicked)
        self.stopPb.clicked.connect(self.stopPbClicked)
        self.addRowPb.clicked.connect(self.addRowClicked)
        for i in range(0, self.biasTable.columnCount()):
            self.biasTable.horizontalHeader().setResizeMode( i, QHeaderView.ResizeToContents )
        self.deleteRowPb.clicked.connect(self.deleteRowClicked)
        self.hkSub = HousekeepingSubscriber(self)
        self.hkSub.adrTemperatureReceived.connect(self.temperatureSb.setValue)
        self.hkSub.start()

        self.clearPb.clicked.connect(self.clearData)

        self.minTempSb.valueChanged.connect(self.updateTemps)
        self.maxTempSb.valueChanged.connect(self.updateTemps)

        self.xAxisCombo.currentIndexChanged.connect(self.updatePlot)
        self.yAxisCombo.currentIndexChanged.connect(self.updatePlot)

    def updateTemps(self):
        self.maxTempSb.setMinimum(self.minTempSb.value()+0.02)
        self.minTempSb.setMaximum(self.maxTempSb.value()-0.02)
        if self.msmThread is not None:
            self.msmThread.setTemperatureRange(self.minTempSb.value(), self.maxTempSb.value())

    def finished(self):
        print "ADR temp thread finished!"

    def makeSr830(self):
        if self.sr830 is None:
            self.sr830 = SR830(str(self.sr830VisaCombo.currentText()))
        if not 'SR830' in self.sr830.visaId():
            self.updateStatus('SR830 not found.')

    def startPbClicked(self):
        self.acSource = None
        self.acMeter = None
        self.dcSource = None
        self.dcMeter = None
        self.stop = False

        if self.acGroupBox.isChecked():
            self.makeSr830()
            self.acSource = VoltageSourceSR830(self.sr830,1)
            self.acMeter = VoltmeterSR830(self.sr830)

        if self.dcGroupBox.isChecked():
            readout = self.dcReadoutCombo.currentText()
            if readout == 'DMM':
                self.dmm = Agilent34401A(self.dmmVisaCombo.currentText())
                if not '34401A' in self.dmm.visaId():
                    self.updateStatus('Agilent DMM not found.')
                    return
                self.dcMeter = VoltmeterDmm(self.dmm)
            elif readout == 'DAQ AI':
                print "DAQ AI"
                r = self.aiConfig.voltageRange()
                self.dcMeter = VoltmeterDaq(self.aiConfig.device(), self.aiConfig.channel(), r.min, r.max)
            else:
                print "Unknown DC readout:", readout

            source = self.dcSourceCombo.currentText()

            if 'SR830' in source:
                self.makeSr830()
                auxOut = int(source[-1])
                self.dcSource = VoltageSourceSR830(self.sr830, auxOut)
            elif source == 'DAQ AO':
                r = self.aoConfig.voltageRange()
                self.dcSource = VoltageSourceDaq(self.aoConfig.device(), self.aoConfig.channel(), r.min, r.max)
            else:
                print "Unknown DC source:", source
        self.enableWidgets(False)
        self.updateStatus('Running')
        self.runNextMeasurement()

    def runNextMeasurement(self):
        print "Run next measurement?"
        if self.runningRow is not None:
            self.enableTableRow(self.runningRow)

        if self.outputFile is not None:
            self.outputFile.close()
        i = self.nextBiasPointSb.value()
        n = self.biasTable.rowCount()
        print "i,n", i, n
        if i > n or self.stop:
            print "Killing all measurements"
            self.msmThread.deleteLater()
            self.msmThread = None
            killInstrument(self.acSource); self.acSource = None
            killInstrument(self.acMeter); self.acMeter = None
            killInstrument(self.dcMeter); self.dcMeter = None
            killInstrument(self.dcSource); self.dcSource = None

            self.nextBiasPointSb.setValue(1)
            self.enableWidgets(True)
            self.updateStatus('Completed')
            return
        else:
            self.scheduleMeasurement(i-1)
            i += 1
            self.nextBiasPointSb.setValue(i)

    def enableTableRow(self, row, enable=True):
        if not enable:
            styleSheet = "background-color:yellow;"
        else:
            styleSheet = ""
        for c in range(4):
            widget = self.biasTable.cellWidget(row,c)
            if widget is not None:
                widget.setEnabled(enable)
                widget.setStyleSheet(styleSheet)


    def scheduleMeasurement(self, row):
        f = self.biasTable.cellWidget(row, 0).value()
        Vac = self.biasTable.cellWidget(row, 1).value()
        Vdc = self.biasTable.cellWidget(row, 2).value()
        cycles = self.biasTable.cellWidget(row, 3).value()

        self.gain = self.preampGainSb.value()

        self.msmThread = TransitionMeasurement(self.dcSource, self.dcMeter, self.acSource, self.acMeter, self)
        self.msmThread.setTemperatureRange(self.minTempSb.value(), self.maxTempSb.value())
        self.msmThread.setRampRate(self.rampRateSb.value())
        self.msmThread.setCycles(cycles)
        self.msmThread.setExcitationParameters(f, Vac, Vdc)

        sm = str(self.sourceModeCombo.currentText())
        scaleSI = {'m':1E-3,' ':1, u'μ': 1E-6, 'u':1E-6, 'n':'1E-9'}
        if sm == 'Voltage source':
            self.Iac = Vac / self.acDriveImpedanceSb.value()
            self.Idc = Vdc / self.dcDriveImpedanceSb.value()
        else:
            i = sm.find('A')
            exponent = sm[i-1:i]
            print "Exponent:", exponent
            exponent = scaleSI[exponent]
            scale = float(sm[:i-2])*exponent
            print "Full scale:",scale
            scale /= 5.0
            print "Scale:", scale
            self.Iac = Vac * scale
            self.Idc = Vdc * scale

        self.msmThread.measurementReady.connect(self.collectMeasurement)
        self.hkSub.adrTemperatureReceived.connect(self.msmThread.updateTemperature)
        self.msmThread.error.connect(self.errorDisplay.append)
        self.msmThread.finished.connect(self.runNextMeasurement)
        self.rampRateSb.valueChanged.connect(self.msmThread.setRampRate)
        self.skipPb.clicked.connect(self.msmThread.stop)

        self.enableTableRow(row, False)
        self.runningRow = row

        self.msmThread.start()
        print "Thread started"

        timeString = time.strftime('%Y%m%d-%H%M%S')
        fileName = self.sampleLineEdit.text()+'_%s_Sweep.dat' % timeString
        self.outputFile = open(fileName, 'a+')
        self.outputFile.write('#Program=Transition2.py\n')
        self.outputFile.write('#Date=%s\n' % timeString)
        self.outputFile.write('#Sample=%s\n' % self.sampleLineEdit.text())
        self.outputFile.write('#Comment=%s\n' % self.commentLineEdit.text())
        self.outputFile.write('#Source=%s\n' % self.sourceModeCombo.currentText())
        self.outputFile.write('#Pre-amp gain=%.5g\n' % self.preampGainSb.value())
        self.outputFile.write('#DC drive enabled=%d\n' % self.dcGroupBox.isChecked())
        self.outputFile.write('#DC drive impedance=%.6g\n' % self.dcDriveImpedanceSb.value())
        self.outputFile.write('#DC drive source=%s\n' % self.dcSourceCombo.currentText())
        self.outputFile.write('#DC readout=%s\n' % self.dcReadoutCombo.currentText())
        self.outputFile.write('#AC drive enabled=%d\n' % self.acGroupBox.isChecked())
        self.outputFile.write('#AC drive impedance=%.6g\n' % self.dcDriveImpedanceSb.value())
        self.outputFile.write('#Temperature sweep min=%.6g\n' % self.minTempSb.value())
        self.outputFile.write('#Temperature sweep max=%.6g\n' % self.maxTempSb.value())
        self.outputFile.write('#Temperature sweep magnet ramp rate=%.6g\n' % self.rampRateSb.value())
        self.outputFile.write('#DC source ID=%s\n' % instrumentVisaId(self.dcSource))
        self.outputFile.write('#AC source ID=%s\n' % instrumentVisaId(self.acSource))
        self.outputFile.write('#DC meter ID=%s\n' % instrumentVisaId(self.dcMeter))
        self.outputFile.write('#AC meter ID=%s\n' % instrumentVisaId(self.acMeter))
        self.outputFile.write('#'+'\t'.join(['time', 'T', 'Vdc', 'f', 'X', 'Y', 'state', 'enabled' ])+'\n')

    def clearData(self):
        self.ts = []
        self.Ts = []
        self.Vdcs = []
        self.Rdcs = []
        self.fs = []
        self.Xs = []
        self.Ys = []
        self.RxAcs = []
        self.RyAcs = []
        self.updatePlot()

    def collectMeasurement(self, t, T, Vdc, f, X, Y, state, enabled):
        string = "%.3f\t%.6f\t%.6g\t%.4g\t%.6g\t%.6g\t%d\t%d\n" % (t, T, Vdc, f, X, Y, state, enabled)
        self.outputFile.write(string)

        #print "Collecting data:", enabled, state, t
        Vdc /= self.gain
        X /= self.gain
        Y /= self.gain

        if not enabled:
            self.VdcZero = Vdc
            print "New offset voltage:", self.VdcZero
            return
        self.ts.append(t)
        self.Ts.append(T)
        self.Vdcs.append(Vdc)
        if self.Idc != 0:
            Rdc = (Vdc-self.VdcZero)/self.Idc
        else:
            Rdc = np.nan
        self.Rdcs.append(Rdc)
        self.fs.append(f)
        self.Xs.append(X)
        self.Ys.append(Y)
        if self.Iac != 0:
            RxAc = X / self.Iac
            RyAc = Y / self.Iac
        else:
            RxAc = np.nan
            RyAc = np.nan
        self.RxAcs.append(RxAc)
        self.RyAcs.append(RyAc)
        self.updatePlot()

    def updatePlot(self):
        xAxis = self.xAxisCombo.currentText()
        if xAxis == 'Time':
            t0 = self.ts[0] if len(self.ts) > 0 else 0
            x = np.asarray(self.ts) - t0
            self.plot.setLabel('bottom', 'time', units='s')
        elif xAxis == 'T (raw)':
            x = self.Ts
            self.plot.setLabel('bottom', 'T', units='K')
        elif xAxis == 'T (smooth)':
            x = smooth(self.Ts)
            self.plot.setLabel('bottom', 'T (smooth)', units='K')

        yAxis = self.yAxisCombo.currentText()
        if yAxis == 'Voltage':
            dc = self.Vdcs
            acx = self.Xs
            acy = self.Ys
            self.plot.setLabel('left', 'V', units='V')
        elif yAxis == 'Resistance':
            dc = self.Rdcs
            acx = self.RxAcs
            acy = self.RyAcs
            self.plot.setLabel('left', 'R', units=u'Ω')

        self.curveDc.setData(x, dc)
        self.curveAcX.setData(x, acx)
        self.curveAcY.setData(x, acy)
        #self.curveT.setData(x, self.Ts)

    def updateStatus(self, message):
        self.stateLineEdit.setText(message)

    def enableWidgets(self, enable=True):
        self.sampleLineEdit.setEnabled(enable)
        self.startPb.setEnabled(enable)
        self.pausePb.setEnabled(not enable)
        self.skipPb.setEnabled(not enable)
        self.stopPb.setEnabled(not enable)
        self.acDriveImpedanceSb.setEnabled(enable)
        self.dcDriveImpedanceSb.setEnabled(enable)
        self.acGroupBox.setEnabled(enable)
        self.dcGroupBox.setEnabled(enable)

    def pausePbClicked(self):
        print "Pause"
        if self.msmThread:
            self.msmThread.togglePause()

    def stopPbClicked(self):
        self.msmThread.stop()
        self.stop = True

    def addRowClicked(self, f=333.8, Vac=0.1, Vdc=0.0, cycles=1):
        row = self.biasTable.currentRow()
        if row < 1:
            row = 0
        self.biasTable.insertRow(row)
        fSb = FrequencySpinBox()
        fSb.setValue(f)
        acSb = AcDriveSpinBox()
        acSb.setValue(Vac)
        dcSb = DcDriveSpinBox()
        dcSb.setValue(Vdc)
        self.biasTable.setCellWidget(row, 0, fSb)
        self.biasTable.setCellWidget(row, 1, acSb)
        self.biasTable.setCellWidget(row, 2, dcSb)
        cycleSpinBox = QSpinBox()
        cycleSpinBox.setMinimum(0)
        cycleSpinBox.setMaximum(20)
        cycleSpinBox.setValue(cycles)
        self.biasTable.setCellWidget(row, 3, cycleSpinBox)
        return row

    def deleteRowClicked(self):
        row = self.biasTable.currentRow()
        self.biasTable.removeRow(row)
        print "Delete row"

    def closeEvent(self, e):
        if self.msmThread is not None:
            self.msmThread.stop()
        if self.hkSub:
            self.hkSub.stop()
        self.saveSettings()
        super(TransitionWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()
        s.setValue('sampleId', self.sampleLineEdit.text())
        s.setValue('comment', self.commentLineEdit.text())
        saveCombo(self.sourceModeCombo, s)
        s.setValue('acDriveImpedance', self.acDriveImpedanceSb.value() )
        s.setValue('dcDriveImpedance', self.dcDriveImpedanceSb.value() )
        s.setValue('acDriveEnable', self.acGroupBox.isChecked() )
        s.setValue('dcDriveEnable', self.dcGroupBox.isChecked() )
        saveCombo(self.dcSourceCombo, s)
        saveCombo(self.dcReadoutCombo, s)
        s.setValue('dcSource', self.dcSourceCombo.currentText() )
        s.setValue('dcReadout', self.dcReadoutCombo.currentText() )
        s.setValue('minTemp', self.minTempSb.value())
        s.setValue('maxTemp', self.maxTempSb.value())
        s.setValue('rampRate', self.rampRateSb.value())
        s.setValue('preampGain', self.preampGainSb.value())
        s.setValue('geometry', self.saveGeometry())
        saveCombo(self.sr830VisaCombo, s)
        saveCombo(self.dmmVisaCombo, s)

        s.beginGroup('ai'); self.aiConfig.saveSettings(s); s.endGroup()
        s.beginGroup('ao'); self.aoConfig.saveSettings(s); s.endGroup()

        nRows = self.biasTable.rowCount()
        s.beginWriteArray('biasTable', nRows)
        for row in range(nRows):
            s.setArrayIndex(row)
            s.setValue('f', self.biasTable.cellWidget(row,0).value())
            s.setValue('Vac', self.biasTable.cellWidget(row,1).value())
            s.setValue('Vdc', self.biasTable.cellWidget(row,2).value())
            s.setValue('cycles', self.biasTable.cellWidget(row,3).value())
        s.endArray()


    def restoreSettings(self):
        s = QSettings()
        self.sampleLineEdit.setText(s.value('sampleId', '', type=QString))
        self.commentLineEdit.setText(s.value('comment', '', type=QString))
        restoreCombo(self.sourceModeCombo, s)
        self.acDriveImpedanceSb.setValue(s.value('acDriveImpedance', 10E3, type=float))
        self.dcDriveImpedanceSb.setValue(s.value('dcDriveImpedance', 10E3, type=float))
        self.acGroupBox.setChecked(s.value('acDriveEnable', True, type=bool))
        self.dcGroupBox.setChecked(s.value('dcDriveEnable', True, type=bool))
        restoreCombo(self.dcSourceCombo, s)
        restoreCombo(self.dcReadoutCombo, s)
        self.minTempSb.setValue(s.value('minTemp', 0.05, type=float))
        self.maxTempSb.setValue(s.value('maxTemp', 0.20, type=float))
        self.rampRateSb.setValue(s.value('rampRate', 10., type=float))
        self.preampGainSb.setValue(s.value('preampGain', 1., type=float))
        restoreCombo(self.sr830VisaCombo, s)
        restoreCombo(self.dmmVisaCombo, s)

        s.beginGroup('ai')
        self.aiConfig.restoreSettings(s)
        s.endGroup()
        s.beginGroup('ao')
        self.aoConfig.restoreSettings(s)
        s.endGroup()

        geometry = s.value('geometry', QByteArray(), type=QByteArray)
        self.restoreGeometry(geometry)

        rows = s.beginReadArray('biasTable')
        for i in range(rows)[::-1]:
            s.setArrayIndex(i)
            f = s.value('f', 333.8, type=float)
            Vac = s.value('Vac', 0.1, type=float)
            Vdc = s.value('Vdc', 0.1, type=float)
            cycles = s.value('cycles', 1, type=int)
            self.addRowClicked(f, Vac, Vdc, cycles)
        s.endArray()


class ExceptionHandler(QObject):

    errorSignal = pyqtSignal()
    silentSignal = pyqtSignal()

    def __init__(self):
	super(ExceptionHandler, self).__init__()

    def handler(self, exctype, value, traceback):
        self.errorSignal.emit()
        print "ERROR CAPTURED", value, traceback
        sys._excepthook(exctype, value, traceback)

if __name__ == '__main__':
    import sys
    import logging

    logging.basicConfig(level=logging.WARN)

    exceptionHandler = ExceptionHandler()
    sys._excepthook = sys.excepthook
    sys.excepthook = exceptionHandler.handler


    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('Transition2')

    mw = TransitionWidget()

    mw.show()
    app.exec_()

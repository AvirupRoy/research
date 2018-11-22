# -*- coding: utf-8 -*-
"""
Use the lock-in for thermometer (resistive sensor) read-out.
Optionally, adjust sine-out amplitude to keep constant sensor excitation.

Created on Wed Dec 16 17:13:15 2015

@author: wisp10
"""

import time

from LabWidgets.Utilities import compileUi
compileUi('LockinThermometerUi2')
import LockinThermometerUi2 as Ui

import pyqtgraph as pg
from PyQt4.QtGui import QWidget, QErrorMessage, QIcon 
from PyQt4.QtCore import QSettings, QTimer, QString
from PyQt4.Qt import Qt

from Calibration.CalibrationDatabase import ThermometerCalIds, getThermometerCalibration

from Visa.SR830_New import SR830
import os.path

from Zmq.Zmq import ZmqPublisher, RequestReplyThreadWithBindings
from Zmq.Ports import LockInPubSub, LockInRequestReply
from Zmq.Subscribers import HousekeepingSubscriber

#import gc
#gc.set_debug(gc.DEBUG_LEAK)


class LockinThermometerWidget(Ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(LockinThermometerWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Lockin Thermometer')
        self.serverThread = None
        self.timer = None
        self.Rthermometer = float('nan')

        axis = pg.DateAxisItem(orientation='bottom')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis})
        self.plot.setBackground('w')
        self.plot.plotItem.showGrid(x=True, y=True)
        self.plot.addLegend()
        self.verticalLayout.addWidget(self.plot)
        self.curve = pg.PlotCurveItem(name='X', symbol='o', pen='b')
        self.plot.addItem(self.curve)
        self.clearPb.clicked.connect(self.clearData)
        self.clearData()
        self.plotYAxisCombo.currentIndexChanged.connect(self.updatePlot)
        
        self.sr830 = None
        self.runPb.clicked.connect(self.run)
        self.parameterItems = [self.attenuatorGainSb, self.sourceImpedanceSb, self.driveResistanceSb, self.leadResistanceSb, self.preampGainSb, self.sensorVoltageSb]
        self.savePb.clicked.connect(self.saveParameterSet)
        self.loadPb.clicked.connect(self.loadParameterSet)
        self.deletePb.clicked.connect(self.deleteParameterSet)
        self.attenuatorAttenuationSb.valueChanged.connect(self.updateAttenuatorGain)
        self.attenuatorGainSb.valueChanged.connect(self.updateAttenuatorAttenuation)
        self.sensorVoltageIndicator.setUnit('V')
        self.sensorCurrentIndicator.setUnit('A')
        self.sensorPowerIndicator.setUnit('W')

        sr830 = SR830(None)
        sr830.sensitivity.populateEnumComboBox(self.minSensitivityCombo)
        
        self.loadParameterSets()
        self.restoreSettings()
        self.hkSub = HousekeepingSubscriber(parent = self)
        self.hkSub.adrResistanceReceived.connect(self.collectAdrResistance)
        self.hkSub.start()
        self.adrResistanceIndicator.setUnit(u'Ω')
        self.adrResistanceIndicator.setPrecision(5)
        self.publisher = None
        
        combo = self.calibrationCombo
        for i, calId in enumerate(ThermometerCalIds):
            try:
                cal = getThermometerCalibration(calId)
                info = cal.info
            except Exception as e:
                import warnings
                warnings.warn('Calibration %s unavailable due to exception %s' % (calId, str(e)))                
            combo.addItem(calId)
            combo.setItemData(i, info, Qt.ToolTipRole)
        
        self.selectCalibration()
        combo.currentIndexChanged.connect(self.selectCalibration)

    def startServerThread(self, port):
        if self.serverThread is not None:
            self.serverThread.stop()
            self.serverThread.wait(1000)
            del self.serverThread
            self.serverThread = None
        self.serverThread = RequestReplyThreadWithBindings(port, parent=self)
        boundWidgets = {'adjustExcitation': self.adjustExcitationCb, 'sensorVoltage':self.sensorVoltageSb, 'tolerance':self.toleranceSb, 'autoRanging': self.autoRangingCb}
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        #logger.info('Starting server thread')
        self.serverThread.start()

    def selectCalibration(self):
        calId = str(self.calibrationCombo.currentText())
        self.calibration = getThermometerCalibration(calId)

    def collectAdrResistance(self, R):
        self.Rthermometer = R
        self.adrResistanceIndicator.setValue(R)
        
    def updateAttenuatorGain(self, v):
        sb = self.attenuatorGainSb
        block = sb.blockSignals(True)
        sb.setValue(1./v)
        sb.blockSignals(block)
        
    def updateAttenuatorAttenuation(self, v):
        sb = self.attenuatorAttenuationSb
        block = sb.blockSignals(True)
        sb.setValue(1./v)
        sb.blockSignals(block)
        
    def saveParameterSet(self):
        s = QSettings()
        s.beginGroup('ParameterSets')
        name = self.configCombo.currentText()
        s.beginGroup(name)
        s.setValue('adjustExcitation', self.adjustExcitationCb.isChecked())
        s.setValue('sensorName', self.sensorNameLe.text())
        s.setValue('sr830Visa', self.visaCombo.currentText())
        s.setValue('autoRanging', self.autoRangingCb.isChecked())
        s.setValue('minSensitivity', self.minSensitivityCombo.currentCode())
        for item in self.parameterItems:
            s.setValue(item.objectName(), item.value())
        s.endGroup()
        s.endGroup()
        
    def loadParameterSet(self):
        s = QSettings()
        name = self.configCombo.currentText()
        s.beginGroup('ParameterSets')
        if not name in s.childGroups():
            dlg = QErrorMessage(self)
            dlg.setWindowTitle('Error')
            dlg.showMessage('No saved parameters available for %s' % name)
            return
        s.beginGroup(name)
        for item in self.parameterItems:
            item.setValue(s.value(item.objectName(), item.value(), type=float))
        self.adjustExcitationCb.setChecked(s.value('adjustExcitation', False, type=bool))
        self.sensorNameLe.setText(s.value('sensorName', '', type=QString))
        self.visaCombo.setCurrentIndex(self.visaCombo.findText(s.value('sr830Visa', 'GPIB0::12', type=QString)))
        self.autoRangingCb.setChecked(s.value('autoRanging', True, type=bool))
        self.minSensitivityCombo.setCurrentCodeSilently(s.value('minSensitivity', 0, type=int))
        s.endGroup()
        s.endGroup()
        
    def loadParameterSets(self):
        s = QSettings()
        s.beginGroup('ParameterSets')
        names = s.childGroups()
        self.configCombo.addItems(names)
        
    def deleteParameterSet(self):
        i = self.configCombo.currentIndex()
        name = self.configCombo.itemText(i)        
        
        s = QSettings()
        s.beginGroup('ParameterSets')
        s.beginGroup(name)
        s.remove('')
        s.endGroup()
        s.endGroup()
        
        self.configCombo.removeItem(i)
        
        
    def closeEvent(self, event):
        if self.timer:
            self.timer.stop()
            
        self.saveSettings()
        self.hkSub.stop()
        self.hkSub.wait(1000)
        
    def restoreSettings(self):
        s = QSettings()
        #visa = s.value('visa', QString(), type=QString)
        #i = self.visaCombo.findText(visa)
        #elf.visaCombo.setCurrentIndex(i)
        self.configCombo.setCurrentIndex(self.configCombo.findText(s.value('parameterSet', '', type=QString)))
        if len(self.configCombo.currentText()):
            self.loadParameterSet()
        #self.sensorNameLe.setText(s.value('sensorName', '', type=QString))
        
    def saveSettings(self):
        s = QSettings()
        #s.setValue('visa', self.visaCombo.currentText())
        s.setValue('parameterSet', self.configCombo.currentText())
        #s.setValue('sensorName', self.sensorNameLe.text())
        
    def enableWidgets(self, enable):
        self.visaCombo.setEnabled(enable)
        self.attenuatorGroupBox.setEnabled(enable)
        self.seriesResistanceGroupBox.setEnabled(enable)
        self.preampGroupBox.setEnabled(enable)
        self.sensorNameLe.setEnabled(enable)
        self.loadPb.setEnabled(enable)
        self.savePb.setEnabled(enable)
        self.deletePb.setEnabled(enable)
        self.configCombo.setEnabled(enable)
        
    def run(self):
        if self.sr830 is not None:
            self.stop()
        else:
            self.start()

    def stop(self):
        self.timer.stop()
        self.timer = None
        self.sr830 = None     
        self.runPb.setText('Start')
        self.enableWidgets(True)
        del self.publisher; self.publisher = None
        
    def sensorName(self):
        return str(self.sensorNameLe.text())
        
    def start(self):
        sensorName = self.sensorName()
        self.setWindowTitle('Lock-In Thermometer %s' % sensorName )
        setAppId(sensorName)
        
        if sensorName == 'BusThermometer':
            icon = QIcon('Icons/LockinThermometer_Bus.ico')
        elif sensorName == 'RuOx2005Thermometer':
            icon = QIcon('Icons/LockinThermometer_BoxOutside.ico')
        elif sensorName == 'BoxThermometer':
            icon = QIcon('Icons/LockinThermometer_BoxInside2.ico')
        else:
            icon = QIcon('Icons/LockinThermometer.ico')

        self.setWindowIcon(icon)

        visa = str(self.visaCombo.currentText())
        self.sr830 = SR830(visa)
        #self.sr830.debug = True

        self.sr830.readAll()
        self.sr830.sineOut.caching = False # Disable caching on this
        
        self.publisher = ZmqPublisher('LockinThermometer', LockInPubSub(sensorName))
        self.startServerThread(LockInRequestReply(sensorName))
        
        self.runPb.setText('Stop')
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.snapSignal)
        self.timer.start()
        self.enableWidgets(False)
        self.rangeChangedTime = 0
        self.exChangedTime = 0
        t = time.time()
        timeString = time.strftime('%Y%m%d-%H%M%S', time.localtime(t))
        dateString = time.strftime('%Y%m%d')
        sensorName = str(self.sensorNameLe.text())

        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))
        fileName = os.path.join(path, '%s_%s.dat' % (sensorName, dateString))
        if not os.path.isfile(fileName): # Maybe create new file
            with open(fileName, 'a+') as f:
                f.write('#LockinThermometer.py\n')
                f.write('#Date=%s\n' % timeString)
                f.write('#SensorName=%s\n' % sensorName)
                f.write('#SR830=%s\n' % self.sr830.visaId())
                f.write('#AttenuatorGain=%f\n' % self.attenuatorGainSb.value())
                f.write('#AttenuatorSourceImpedance=%f\n' % self.sourceImpedanceSb.value())
                f.write('#DriveResistance=%f\n' % self.driveResistanceSb.value())
                f.write('#LeadResistance=%f\n' % self.leadResistanceSb.value())
                f.write('#PreampGain=%f\n' % self.preampGainSb.value())
                f.write('#DesiredExcitation=%f\n' % self.sensorVoltageSb.value())
                k = self.sr830.allSettingValues()
                for key,value in k.iteritems():
                    f.write('#SR830/%s=%s\n' % (key,value))
                f.write('#'+'\t'.join(['time', 'VsineOut', 'X', 'Y', 'f', 'Sensitivity', 'RxCalc', 'Rtherm'])+'\n')
        self.fileName = fileName
        
    def snapSignal(self):
        t = time.time()
        self.sr830.snapSignal()
        VsineOut = self.sr830.sineOut.value
        X = self.sr830.X
        Y = self.sr830.Y
        f = self.sr830.f

        rangeChangeAge = t - self.rangeChangedTime
        exChangeAge = t - self.exChangedTime
        
        sensitivity = self.sr830.sensitivity.value
        
        if self.autoRangingCb.isChecked():
            self.sr830.checkStatus()
            minCode = self.minSensitivityCombo.currentCode()
            currentCode = self.sr830.sensitivity.code
            if self.sr830.overload and rangeChangeAge > 10:
                self.sr830.sensitivity.code = currentCode+1
                self.rangeChangeTime = t
            elif X > 0.9*sensitivity and rangeChangeAge > 10:
                self.sr830.sensitivity.code = currentCode+1
                self.rangeChangedTime = t
            elif X < 0.3*sensitivity and rangeChangeAge > 10:
                if  currentCode > minCode:
                    self.sr830.sensitivity.code = currentCode - 1
                    self.rangeChangedTime = t
            elif currentCode < minCode:
                self.sr830.sensitivity.code = minCode
                self.rangeChangedTime = t
                    
        
        G1 = self.attenuatorGainSb.value()
        G2 = self.preampGainSb.value()
        Rsource = self.sourceImpedanceSb.value()
        Rd = self.driveResistanceSb.value()
        Rl = self.leadResistanceSb.value()
        Rs = Rsource+Rd+Rl

        Vx = X / G2
        
        Vex = VsineOut * G1 # Real excitation
        self.sensorVoltageIndicator.setValue(Vx)

        
        Rx = Rs / (Vex/Vx-1.)
        I = Vx / Rx
        self.sensorCurrentIndicator.setValue(I)
        P = Vx*I
        Temp = self.calibration.calculateTemperature([Rx])[0] # @todo This is really a crutch
        
        Tbase = self.calibration.correctForReadoutPower(Temp, P)
        
        if self.publisher is not None:
            if rangeChangeAge > 10 and exChangeAge > 10 and Temp == Temp and Temp > 0 and Temp < 10:
                self.publisher.publishDict(self.sensorName(), {'t': t, 'R': Rx, 'T': Temp, 'P': P, 'Tbase': Tbase})
                #self.publisher.publish('ADR_Sensor_R', Rx)
                #self.publisher.publish('ADR_Temperature', Temp)

        # Log data
        with open(self.fileName, 'a+') as of:
            of.write('%.3f\t%.3f\t%.5E\t%.5E\t%.3f\t%.1E\t%.5E\t%.5E\n' % (t, VsineOut, X, Y, f, sensitivity, Rx, self.Rthermometer))

        self.ts.append(t)
        self.xs.append(X)
        self.ys.append(Y)
        self.fs.append(f)
        self.VsineOuts.append(VsineOut)
        self.Rs.append(Rx)
        self.Vxs.append(Vx)
        self.Ps.append(P)
        self.Ts.append(Temp)
        self.Tbases.append(Tbase)

        self.sensorIndicator.setValue(Rx)
        self.temperatureIndicator.setKelvin(Temp)
        self.baseTempIndicator.setKelvin(Tbase)
        self.sensorPowerIndicator.setValue(P)
        self.updateLed.flashOnce()
        self.updatePlot()

        # Not sure where this code came from. Seems questionable (FJ)
        # if len(self.Ts) > 2 :
        #     dTdt = abs((self.Ts[-1] - self.Ts[-2]) / (self.ts[-1] - self.ts[-2]))
        #     if dTdt > 0.1:
        #         self.temperatureIndicator.setKelvin('N/A')
        #         self.stop()
        
        
        # Perhaps change excitation
        if exChangeAge < 10 or rangeChangeAge < 10 or not self.adjustExcitationCb.isChecked():
            return
        VxDesired = self.sensorVoltageSb.value()
        IDesired = VxDesired / Rx
        VexDesired = IDesired*(Rx+Rs)
        change = (VexDesired-Vex)/Vex
        tolerance = 1E-2*self.toleranceSb.value()
        if abs(change) < tolerance:
            return
        
        VsineOutDesired = VexDesired / G1 # This is what we would like to see
        # What we actually get may be something different
        Vnew = min(5,max(VsineOutDesired,0.004))
        if tolerance == 0 and abs(Vnew - VsineOut) > 0.009:   # If a large step is required, do it slowly
            Vnew = (3.*VsineOut+1.*Vnew)/4.
        
        if abs(Vnew - VsineOut) < 0.002:
            return
        self.exChangedTime = t
        self.sr830.sineOut.value = Vnew
        
    def clearData(self):
        self.ts = []
        self.xs = []
        self.ys = []
        self.fs = []
        self.Rs = []
        self.Ps = []
        self.VsineOuts = []
        self.Vxs = []
        self.Ts = []
        self.Tbases = []
        self.updatePlot()
        
    def updatePlot(self):
        yAxis = self.plotYAxisCombo.currentText()
        pl = self.plot
        if yAxis == 'X':
            y = self.xs
            pl.setLabel('left', 'Lock-in X', 'V')
        elif yAxis == 'Y':
            y = self.ys
            pl.setLabel('left', 'Lock-in Y', 'V')
        elif yAxis == 'R':
            y = self.Rs
            pl.setLabel('left', 'R sensor', u'Ω')
        elif yAxis == 'V sine out':
            y = self.VsineOuts
            pl.setLabel('left', 'V sine out', 'V')
        elif yAxis == 'V sensor':
            y = self.Vxs
            pl.setLabel('left', 'V sensor', 'V')
        elif yAxis == 'P sensor':
            y = self.Ps
            pl.setLabel('left', 'P sensor', 'W')
        elif yAxis == 'Sensor temperature':
            y = self.Ts
            pl.setLabel('left', 'T sensor', 'K')
        elif yAxis == 'Base temperature':
            y = self.Tbases
            pl.setLabel('left', 'T base', 'K')
            
        x = self.ts
        self.curve.setData(x, y)

def setAppId(name):
    import ctypes
    myappid = u'WISCXRAYASTRO.ADR3.%s.1' % name # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)  
                        

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.WARN)
    
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    app.setApplicationName('Lockin Thermometer')
    app.setApplicationVersion('0.1')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setOrganizationName('McCammon X-ray Astrophysics')
    
    setAppId('LockInThermometer')
    
    mainWindow = LockinThermometerWidget()
    
    icon = QIcon('Icons/LockinThermometer.ico')
    mainWindow.setWindowIcon(icon)
    mainWindow.show()
    app.exec_()
  
# -*- coding: utf-8 -*-
"""
ADR Temperature control
Branched from old UNM/FJ code
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
import time

from LabWidgets.Utilities import compileUi
compileUi('AdrTemperatureControl2Ui')
import AdrTemperatureControl2Ui as Ui

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S', filename='AdrTemperatureControlPid%s.log' % time.strftime('%Y%m%d'), filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.WARN)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)


class SIUnits:
    milli = 1E-3
    mK = milli
    minute = 60.
    
class StopThread(Exception):
    pass

#from math import isnan
from PyQt4.QtCore import QObject

class Pid(QObject):
    def __init__(self, parent=None):
        super(Pid, self).__init__(parent=parent)
        self.K = 0        # Proportional gain
        self.Ti = 0       # Integral time [s]
        self.Td = 0       # Differential time [s]
        self.Tt = 0       # Tracking time constant [s]
        self.Tf = 0       # Differential term filter time constant [s]
        self.beta = 1.0
        self.gamma = 0.0

        # State variables
        self.I = 0       # I term for next iteration
        self.D = 0       # Old D term
        self.pv = None      # Old process value
        self.sp = None      # Old setpoint value
        self.t = None          # Old time


    def setControlMaximum(self, controlMax):
        self.controlMax = controlMax

    def setControlMinimum(self, controlMin):
        self.controlMin = controlMin

    def updateParameters(self, K, Ti, Td, Tt, Tf, beta = 1.0, gamma = 1.0):
        '''Perform a bumpless update of PID parameters by adjusting the integral term to provide unchanged control output
        Parameters are:
            K:  proportional gain
            Ti: integral time (infinity to disable)
            Td: differential time
            Tt: tracking time constant ()
            Tf: filter time for differential term (Tf = Td/N)
            beta:  setpoint weight for proportional term (between 0 and 1)
            gamma:  setpoint weight for integral term (between 0 and 1)
        '''
        if self.sp is not None:
            self.I = self.I + self.K*(self.beta*self.sp-self.pv) - K*(beta*self.sp - self.pv)  # Trying for bumpless transfer
        else:
            self.I = 0
        self.K = K
        if Ti == 0:
            self.Ti = 1E20
        else:
            self.Ti = Ti
        self.Td = Td
        self.Tt = Tt
        self.Tf = Tf
        self.beta = beta
        self.gamma = gamma

    def updateLoop(self, sp, pv):
        '''Feed a new value of the process variable pv to the PID loop and obtained an updated controller output.
           Inputs:
             sp: setpoint value
             pv: process value

            Returns:
            u: control output with limits applied
            p: proportional term
            i: integral term
            d: differential term

        '''

        t = time.time()
        if self.t is None:
            self.t = t-1

        h = t - self.t
        e = sp - pv
        p = self.K*(self.beta*sp-pv)
        i = self.I # from last iteration
        if self.pv is not None:
            d = self.Tf/(self.Tf+h)*self.D + self.K*self.Td/(self.Tf+h)*(self.gamma*(sp-self.sp)-(pv-self.pv))
        else:
            d = 0

        v = p+i+d # Desired control output

        # Bounded control output
        if v < self.controlMin:
            u = self.controlMin
        elif v > self.controlMax:
            u = self.controlMax
        elif v != v: # Somehow it became infinite
            u = 0
            v = 0
        else:
            u = v

        # Error in control output
        se = u - v

        if se != 0:
            #print "Setpoint error:", se
            pass
        
        # Update all state variables
        self.I = self.I + self.K/self.Ti * (t - self.t) * (e + se/self.Tt)  # New I for next iteration
        self.D = d
        self.pv = pv
        self.sp = sp
        self.t = t
        return (u, p, i, d)


from Zmq.Subscribers import HousekeepingSubscriber

from LabWidgets.Utilities import saveWidgetToSettings, restoreWidgetFromSettings
import pyqtgraph as pg

mAperMin = 1E-3/60
from Zmq.Ports import RequestReply

from PyQt4.QtGui import QMainWindow
from PyQt4.QtCore import QSettings, QTimer
#from PyQt4.Qt import Qt

from MagnetControlRemote import MagnetControlRemote
from Zmq.Zmq import RequestReplyThreadWithBindings

class TemperatureControlMainWindow(Ui.Ui_MainWindow, QMainWindow):
    def __init__(self, parent = None):
        super(TemperatureControlMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setpointSb.setDecimals(7)
        self.setpointSb.setSingleStep(1E-7)
        self.rampRateSb.setDecimals(2)
        self.rampRateSb.setSingleStep(1E-2)
        self.serverThread = None
        self.selectedSensorName = ''
        self.clearData()
        self.pid = None
        self.outputFile = None
        self.magnetControlRemote = None
        self.rampEnableCb.toggled.connect(self.fixupRampRate)
        self.updatePlotsCb.toggled.connect(self.showPlots)
        
        self.widgetsForSettings = [self.thermometerCombo, 
                                   self.setpointSb, self.KSb, self.TiSb, self.TdSb,
                                   self.TtSb, self.TfSb, self.betaSb, self.gammaSb,
                                   self.controlMinSb, self.controlMaxSb, self.rampRateSb,
                                   self.rampTargetSb, self.rampEnableCb, self.updatePlotsCb,
                                   self.useBaseTemperatureCb]
        
        axis = pg.DateAxisItem(orientation='bottom')
        self.pvPlot = pg.PlotWidget(axisItems={'bottom': axis})
        self.mainVerticalLayout.addWidget(self.pvPlot)

        self.pvPlot.addLegend()
        self.curvePv = pg.PlotCurveItem(name='Actual', symbol='o', pen='g')
        self.curveSetpoint = pg.PlotCurveItem(name='Setpoint', symbol='o', pen='r')
        self.pvPlot.addItem(self.curvePv)
        self.pvPlot.addItem(self.curveSetpoint)


        axis = pg.DateAxisItem(orientation='bottom')
        self.pidPlot = pg.PlotWidget(axisItems={'bottom': axis})
        self.mainVerticalLayout.addWidget(self.pidPlot)
        self.pidPlot.addLegend()
        self.curveP = pg.PlotCurveItem(name='P', symbol='o', pen='r')
        self.curveI = pg.PlotCurveItem(name='I', symbol='o', pen='g')
        self.curveD = pg.PlotCurveItem(name='D', symbol='o', pen='b')
        self.curveControl = pg.PlotCurveItem(name='control', symbol='o', pen='w')
        self.pidPlot.addItem(self.curveP)
        self.pidPlot.addItem(self.curveI)
        self.pidPlot.addItem(self.curveD)
        self.pidPlot.addItem(self.curveControl)

        self.KSb.setMinimum(-1E6)
        self.KSb.setMaximum(1E6)

        self.hkSub = HousekeepingSubscriber(self)
        self.hkSub.thermometerListUpdated.connect(self.updateThermometerList)
        self.hkSub.thermometerReadingReceived.connect(self.receiveTemperature)
        self.hkSub.start()

        self.startPb.clicked.connect(self.startPid)
        self.stopPb.clicked.connect(self.stopPid)

        self.timer = QTimer(self)   # A 250 ms timer to implement ramping
        self.timer.timeout.connect(self.updateSetpoint)
        self.tOld = time.time()
        self.timer.start(250)

        self.thermometerCombo.currentIndexChanged.connect(self.updateThermometerSelection)

        self.restoreSettings()
        # Give the hkSub some time to update thermometer list before we update thermometer selection
        QTimer.singleShot(2000, self.restoreThermometerSelection) 
        
    def restoreThermometerSelection(self):
        s = QSettings()
        restoreWidgetFromSettings(s, self.thermometerCombo)

    def updateThermometerSelection(self):
        t = str(self.thermometerCombo.currentText())
        self.selectedSensorName = t
        
    def updateThermometerList(self, thermometerList):
        selected = self.thermometerCombo.currentText()
        self.thermometerCombo.clear()
        self.thermometerCombo.addItems(thermometerList)
        i = self.thermometerCombo.findText(selected)
        self.thermometerCombo.setCurrentIndex(i)
        
    def startServerThread(self):
        self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.AdrPidControl, parent=self)
        boundWidgets = {'stop': self.stopPb,'start': self.startPb,'rampRate':self.rampRateSb, 'rampTarget':self.rampTargetSb, 'rampEnable':self.rampEnableCb, 'setpoint':self.setpointSb}
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        logger.info('Starting server thread')
        self.serverThread.start()
        
    def showPlots(self, enable):
        self.pvPlot.setVisible(enable)
        self.pidPlot.setVisible(enable)
        self.adjustSize()
    
    def fixupRampRate(self, doIt):
        if doIt:
            Tset = self.setpointSb.value()
            Ttarget = self.rampTargetSb.value()
            absRate = abs(self.rampRateSb.value())
            if Tset < Ttarget:
                self.rampRateSb.setValue(+absRate)
            else:
                self.rampRateSb.setValue(-absRate)
        
    def updateSetpoint(self):
        t = time.time()
        if self.rampEnableCb.isChecked():
            Tset = self.setpointSb.value()
            Ttarget = self.rampTargetSb.value()
            rate = self.rampRateSb.value() * SIUnits.mK/SIUnits.minute
            deltaT = rate * (t-self.tOld)
            if rate > 0:
                Tset = min(Ttarget, Tset+deltaT)
            elif rate < 0:
                Tset = max(Ttarget, Tset+deltaT)
            self.setpointSb.setValue(Tset)
            if Tset == Ttarget:
                self.rampEnableCb.setChecked(False)
        self.tOld = t                

    def startPid(self):
        self.enableControls(False)
        pid = Pid(parent=self)
        pid.setControlMaximum(self.controlMaxSb.value()*mAperMin)
        pid.setControlMinimum(self.controlMinSb.value()*mAperMin)
        
        self.setpointSb.setValue(self.pv)

        self.KSb.valueChanged.connect(self.updatePidParameters)
        self.TiSb.valueChanged.connect(self.updatePidParameters)
        self.TdSb.valueChanged.connect(self.updatePidParameters)
        self.TfSb.valueChanged.connect(self.updatePidParameters)
        self.TtSb.valueChanged.connect(self.updatePidParameters)
        self.betaSb.valueChanged.connect(self.updatePidParameters)
        self.gammaSb.valueChanged.connect(self.updatePidParameters)
        self.controlMinSb.valueChanged.connect(lambda x: pid.setControlMinimum(x*mAperMin))
        self.controlMaxSb.valueChanged.connect(lambda x: pid.setControlMaximum(x*mAperMin))
        self.magnetControlRemote = MagnetControlRemote('AdrTemperatureControlPid', parent=self)
        if not self.magnetControlRemote.checkConnection():
            self.appendErrorMessage('Cannot connect to magnet control')
            self.stopPid(abort=True)
            return
        self.magnetControlRemote.error.connect(self.appendErrorMessage)
        self.magnetControlRemote.disableDriftCorrection()
        self.pid = pid # This effectively enables the loop
        self.updatePidParameters()
        self.startServerThread()

    def endServerThread(self):
        if self.serverThread is not None:
            logger.info('Stopping server thread')
            self.serverThread.stop()
            self.serverThread.wait(1000)
            del self.serverThread
            self.serverThread = None

    def stopPid(self, abort=False):
        self.endServerThread()
        if self.pid:
            del self.pid
            self.pid = None
        if self.magnetControlRemote:
            if not abort:
                self.requestRampRate(0.0)
                self.magnetControlRemote.enableDriftCorrection()
            self.magnetControlRemote.stop()
            self.magnetControlRemote.wait(2)
            self.magnetControlRemote.deleteLater()
            self.magnetControlRemote = None
        
        if self.outputFile is not None:
            self.outputFile.close()
        self.enableControls(True)

    def updatePidParameters(self):
        if self.pid is None: return
        #print "Updating PID parameters"
        K = self.KSb.value()*mAperMin
        Ti = self.TiSb.value()
        Td = self.TdSb.value()
        Tt = self.TtSb.value()
        Tf = self.TfSb.value()

        beta = self.betaSb.value()
        gamma = self.gammaSb.value()

        self.pid.updateParameters(K, Ti, Td, Tt, Tf, beta, gamma)

        if self.outputFile is not None:
            self.outputFile.close()
            self.outputFile = None

        s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
        path = str(s.value('runPath', '', type=str))

        timeString = time.strftime('%Y%m%d-%H%M%S')
        fileName = path+'/AdrPID_%s.dat' % timeString
        self.outputFile = open(fileName, 'a+')
        self.outputFile.write('#AdrTemperatureControlPid.py\n')
        self.outputFile.write('#Date=%s\n' % timeString)
        self.outputFile.write('#K=%.8g\n' % K)
        self.outputFile.write('#ti=%.6g\n' % Ti)
        self.outputFile.write('#td=%.6g\n' % Td)
        self.outputFile.write('#tt=%.6g\n' % Tt)
        self.outputFile.write('#tf=%.6g\n' % Tf)
        self.outputFile.write('#beta=%.6g\n' % beta)
        self.outputFile.write('#gamma=%.6g\n' % gamma)
        self.outputFile.write('#'+'\t'.join(['time', 'Ts', 'T', 'u', 'p', 'i', 'd' ])+'\n')

    def requestRampRate(self, rate):
        '''Request new ramp rate [units: A/s]'''
        #print "Requesting new ramp rate:", rate, 'A/s'
        ok = self.magnetControlRemote.changeRampRate(rate)
        if not ok: 
            self.appendErrorMessage('Unable to change ramp rate. Aborting.')
            self.stopPid(abort=True)

    def appendErrorMessage(self, message):
        timeString = time.strftime('%Y%m%d-%H%M%S')
        self.errorTextEdit.append('%s: %s' % (timeString, str(message)))        
        logger.error('%s: %s' % (timeString, str(message)))
        
    def updateLoop(self, sp, pv):
        if self.pid is None: return
        if self.pv == 0: return
        (u, p, i, d) = self.pid.updateLoop(sp, pv)
        self.requestRampRate(u)

        t = time.time()
        string = "%.3f\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\n" % (t, sp, pv, u, p, i, d)
        self.outputFile.write(string)

        unit = mAperMin
        total = p+i+d
        self.controlIndicator.setValue(u/unit)
        self.pIndicator.setValue(p/unit)
        self.iIndicator.setValue(i/unit)
        self.dIndicator.setValue(d/unit)
        self.totalIndicator.setValue(total/unit)
        
        self.ts_pid.append(t)
        self.ps.append(p/unit)
        self.Is.append(i/unit)
        self.ds.append(d/unit)
        self.controls.append(u/unit)
        
        historyLength = 10000
        if len(self.ts_pid) > 1.1*historyLength:
            self.ts_pid = self.ts_pid[-historyLength:]
            self.ps = self.ps[-historyLength:]
            self.Is = self.Is[-historyLength:]
            self.ds = self.ds[-historyLength:]
            self.controls = self.controls[-historyLength:]
            
        if self.updatePlotsCb.isChecked():
            self.curveP.setData(self.ts_pid, self.ps)
            self.curveI.setData(self.ts_pid, self.Is)
            self.curveD.setData(self.ts_pid, self.ds)
            self.curveControl.setData(self.ts_pid, self.controls)

    def enableControls(self, enable):
        self.thermometerCombo.setEnabled(enable)
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)

    def restoreSettings(self):
        settings = QSettings()
        for widget in self.widgetsForSettings:
            restoreWidgetFromSettings(settings, widget)

    def saveSettings(self):
        settings = QSettings()
        for widget in self.widgetsForSettings:
            saveWidgetToSettings(settings, widget)

    def clearData(self):
        self.ts_pid = []
        self.ps = []
        self.Is = []
        self.ds = []
        self.controls = []

        self.ts_pv = []
        self.pvs = []

        #self.ts_setpoint = []
        self.setpoints = []

    def receiveTemperature(self, sensorName, t, R, T, P, Tbase):
        if sensorName != self.selectedSensorName:
            return
        
        if self.useBaseTemperatureCb.isChecked():
            pv = Tbase
        else:
            pv = T
            
        sp = self.setpointSb.value()
        self.pv = pv
        self.updateLoop(sp, pv)

        t = time.time()
        self.pvIndicator.setValue(pv)
        self.ts_pv.append(t)
        self.pvs.append(pv)
        self.setpoints.append(sp)
        
        historyLength = 10000
        if len(self.ts_pv) > 1.1*historyLength:
            self.ts_pv = self.ts_pv[-historyLength:]
            self.pvs = self.pvs[-historyLength:]
            self.setpoints = self.setpoints[-historyLength:]

        if self.updatePlotsCb.isChecked():
            self.curvePv.setData(self.ts_pv, self.pvs)
            self.curveSetpoint.setData(self.ts_pv, self.setpoints)

    def closeEvent(self, e):
        if self.pid is not None:
            self.stopPid()
        self.hkSub.stop()
        if self.serverThread is not None:
            self.serverThread.stop()
            self.serverThread.wait(1000)
        if self.magnetControlRemote is not None:
            self.magnetControlRemote.stop()
            self.magnetControlRemote.wait(1000)
        self.hkSub.wait(1000)
        self.saveSettings()


if __name__ == "__main__":
    import sys
        
    from PyQt4.QtGui import QApplication, QIcon

    app = QApplication(sys.argv)
    app.setApplicationName('AdrTemperatureControl')
    app.setOrganizationName('WiscXrayAstro')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationVersion('0.1')
    
    import ctypes
    myappid = u'WISCXRAYASTRO.ADR3.AdrTemperatureControlPid' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    mw = TemperatureControlMainWindow()
    mw.setWindowIcon(QIcon('Icons/PID.ico'))
    mw.show()
    sys.exit(app.exec_())

# -*- coding: utf-8 -*-
"""
ADR Temperature control
Branched from old UNM/FJ code
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

#from math import sqrt
#import numpy as np
#import scipy.io as scio
#import math
import time
import datetime

from PyQt4 import uic
uic.compileUiDir('.')
print "Done"

class SIUnits:
    milli = 1E-3
    mK = milli
    minute = 60.
    
class StopThread(Exception):
    pass

from math import isnan

class Pid(object):
    def __init__(self):
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
        else:
            u = v

        # Error in control output
        se = u - v

        if se != 0:
            print "Setpoint error:", se

        # Update all state variables
        self.I = self.I + self.K/self.Ti * (t - self.t) * (e + se/self.Tt)  # New I for next iteration
        self.D = d
        self.pv = pv
        self.sp = sp
        self.t = t
        return (u, p, i, d)


import AdrTemperatureControl2Ui as Ui

from Zmq.Subscribers import TemperatureSubscriber
from Zmq.Zmq import ZmqBlockingRequestor, ZmqRequest

from LabWidgets.Utilities import connectAndUpdate, saveWidgetToSettings, restoreWidgetFromSettings
import pyqtgraph as pg

mAperMin = 1E-3/60
from Zmq.Ports import RequestReply

from PyQt4.QtGui import QMainWindow
from PyQt4.QtCore import QSettings, QTimer # pyqtSignal, QThread, 
#from PyQt4.Qt import Qt

from Zmq.Zmq import RequestReplyRemote # ,ZmqReply, ZmqRequestReplyThread
import logging
logging.basicConfig(level=logging.DEBUG)

from MagnetSupply import MagnetControlRemote

class PidControlRemote(RequestReplyRemote):
    '''Remote control of ADR temperature PID via ZMQ request-reply socket.
    Use this class to interface with the ADR temperature PID control from other programs.'''
    
    def __init__(self, origin, parent=None):
        super(PidControlRemote, self).__init__(origin=origin, port=RequestReply.AdrPidControl, parent=parent)
        
    def rampRate(self):
        return self._queryValue('rampRate')
        
    def setRampRate(self, rate):
        return self._setValue('rampRate', rate)
        
    def rampTarget(self):
        return self._queryValue('rampTarget')

    def setRampTarget(self, T):
        return self._setValue('rampTarget', T)
        
    def enableRamp(self, enable=True):
        return self._setValue('rampEnable', enable)
        
    def rampEnabled(self):
        return self._queryValue('rampEnable')
    
    def setpoint(self):
        return self._queryValue('setpoint')

    def setSetpoint(self, T):
        return self._setValue('setpoint', T)

from Zmq.Zmq import RequestReplyThreadWithBindings

class TemperatureControlMainWindow(Ui.Ui_MainWindow, QMainWindow):
    def __init__(self, parent = None):
        super(TemperatureControlMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.clearData()
        self.pid = None
        self.requestor = None
        self.outputFile = None
        self.rampEnableCb.toggled.connect(self.fixupRampRate)
        
        self.widgetsForSettings = [self.setpointSb, self.KSb, self.TiSb, self.TdSb, self.TtSb, self.TfSb, self.betaSb, self.gammaSb, self.controlMinSb, self.controlMaxSb, self.rampRateSb, self.rampTargetSb, self.rampEnableCb]
        self.restoreSettings()

        self.pvPlot.addLegend()
        self.curvePv = pg.PlotCurveItem(name='Actual', symbol='o', pen='g')
        self.curveSetpoint = pg.PlotCurveItem(name='Setpoint', symbol='o', pen='r')
        self.pvPlot.addItem(self.curvePv)
        self.pvPlot.addItem(self.curveSetpoint)

        self.pidPlot.addLegend()
        self.curveP = pg.PlotCurveItem(name='P', symbol='o', pen='r')
        self.curveI = pg.PlotCurveItem(name='I', symbol='o', pen='g')
        self.curveD = pg.PlotCurveItem(name='D', symbol='o', pen='b')
        self.curveControl = pg.PlotCurveItem(name='D', symbol='o', pen='w')
        self.pidPlot.addItem(self.curveP)
        self.pidPlot.addItem(self.curveI)
        self.pidPlot.addItem(self.curveD)

        self.KSb.setMinimum(-1E6)
        self.KSb.setMaximum(1E6)

        self.adrTemp = TemperatureSubscriber(self)
        self.adrTemp.adrTemperatureReceived.connect(self.collectPv)
        self.adrTemp.start()

        self.startPb.clicked.connect(self.startPid)
        self.stopPb.clicked.connect(self.stopPid)
        self.t0 = time.time()

        self.timer = QTimer(self)   # A 250 ms timer to implement ramping
        self.timer.timeout.connect(self.updateSetpoint)
        self.tOld = time.time()
        self.timer.start(250)

        #connectAndUpdate(self.setpointSb, self.collectSetpoint)
        
        self.serverThread = RequestReplyThreadWithBindings(port=RequestReply.AdrPidControl, parent=self)
        boundWidgets = {'rampRate':self.rampRateSb, 'rampTarget':self.rampTargetSb, 'rampEnable':self.rampEnableCb, 'setpoint':self.setpointSb}
        for name in boundWidgets:
            self.serverThread.bindToWidget(name, boundWidgets[name])
        self.serverThread.start()
    
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
        self.pid = Pid()
        self.pid.setControlMaximum(self.controlMaxSb.value()*mAperMin)
        self.pid.setControlMinimum(self.controlMinSb.value()*mAperMin)
        
        self.setpointSb.setValue(self.pv)

        self.KSb.valueChanged.connect(self.updatePidParameters)
        self.TiSb.valueChanged.connect(self.updatePidParameters)
        self.TdSb.valueChanged.connect(self.updatePidParameters)
        self.TfSb.valueChanged.connect(self.updatePidParameters)
        self.TtSb.valueChanged.connect(self.updatePidParameters)
        self.betaSb.valueChanged.connect(self.updatePidParameters)
        self.gammaSb.valueChanged.connect(self.updatePidParameters)
        self.controlMinSb.valueChanged.connect(lambda x: self.pid.setControlMinimum(x*mAperMin))
        self.controlMaxSb.valueChanged.connect(lambda x: self.pid.setControlMaximum(x*mAperMin))
        self.enableControls(False)
        self.updatePidParameters()
        self.magnetControlRemote = MagnetControlRemote('AdrTemperatureControlPid')
        self.magnetControlRemote.error.connect(self.appendErrorMessage)
        self.requestor = ZmqBlockingRequestor(port=RequestReply.MagnetControl, origin='AdrTemperatureControlPid')

    def stopPid(self):
        del self.pid
        self.pid = None
        if self.outputFile is not None:
            self.outputFile.close()
        self.requestRampRate(0.0)
        self.enableControls(True)

    def updatePidParameters(self):
        if self.pid is None: return
        print "Updating PID parameters"
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

        timeString = time.strftime('%Y%m%d-%H%M%S')
        fileName = 'AdrPID_%s.dat' % timeString
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
        print "Requesting new ramp rate:", rate, 'A/s'
        ok = self.magnetControlRemote.changeRampRate(rate)
        if not ok: 
            self.appendErrorMessage('Unable to change ramp rate')

    def appendErrorMessage(self, message):
        self.errorTextEdit.append(message)        
        
    def updateLoop(self, sp, pv):
        if self.pid is None: return
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

        self.ts_pid.append(time.time()-self.t0)
        self.ps.append(p/unit)
        self.Is.append(i/unit)
        self.ds.append(d/unit)
        self.controls.append(u/unit)
        self.curveP.setData(self.ts_pid, self.ps)
        self.curveI.setData(self.ts_pid, self.Is)
        self.curveD.setData(self.ts_pid, self.ds)
        self.curveControl.setData(self.ts_pid, self.controls)


    def enableControls(self, enable):
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

    def collectPv(self, pv):
        sp = self.setpointSb.value()
        self.pv = pv
        self.updateLoop(sp, pv)

        t = time.time()-self.t0
        self.pvIndicator.setValue(pv)
        self.ts_pv.append(t)
        self.pvs.append(pv)
        self.curvePv.setData(self.ts_pv, self.pvs)
        self.setpoints.append(sp)
        self.curveSetpoint.setData(self.ts_pv, self.setpoints)

    def closeEvent(self, e):
        if self.pid is not None:
            self.stopPid()
        self.saveSettings()

    def logData(self):
        pass
#        filename = 'Heater_%s.txt' % (time.strftime("%Y-%m-%d"))
#        with open(filename, "a") as f:
#            mlt = MatlabDate(datetime.datetime.fromtimestamp(t))
#            f.write(str(mlt))
#            f.write('\t')
#            f.write(str(T))
#            f.write('\t')
#            f.write(str(heaterCurrent))
#            f.write('\t')
#            f.write(str(heaterVoltage))
#            f.write('\r\n')


if __name__ == "__main__":
    import sys
    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName('AdrTemperatureControl')
    app.setOrganizationName('WiscXrayAstro')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationVersion('0.1')

    mw = TemperatureControlMainWindow()
    mw.show()
    sys.exit(app.exec_())

# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 17:45:56 2015

@author: wisp10
"""

from PyQt4.QtGui import QWidget, QDoubleSpinBox, QHeaderView, QCheckBox, QFileDialog
from PyQt4.QtCore import QSettings
#from PyQt4.QtCore import QObject, pyqtSignal, QThread, QSettings, QString, QByteArray

from MagnetControlRemote import MagnetControlRemote

from Zmq.Subscribers import HousekeepingSubscriber


from LabWidgets.Utilities import compileUi
compileUi('AdrControlUi')
import AdrControlUi

import time

class State:
    IDLE = 0
    RAMPING = 1
    HOLDING = 2

class CurrentRateSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setAccelerated(True)
        self.setMinimum(0)
        self.setMaximum(800)
        self.setSuffix(' mA/min')
        self.setSingleStep(0.1)
        self.setDecimals(1)

class CurrentSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setAccelerated(True)
        self.setMinimum(0)
        self.setMaximum(8.5)
        self.setSuffix(' A')
        self.setSingleStep(0.001)
        self.setDecimals(3)

class HoldTimeSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        QDoubleSpinBox.__init__(self, parent)
        self.setAccelerated(True)
        self.setMinimum(-1)
        self.setMaximum(1E5)
        self.setSuffix(' s')
        self.setSingleStep(1)
        self.setDecimals(0)
        self.setSpecialValueText('Indefinite')

class AdrControlWidget(AdrControlUi.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(AdrControlWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('ADR Control')
        self.addRowPb.clicked.connect(self.addRowClicked)
        for i in range(0, self.currentTable.columnCount()):
            self.currentTable.horizontalHeader().setResizeMode( i, QHeaderView.ResizeToContents )
        self.deleteRowPb.clicked.connect(self.deleteRowClicked)

        self.restoreSettings()

        magnetRemote = MagnetControlRemote('AdrControl', parent=parent)

        magnetRemote.supplyVoltageReceived.connect(self.supplyVoltageSb.setValue)
        magnetRemote.supplyCurrentReceived.connect(self.supplyCurrentSb.setValue)
        magnetRemote.magnetVoltageReceived.connect(self.magnetVoltageSb.setValue)
        magnetRemote.magnetCurrentReceived.connect(self.magnetCurrentSb.setValue)        
        magnetRemote.magnetCurrentReceived.connect(self.magnetCurrentUpdated)
        #magnetRemote.dIdtReceived.connect(self.updateRampRate)
        self.magnetRemote = magnetRemote

        hkSub = HousekeepingSubscriber(parent=parent)
        hkSub.adrTemperatureReceived.connect(self.adrTemperatureSb.setValue)
        hkSub.start()
        self.hkSub = hkSub

        self.state = State.IDLE
        self.startPb.clicked.connect(self.startPbClicked)
        self.stopPb.clicked.connect(self.stopPbClicked)
        self.skipPb.clicked.connect(self.skip)
        self.loadPb.clicked.connect(self.loadTable)
        self.savePb.clicked.connect(self.saveTable)
        
#    def updateRampRate(self, dIdt):
#        self.rampRate = dIdt / (1E-3/60)
#        print "New ramp rate:", self.rampRate, "mA/min"

    def saveTable(self):
        fileName = QFileDialog.getSaveFileName(filter='*.dat')
        if fileName is None:
            return
        table = self.currentTable
        with open(fileName, 'w') as f:
            f.write('#Enabled\tRampRate\tTarget\tHoldTime\n')
            rows = table.rowCount()
            for row in range(rows):
                enabled = 1 if table.cellWidget(row,0).isChecked() else 0
                rampRate = table.cellWidget(row,1).value()
                target = table.cellWidget(row,2).value()
                holdTime = table.cellWidget(row,3).value()
                f.write('%d\t%f\t%f\t%f\n' % (enabled, rampRate, target, holdTime))

    def loadTable(self):
        fileName = QFileDialog.getOpenFileName(filter='*.dat')
        if fileName is None:
            return
        #self.currentTable.clear()
        with open(fileName, 'r') as f:
            for line in f.readlines():
                print "Line:",line
                if line[0] == '#':
                    continue
                d = line.split('\t')
                if len(d) != 4:
                    continue
                try:
                    enabled = bool(d[0])
                    rampRate = float(d[1])
                    target = float(d[2])
                    holdTime = float(d[3])
                    self.addRowClicked(enabled, rampRate, target, holdTime, atEnd = True)
                except Exception,e:
                    print "Error:", e
                    continue


    def addRowClicked(self, enable=True, rampRate=10, target=0.2, holdTime=60, atEnd=False):
        table = self.currentTable
        if atEnd:
            row = table.rowCount()
        else:
            row = table.currentRow()
        if row < 1:
            row = 0

        table.insertRow(row)
        enableCb = QCheckBox()
        enableCb.setChecked(enable)

        rampRateSb = CurrentRateSpinBox()
        rampRateSb.setValue(rampRate)
        print rampRateSb
        targetSb = CurrentSpinBox()
        targetSb.setValue(target)
        print targetSb
        holdTimeSb = HoldTimeSpinBox()
        holdTimeSb.setValue(holdTime)
        table.setCellWidget(row, 0, enableCb)
        table.setCellWidget(row, 1, rampRateSb)
        table.setCellWidget(row, 2, targetSb)
        table.setCellWidget(row, 3, holdTimeSb)
        return row

    def deleteRowClicked(self):
        table = self.currentTable
        row = table.currentRow()
        table.removeRow(row)
        print "Delete row"

    def startPbClicked(self):
        self.enableWidgets(False)
        self.nextRampIndex = 1
        self.nextRamp()

    def skipHoldPbClicked(self):
        self.holdTime = 0

    def stopPbClicked(self):
        self.enterIdle()

    def enterIdle(self):
        self.state = State.IDLE
        self.updateStatus('Idle')
        self.enableWidgets(True)
        self.currentTable.clearSelection()

    def nextRamp(self):
        i = self.nextRampIndex
        n = self.currentTable.rowCount()
        if i > n: # Check if done
            self.enterIdle()
            return
        else: # start the next ramp
            self.startRamp(i-1)
            i += 1
            self.nextRampIndex = i

    def startRamp(self, row):
        table = self.currentTable
        table.selectRow(row)
        enabled = table.cellWidget(row, 0).isChecked()
        if enabled: # go for it
            rampRate = table.cellWidget(row, 1).value()
            self.target = table.cellWidget(row, 2).value()
            if self.target < self.magnetCurrentSb.value():
                rampRate = -rampRate
            self.requestRampRate(rampRate)

            self.holdTime = table.cellWidget(row, 3).value()
        else: #skip
            self.nextRamp()

    def magnetCurrentUpdated(self, current):
        if self.state == State.IDLE:
            return
        print "Target:", self.target
        if self.rampRate > 0: # Ramping up
            if current >= self.target:
                self.enterHold()
        elif self.rampRate < 0: # Ramping down
            if current <= self.target:
                self.enterHold()
        elif self.state == State.HOLDING: # Holding
            if self.holdTime > 0:
                remainingTime = self.holdTime - (time.time()-self.tHoldStart)
                self.updateStatus('Hold %.1f s' % remainingTime)
                if remainingTime <= 0:
                    self.nextRamp()
            elif self.holdTime == 0:
                self.nextRamp()

    def requestRampRate(self, rampRate):
        print "New ramp rate:", rampRate
        A_per_s = rampRate * 1E-3/60.
        ok = self.magnetRemote.changeRampRate(A_per_s)
        self.rampRate = rampRate
        if not ok:
            self.stopPbClicked()

        if rampRate == 0:
            self.state = State.HOLDING
            self.updateStatus('Holding')
        else:
            self.skipPb.setText('&Skip ramp')
            self.state = State.RAMPING
            self.updateStatus('Ramping')

    def skip(self):
        if self.state == State.RAMPING:
            self.enterHold()
        elif self.state == State.HOLDING:
            self.nextRamp()

    def enterHold(self):
        print "Entering hold"
        self.skipPb.setText('&Skip hold')

        self.requestRampRate(0)
        self.tHoldStart = time.time()

    def updateStatus(self, message):
        self.statusLe.setText(message)

    def enableWidgets(self, enable=True):
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)
        self.skipPb.setEnabled(not enable)

    def closeEvent(self, e):
        self.saveSettings()
        self.magnetRemote.stop()
        self.hkSub.stop()
        super(AdrControlWidget, self).closeEvent(e)

    def saveSettings(self):
        s = QSettings()

        table = self.currentTable

        nRows = table.rowCount()
        s.beginWriteArray('currentTable', nRows)
        for row in range(nRows):
            s.setArrayIndex(row)
            s.setValue('enabled', table.cellWidget(row,0).isChecked())
            s.setValue('rampRate', table.cellWidget(row,1).value())
            s.setValue('target', table.cellWidget(row,2).value())
            s.setValue('holdTime', table.cellWidget(row,3).value())
        s.endArray()

    def restoreSettings(self):
        s = QSettings()

#        geometry = s.value('geometry', QByteArray(), type=QByteArray)
#        self.restoreGeometry(geometry)

        rows = s.beginReadArray('currentTable')
        for i in range(rows)[::-1]:
            s.setArrayIndex(i)
            enabled = s.value('enabled', True, type=bool)
            rampRate = s.value('rampRate', 10, type=float)
            target = s.value('target', 0.2, type=float)
            holdTime = s.value('holdTime', 60, type=float)
            self.addRowClicked(enabled, rampRate, target, holdTime)
        s.endArray()


if __name__ == '__main__':
    import sys
    import logging
    from Utility.Utility import ExceptionHandler
    logging.basicConfig(level=logging.DEBUG)

    exceptionHandler = ExceptionHandler()
    sys._excepthook = sys.excepthook
    sys.excepthook = exceptionHandler.handler


    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('AdrControl')

    mw = AdrControlWidget()
    mw.show()
    app.exec_()

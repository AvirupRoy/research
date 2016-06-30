# -*- coding: utf-8 -*-
"""
Created on Thu Jun 09 10:51:15 2016

@author: wisp10
"""

from LabWidgets.Utilities import compileUi
compileUi('WaterLeak')
import WaterLeakUi as ui

from PyQt4.QtGui import QWidget, QApplication, QListWidgetItem
from PyQt4.QtCore import QTimer, Qt, QSettings, QString
from GmailDetector import sendGmail


import DAQ.PyDaqMx as daq

import time 
import numpy as np
class WaterLeakWidget(QWidget, ui.Ui_Form):
    def __init__(self, parent=None):
        super(WaterLeakWidget, self).__init__(parent)
        self.setupUi(self)
        self.testPb.clicked.connect(self.sendTestAlert)
        self.armPb.toggled.connect(self.updateArmedText)
        self.addEmailPb.clicked.connect(self.addEmail)
        self.deleteEmailPb.clicked.connect(self.deleteEmail)
        self.restoreSettings()
        timer = QTimer()
        timer.setInterval(1000)
        timer.timeout.connect(self.checkForLeak)
        timer.start()
        self.timer = timer
        
    def restoreSettings(self):
        s = QSettings()
        n = s.beginReadArray('EMailList')
        print "n=", n
        for i in range(n):
            s.setArrayIndex(i)
            checked = s.value('Checked', Qt.Checked, type = Qt.CheckState)
            address = s.value('EMail', '', type=QString)
            print i, checked, address
            item = QListWidgetItem(address)
            item.setCheckState(checked)
            self.emailListWidget.insertItem(0, item)
        s.endArray()
    
    def saveSettings(self):
        s = QSettings()
        s.beginWriteArray('EMailList')
        for row in range(self.emailListWidget.count()):
            s.setArrayIndex(row)
            item = self.emailListWidget.item(row)
            print row, item.checkState(), item.text()
            s.setValue('Email', item.text())
            s.setValue('Checked', item.checkState())
        s.endArray()
    
    def closeEvent(self, event):
        self.timer.stop()
        self.saveSettings()
        
    def addEmail(self):
        address = self.emailLe.text()
        item = QListWidgetItem(address)
        item.setCheckState(Qt.Checked)
        self.emailListWidget.insertItem(0, item)
    
    def deleteEmail(self):
        Row = self.emailListWidget.currentRow()
        self.emailListWidget.takeItem(Row)
    
    def updateArmedText(self, toggled):
        if toggled:
            self.armPb.setText('Detector armed')
            self.appendLogMessage('Detector armed')
        else:
            self.armPb.setText('Detector disarmed')     
            self.appendLogMessage('Detector disarmed')

    def checkForLeak(self):
        print "Checking for leak"
        task = daq.DiTask('Check leak sensor')
        channel = daq.DiChannel('PXI6025E/port0/line7')
        task.addChannel( channel )
        task.commit()
        data = task.readData(10)
        print data
        n = np.count_nonzero(data)
        print n
        if n > 7:
            leak = False
        elif n < 3:
            leak = True
        self.alarmLed.setValue(leak)
        print leak
        if leak and self.armPb.isChecked():
             self.sendAlert()
             self.armPb.setChecked(False)
             
    def activeRecipients(self):
        receivers = []
        for row in range(self.emailListWidget.count()):
            item = self.emailListWidget.item(row)
            if item.checkState() == Qt.Checked:
                receivers.append(str(item.text()))
        return receivers 
        
    def sendAlert(self):
        msg = 'Water detected in the big lab'
        receivers = self.activeRecipients() 
        self.appendLogMessage('Flood detected')
        try:
            sendGmail(receivers, msg)
        except Exception, e: 
            self.appendLogMessage('Failed to send flood detection alert (error: %s)' % e)
            
    def sendTestAlert(self):
        msg = 'Test alert'
        #receivers = ['daniel.timbie@gmail.com', '6089572745@messaging.sprintpcs.com','6085560289@txt.att.net']
        receivers = self.activeRecipients()
        self.appendLogMessage('Sent test email')
        try:
            sendGmail(receivers, msg)
        except Exception, e: 
            self.appendLogMessage('Failed to send test email (error: %s)' % e)
            
    def appendLogMessage(self, message):
        self.logTextEdit.appendPlainText('%s: %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), message))
    
    
if __name__ == '__main__':
    import ctypes
    from PyQt4.QtGui import QIcon
    myappid = u'LeakDetector' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)    
    app = QApplication([])
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('WaterLeak')
    app.setWindowIcon(QIcon('Icons/flood-zone-sign.png'))

    w = WaterLeakWidget()
    w.show()
    app.exec_()
    time.sleep(100)
     
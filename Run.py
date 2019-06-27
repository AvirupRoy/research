# -*- coding: utf-8 -*-
"""
RUN information dialog
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""


from LabWidgets.Utilities import compileUi
compileUi('RunUi')
import RunUi as Ui
from PyQt4.QtGui import QDialog, QFileDialog
from PyQt4.QtCore import QSettings, QString # pyqtSignal, QThread, 
import os

class RunDialog(Ui.Ui_Dialog, QDialog):
    def __init__(self, parent = None):
        super(RunDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('ADR3 run info')
        self.selectPb.clicked.connect(self.selectBasePath)
        self.buttonBox.accepted.connect(self.saveSettings)
        self.runLe.textChanged.connect(self.updatePath)
        self.restoreSettings()
    
    def selectBasePath(self):
        newPath = QFileDialog.getExistingDirectory(parent=self, caption='Select the base directory for the runs.', directory=self.basePath)
        if newPath:
            self.basePath = newPath
            self.updatePath()
        
    def updatePath(self):
        self.runPath = self.basePath + '/' + self.runLe.text()
        self.pathLe.setText(self.runPath)
        if os.path.isdir(self.runPath):
            self.existsLabel.setText('Already exists!')
        else:
            self.existsLabel.setText('')
        
    def restoreSettings(self):
        s = QSettings()
        self.basePath = s.value('basePath', '', type=QString)
        runNumber = s.value('runNumber', 'F7C', type=QString)
        self.runLe.setText(runNumber)
        
    def saveSettings(self):
        s = QSettings()
        s.setValue('basePath', self.basePath)
        s.setValue('runNumber', self.runLe.text())
        s.setValue('runPath', self.runPath )
        path = str(self.runPath)
        if not os.path.isdir(path):
            os.makedirs(path)

if __name__ == "__main__":
    import sys
    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName('ADR3RunInfo')
    app.setOrganizationName('WiscXrayAstro')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationVersion('0.1')
    
    import ctypes
    myappid = u'WISCXRAYASTRO.ADR3.AdrRunInfo' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    dlg = RunDialog()
    dlg.exec_()
    s = QSettings()
    sys.exit()

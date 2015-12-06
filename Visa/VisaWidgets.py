# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 15:07:57 2015

@author: wisp10
"""

from PyQt4.QtGui import QComboBox, QMenu, QAction
from PyQt4.QtCore import QThread, pyqtSignal
from PyQt4.Qt import Qt
from VisaInstrument import findVisaResources, VisaInstrument

class QueryIdThread(QThread):
    idObtained = pyqtSignal(str,str)    
    def __init__(self, visaResources, parent=None):
        QThread.__init__(self, parent)
        self.visaResources = visaResources
        
    def run(self):
        for resource in self.visaResources:
            inst = VisaInstrument(resource)
            try:
                ID = inst.visaId()
            except:
                ID = 'No response'
            self.idObtained.emit(resource,ID)
            if '34401A' in ID:
                inst.commandString(':SYST:BEEP')
    
class VisaCombo(QComboBox):
    def __init__(self, parent=None):
        QComboBox.__init__(self, parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.populate()
        
    def populate(self):
        resources = findVisaResources()
        self.clear()
        for r in resources:
            self.addItem(r)
            
    def updateToolTip(self, visaResource, ID):
        item = self.findText(visaResource)
        if item is not None:
            self.setItemData(item, ID, Qt.ToolTipRole)
            
    def visaResource(self):
        return str(self.currentText())
    
    def contextMenu(self, point):
        globalPos = self.mapToGlobal(point)
        menu = QMenu()
        resource = self.currentText()
        refreshAction = QAction("&Refresh", menu)
        if len(resource):
            queryIdAction = QAction("Query %s for ID" % resource, menu)
            menu.addAction(queryIdAction)
        queryAllAction = QAction("Query all for ID", menu)
        menu.addAction(queryAllAction)
        menu.addSeparator()
        menu.addAction(refreshAction)
        selected = menu.exec_(globalPos)
        
        if selected == queryIdAction:
            print "Query selected"
            thread = QueryIdThread([resource], self)
            thread.idObtained.connect(self.updateToolTip)
            thread.start()
        elif selected == queryAllAction:
            resources = []
            for i in range(self.count()):
                resources.append(self.itemText(i))
            thread = QueryIdThread(resources, self)
            thread.idObtained.connect(self.updateToolTip)
            thread.start()
        elif selected == refreshAction:
            print "Refresh"
            self.populate()

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    mw = VisaCombo()
    mw.show()
    app.exec_()
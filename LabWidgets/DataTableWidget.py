# -*- coding: utf-8 -*-
"""
A QTableWidget subclass to support named columns with custom widgets,
 as well as saving and restoring rows to QSettings.
 The idea is nice, however it's hard to use with Qt Designer because of the
 extra constructor arguments required.
Created on Mon Mar 21 18:29:59 2016
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from PyQt4.QtGui import QTableWidget, QHeaderView, QTableWidgetItem, QAbstractItemView
from PyQt4.QtCore import QSettings
from LabWidgets.Utilities import restoreWidgetFromSettings, saveWidgetToSettings, widgetValue, setWidgetValue

def rowHeaderFormatter(i):
    return "CH %d" % (i+1)
    
class DataTableWidget(QTableWidget):
    def __init__(self, widgetFactory, columnNames, nRows=0, rowHeaders=rowHeaderFormatter, parent=None):
        '''Construct the table with columnsNames and custom cell widgets for each column provided by widgetFactory.'''
        super(DataTableWidget, self).__init__(parent)
        self.columnIndices = {}
        self.columnNames = columnNames
        self.setColumnCount(len(columnNames)) 
        self.setHorizontalHeaderLabels(columnNames)
        self.rowHeaders = rowHeaderFormatter
        self.widgetFactory = widgetFactory
        horizontalHeader = self.horizontalHeader()
        for column,name in enumerate(columnNames):
            self.columnIndices[name] = column
            #horizontalHeader.setResizeMode(column, QHeaderView.ResizeToContents )

        self.setRowCount(nRows)
        for row in range(nRows):
            self.populateRow(row)
        #self.setVisible(False)
        self.resizeRowsToContents()
        #self.setVisible(True)
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        #self.setDragEnabled(True)
        #self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
    def setRowBackground(self, row, color='yellow'):
        styleSheet = "background-color:%s;" % color
        for column in range(self.columnCount()):
            self.cellWidget(row, column).setStyleSheet(styleSheet)

    def populateRow(self, row):
        for column, columnName in enumerate(self.columnNames):
            self.setCellWidget(row, column, self.widgetFactory(columnName, row))
        self.setVerticalHeaderItem(row, QTableWidgetItem(self.rowHeaders(row)))
        
    def insertRow(self, row):
        super(DataTableWidget, self).insertRow(row)
        self.populateRow(row)
            
    def columnForName(self, name):
        return self.columnIndices[name]
    
    def saveSettings(self, s=None):
        '''Save table contents to QSettings'''
        if s is None:
            s = QSettings()
        name = self.objectName()
        if len(name) == 0:
            raise Exception('Cannot save settings without objectName property set.')
        s.beginWriteArray(name)
        for row in range(self.rowCount()):
            s.setArrayIndex(row)
            for columnName in self.columnNames:
                w = self.cellValue(row, columnName)
                print row,columnName, w
                s.setValue(columnName, w)
        s.endArray()
        
    def loadSettings(self, s=None):
        '''Load table contents from QSettings'''
        if s is None:
            s = QSettings()
        name = self.objectName()
        if len(name) == 0:
            raise Exception('Cannot load settings without objectName property set.')
        rowCount = s.beginReadArray(name)
        rowCount = min(self.rowCount(), rowCount)
        rowCount = self.rowCount()
        print rowCount
        for row in range(rowCount):
            s.setArrayIndex(row)
            for columnName in self.columnNames:
                w = self.cellWidgetByName(row, columnName)
                restoreWidgetFromSettings(s, w, columnName)
        s.endArray()
        
    def cellValue(self, row, columnName):
        w = self.cellWidgetByName(row, columnName)
        return widgetValue(w)
        
    def setCellValue(self, row, columnName, value):
        w = self.cellWidgetByName(row, columnName)
        setWidgetValue(w, value)

    def cellWidgetByName(self, row, columnName):
        return self.cellWidget(row, self.columnForName(columnName))        

if __name__ == '__main__':
    import PyQt4.QtGui as gui    
    app = gui.QApplication([])

    def widgetFactory(name, row):
        if name == 'Enabled':
            w = gui.QCheckBox()
        elif name == 'Range':
            w = gui.QDoubleSpinBox()
            w.setMinimum(0.1)
            w.setMaximum(10)
            w.setDecimals(3)
            w.setToolTip('Spin it up!')
        elif name == 'Sample':
            w = gui.QLineEdit()
        elif name == 'Calibration':
            w = gui.QComboBox()
            w.addItems(['Bla', 'Blub', 'Blaeh'])
        return w
            
    table = DataTableWidget(widgetFactory, ['Enabled', 'Range', 'Calibration', 'Sample'], 5)
    table.setObjectName('TestTable')
    s = QSettings('Test', 'TestTable')
    table.loadSettings(s)
    for i in range(table.rowCount()/2):
        table.setRowBackground(2*i, 'red')
        table.setRowBackground(2*i+1, 'yellow')
    table.closeEvent = lambda x: table.saveSettings(s)
    table.show()
    table.resizeColumnsToContents()
    #table.adjustSize()
    app.exec_()
    
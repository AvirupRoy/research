# -*- coding: utf-8 -*-
"""
Created on Sat Jan 13 20:36:15 2018

@author: wisp10
"""

from Analysis.TesIvSweepReader import IvSweepCollection
from PyQt4.QtGui import QWidget, QMainWindow, QAction, QToolBar, QFileDialog, QMdiArea, QIcon, QKeySequence, qApp, QMessageBox
from PyQt4.QtGui import QTableView, QDockWidget
from PyQt4.Qt import Qt

from PyQt4.QtCore import QAbstractTableModel, QVariant, QSignalMapper

from PyQt4.QtCore import pyqtSignal #, pyqtSlot

import numpy as np


class SweepTableModel(QAbstractTableModel):
    plotToggled = pyqtSignal(int, bool)
    badToggled = pyqtSignal(int, bool)
    
    def __init__(self, sweepCollection, parent = None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.sc = sweepCollection
        n = self.sc.nSweeps
        self.bad = np.zeros((n,), dtype=bool)
        self.plot = np.zeros((n,), dtype=bool)
        self.header = ['Plot', 'Bad', 'Tbase', 'Ic+', 'Ic-']
        
    def rowCount(self, parent):
        return self.sc.nSweeps
        
    def columnCount(self, parent):
        return 5
        
    def data(self, index, role):
        if not index.isValid() or role != Qt.DisplayRole:
            return QVariant()
        row = index.row()
        col = index.column()
#        if role == Qt.CheckStateRole:
#            if col == 0:
#                return Qt.Checked if self.plot[row] else Qt.Unchecked
#            elif col == 1:
#                return Qt.Checked if self.bad[row] else Qt.Unchecked
        if role == Qt.DisplayRole:
            print('Data @ row, column:',row, col)
            if col == 0:
                return self.plot[row]
            elif col == 1:
                return self.bad[row]
            elif col == 2:
                v = self.sc.adrR[row]
                #print('ADR R:', v)
                return str(v)
            elif col in [3, 4]:
                return 'NA'
        return QVariant()
            
    def setData(self, index, value, role):
        print('Set data')
        if not index.isValid():
            return False
        if role == Qt.EditRole or role == Qt.DisplayRole:
            col = index.column()
            row = index.row()
            checked = bool(value)
            print('Set value: row,col,checked=', row, col, checked)
            if col == 0:
                self.plot[row] = checked
                self.dataChanged.emit(index,index)
                self.plotToggled.emit(row, checked)
            elif col == 1:
                self.bad[row] = checked
                print('About to emit!')
                self.dataChanged.emit(index,index)
                print(type(row), type(checked), self.badToggled)
                self.badToggled.emit(row, checked)
                print('Emitted!')
            
    def flags(self, index):
        if not index.isValid():
            return
        col = index.column()
        #print('Flags for col', col)
        if col in [0,1]:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled
        
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[section]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section)
            

from ItemDelegates import CheckBoxDelegate

from IvGraph import IvGraphWidget


from PyQt4.QtGui import QSplitter
        
import pyqtgraph as pg        
class HkView(QDockWidget):
    def __init__(self, hkData, parent = None):
        QDockWidget.__init__(self)
        self.hkData = hkData

        faaTimeAxis = pg.DateAxisItem(orientation='bottom')
        faaTempPlot = pg.PlotWidget(axisItems={'bottom': faaTimeAxis})
        faaTempPlot.setBackground('w')
        faaTempPlot.showGrid(x=True, y=True)
        faaTempPlot.setLabel('bottom', 'time')
        faaTempPlot.setLabel('left', 'T', 'K')

        gggTimeAxis = pg.DateAxisItem(orientation='bottom')
        gggTempPlot = pg.PlotWidget(axisItems={'bottom': gggTimeAxis})
        gggTempPlot.setLabel('left', 'T', 'K')

        faaTempPlot.addLegend()
        gggTempPlot.addLegend()
        
        pens = {'BusThermometer': 'r', 'RuOx2005': 'b', 'BoxThermometer': 'g', 'GGG': 'k'}
        for thermometerId in self.hkData.thermometers.keys():
            thermo = self.hkData.thermometers[thermometerId]
            try:
                pen = pens[thermometerId]
            except KeyError:
                pen = 'k'
            curve = pg.PlotDataItem(name=thermometerId, pen = pen)
            curve.setData(thermo.t, thermo.T)
            #curve.setPen(pen)
            if thermometerId in ['BoxThermometer', 'BusThermometer', 'RuOx2005']:
                faaTempPlot.addItem(curve)
            elif thermometerId in ['GGG']:
                gggTempPlot.addItem(curve)
            else:
                print('Ignoring thermometer:', thermometerId)
        
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(faaTempPlot)
        splitter.addWidget(gggTempPlot)
        self.setWidget(splitter)


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('IV Analyzer')
        self.mdiArea  = QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setCentralWidget(self.mdiArea)

        self.windowMapper = QSignalMapper(self)
#        self.windowMapper.mapped[QWidget].connect(self.setActiveSubWindow) # This indirection check whether window actual existed; not sure it's needed
        self.windowMapper.mapped[QWidget].connect(self.mdiArea.setActiveSubWindow)
        
        self.setupActions()
        self.setupMenuBar()

        
        toolbar = QToolBar('Analysis')
        toolbar.addAction(self.circuitParametersAction)
        self.addToolBar(toolbar)

    def setupActions(self):
        self.openAct = QAction(QIcon(':/images/open.png'),
                               "&Open...", self, shortcut=QKeySequence.Open,
                               statusTip="Open an existing file", triggered=self.openFile)

        self.exitAct = QAction("E&xit", self, shortcut=QKeySequence.Quit,
                               statusTip="Exit the application", triggered=qApp.closeAllWindows)

        self.closeAct = QAction("Cl&ose", self, statusTip="Close the active window",
                                triggered=self.mdiArea.closeActiveSubWindow)                               

        self.closeAllAct = QAction("Close &All", self, statusTip="Close all the windows",
                                   triggered=self.mdiArea.closeAllSubWindows)                       

        self.tileAct = QAction("&Tile", self, statusTip="Tile the windows",
                               triggered=self.mdiArea.tileSubWindows)
        
        self.cascadeAct = QAction("&Cascade", self, statusTip="Cascade the windows", triggered=self.mdiArea.cascadeSubWindows)
        self.nextAct = QAction("Ne&xt", self, shortcut=QKeySequence.NextChild,
                        statusTip="Move the focus to the next window",
                        triggered=self.mdiArea.activateNextSubWindow)
                        
        self.previousAct = QAction("Pre&vious", self, shortcut=QKeySequence.PreviousChild,
                                   statusTip="Move the focus to the previous window",
                                   triggered=self.mdiArea.activatePreviousSubWindow)
        self.separatorAct = QAction(self)
        self.separatorAct.setSeparator(True)
        self.aboutAct = QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)
        
        self.aboutQtAct = QAction("About &Qt", self,
                statusTip="Show the Qt library's About box",
                triggered=qApp.aboutQt)                                  
        
        action = QAction('&Apply circuit parameters', self)
        #action.triggered.connect(self.circuitParamtersTriggered)
        self.circuitParametersAction = action
        
    def setupMenuBar(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)        

        self.windowMenu = self.menuBar().addMenu("&Window")
        self.updateWindowMenu()
        self.windowMenu.aboutToShow.connect(self.updateWindowMenu)
        self.menuBar().addSeparator()
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)
        
    def updateWindowMenu(self):
        self.windowMenu.clear()
        self.windowMenu.addAction(self.closeAct)
        self.windowMenu.addAction(self.closeAllAct)
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.tileAct)
        self.windowMenu.addAction(self.cascadeAct)
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.nextAct)
        self.windowMenu.addAction(self.previousAct)
        self.windowMenu.addAction(self.separatorAct)
 
        windows = self.mdiArea.subWindowList()
        self.separatorAct.setVisible(len(windows) != 0)
 
        for i, window in enumerate(windows):
            child = window.widget()
 
            text = "%d %s" % (i + 1, child.windowTitle())
            if i < 9:
                text = '&' + text
 
            action = self.windowMenu.addAction(text)
            action.setCheckable(True)
            action.setChecked(child is self.activeMdiChild())
            action.triggered.connect(self.windowMapper.map)
            self.windowMapper.setMapping(action, window)
        
    def createToolBars(self):
        self.fileToolBar = self.addToolBar("File")
        self.fileToolBar.addAction(self.openAct)
        self.addToolBar(self.fileToolBar)
        
    def openFile(self):
        fileName = QFileDialog.getOpenFileName(parent=self, caption='Select file', directory='D:\\Users\\Runs\\G4C\\IV', filter = '*.h5')
        if len(fileName) > 0:
            print(fileName)
            self.loadSweepFile(fileName)
            
    def about(self):
        QMessageBox.about(self, "About IvAnalyzer",
                "IvAnalyzer application allows exploring and analyzing sets of IV sweeps.\n"
                "(c) 2018 Felix Jaeckel <felix.jaeckel@wisc.edu>")            
        
    def loadSweepFile(self, fileName):  # This needs to go in its own class, I think. Since it's sets up the model and view, probably make a new controller class?!
        sweepCollection = IvSweepCollection(str(fileName))
        
        tableModel = SweepTableModel(sweepCollection)
        
        tableView = QTableView()
        tableView.setModel(tableModel)
        tableView.setItemDelegateForColumn(0, CheckBoxDelegate(parent=tableView))
        tableView.setItemDelegateForColumn(1, CheckBoxDelegate(parent=tableView))
        self.tableModel = tableModel
        tableView.resizeColumnsToContents()
        
        dockWidget = QDockWidget('Sweeps', self)
        dockWidget.setWidget(tableView)
        self.addDockWidget(Qt.RightDockWidgetArea, dockWidget)
        
        hkDock = HkView(sweepCollection.hk)
        hkDock.setWindowTitle('HK - %s' % str(fileName))
        self.addDockWidget(Qt.BottomDockWidgetArea, hkDock)
        
        ivGraphWidget = IvGraphWidget(sweepCollection)
        
        tableModel.plotToggled.connect(ivGraphWidget.showSweep)
        #tableModel.badToggled.connect(self.toggleBad)
        
        self.ivGraphWidget = ivGraphWidget
        
        subWindow = self.mdiArea.addSubWindow(ivGraphWidget)
        subWindow.setWindowTitle(fileName)
        subWindow.show()
        self.mdiArea.setActiveSubWindow(subWindow)
        

        # By default, show about 20 curves
        n = len(sweepCollection)
        nStep = int(n / 20)
        for i in range(0, n, nStep):
            pass
            #self.togglePlot(i, True)
        
        
#    def dataChanged(self, index1, index2):
#        print('Data changed:', index1, index2)
        
        


if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    path = 'D:\\Users\\Runs\\G4C\\IV\\'
    fileName = path+'TES1_IV_DirectShapiro_RampT_20180112_175638.h5'

    app = QApplication([])
    mw = MainWindow()
    #mw.openFile(fileName)
    mw.show()
    
#    sweepCollection = IvSweepCollection(fileName)
#    #sweepCollection.ad
#    
#    tableModel = SweepTableModel(sweepCollection)
#    
#    tableView = QTableView()
#    tableView.setItemDelegateForColumn(0, CheckBoxDelegate(parent=tableView))
#    tableView.setItemDelegateForColumn(1, CheckBoxDelegate(parent=tableView))
#    tableView.setModel(tableModel)
#    tableView.show()
    
    app.exec_()
    
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 04 15:30:15 2016

@author: wisp10
"""

#from PyQt4 import uic
#uic.compileUiDir('.')
#print "Done"

#from math import isnan

from PyQt4.QtGui import QWidget, QLabel, QPixmap, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, QGroupBox, QFrame, QMainWindow, QProgressBar, QDockWidget, QTextEdit, QAction, QToolBar, QFileDialog, QPainter
from PyQt4.QtCore import QSettings, QTimer, QString, pyqtSignal, QThread, QSignalMapper, pyqtSlot, QByteArray, Qt, QPoint

#import gc
#gc.set_debug(gc.DEBUG_LEAK)

# Issues:
# Downloading gif cancels edit


import Queue
class WorkerThread(QThread):
    gifDownloadStarted = pyqtSignal(int)
    '''Emitted just before the download is started'''
    gifReceived = pyqtSignal(int, QByteArray)
    keyPressSimulated = pyqtSignal(int)
    knobRotated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super(WorkerThread, self).__init__(parent=parent)
        self.queue = Queue.Queue()
    
    def associateInstrument(self, sr785):
        self.sr785 = sr785

    def stop(self):
        self.stopRequested = True
        
    def requestKeyPress(self, keyCode):
        self.queue.put(('KEY',keyCode))
        
    def requestScreenshot(self, screen):
        self.queue.put(('SCREEN', screen))
    
    def requestKnobRotateCw(self):
        self.queue.put(('KNOB', 1))

    def requestKnobRotateCcw(self):
        self.queue.put(('KNOB', 0))
    
    def run(self):
        self.stopRequested = False
        try:
            sr = self.sr785
            while not self.stopRequested:
                while self.queue.empty():
                    if self.stopRequested:
                        raise Exception('Done')
                    self.msleep(50)
                job = self.queue.get()
                task = job[0]
                if task == 'KEY':
                    keyCode = job[1]
                    sr.simulateKeyPress(keyCode)
                    self.keyPressSimulated.emit(keyCode)
                elif task == 'KNOB':
                    steps = job[1]
                    sr.rotateKnob(steps)
                    self.knobRotated.emit(steps)
                elif task == 'SCREEN':
                    screen = job[1]
                    self.gifDownloadStarted.emit(screen)
                    data = sr.downloadScreen(screen)
                    self.gifReceived.emit(screen, data)
                elif task == 'STOP':
                    raise Exception('Done')
            print "Worker done"
        except Exception, e:
            print "Encountered exception:", e


class ClickableLabel(QLabel):
    clicked = pyqtSignal(QPoint)
#    doubleClicked = pyqtSignal(QPoint)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(event.pos())
        
            
class SR785_Screen(QWidget):
    softKeyClicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super(SR785_Screen, self).__init__(parent)
        self.workerThread = None
        self.setupUi()
        
    def setupUi(self):
        label = QLabel(parent=self)
        label.setGeometry(0,0,640,100)
        label.setFixedSize(640,100)
        label.setText('Status...')
        label.setToolTip('<b>Status area</b>\nDouble click to refresh.')
        self.statusLabel = label

        label = QLabel(parent=self)
        label.setGeometry(0,100,640, 500)
        label.setFixedSize(640,500)
        label.setText('Graphs...')
        label.setToolTip('<b>Graph area</b>\nDouble click to refresh.')
        self.graphsLabel = label
        
        label = ClickableLabel(parent=self)
        label.setGeometry(640,0, 160, 600)
        label.setFixedSize(160,600)
        label.clicked.connect(self.menuClicked)
        label.setText('Menu...')
        label.setToolTip('<b>Menu area</b>\nClick on buttons (soft-keys) to enter menu.\nDouble click to refresh.')
        self.menuLabel = label
        
    def pixmap(self):
        pixmap = QPixmap(800,600)
        painter = QPainter(pixmap)
        painter.drawPixmap(0,0, self.statusLabel.pixmap())
        painter.drawPixmap(0,100, self.graphsLabel.pixmap())
        painter.drawPixmap(640,0, self.menuLabel.pixmap())
        return pixmap
        
    def mouseDoubleClickEvent(self, event):
        print "Double clicked:", event.pos()

    def menuClicked(self, point):
        #print "Menu clicked at", point.x(), point.y()
        softKey = int(1+(point.y()-30)/57)
        #print "Softkey:", softKey
        if softKey < 1 or softKey > 10:
            return
        self.softKeyClicked.emit(softKey)
        
    def setGraphsPixmap(self, pixmap):
        self.graphsLabel.setPixmap(pixmap)
        
    def setMenuPixmap(self, pixmap):
        self.menuLabel.setPixmap(pixmap)
    
    def setStatusPixmap(self, pixmap):
        self.statusLabel.setPixmap(pixmap)
        
class SR785_Keyboard(QWidget):
#    keyClicked = pyqtSignal(int)
    enterClicked = pyqtSignal()
    knobRotatedCw = pyqtSignal()
    knobRotatedCcw = pyqtSignal()
    
    def __init__(self, parent=None):
        super(SR785_Keyboard, self).__init__(parent=parent)
        entryKeyMap = [('Alt', 7), ('<-', 6), ('EXP', 5), ('7',2), ('8',3), ('9',4), ('4', 13), ('5',14), ('6', 15), ('1', 21), ('2', 22), ('3', 23), ('0', 29), ('.',30), ('-', 31)]
        controlKeyMap = [('Start\nReset', 17), ('Start\ncapture', 18), ('Active\nDisplay', 19), ('Print\nScreen',20), ('Pause\nCont',25), ('Stop\nCapture', 26), ('Link',14), ('Help\nLocal',28)]
        menuKeyMap = [('Freq',33,'A'), ('Display\nSetup',34,'B'), ('Display\nOptions',35,'C'), ('Marker',36,'D'), ('Source',41,'H'), ('Input',42,'I'), ('Trigger',43,'J'), ('Average',44,'K'), ('User\nMath',49,'O'), ('Window',50,'P'), ('Water\nFall',51,'Q'), ('Capture',52,'R'), ('Analysis',57,'V'), ('Disk',58,'W'), ('Output',59,'X'), ('System',60,'Y')]
        functionKeyMap = [('Auto\nScale A',37,'E'), ('Auto\nRange Ch1',38,'F'), ('Marker\nRef',39,'G'), ('Auto\nScale B',45,'L'), ('AutoRange\nCh2',46,'M'), ('Display\nRef', 47,'N'), ('Span\nUp',53,'S'), ('Marker\nMax', 54,'T'), ('Marker\nCenter',55,'U'), ('Span\nDown',61,'Z'), ('Marker\nMin',62,'\\'), ('Show\nSetup',63,' ')]
        entryKeys = SR785_KeyArray('ENTRY', 3, 5, entryKeyMap)
        menuKeys = SR785_KeyArray('MENU', 4, 4, menuKeyMap)
        controlKeys = SR785_KeyArray('CONTROL', 4, 2, controlKeyMap)
        functionKeys = SR785_KeyArray('FUNCTION', 3, 4, functionKeyMap)
        self.entryKeys = entryKeys
        self.functionKeys = functionKeys
        self.controlKeys = controlKeys
        self.menuKeys = menuKeys

        enterKey1 = QPushButton('Enter')
        enterKey1.setStyleSheet('font: bold 20 px;')
        enterKey1.setFixedHeight(50)
        enterKey1.clicked.connect(self.enterClicked)
        upKey = QPushButton('^')
        upKey.setFixedHeight(50)
        upKey.clicked.connect(self.knobRotatedCw)
        downKey = QPushButton('v')
        downKey.setFixedHeight(50)
        downKey.clicked.connect(self.knobRotatedCcw)
        enterKey2 = QPushButton('Enter')
        enterKey2.setFixedHeight(50)
        enterKey2.clicked.connect(self.enterClicked)
        upDownLayout = QVBoxLayout()
        upDownLayout.addWidget(upKey)
        upDownLayout.addWidget(downKey)
        hLayout = QHBoxLayout()
        hLayout.addWidget(enterKey1)
        hLayout.addLayout(upDownLayout)
        hLayout.addWidget(enterKey2)
        
        layout = QGridLayout()
        layout.addLayout(hLayout,0,0)
        layout.addWidget(controlKeys,1,0)
        layout.addWidget(entryKeys,0,1, 2, 1)
        layout.addWidget(menuKeys,2,0)
        layout.addWidget(functionKeys,2,1)
        self.setLayout(layout)
        
#    def enterClicked(self):
    
class SR785_Widget(QWidget):
    def __init__(self, parent=None):
        super(SR785_Widget, self).__init__(parent=parent)
        self.screenActions = []
        action = QAction('Screen', self)
        action.setToolTip('Refresh the entire screen')
        action.triggered.connect(self.refreshAll)
        self.screenActions.append(action)
        self.refreshScreenAction = action
        action = QAction('Status', self)
        action.setToolTip('Refresh only the status area')
        action.triggered.connect(self.refreshStatus)
        self.screenActions.append(action)
        self.refreshStatusAction = action
        action = QAction('Menu', self)
        action.setToolTip('Refresh only the menu area')
        action.triggered.connect(self.refreshMenu)
        self.screenActions.append(action)
        self.refreshMenuAction = action
        action = QAction('Graphs', self)
        action.setToolTip('Refresh only the graph area')
        action.triggered.connect(self.refreshGraphs)
        self.screenActions.append(action)
        self.refreshGraphsAction = action
        self.setupUi()
        
    def setupUi(self):
        self.setWindowTitle('SR785 Front Panel Emulation')
        frame = QFrame()
        frame.setObjectName('CRT')
        frame.setStyleSheet('QFrame#CRT {border: 2px solid red; border-radius: 30px; background-color: black;}')
        frame.setFixedSize(830,630)
        frame.setContentsMargins(10,10,10,10)
        self.screen = SR785_Screen(parent=self)
        l1 = QHBoxLayout()
        l1.addWidget(self.screen)
        frame.setLayout(l1)
        self.keyboard = SR785_Keyboard(parent=self)
        self.screen.softKeyClicked.connect(self.handleSoftKey)
        layout = QHBoxLayout(self)
        layout.addWidget(frame)
        layout.addWidget(self.keyboard)
        
    def associateInstrument(self, sr785):
        workerThread = WorkerThread(parent=self)
        workerThread.associateInstrument(sr785)
        workerThread.gifReceived.connect(self.gifReceived)
        workerThread.start()

        self.workerThread = workerThread
        self.refreshAll()
        self.keyboard.menuKeys.keyClicked.connect(self.handleMenuKey)
        self.keyboard.functionKeys.keyClicked.connect(self.handleFunctionKey)
        self.keyboard.entryKeys.keyClicked.connect(self.handleEntryKey)
        self.keyboard.enterClicked.connect(self.handleEnterKey)
        self.keyboard.knobRotatedCcw.connect(workerThread.requestKnobRotateCcw)
        self.keyboard.knobRotatedCw.connect(workerThread.requestKnobRotateCw)
        
    def handleMenuKey(self, keyCode):
        self.workerThread.requestKeyPress(keyCode)
        self.refreshMenu()
        
    def handleFunctionKey(self, keyCode):
        self.workerThread.requestKeyPress(keyCode)
        self.refreshGraphs()        
    
    def handleEntryKey(self, keyCode):
        self.workerThread.requestKeyPress(keyCode)
        self.refreshStatus()
        
    def handleEnterKey(self):
        self.workerThread.requestKeyPress(1)
        self.refreshMenu()
        self.refreshStatus()

    def handleSoftKey(self, softKey):
        softKeyMap = {1:0, 2:12, 3:11, 4:10, 5:9, 6:8, 7:16, 8:24, 9:32, 10:40}
        keyCode = softKeyMap[softKey]
        self.workerThread.requestKeyPress(keyCode)
        #self.refreshMenu()   # Only sometimes... should have a way of determining...
        #self.refreshStatus()       # Would like to, but can't

    def closeEvent(self, event):
        if self.workerThread is not None:
            print "Trying to stop..."
            self.workerThread.stop()
            print "Waiting"
            self.workerThread.wait(5000)
            print "Done waiting"
            event.accept()
        
    def refreshStatus(self):
        self.workerThread.requestScreenshot(2)

    def refreshMenu(self):
        self.workerThread.requestScreenshot(1)
    
    def refreshGraphs(self):
        self.workerThread.requestScreenshot(0)
        
    def refreshAll(self):
        self.refreshStatus()
        self.refreshMenu()
        self.refreshGraphs()

    def gifReceived(self, screen, data):
        pixmap = QPixmap()
        print "Data:", len(data)#, data[0:5], data[-3:]
        pixmap.loadFromData(data)
        s = pixmap.size()
        print "Size:", s.width(), s.height()

        if screen == 0:
            self.screen.setGraphsPixmap(pixmap)
        elif screen == 1:
            self.screen.setMenuPixmap(pixmap)
        elif screen == 2:
            self.screen.setStatusPixmap(pixmap)

        
            
class SR785_KeyArray(QGroupBox):
    keyClicked = pyqtSignal(int)
    
    def __init__(self, title, nx, ny, keys, parent=None):
        super(SR785_KeyArray, self).__init__(title, parent)
        self.setupUi(nx, ny, keys)
        self.setStyleSheet('QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top center; padding: 2 60px; border: 3px solid lightgray; border-radius: 5px; font: bold 18 px;}')
        
    def setupUi(self, nx, ny, keys):
        mapper = QSignalMapper()
        
        layout = QGridLayout(self)
        for ix in range(nx):
            for iy in range(ny):
                key = keys[iy*nx+ix]
                keyPb = QPushButton(self)
                keyPb.setFixedHeight(40)
                keyPb.setText(key[0])
                keyPb.clicked.connect(mapper.map)
                layout.addWidget(keyPb, iy, ix)
                mapper.setMapping(keyPb, key[1])
        mapper.mapped.connect(self.keyClicked)
        self.mapper = mapper


from SR785 import SR785

class SR785_MainWindow(QMainWindow):
    GifInfo = {SR785.SCREEN_ALL: (21200, 'all'), SR785.SCREEN_MENU: (4840, 'menu'), SR785.SCREEN_STATUS: (4410, 'status'), SR785.SCREEN_GRAPHS: (11420, 'graphs')}
    def __init__(self, parent=None):
        super(SR785_MainWindow, self).__init__(parent)
        centralWidget = SR785_Widget()
        self.setCentralWidget(centralWidget)

        visaResource = 'GPIB1::10'
        sr785 = SR785(visaResource)
        sr785.configureScreenDump()
        centralWidget.associateInstrument(sr785)
        self.setWindowTitle('SR785 Front Panel Emulation: %s' % sr785.visaId())
        self.progressBar = QProgressBar()
        statusBar = self.statusBar()
        statusBar.addWidget(self.progressBar)

        toolBar = QToolBar('Screen')
        toolBar.addActions(centralWidget.screenActions)
        self.addToolBar(toolBar)
        
        thread = centralWidget.workerThread
        thread.gifDownloadStarted.connect(self.gifDownloadStarted)
        thread.gifReceived.connect(self.gifReceived)
        thread.keyPressSimulated.connect(self.keyPressSimulated)
        thread.knobRotated.connect(self.knobRotated)

        dockWidget = QDockWidget('History')
        self.historyTe = QTextEdit()
        dockWidget.setWidget(self.historyTe)
        self.addDockWidget(Qt.TopDockWidgetArea, dockWidget)
        
        toolBar = self.addToolBar('File')
        action = QAction('Save screen', self)
        action.triggered.connect(self.saveScreen)
        toolBar.addAction(action)
        action = QAction('Print', self)
        action.triggered.connect(self.printScreen)
        toolBar.addAction(action)
        
        
    def saveScreen(self):
        directory = ''
        saveFile = QFileDialog.getSaveFileName(self, 'Save screen to', directory, '*.png *.gif', '*.png')
        print "saving as:", saveFile
        screenPixmap = self.centralWidget().screen.pixmap()
        screenPixmap.save(saveFile)
        self.log('Screen saved as: %s' % saveFile)
        
    def printScreen(self):
        pass

    def gifDownloadStarted(self, screen):
        self.progressBar.setMaximum(self.GifInfo[screen][0])
        self.progressBar.setValue(0)
        label = self.GifInfo[screen][1]
        self.progressBar.setFormat('%s %%p%%' % label)
        self.log('Downloading %s' % label)
        
    def gifReceived(self, screen):
        self.progressBar.setValue(self.GifInfo[screen][0])
        
    def keyPressSimulated(self, keyCode):
        self.log('Key %d pressed.' % keyCode)
        
    def knobRotated(self, steps):
        if steps > 0:
            self.log('Knob rotated CW.')
        else:
            self.log('Knob rotated CCW.')
        
    def log(self, message):
        self.historyTe.append(message+'\n')
        self.statusBar().showMessage(message, 2000)
    
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    #import sys

    app = QApplication([])
    mw = SR785_MainWindow()
    mw.show()
    app.exec_()

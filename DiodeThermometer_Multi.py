# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 12:12:32 2017

@author: Lan Hu
"""

from LabWidgets.Utilities import compileUi
compileUi('DiodeThermometer_MultiUi')
import DiodeThermometer_MultiUi as ui

#from DiodeThermometer2Copy import DiodeThermometerWidget
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import pyqtgraph as pg
from Visa.Agilent34401A import Agilent34401A

import numpy as np
import time
from Calibration.DiodeThermometers import DT470Thermometer, DT670Thermometer, Si70Thermometer
from Visa.VisaWidgets import VisaCombo
from LabWidgets.Utilities import saveWidgetToSettings, restoreWidgetFromSettings
import os

class DiodeThermometerThread(QThread):

    measurementReady = pyqtSignal(float, float)
    error = pyqtSignal(str)

    def __init__(self, dmm, parent=None):
        #QThread.__init__(self, parent)
        super(QThread,self).__init__()
        self.dmm = dmm
        self.interval = 1.0   
        #self.publisher = ZmqPublisher('DiodeThermometerThread', 5558, self)

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, seconds):
        self._interval = float(seconds)

    def stop(self):
        self.stopRequested = True
        #logger.debug("MagnetControlThread stop requested.")

    def sleepPrecise(self,tOld):
            tSleep = int(1E3*(self.interval-time.time()+tOld-0.010))
            if tSleep>0.010:
                self.msleep(tSleep)
            while(time.time()-tOld < self.interval):
                pass

    def run(self):
        self.stopRequested = False
        dmm = self.dmm
        #logger.info("Thread starting")
        dmm.setFunctionVoltageDc()
        try:
            while not self.stopRequested:
                t = time.time()
                V = dmm.reading()
                self.measurementReady.emit(t, V)
                self.sleepPrecise(t)
        except Exception as e:
            print('Error:', e)
            self.error.emit(e.message)
        finally:
            pass
        
class DiodeThermometer():
    def __init__(self, startPb,stopPb,dmmVisaCombo,
                     thermometerCombo,currentCombo,voltageSb,temperatureSb,
                     yAxisCombo, plot, n
                     ,errorDisplayTE,errorDisplayArray):
                    
        self.startPb = startPb
        self.stopPb = stopPb
        self.dmmVisaCombo = dmmVisaCombo
        self.thermometerCombo = thermometerCombo
        self.currentCombo = currentCombo
        self.voltageSb = voltageSb
        self.temperatureSb = temperatureSb
        self.yAxisCombo = yAxisCombo
        self.plot = plot
        self.errorDisplayTE = errorDisplayTE
        self.errorDisplayArray = errorDisplayArray
        self.index = n
        
        
        a = pg.intColor(self.index, hues=9, values=1, maxValue=255, minValue=150, maxHue=360, minHue=0, sat=255, alpha=255)
        p = pg.colorStr(a)        
        self.curve = pg.PlotCurveItem(name = 'DC' + str(self.index+1), symbol='o', pen = p)
        self.plot.addItem(self.curve)
        
        self.clearData()

        self.msmThread = None
       # self.restoreSettings()
        self.startPb.clicked.connect(self.startPbClicked)
        self.stopPb.clicked.connect(self.stopPbClicked)
        self.yAxisCombo.currentIndexChanged.connect(self.updatePlot)
        
            
    
    def displayError(self, error):
        self.errorDisplayTE.clear()
       #QMessageBox.critical(self, 'Error in measurement thread', error)
        message = 'Error in row {}: {}'.format(self.index+1,error)
        #self.errorDisplayTE.append('Error in Row %d: %s' % int(self.index+1),error)
        self.errorDisplayArray[self.index] = message
        for i in range(self.errorDisplayArray.__len__()):
            self.errorDisplayTE.append(self.errorDisplayArray[i])
    
    def update(self):
        
        ts = self.ts
        vs = self.Vs
        ys = self.Ts
        self.curve.clear()
        
        self.ts = ts
        self.Vs = vs
        self.Ts = ys

        self.index -= 1
        a = pg.intColor(self.index, hues=9, values=1, maxValue=255, minValue=150, maxHue=360, minHue=0, sat=255, alpha=255)
        p = pg.colorStr(a)        
        self.curve = pg.PlotCurveItem(symbol='o', pen = p)
        self.updatePlot()
        self.plot.addItem(self.curve)
#        self.clearData()
#        self.curve = pg.PlotCurveItem(name = 'DC' + str(self.index+1), symbol='o', pen='g' )
#        self.plot.addItem(self.curve)

    

    def startPbClicked(self):
        #self.errorDisplayTE.clear()
        #self.errorDisplayArray[self.index] = ""
        #self.errorDisplayTE.append(','.join(self.errorDisplayArray))

            
        address = str(self.dmmVisaCombo.currentText())
        self.dmm = Agilent34401A(address)
        self.visaId = self.dmm.visaId()
        
        
        thermo = self.thermometerCombo.currentText()
        if 'DT-470' in thermo:
            self.diodeCalibration = DT470Thermometer()
        elif 'DT-670' in thermo:
            self.diodeCalibration = DT670Thermometer()
        elif 'Si70' in thermo:
            self.diodeCalibration = Si70Thermometer()
        
        if thermo == 'Magnet stage DT-470':
            self.suffix = 'Magnet'
        elif thermo == '3K stage DT-670':
            self.suffix = '3K'
        elif thermo == '60K stage Si70':
            self.suffix = '60K'
        
        current = self.currentCombo.currentText()
        if '10' in current:
            self.I = 10E-6
        else:
            self.I = 1E-6
            
        thread = DiodeThermometerThread(dmm = self.dmm, parent = self)
        thread.measurementReady.connect(self.collectMeasurement)
        thread.error.connect(self.displayError)
        thread.finished.connect(self.threadFinished)
        self.stopPb.clicked.connect(thread.stop)
        self.msmThread = thread

        self.enableWidgets(False)
        self.msmThread.start()

        
    def threadFinished(self):
        self.enableWidgets(True)

    def collectMeasurement(self, t, V):
        T = self.diodeCalibration.calculateTemperature(V)

        dateString = time.strftime('%Y%m%d')
        fileName = 'DiodeThermometer%s_%s.dat' % (self.suffix, dateString)
        exists = os.path.isfile(fileName)
        with open(fileName, 'a') as of:
            if not exists:
                of.write(u'#DiodeThermometer4.py\n')
                of.write(u'#Date=%s\n' % time.strftime('%Y%m%d-%H%M%S'))
                of.write(u'#Instrument=%s\n' % self.visaId)
                of.write(u'#Thermometer=%s\n' % self.thermometerCombo.currentText())
                of.write(u'#Current=%s\n' % self.currentCombo.currentText())
                #of.write(u'#Calibration=%s\n' % self.calibration.name)
                of.write(u'#'+'\t'.join(['time', 'V', 'T', 'I'])+'\n')
                
            of.write("%.3f\t%.6f\t%.4f\t%.0e\n" % (t, V, T, self.I) )

        self.voltageSb.setValue(V)
        self.temperatureSb.setValue(T)
        self.ts.append(t) 
        self.Ts.append(T)
        self.Vs.append(V)
        self.updatePlot()
        
    def clearData(self):
        self.ts = []
        self.Vs = []
        self.Ts = []
        self.updatePlot()

    def updatePlot(self):
        x = np.asarray(self.ts)

        yAxis = self.yAxisCombo.currentText()
        if yAxis == 'Voltage':
            y = self.Vs
        elif yAxis == 'Temperature':
            y = self.Ts

        self.curve.setData(x, y)

    def updateStatus(self, message):
        self.stateLineEdit.setText(message)

    def enableWidgets(self, enable=True):
        self.startPb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)
        self.thermometerCombo.setEnabled(enable)
        self.currentCombo.setEnabled(enable)
        self.dmmVisaCombo.setEnabled(enable)
        
    def stopPbClicked(self):
        self.msmThread.stop()
        self.msmThread.wait(2000)
        self.stop = True
        
    def checkClicked(self):
        self.clickable = 0
        if self.startPb.isEnabled():
            self.clickable = 1
        else:
            self.clickable = 0
        #print self.clickable
        return self.clickable
        
    def getDmmVisaText(self):
        return self.dmmVisaCombo.currentText()
    def getThermoText(self):
        return self.thermometerCombo.currentText()
    def getCurrentText(self):
        return self.currentCombo.currentText()
        

class mainWindow(ui.Ui_Form, QWidget):
    def __init__(self, parent=None):
        super(mainWindow,self).__init__(parent)
        self.setupUi(self)
        #set plot
        self.yAxisCombo.currentIndexChanged.connect(self.plotLabel)
        axis = pg.DateAxisItem(orientation='bottom')
        self.plot = pg.PlotWidget(axisItems={'bottom': axis})
        self.verticalLayout.addWidget(self.plot)
        self.plot.addLegend()
        self.plot.setLabel('bottom', 'time')
        
        #connect
        self.clearPb.clicked.connect(self.clearData)
        self.StartAllPb.clicked.connect(self.startAll)
        self.StopAllPb.clicked.connect(self.stopAll)
        self.addRowPb.clicked.connect(self.addRow)
        self.deleteRowPb.clicked.connect(self.deleteRow)
        
        #set table
        self.rowCount = 0;
        self.tableWidget.setColumnCount(6)
        header = u'Enable,DMM VISA,Thermometer,Current (µA),Voltage,Temperature'
        self.tableWidget.setHorizontalHeaderLabels(header.split(','))
        self.tableWidget.setColumnWidth(1,150)
        self.tableWidget.setColumnWidth(2,150)
        
        
        self.objectList = []
        self.errorDisplayArray = [None for x in range(self.rowCount)]
        for i in range(self.errorDisplayArray.__len__()):
            self.errorDisplayTE.append(self.errorDisplayArray[i])
            
        
        self.rowSelected = -1
        self.settingsWidgets = [self.yAxisCombo]
        self.tableWidget.connect(self.tableWidget.verticalHeader(),SIGNAL("sectionClicked(int)"),self.selectRow)
        
        self.restoreSetting() 
    
       
    def plotLabel(self):
        yAxis = self.yAxisCombo.currentText()
        if yAxis == 'Voltage':
            self.plot.setLabel('left', 'V', units='V')
        elif yAxis == 'Temperature':
            self.plot.setLabel('left', 'T', units='K')
         
    def clearData(self):
        for i,a in enumerate(self.objectList):
            a.clearData()
            
    def startAll(self):
        #self.stopAll()
        for i,a in enumerate(self.objectList):
            if a.checkClicked() == 0:
                continue
            elif a.checkClicked() == 1:
                a.startPbClicked()
            
    def stopAll(self):
        for i,a in enumerate(self.objectList):
            #a.stopPbClicked()
            try:
                a.stopPbClicked()
            except AttributeError:
                continue
            
    def addRow(self, dmmVisaValue = "ASRL1::LNSTR", thermoValue = "Magnet stage DT-470", currentValue = "1"):
        if dmmVisaValue == False:
            dmmVisaValue = "ASRL1::LNSTR"
        
        self.rowCount += 1
        self.tableWidget.insertRow(self.rowCount - 1)
        self.errorDisplayArray.append(None)
        
        start = QPushButton()
        start.setText("Start")
        start.setFixedHeight(15)
        stop = QPushButton()
        stop.setText("Stop")
        stop.setFixedHeight(15)
        
        layout = QHBoxLayout()
        layout.addWidget(start)
        layout.addWidget(stop)            
        centralWidget = QWidget()
        centralWidget.setLayout(layout)

        dmmVisa = VisaCombo()
        dmmVisaList=["ASRL1::LNSTR","ASRL10::LNSTR"]
        dmmVisa.addItems(dmmVisaList)
        dmmVisaIndex = dmmVisa.findText(dmmVisaValue)
        dmmVisa.setCurrentIndex(dmmVisaIndex)
            
        thermometer = QComboBox()
        thermometerList=["Magnet stage DT-470","3K stage DT-670","60K stage Si70"]
        thermometer.addItems(thermometerList)
        thermoIndex = thermometer.findText(thermoValue)
        thermometer.setCurrentIndex(thermoIndex)
            
        current = QComboBox()
        currentList = ["1", "10"]
        current.addItems(currentList)
        currentIndex = current.findText(currentValue)
        current.setCurrentIndex(currentIndex)

        voltage = QDoubleSpinBox()
        voltage.setSuffix("V")
        voltage.setDecimals(4)
        voltage.setButtonSymbols(QAbstractSpinBox.NoButtons)
        voltage.setRange(-1000.0000,+1000.0000)
        voltage.setSingleStep(0.0001)
            
        temperature = QDoubleSpinBox()
        temperature.setSuffix("K")
        temperature.setDecimals(3)
        temperature.setButtonSymbols(QAbstractSpinBox.NoButtons)
        temperature.setRange(0.000,400.0000)
        temperature.setSingleStep(0.001)
            
        self.tableWidget.setCellWidget(self.rowCount-1,0,centralWidget)
        self.tableWidget.setCellWidget(self.rowCount-1,1,dmmVisa)
        self.tableWidget.setCellWidget(self.rowCount-1,2,thermometer)
        self.tableWidget.setCellWidget(self.rowCount-1,3,current)
        self.tableWidget.setCellWidget(self.rowCount-1,4,voltage)
        self.tableWidget.setCellWidget(self.rowCount-1,5,temperature)
            
        a = DiodeThermometer(start, stop, dmmVisa, thermometer,current, voltage, temperature, 
                                   self.yAxisCombo, self.plot, self.rowCount - 1
                                   ,self.errorDisplayTE,self.errorDisplayArray)
        self.objectList.append(a)
    
    def selectRow(self,i):
        self.rowSelected = i
        #print "selected Row: %d" % i
    
    def deleteRow(self):
        
        if self.rowSelected != -1:
            rowIndex = self.tableWidget.currentRow()
        else:
            rowIndex = -1
        #print "delete Row: %d" % rowIndex
        self.objectList[rowIndex].clearData()
        
        if self.tableWidget.rowCount()-1 == rowIndex:
            pass
        elif rowIndex == -1:
            rowIndex = self.tableWidget.rowCount()-1
        elif rowIndex < self.tableWidget.rowCount() - 1:
            for i in range (rowIndex+1, self.tableWidget.rowCount()):
                self.objectList[i].update()
            
        self.rowCount -= 1
        #print rowIndex
        self.tableWidget.removeRow(rowIndex)
        del self.objectList[rowIndex]
        
        self.rowSelected = -1
        
    def closeEvent(self, e):
        s = QSettings()
        s.beginWriteArray('Row', self.tableWidget.rowCount())
#        for i,a in enumerate(self.objectList):
#            s.setArrayIndex(i)
#            a.saveSettings(s)
            
        for i,a in enumerate(self.objectList):
            s.setArrayIndex(i)
            s.setValue('dmmVisaCombo', a.getDmmVisaText())
            s.setValue('currentCombo', a.getCurrentText())
            s.setValue('thermometerCombo', a.getThermoText())
        
        s.endArray()
        for widget in self.settingsWidgets:
            saveWidgetToSettings(s, widget)
        super(mainWindow,self).closeEvent(e)

        
    def restoreSetting(self):
        s = QSettings()
        n = s.beginReadArray('Row')
        for i in range(n)[::1]:
            s.setArrayIndex(i)
            dmmVisaValue = s.value('dmmVisaCombo', "ASRL1::LNSTR", type=str)
            currentValue = s.value('currentCombo', "1", type=str)
            thermoValue = s.value('thermometerCombo', "Magnet stage DT-470", type=str)
            self.addRow(dmmVisaValue, thermoValue, currentValue)
            
        s.endArray()
        for widget in self.settingsWidgets:
            restoreWidgetFromSettings(s, widget)
        
        
if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.WARN)

    from PyQt4.QtGui import QApplication, QIcon
    
    appName = 'Diode Thermometers'
    app = QApplication(sys.argv)
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName(appName)

    import ctypes
    myappid = u'WISCXRAYASTRO.ADR3.DiodeThermometer' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)  

    mw = mainWindow()
    mw.setWindowIcon(QIcon('Icons/DiodeThermomter.ico'))
    mw.setWindowTitle(appName)
    mw.show()
    app.exec_()
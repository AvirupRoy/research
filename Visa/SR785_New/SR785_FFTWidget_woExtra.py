# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 10:25:39 2015

@author: Cole Cook
"""

import SR785_FFTUi

import fileGeneratorDialog

import SR785_GUI

from PyQt4.QtGui import QWidget, QDialog, QVBoxLayout

from PyQt4 import Qt, Qwt5, QtGui, QtCore

from time import strftime

import pyqtgraph

import numpy as np

import os

import visa

class SR785_FFTWidget(QWidget, SR785_FFTUi.Ui_Form):
    A = np.empty([1,])
#    B = np.empty([1,])
    Freq = np.empty([1,])
    deviceNumber = int
    runNumber = str
    sequenceString = str

    def __init__(self, sr785, parent=None):
        QWidget.__init__(self, parent)
        SR785_FFTUi.Ui_Form.__init__(self)
        self.sr785 = sr785
        self.setupUi(self)
        self.dlg = fileGeneratorDialog.fileGenerator(self)

        inputLayout = QVBoxLayout(self.inputPage)
        self.inputA = SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'A')
#        self.inputB = SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'B')
        inputLayout.addWidget(self.inputA)
#        inputLayout.addWidget(self.inputB)

        sourceLayout = QVBoxLayout(self.sourcePage)
        self.sourceGroupBox = SR785_GUI.SR785_SourceGroupBox(self.sr785)
        sourceLayout.addWidget(self.sourceGroupBox)

        # Frequency Menu
        self.sr785.fft.lines.bindToEnumComboBox(self.linesCombo)
        self.linesCombo.currentIndexChanged.connect(self.setForceLengthMax)
        self.sr785.fft.baseFrequency.bindToEnumComboBox(self.baseFrequencyCombo)
        self.baseFrequencyCombo.currentIndexChanged.connect(self.getFrequencySpan)
        self.sr785.fft.centerFrequency.bindToSpinBox(self.centerFrequencySb)
        self.frequencySpanCombo.setToolTip(self.sr785.fft.frequencySpanToolTip())
        self.frequencySpanCombo.currentIndexChanged.connect(self.setFreqSpan)
        self.settlePb.clicked.connect(self.sr785.fft.settleMeasurement)

        # Average Menu
        self.sr785.fft.computeAverage.bindToCheckBox(self.computeAverageCheck)
        self.sr785.fft.averageType.bindToEnumComboBox(self.averageTypeCombo)
        self.sr785.fft.fftAverageType.bindToEnumComboBox(self.fftAverageTypeCombo)
        self.sr785.fft.numberOfAverages.bindToSpinBox(self.numberOfAveragesSb)
        self.sr785.fft.fftTimeRecordIncrement.bindToSpinBox(self.fftTimeRecordIncrementSb)
        self.sr785.fft.overloadReject.bindToEnumComboBox(self.overloadRejectCombo)
        self.sr785.fft.triggerAverageMode.bindToEnumComboBox(self.triggerAverageModeCombo)
        self.averageTypeCombo.currentIndexChanged.connect(self.setTimeRecord)
#        self.computeAverageCheck.setToolTip(self.sr785.fft.computeAverageToolTip())
#        self.sr785.fft.averagePreview.bindToEnumComboBox(self.averagePreviewCombo)

        # Windowing Menu
        self.sr785.fft.windowType.bindToEnumComboBox(self.windowTypeCombo)
        self.windowTypeCombo.currentIndexChanged.connect(self.forceOrExponentialEnable)
        self.forceOrExponentialCombo.currentIndexChanged.connect(self.forceOrExponentialChoice)
        self.sr785.fft.forceOrExponential1.bindToEnumComboBox(self.forceOrExponentialCombo)
        self.sr785.fft.expoWindowTimeConstant.bindToSpinBox(self.expoWindowTimeConstantSb)
        self.expoWindowTimeConstantSb.setEnabled(False)
        self.forceOrExponentialCombo.setEnabled(False)
        self.sr785.fft.forceLength.bindToSpinBox(self.forceLengthSb)

#        self.computeAverageCheck.stateChanged.connect(self.computeAverage)

        self.display1Plot
#        self.display2Plot

        self.startPb.clicked.connect(self.startMeasurement)
        self.pausePb.clicked.connect(self.pauseMeasurement)
        self.sampleInfoPb.clicked.connect(self.sampleInfo)

        self.pathnameLe.setReadOnly(True)
        self.fileNameLe.setReadOnly(True)

        self.startPb.setEnabled(False)
        self.pausePb.setEnabled(False)
#        self.sampleInfoPb.setEnabled(False)
        self.restoreSettings()


        self.ownFilenameCheck.stateChanged.connect(self.filenameNeeded) # One issue is that the file type might not be what we want if people generate their own. Is this a concern?
# Might not need includeSampleInfoCheck box how it is currently setup
#        self.includeSampleInfoCheck.stateChanged.connect(self.sampleInfoNeeded)
# Still need to include the sample information dialog but I think I want to make sure that is works and that it works in the other one before doing that.

        self.fileDialog = QtGui.QFileDialog()
        self.fileDialogPb.setEnabled(False)
        self.fileDialogPb.clicked.connect(self.fileInfo)

    def computeAverage(self):
        if self.computeAverageCheck.isChecked():
            self.sr785.fft.setComputeAverage(1)
        else:
            self.sr785.fft.setComputeAverage(0)

    def isComputeAverage(self, onOff):
        if onOff == '0':
            self.computeAverageCheck.setCheckState(False)
        else:
            self.computeAverageCheck.setCheckState(True)

    def saveSettings(self):
        s = QtCore.QSettings()

        # File location info
        s.setValue('pathname', self.pathnameLe.text())
        s.setValue('filename', self.fileNameLe.text())

        # Need to add in the run number, sequence and other stuff
        # Dialog
        self.dlg.saveSettings(s)
        # Don't think I need the stuff below now
        data = self.dlg.data()
        s.setValue('device id', data['device id'])
        s.setValue('item description', data['item description'])
        s.setValue('item id', data['item id'])
        s.setValue('secondary id', data['secondary id'])
        s.setValue('device length', data['device length'])
        s.setValue('device width', data['device width'])
        s.setValue('device thickness', data['device thickness'])
        s.setValue('load resistor', data['load resistor'])
        s.setValue('fet dc gain', data['fet dc gain'])
        s.setValue('ac gain', data['ac gain'])
        s.setValue('internal divider ratio', data['internal divider ratio'])
        s.setValue('bias current', data['bias current'])
        s.setValue('bias voltage', data['bias voltage'])
        s.setValue('source x position', data['source x position'])
        s.setValue('source y position', data['source y position'])
        s.setValue('external gain', data['external gain'])
        s.setValue('cold plate temperature', data['cold plate temperature'])
        s.setValue('run number', self.runNumber)
        s.setValue('sequence', self.sequenceString)
        s.setValue('device number', self.deviceNumber)


    def restoreSettings(self):
        s = QtCore.QSettings()
#        self.pathnameLe.setPlaceholderText(s.value('pathName', '', type=QtCore.QString))
#        self.deviceNumber = s.value('device number').toInt()[0]
#        self.runNumber = s.value('run number', '', type=QtCore.QString)
#        self.sequenceString = s.value('sequence', '', type=QtCore.QString)
#        while len(self.sequenceString) < 4:
#            self.sequenceString = '0%s' %self.sequenceString
#        # Is swp the correct file extension? Or do we want the one for transfer functions?
#        self.fileNameLe.setPlaceholderText('%s%s%s.swp' %(s.value('device number', '', type=QtCore.QString),s.value('run number','',type=QtCore.QString),self.sequenceString))
#
## Dialog Information
## Should I use setText or setPlaceholderText fot line edits?
#        self.dlg.pathnameLe.setText(self.pathnameLe.text())
#        self.dlg.pathnameLe.setText(s.value('pathName', '', type=QtCore.QString))
#        self.dlg.filenameLe.setText(self.fileNameLe.text())
#        self.dlg.filenameLe.setText('%s%s%s.swp'  %(s.value('device number', '', type=QtCore.QString),s.value('run number','',type=QtCore.QString),self.sequenceString))
#        self.dlg.deviceNumberSb.setValue(s.value('device number').toInt()[0])
#        self.dlg.deviceIDLe.setText(s.value('device id','',type=QtCore.QString))
#        self.dlg.itemDescriptionLe.setText(s.value('item description','',type=QtCore.QString))
#        self.dlg.twoCharItemIDLe.setText(s.value('item id','',type=QtCore.QString))
#        self.dlg.secondaryIDLe.setText(s.value('secondary id','',type=QtCore.QString))
#        self.dlg.deviceLengthSb.setValue(s.value('device length').toFloat()[0])
#        self.dlg.deviceWidthSb.setValue(s.value('device width').toFloat()[0])
#        self.dlg.deviceThicknessSb.setValue(s.value('device thickness').toFloat()[0])
#        self.dlg.runNumberLe.setText(s.value('run number', '', type=QtCore.QString))
#        self.dlg.sequenceNumberSb.setValue(s.value('sequence number').toInt()[0])
#        self.dlg.loadResistorSb.setValue(s.value('load resistor').toInt()[0])
#        self.dlg.fetDCGainSb.setValue(s.value('fet dc gain').toInt()[0])
#        self.dlg.acGainSb.setValue(s.value('ac gain').toInt()[0])
#        self.dlg.internalDividerRatioSb.setValue(s.value('internal divider ratio').toFloat()[0])
#        self.dlg.biasCurrentSb.setValue(s.value('bias current').toFloat()[0])
#        self.dlg.biasVoltageSb.setValue(s.value('bias voltage').toFloat()[0])
#        self.dlg.sourceXPositionSb.setValue(s.value('source x position').toInt()[0])
#        self.dlg.sourceYPositionSb.setValue(s.value('source y position').toInt()[0])
#        self.dlg.externalGainSb.setValue(s.value('external gain').toFloat()[0])
#        self.dlg.coldPlateTemperatureSb.setValue(s.value('cold plate temperature').toFloat()[0])
# Might want to change the readAll function call here
        self.sr785.clearGarbage()
        print "STYP:", self.sr785.queryString('STYP?')
#        self.sr785.readAll()
        self.sr785.fft.readAll()
#        self.dlg.restoreSettings(s)

        self.inputA.restoreSettings(0)
#        self.inputB.restoreSettings(1)
        self.sourceGroupBox.restoreSettings()

        self.frequencySpanCombo.addItems(self.sr785.fft.availableFrequencySpans(self.baseFrequencyCombo.currentText()))
        self.frequencySpanCombo.setCurrentIndex(self.frequencySpanCombo.findText('%f Hz' %self.sr785.fft.frequencySpan()))
#        self.isComputeAverage(self.sr785.fft.isComputeAverage())

    def setTimeRecord(self):
        if self.averageTypeCombo.currentText() == "vector":
            self.fftTimeRecordIncrementSb.setValue(100)

    def setForceLengthMax(self):
        self.forceLengthSb.setMaximum(int(self.linesCombo.currentText()))

    def getFrequencySpan(self):
        self.frequencySpanCombo.clear()
        self.frequencySpanCombo.addItems(self.sr785.fft.availableFrequencySpans(self.baseFrequencyCombo.currentText()))

    def setFreqSpan(self):
        freqSpan = self.frequencySpanCombo.currentText()[:-3]
        self.sr785.fft.setFrequencySpan(freqSpan)
        # Doesn't want to convert the string freqSpan to a float...
#        self.centerFrequencySb.setMinimum(float(freqSpan)/2)

    def filenameNeeded(self):
        if self.ownFilenameCheck.isChecked():
            self.fileDialogPb.setEnabled(True)
            self.sampleInfoPb.setEnabled(False)
        else:
            self.fileDialogPb.setEnabled(False)
            self.sampleInfoPb.setEnabled(True)

    def fileInfo(self):
        # How would I do the commented out code below?
#        if self.ownFilenameCheck.isChecked():
#            dont have a placeholdername for filename
#        else:
#            put a placeholdername for filename
        filename = self.fileDialog.getSaveFileName(self, 'Save File as', '', filter="Data File (*.dat)")
#        filename = self.fileDialog.getSaveFileName(self,'Save File as', '%s' %self.pathnameLe.text(), filter="Data File (*.dat)")
        print 'File name', filename
        fileInfo = QtCore.QFileInfo(filename)

        self.pathnameLe.setText(fileInfo.absolutePath())
        self.fileNameLe.setText(fileInfo.fileName())
        print 'Pathname', self.pathnameLe.text()
        print 'Filename', self.fileNameLe.text()
        self.pathnameLe.setReadOnly(True)
        self.fileNameLe.setReadOnly(True)
        self.startPb.setEnabled(True)

    def sampleInfo(self):
        self.restoreSettings()
        result  = self.dlg.exec_()
        if result == QDialog.Accepted:
            data = self.dlg.data()
            print 'Device Number', self.deviceNumber
            print 'Run Number', self.runNumber
            print 'Run Number Line Edit', data['run number']
            print 'Sequence', self.sequenceString

# Using the line edits and boxes
            if self.deviceNumber == data['device number']:
                if self.runNumber == data['run number']:
                    self.sequenceString = str(data['sequence number'])
                    while len(self.sequenceString) < 4:
                        self.sequenceString = '0%s' %self.sequenceString
                else:
                    self.runNumber = data['run number']
                    self.sequenceString = '0001'
                self.deviceNumber == data['device number']
            else:
                self.deviceNumber = data['device number']
                self.runNumber = data['run number']
                self.sequenceString = '0001'

            print 'Device Number', self.deviceNumber
            print 'Run Number', self.runNumber
            print 'Sequence', self.sequenceString
            self.pathnameLe.setText('%s' %data['path name'])
            # Need to change file extension to whatever it should be for fft stuff
            self.fileNameLe.setText('%d%s%s.swp' %(self.deviceNumber,self.runNumber,self.sequenceString))

            print data['device number']

#            os.chdir("%s" %self.pathnameLe.text())
#            dataFile = open("%s" %self.fileNameLe.text(),"a")
            dataFile = open("%s/%s" %(self.pathnameLe.text(),self.fileNameLe.text()),"a")
            dataFile.write("%s\%s\n" %(self.pathnameLe.text(),self.fileNameLe.text()))
            dataFile.write("Date and Time of Measurement: %s\n" %strftime("%Y-%m-%d %H:%M:%S") )
            dataFile.write("Device Information\n")
            dataFile.write("Device number: %d\n" %data['device number'])
            dataFile.write("Device ID: %s\n" %data['device id'])
            dataFile.write("Item Description: %s\n" %data['item description'])
            dataFile.write("Item ID (2 chars): %s\n" %data['item id'])
            dataFile.write("Secondary Id (8 chars): %s\n" %data['secondary id'])
            dataFile.write("Device Length: %f\n" %data['device length'])
            dataFile.write("Device Width: %f\n" %data['device width'])
            dataFile.write("Device Thickness: %f\n\n" %data['device thickness'])
        # Channel Information
            dataFile.write("Channel Information\n")
            dataFile.write("Load Resistor: %d\n" %data['load resistor'])
            dataFile.write("FET DC Gain: %d\n" %data['fet dc gain'])
            dataFile.write("AC Gain: %d\n" %data['ac gain'])
            dataFile.write("Internal Divider Ratio: %f\n\n" %data['internal divider ratio'])
        # General Operating Conditions
            dataFile.write("General Operating Conditions\n")
            dataFile.write("Bias Current: %f\n" %data['bias current'])
            dataFile.write("Bias Voltage: %f\n" %data['bias voltage'])
            dataFile.write("Source X Position: %d\n" %data['source x position'])
            dataFile.write("Source Y Position: %d\n" %data['source y position'])
            dataFile.write("External Gain: %f\n" %data['external gain'])
            dataFile.write("Cold Plate Temperature (GeA): %f\n\n" %data['cold plate temperature'])
            dataFile.write("Program Specific Parameters\n")
            ## Seems these parameters aren't the ones of interest for the sine sweep...
            dataFile.write("Settle Time: %f\n" %self.settleTimeSb.value())
            dataFile.write("Settle Cycles: %f\n" %self.settleCycleSb.value())
            dataFile.write("Integration Time: %f\n" %self.integrationTimeSb.value())
            dataFile.write("Integration Cycles: %f\n" %self.integrationCyclesSb.value())
            ## According to the Standard_Header.doc these are the parameters of interest, note these are unknown parameters at this point
            dataFile.write("Source Position: \n")
            dataFile.write("Sample Time: \n")
            dataFile.write("Number of Pulses: \n")
            dataFile.write("Bits/Pulse: \n")
            dataFile.write("DET Voltage: \n")
            dataFile.write("External Divider Ratio: \n\n")
        self.startPb.setEnabled(True)
        self.saveSettings() # I don't remember why I put this here but I did for some reason

    def forceOrExponentialChoice(self):
        if self.forceOrExponentialCombo.currentText() == 'force window':
            self.sr785.commandString('W1FE 0')
            self.sr785.commandString('W2FE 0')
            self.expoWindowTimeConstantSb.setEnabled(False)
        else:
            self.sr785.commandString('W1FE 1')
            self.sr785.commandString('W2FE 1')
            self.expoWindowTimeConstantSb.setEnabled(True)

    def forceOrExponentialEnable(self):
        if self.windowTypeCombo.currentText() == 'force/exponential':
            self.forceOrExponentialCombo.setEnabled(True)
        else:
            self.forceOrExponentialCombo.setEnabled(False)
            self.expoWindowTimeConstantSb.setEnabled(False)

    def startMeasurement(self):
        self.enableSomeParameters(False)
        self.sr785.startMeasurement()
        # The if statement below is needed because if the sample information is included, then the filename and data is already written
        if self.ownFilenameCheck.isChecked():
#            os.chdir("%s" %self.pathnameLe.text())
#            dataFile = open("%s" %self.fileNameLe.text(),"a")
            dataFile = open("%s/%s" %(self.pathnameLe.text(),self.fileNameLe.text()),"a")
            # The next two lines didn't execute...
            dataFile.write("%s\%s\n" %(self.pathnameLe.text(),self.fileNameLe.text()))
            dataFile.write("Date and Time of Measurement: %s\n" %strftime("%Y-%m-%d %H:%M:%S") )
            dataFile.close()
        self.initPlots()
        self.checkMeasurementStatus()

# Might want to go ahead and add the other things that are enabled/disabled in the start measurement function
    def enableSomeParameters(self, enable):
        self.startPb.setEnabled(enable)
        self.pausePb.setEnabled(not enable)

    def initPlots(self):
        # One issue is that sometimes we get negative numbers which then give a warning when we try to convert to a log scale
        # X axis labels
        self.display1Plot.setLabel('bottom', text='Frequency', units='Hz')
#        self.display2Plot.setLabel('bottom', text='Hz')
        # Y axis labels
        self.display1Plot.setLabel('left',text='Magnitude')
#        self.display1Plot.setLabel('left',text='%s' %self.sr785.queryString('UNIT ? 0'))
#        self.display2Plot.setLabel('left',text='%s' %self.sr785.queryString('UNIT ? 1'))
#        self.display1Plot.setLogMode(x=True,y=True)
#        self.display2Plot.setLogMode(x=True,y=True)
        self.display1Plot.showGrid(x=True,y=True)
#        self.display2Plot.showGrid(x=True,y=True)
        self.curve1 = self.display1Plot.plot([],[], pen='r', name='Magnitude')
#        self.curve2 = self.display2Plot.plot([],[], pen='b', name='Phase')
        # Should it be log-log for the phase plot as well?

    def checkMeasurementStatus(self):
        self.sr785.commandString('*CLS') # Clearing status words so that it doesn't automatically start reading data because when a new measurement starts, it doesn't auto clear the registry
        status = self.sr785.queryInteger('DSPS?')
        while not bool(status & 2**0) and not bool(status & 2**8): ## the user manual says that we shouldn't be checking both status words together because display A and display B are not likely to update at the same time
            status = self.sr785.queryInteger('DSPS?')
        nrOfPoints = self.sr785.queryInteger('DSPN? 0')
        self.setArraySize(nrOfPoints)

    def setArraySize(self, nrOfPoints):
        self.Freq = np.empty([nrOfPoints,])
        self.A = np.empty([nrOfPoints,])
#        self.B = np.empty([nrOfPoints,])
        self.collectData(nrOfPoints)

    def collectData(self,nrOfPoints):
#        os.chdir("%s" %self.pathnameLe.text())
#        dataFile = open("%s" %self.fileNameLe.text(),"a")
        dataFile = open("%s/%s" %(self.pathnameLe.text(),self.fileNameLe.text()),"a")
#        dataFile.write("Frequency (Hz)\tMagnitude\tPhase\n")
        dataFile.write("Frequency (Hz)\tMagnitude\n")
        self.A = self.sr785.display.retrieveData(0)
#        self.B = self.sr785.display.retrieveData(1)
        binNumber = 0
        while binNumber <= nrOfPoints-1:
            self.Freq[binNumber] = self.sr785.queryFloat('DBIN? 0, %d' %binNumber)
#            dataFile.write("%f\t%g\t%g\n" %(self.Freq[binNumber], self.A[binNumber], self.B[binNumber]))
            dataFile.write("%f\t%g\n" %(self.Freq[binNumber], self.A[binNumber]))
            binNumber +=1
        dataFile.close()
        self.updatePlots()

    def updatePlots(self):
        self.curve1.setData(self.Freq, self.A)
#        self.curve2.setData(self.Freq, self.B)
        self.enableSomeParameters(True)

    def pauseMeasurement(self):
        self.startPb.setText('Restart Measurement')
        if self.pausePb.text() == 'Pause Measurement':
            self.sr785.pauseMeasurement()
            self.pausePb.setText('Continue Measurement')
        elif self.pausePb.text() == 'Continue Measurement':
            self.sr785.continueMeasurement()
            self.pausePb.setText('Pause Measurement')

    def closeEvent(self, event):
        self.saveSettings()
        QWidget.closeEvent(self,event)

if __name__ == '__main__':
    import sys
    from SR785 import SR785
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('SR785 FFT')

    visaAddress = 'GPIB1::10'
    sr785 = SR785(visaAddress)
#    sr785 = SR785(None)
    sr785.debug = True
    #sr785.Instrument.delay = 0.01


# Setting the measurement to fft
    sr785.commandString('MGRP 2, 0')
# Setting the measurement type to FFT1, so a FFT from channel 1 only, for both displays. See page 437 of the pdf of the User Manual for more measurement types
    sr785.commandString('MEAS 0, 0')
    sr785.commandString('MEAS 1, 0')
# Setting the measurement type to frequency response for both displays
#    sr785.commandString('MEAS 0, 11')
#    sr785.commandString('MEAS 1, 11')
# Setting the displays to the real and imaginary part of the frequency response
    sr785.commandString('VIEW 0, 1')
    sr785.commandString('VIEW 1, 5')
    #import time
    #time.sleep(2)

    mainWindow = SR785_FFTWidget(sr785)
    mainWindow.show()

    sys.exit(app.exec_())

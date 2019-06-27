# -*- coding: utf-8 -*-
"""
Created on Mon Oct 19 11:13:30 2015

@author: Cole Cook
"""
# Might want to check that the output is what I actually want to be given...
# To delete something that is in the dictionary that is an ndarray, can use np.delete(arrayName, indicesToBeDeleted)
# Now go through this and get rid of the commented out stuff and make sure that logically it all should work.
# Then test it!
import SR785_FFTLogUi

import fileGeneratorDialog

import SR785_GUI

from PyQt4.QtGui import QWidget, QDialog, QVBoxLayout

from PyQt4 import Qt, Qwt5, QtGui, QtCore

from time import strftime

import pyqtgraph

import numpy as np

import os

import visa

class SR785_FFTWidget(QWidget, SR785_FFTLogUi.Ui_Form):
    # Should create numpy arrays with length zero
    Magnitude = np.array([])
    Phase = np.array([])
    Frequency = np.array([])
    SpanResolutions = np.array([])
    spansAndLines = []
    dataDictionary = {}
    deviceNumber = int
    runNumber = str
    sequenceString = str

    def __init__(self, sr785, parent=None):
        QWidget.__init__(self, parent)
        SR785_FFTLogUi.Ui_Form.__init__(self)
        self.sr785 = sr785
        self.setupUi(self)
        self.dlg = fileGeneratorDialog.fileGenerator(self)

        inputLayout = QVBoxLayout(self.inputPage)
        self.inputChannelGbA = SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'A')
        inputLayout.addWidget(self.inputChannelGbA)
        #inputLayout.addWidget(SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'A'))
        self.inputChannelGbB = SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'B')
        inputLayout.addWidget(self.inputChannelGbB)
#        inputLayout.addWidget(SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'B'))

        sourceLayout = QVBoxLayout(self.sourcePage)
        self.sourceGb = SR785_GUI.SR785_SourceGroupBox(self.sr785)
        sourceLayout.addWidget(self.sourceGb)
#        sourceLayout.addWidget(SR785_GUI.SR785_SourceGroupBox(self.sr785))

        # Frequency Menu
#        self.sr785.fft.lines.bindToEnumComboBox(self.linesCombo)
#        self.linesCombo.currentIndexChanged.connect(self.setForceLengthMax)
        self.sr785.fft.baseFrequency.bindToEnumComboBox(self.baseFrequencyCombo)
#        self.baseFrequencyCombo.currentIndexChanged.connect(self.getFrequencySpan)
#        self.sr785.fft.centerFrequency.bindToSpinBox(self.centerFrequencySb)
#        self.frequencySpanCombo.setToolTip(self.sr785.fft.frequencySpanToolTip())
#        self.frequencySpanCombo.currentIndexChanged.connect(self.setFreqSpan)
#        self.sr785.fft.startFrequency.bindToSpinBox(self.startFrequencySb)
#        self.sr785.fft.endFrequency.bindToSpinBox(self.endFrequencySb)
        # Don't want the start and end frequencies to be bound to the instrument commands because these aren't the actual frequencies we want to use
        self.startFrequencySb
        self.startFrequencySb.setToolTip('The start frequency for the log averaged span.')
        self.endFrequencySb
        self.endFrequencySb.setToolTip('The end frequency for the log averaged span.')
        self.settlePb.clicked.connect(self.sr785.fft.settleMeasurement)
# Might want to save these two settings given that they won't auto update
        self.maxDesiredResolutionSb
        self.numberOfPointsLogSb
        self.numberOfPointsLogSb

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
        self.display2Plot

        self.startPb.clicked.connect(self.startMeasurement)
        self.pausePb.clicked.connect(self.pauseMeasurement)
        self.sampleInfoPb.clicked.connect(self.sampleInfo)

#        self.pathnameLe.setReadOnly(True)
#        self.fileNameLe.setReadOnly(True)

#        self.startPb.setEnabled(False)
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

    def saveSettings(self):
        s = QtCore.QSettings()

        # File location info
        s.setValue('pathname', self.pathnameLe.text())
        s.setValue('filename', self.fileNameLe.text())

        s.setValue('number of points', self.numberOfPointsLogSb.value())
        s.setValue('max desired resolution', self.maxDesiredResolutionSb.value())
        s.setValue('start frequency', self.startFrequencySb.value())
        s.setValue('end frequency', self.endFrequencySb.value())


        # Need to add in the run number, sequence and other stuff
        # Dialog
        self.dlg.saveSettings(s)
        # Don't think I need the stuff below now
#        data = self.dlg.data()
#        s.setValue('device id', data['device id'])
#        s.setValue('item description', data['item description'])
#        s.setValue('item id', data['item id'])
#        s.setValue('secondary id', data['secondary id'])
#        s.setValue('device length', data['device length'])
#        s.setValue('device width', data['device width'])
#        s.setValue('device thickness', data['device thickness'])
#        s.setValue('load resistor', data['load resistor'])
#        s.setValue('fet dc gain', data['fet dc gain'])
#        s.setValue('ac gain', data['ac gain'])
#        s.setValue('internal divider ratio', data['internal divider ratio'])
#        s.setValue('bias current', data['bias current'])
#        s.setValue('bias voltage', data['bias voltage'])
#        s.setValue('source x position', data['source x position'])
#        s.setValue('source y position', data['source y position'])
#        s.setValue('external gain', data['external gain'])
#        s.setValue('cold plate temperature', data['cold plate temperature'])
#        s.setValue('run number', self.runNumber)
#        s.setValue('sequence', self.sequenceString)
#        s.setValue('device number', self.deviceNumber)


    def restoreSettings(self):
        s = QtCore.QSettings()
        self.pathnameLe.setPlaceholderText(s.value('pathname', '', type=QtCore.QString))
        self.deviceNumber = s.value('device number').toInt()[0]
        self.runNumber = s.value('run number', '', type=QtCore.QString)
        self.sequenceString = s.value('sequence', '', type=QtCore.QString)
        while len(self.sequenceString) < 4:
            self.sequenceString = '0%s' %self.sequenceString
#        # Is swp the correct file extension? Or do we want the one for transfer functions?
        self.fileNameLe.setPlaceholderText('%s%s%s.swp' %(s.value('device number', '', type=QtCore.QString),s.value('run number','',type=QtCore.QString),self.sequenceString))

        self.numberOfPointsLogSb.setValue(s.value('number of points').toInt()[0])
        self.maxDesiredResolutionSb.setValue(s.value('max desired resolution').toFloat()[0])
        self.startFrequencySb.setValue(s.value('start frequency').toFloat()[0])
        self.endFrequencySb.setValue(s.value('end frequency').toFloat()[0])
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
#        self.sr785.readAll()
        self.sr785.fft.readAll()
        self.dlg.restoreSettings(s)
        self.inputChannelGbA.restoreSettings(0)
        self.inputChannelGbB.restoreSettings(1)
        self.sourceGb.restoreSettings()

#        SR785_GUI.SR785_InputChannelGroupBox('B').restoreSettings(1)
#        SR785_GUI.SR785_SourceGroupBox.restoreSettings()

#        self.frequencySpanCombo.addItems(self.sr785.fft.availableFrequencySpans(self.baseFrequencyCombo.currentText()))
#        self.frequencySpanCombo.setCurrentIndex(self.frequencySpanCombo.findText('%f Hz' %self.sr785.fft.frequencySpan()))

    def setTimeRecord(self):
        if self.averageTypeCombo.currentText() == "vector":
            self.fftTimeRecordIncrementSb.setValue(100)

    def setForceLengthMax(self):
        self.forceLengthSb.setMaximum(int(self.linesCombo.currentText()))

    def filenameNeeded(self):
        if self.ownFilenameCheck.isChecked():
            self.fileDialogPb.setEnabled(True)
            self.sampleInfoPb.setEnabled(False)
        else:
            self.fileDialogPb.setEnabled(False)
            self.sampleInfoPb.setEnabled(True)

    def fileInfo(self):
        filename = self.fileDialog.getSaveFileName(self,'Save File as', self.pathnameLe.text(), filter="Data File (*.dat)")
        print 'File name', filename
        fileInfo = QtCore.QFileInfo(filename)

        self.pathnameLe.setText(fileInfo.canonicalPath())
        self.fileNameLe.setText(fileInfo.completeBaseName())
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
#######            # Need to change file extension to whatever it should be for fft stuff
            self.fileNameLe.setText('%d%s%s.swp' %(self.deviceNumber,self.runNumber,self.sequenceString))

            print data['device number']

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
#            dataFile.write("Settle Time: %f\n" %self.settleTimeSb.value())
#            dataFile.write("Settle Cycles: %f\n" %self.settleCycleSb.value())
#            dataFile.write("Integration Time: %f\n" %self.integrationTimeSb.value())
#            dataFile.write("Integration Cycles: %f\n" %self.integrationCyclesSb.value())
            ## According to the Standard_Header.doc these are the parameters of interest, note these are unknown parameters at this point
            dataFile.write("Source Position: \n")
            dataFile.write("Sample Time: \n")
            dataFile.write("Number of Pulses: \n")
            dataFile.write("Bits/Pulse: \n")
            dataFile.write("DET Voltage: \n")
            dataFile.write("External Divider Ratio: \n\n")
            dataFile.close()
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
        self.sr785.commandString('FSTR 2, 0') # Need to force the starting frequency to be zero
        self.enableSomeParameters(False)
        self.computeSpans()
#        self.sr785.startMeasurement()
        # The if statement below is needed because if the sample information is included, then the filename and data is already written
        if self.ownFilenameCheck.isChecked():
#            os.chdir("%s" %self.pathnameLe.text())
#            dataFile = open("%s" %self.fileNameLe.text(),"a")
            dataFile = open("%s/%s" %(self.pathnameLe.text(),self.fileNameLe.text()),"a")
            # The next two lines didn't execute...
            dataFile.write("%s\%s\n" %(self.pathnameLe.text(),self.fileNameLe.text()))
            dataFile.write("Date and Time of Measurement: %s\n" %strftime("%Y-%m-%d %H:%M:%S") )
            dataFile.close()
#        self.initPlots()
#        self.checkMeasurementStatus()

    def computeSpans(self):
        possibleSpans = []
        print 'Base Frequency', self.baseFrequencyCombo.currentText()
        if self.baseFrequencyCombo.currentText() == '100.0 kHz':
            print 'Hello'
            possibleSpans = [x for x in 100E3*np.logspace(-19,0,20,base=2)]
        elif self.baseFrequencyCombo.currentText() ==  '102.4 kHz':
            print 'Goodbye'
            possibleSpans = [x for x in 102.4E3*np.logspace(-19,0,20,base=2)]

        print 'Possible Spans', possibleSpans

        possibleFFTLines = [100,200,400,800] # Don't think this is needed
        startFrequency = self.startFrequencySb.value()
        endFrequency = self.endFrequencySb.value()
        numberOfPoints = self.numberOfPointsLogSb.value()
        maxDesiredResolution = self.maxDesiredResolutionSb.value()

        i = len(possibleSpans)-1
        print 'Index', i
        while(endFrequency <= possibleSpans[i]):
            print 'Possible Span', possibleSpans[i]
            i -= 1
            print 'Index', i
        maxSpan = possibleSpans[i]
        maxIndex = i

        i = 0
        while(startFrequency >= possibleSpans[i]):
            i += 1
        minSpan = possibleSpans[i]
        minIndex = i

        base = np.log10(endFrequency/startFrequency)/(numberOfPoints-1)

# Getting things ready for the while loop to find the first span to run
        i = maxIndex+1
        currentSpan = possibleSpans[i]
        spanResolution = currentSpan/100

        while((spanResolution > maxDesiredResolution) and (currentSpan >= minSpan)):
            j = 100
            spanResolution = currentSpan/j
            while((spanResolution > maxDesiredResolution) and (j != 800)):
                spanResolution = currentSpan/j
                j *= 2
            i -= 1
            currentSpan = possibleSpans[i]
            spanResolution = currentSpan/j
        firstSpanIndex = i # Don't think I need this either
        self.spansAndLines.append((currentSpan, j))

# Looking to see if we need another span and if so computing those values
        if endFrequency > self.spansAndLines[0][0]:
            print 'Current Span', currentSpan
            while((currentSpan <= endFrequency) and (currentSpan != possibleSpans[19])):
                i = maxIndex+1
                print 'Index i', i
                currentSpan = possibleSpans[i]
                print 'Current Span', currentSpan
                j = 100
                LineW = currentSpan/j
                something = (10**(np.floor((1/base)*(np.log10(LineW/startFrequency)-np.log10(10**(base/2)-10**(0-base/2))))*base))*startFrequency
                while((currentSpan != self.spansAndLines[len(self.spansAndLines)-1][0]) and (something >= self.spansAndLines[len(self.spansAndLines)-1][0])):
                    currentSpan = possibleSpans[i]
                    j = 100
                    print 'Index j', j
                    LineW = currentSpan/j
                    something = (10**(np.floor((1/base)*(np.log10(LineW/startFrequency)-np.log10(10**(base/2)-10**(0-base/2))))*base))*startFrequency
                    while((something >= self.spansAndLines[len(self.spansAndLines)-1][0]) and (j != 800)):
                        j *= 2
                        print 'Index j', j
                        LineW = currentSpan/j
                        something = (10**(np.floor((1/base)*(np.log10(LineW/startFrequency)-np.log10(10**(base/2)-10**(0-base/2))))*base))*startFrequency
                    i -= 1
                    print 'Index i', i
                    currentSpan = possibleSpans[i]
                    print 'Current Span', currentSpan
                    LineW = currentSpan/j
                    something = (10**(np.floor((1/base)*(np.log10(LineW/startFrequency)-np.log10(10**(base/2)-10**(0-base/2))))*base))*startFrequency
                self.spansAndLines.append((currentSpan, j))

        self.multipleRuns()

    def multipleRuns(self):
        print 'Spans and Lines', self.spansAndLines
        for i in range(len(self.spansAndLines)):
            self.sr785.fft.setFrequencySpan('%f Hz' %self.spansAndLines[i][0])
            if self.spansAndLines[i][1] == 100:
                self.sr785.commandString('FLIN 2, 0')
            elif self.spansAndLines[i][1] == 200:
                self.sr785.commandString('FLIN 2, 1')
            elif self.spansAndLines[i][1] == 400:
                self.sr785.commandString('FLIN 2, 2')
            elif self.spansAndLines[i][1] == 800:
                self.sr785.commandString('FLIN 2, 3')
        #Might want to implement an exception here
#            self.sr785.commandString('FLIN 2, %d' %self.spansAndLines[i][1])
            self.sr785.startMeasurement()
            self.initPlot1(i) # This might only be needed once I guess it depends on if we want to actually see all the data at once or not
            self.checkMeasurementStatus(i)

        self.initPlot2()
        self.combineData()
#        self.deleteExtraData()
        self.calculateAverage() # This should take all of the data and compute an average.
        self.enableSomeParameters(True)


    def enableSomeParameters(self, enable):
        self.startPb.setEnabled(enable)
        self.pausePb.setEnabled(not enable)

    def initPlot1(self, i):
        # One issue is that sometimes we get negative numbers which then give a warning when we try to convert to a log scale
        # First clear the plots so that new data can be plotted nicely
        self.display1Plot.clear()
#        self.display2Plot.clear()
        # X axis labels
        self.display1Plot.setLabel('bottom', text='Hz')
#        self.display2Plot.setLabel('bottom', text='Hz')
        # Y axis labels
#        self.display1Plot.setLabel('left',text='%s' %self.sr785.queryString('UNIT ? 0'))
#        self.display2Plot.setLabel('left',text='%s' %self.sr785.queryString('UNIT ? 1'))
#        self.display1Plot.setLogMode(x=True,y=True)
#        self.display2Plot.setLogMode(x=True,y=True)
        self.display1Plot.showGrid(x=True,y=True)
#        self.display2Plot.showGrid(x=True,y=True)
        self.curve1 = self.display1Plot.plot([],[], pen=(i,3), name='Magnitude')
#        self.curve2 = self.display2Plot.plot([],[], pen='r', name='Magnitude')
        # Should it be log-log for the phase plot as well?

    def initPlot2(self):
        # This function is to initialize the second plot which is used for plotting the averaged values in log spaced frequencies
        self.display2Plot.setLabel('bottom', text='Hz')
        self.display2Plot.showGrid(x=True,y=True)
        self.curve2 = self.display2Plot.plot([],[], pen='r', name='Magnitude')


    def checkMeasurementStatus(self, i):
        # This function asks the SR785 if there is new data to display. If so, it stops and then gives the number of points that were obtained by this measurement.
        self.sr785.commandString('*CLS') # Clearing status words so that it doesn't automatically start reading data because when a new measurement starts, it doesn't auto clear the registry
        status = self.sr785.queryInteger('DSPS?')
        while not bool(status & 2**0) and not bool(status & 2**8): ## Not sure I understand this... What does the & do? Also, the user manual says that we shouldn't be checking both status words together because display A and display B are not likely to update at the same time
            status = self.sr785.queryInteger('DSPS?')
#            QtCore.QTimer.start(200) # Might want to put this back in just so we dont' overwhelm the instrument
        nrOfPoints = self.sr785.queryInteger('DSPN? 0')
        print 'Number of Points', nrOfPoints
        self.setArraySize(nrOfPoints, i)

# Might not actually need this function...
    def setArraySize(self, nrOfPoints, i):
        # Setting the size of the arrays to be used for data collection
        # Using only one scan
#        self.dataDictionary['span %d frequencies' %i] = np.empty([nrOfPoints,])
        self.dataDictionary['span %d frequencies' %i] = np.linspace(0, self.spansAndLines[i][0],nrOfPoints)
        self.dataDictionary['span %d magnitudes' %i] = np.empty([nrOfPoints,])
        self.dataDictionary['span %d resolution' %i] = np.empty([nrOfPoints,])
        self.collectDataSingleSpan(nrOfPoints, i)

    def collectDataSingleSpan(self, nrOfPoints, i):
        # This function is used to collect the magnitudes for a single span and then prints these values allow with the corresponding frequencies and resolutions for each data point.
        # Note that the resolution is the same for each span so it would in theory be possible and probably practical to only print the resolution once.
        dataFile = open("%s/%s" %(self.pathnameLe.text(),self.fileNameLe.text()),"a") # @todo: Use portable, correct code to figure out full file path
        dataFile.write("Frequency (Hz)\tMagnitude\tResolution\n")
        self.dataDictionary['span %d magnitudes' %i] = self.sr785.display.retrieveData(0)
        for j in range(nrOfPoints):
            self.dataDictionary['span %d resolution' %i][j] = self.spansAndLines[i][0]/self.spansAndLines[i][1]
            dataFile.write('%f\t%g\t%f\n' %(self.dataDictionary['span %d frequencies' %i][j], self.dataDictionary['span %d magnitudes' %i][j], self.spansAndLines[i][0]/self.spansAndLines[i][1]))
            #            dataFile.write("%f\t%g\t%g\n" %(self.Freq[binNumber], self.A[binNumber], self.B[binNumber]))
        dataFile.close()
        self.updatePlotsSingleSpan(i)
        if i != 0:
            self.deleteData(i)
        else:
            self.dataDictionary['span 0 frequencies in average'] = self.dataDictionary['span 0 frequencies']
            self.dataDictionary['span 0 magnitudes in average'] = self.dataDictionary['span 0 magnitudes']
            self.dataDictionary['span 0 resolution in average'] = self.dataDictionary['span 0 resolution']

    def updatePlotsSingleSpan(self, i):
        # This function updates the single span plot when new data is available.
        print 'Spans and Lines', self.spansAndLines
        freq = np.asarray(self.dataDictionary['span %d frequencies' %i])
        magn = np.asarray(self.dataDictionary['span %d magnitudes' %i])
        self.curve1.setData(freq, magn)
#        self.curve1.setData(self.dataDictionary['span %d frequencies' %i], self.dataDictionary['span %d magnitudes' %i])

    def pauseMeasurement(self):
        # This function changes the text on the start and pause buttons
        self.startPb.setText('Restart Measurement')
        if self.pausePb.text() == 'Pause Measurement':
            self.sr785.pauseMeasurement()
            self.pausePb.setText('Continue Measurement')
        elif self.pausePb.text() == 'Continue Measurement':
            self.sr785.continueMeasurement()
            self.pausePb.setText('Pause Measurement')

    def deleteData(self, i):
        # This function deletes the overlapping data between the current span and the previous span.
        # All spans start at zero so the data being deleted is from zero to the end of the previous span.
        j = 0 # Thing to increment which indices to delete
        deleteIndices = []
# Want to delete the overlapping data so the data for which the frequency is less than or equal to the previous maximum of the span.
        while(self.dataDictionary['span %d frequencies' %i][j] <= self.spansAndLines[i-1][0]):
            deleteIndices.append(j)
            j += 1

        self.dataDictionary['span %d frequencies in average' %i] = np.delete(self.dataDictionary['span %d frequencies' %i], deleteIndices)
        self.dataDictionary['span %d magnitudes in average' %i] = np.delete(self.dataDictionary['span %d magnitudes' %i], deleteIndices)
        self.dataDictionary['span %d resolution in average' %i] = np.delete(self.dataDictionary['span %d resolution' %i], deleteIndices)

    def combineData(self):
#        d = self.dataDi
# This function combines the unique data from each span into a single array
        self.dataDictionary['unaveraged frequencies'] = np.array([0.])
        self.dataDictionary['unaveraged resolution'] = np.array([0.])
        self.dataDictionary['unaveraged magnitudes'] = np.array([0.])
        print 'Span 0 Frequencies in Average', self.dataDictionary['span 0 frequencies in average']
        for i in range(len(self.spansAndLines)):
            self.dataDictionary['unaveraged frequencies'] = np.append(self.dataDictionary['unaveraged frequencies'], self.dataDictionary['span %d frequencies in average' %i])
            self.dataDictionary['unaveraged resolution'] = np.append(self.dataDictionary['unaveraged resolution'], self.dataDictionary['span %d resolution in average' %i])
            self.dataDictionary['unaveraged magnitudes'] = np.append(self.dataDictionary['unaveraged magnitudes'], self.dataDictionary['span %d magnitudes in average' %i])
            print 'Index i', i
            print 'Length of Span', len(self.dataDictionary['span %d frequencies' %i])
        self.dataDictionary['unaveraged frequencies'] = np.delete(self.dataDictionary['unaveraged frequencies'],0)
        self.dataDictionary['unaveraged resolution'] = np.delete(self.dataDictionary['unaveraged resolution'],0)
        self.dataDictionary['unaveraged magnitudes'] = np.delete(self.dataDictionary['unaveraged magnitudes'], 0)


# Think about maybe doing this sometime...
#    class DataDictionary:
#        _unaveragedFrequencies = None
#
#        @property
#        def unaverageFrequencies(self):
#            return _unaverageFrequencies[_unaveragedFrequency>0]
#
#        @setter.unaveragedFrequencies
#        def setUnaverageedFrequencies(self, fs):
#            _unveragedFrequencies = fs[np.abs(fs) > 0.1]
#
#        def doSomething(self):
#            jfaslfsjklj
#
#
#
#    d = DataDictionary()
#    d.setUnaverageFrequencies = [-1, 0.0, 0.5, 53253]
#    print d.unaverageFrequencies # 0.5, 535253
#
#    Erlang (Erlangen)
#
#    d.unaveragedFrequencies = np.linspace()

    def calculateAverage(self):
        numberOfPoints = self.numberOfPointsLogSb.value()
        startFrequency = self.startFrequencySb.value()
        endFrequency = self.endFrequencySb.value()
        binBorders = np.logspace(np.log10(startFrequency), np.log10(endFrequency), 2*numberOfPoints-1)
        lowestBorder = 2*binBorders[0]-binBorders[1]
        if lowestBorder <0:
            lowestBorder = 0
        highestBorder = 2*binBorders[len(binBorders)-1]-binBorders[len(binBorders)-2]
        if (highestBorder > 102400) and (self.baseFrequencyCombo.currentText() == '102.4 kHz'):
            highestBorder = 102400
        elif (highestBorder > 100000) and (self.baseFrequencyCombo.currentText() == '100.0 kHz'):
            highestBorder = 100000
        binBorders = np.insert(binBorders, 0, lowestBorder)
        binBorders = np.append(binBorders, highestBorder)
        logFrequencies = np.logspace(np.log10(startFrequency), np.log10(endFrequency), numberOfPoints)
        binMidPointAmp = np.empty([numberOfPoints,])
        self.dataDictionary['averaged frequencies'] = logFrequencies
        self.dataDictionary['averaged magnitudes'] = np.zeros([numberOfPoints,])

        print 'Unaveraged frequencies', self.dataDictionary['unaveraged frequencies']
        print 'Length of Unaveraged frequencies', len(self.dataDictionary['unaveraged frequencies'])

        i = 0
        for j in range(numberOfPoints):
            binMidPoint = logFrequencies[j]
            binLowEnd = binBorders[2*j]
            binHighEnd = binBorders[2*j+2]
            # Note that we need to take the square root of each point at the end and should square them before adding them to the average
            #i<len(self.dataDictionary['unaveraged frequencies']) and Should this be included in the condition for the while loop?
            while (i <= len(self.dataDictionary['unaveraged frequencies'])) and (self.dataDictionary['unaveraged frequencies'][i] <= binHighEnd):
                print 'Index i', i
#                print 'Unave2
                dataHighEnd = self.dataDictionary['unaveraged frequencies'][i] + self.dataDictionary['unaveraged resolution'][i]/2
                dataLowEnd = self.dataDictionary['unaveraged frequencies'][i] - self.dataDictionary['unaveraged resolution'][i]/2
                if not ((dataLowEnd == 0) or (np.sign(dataLowEnd - binHighEnd) > 0)):
                    dHiMbLo = np.sign(dataHighEnd - binLowEnd)
                    dHiMbHi = np.sign(dataHighEnd - binHighEnd)
                    dLoMbLo = np.sign(dataLowEnd - binLowEnd)
                    if (dHiMbLo == 1) and (dHiMbHi == 1) and (dLoMbLo == 1): # point stradles the upper border of the bin
                        self.dataDictionary['averaged magnitudes'][j] += (self.dataDictionary['unaveraged frequencies'][i]**2)*(binHighEnd-dataLowEnd)/(binHighEnd-binLowEnd)
                    elif (dHiMbLo == 1) and (dHiMbHi == 1) and (dLoMbLo != 1): # point covers the entire range of the bin
                        self.dataDictionary['averaged magnitudes'][j] += (self.dataDictionary['unaveraged frequencies'][i]**2)
                    elif (dHiMbLo == 1) and (dHiMbHi != 1) and (dLoMbLo == 1): # point is entirely inside of the bin range
                        self.dataDictionary['averaged magnitudes'][j] += (self.dataDictionary['unaveraged frequencies'][i]**2)*(dataHighEnd-dataLowEnd)/(binHighEnd-binLowEnd)
                    elif (dHiMbLo == 1) and (dHiMbHi != 1) and (dLoMbLo != 1): # point stradles the lower border of the bin
                        self.dataDictionary['averaged magnitudes'][j] += (self.dataDictionary['unaveraged frequencies'][i]**2)*(dataHighEnd-binLowEnd)/(binHighEnd-binLowEnd)
                    else:
                        self.dataDictionary['averaged magnitudes'][j] += 0
                i += 1
            i -= 1
        # Note that the below is needed because things must be averaged in the squared values and then the square root should be taken as that is what we want
        self.dataDictionary['averaged magnitudes'] = np.sqrt(self.dataDictionary['averaged magnitudes'])
        self.curve2.setData(logFrequencies, self.dataDictionary['averaged magnitudes'])
# Add the new data that has been averaged over to the file
        dataFile = open("%s/%s" %(self.pathnameLe.text(),self.fileNameLe.text()),"a")
        dataFile.write("## Averaged Data Below ##\n")
        dataFile.write("Frequency (Hz)\tMagnitude\n")
        for i in range(numberOfPoints):
            dataFile.write("%f\t%g\n" %(self.dataDictionary['averaged frequencies'][i], self.dataDictionary['averaged magnitudes'][i]))
        dataFile.close()

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
    sr785.source.sine.amplitude = 1.9
    
#    sr785 = SR785(None)
    sr785.debug = True

    mainWindow = SR785_FFTWidget(sr785)
    mainWindow.show()

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

    sys.exit(app.exec_())

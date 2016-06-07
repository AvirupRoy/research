# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 19:03:30 2015

@author: jaeckel
"""
#from PyQt4.QtGui import QGroupBox

#include <Qtimer>

import SR785_SineSweep3Ui

import fileGeneratorDialog

import SR785_GUI

from PyQt4.QtGui import QWidget, QDialog, QVBoxLayout

from PyQt4 import Qt, Qwt5, QtGui, QtCore

from time import strftime

import pyqtgraph

import numpy as np

import os

class MeasurementThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    dataAvailable = QtCore.pyqtSignal(float, float, float, int)

    def __init__(self, sr785, nrOfPoints, repeatType, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.sr785 = sr785
        self.nrOfPoints = nrOfPoints
        self.repeatType = repeatType

    def stop(self):
        self.stopRequested = True

    def run(self):
        binNumber = 0
        self.stopRequested = False
        self.sr785.startMeasurement()
        while binNumber <= self.nrOfPoints-1:
            status = sr785.queryInteger('DSPS?')
            if bool(self.repeatType == 'single shot'):
                if bool(status & 2**0) and bool(status & 2**8):
                    i = self.sr785.sweptSine.measurementProgress()
                    while binNumber <= i:
                        try:
                            Freq = sr785.queryFloat('DBIN? 0,%d' % binNumber)
                            A = sr785.queryFloat('DSPY? 0,%d' % binNumber)
                            B = sr785.queryFloat('DSPY? 1,%d' % binNumber)
                        except:
                            print "Bailing out"
                            break
                        self.dataAvailable.emit(Freq, A, B, binNumber)
                        binNumber += 1
                        self.progress.emit(i)
            elif bool(self.repeatType == 'continuous'): # Might want to add some sort of time delay not sure what it should be through. Maybe try a longer sweep sometime to see what happens
            # Might still want to give some sort of time delay. Seems like it is pasible that it would finish and start a new one but I am not sure
                if bool(status & 2**4) and bool(status & 2**12):
                    while binNumber <= self.nrOfPoints-1:
                        try:
                            Freq = sr785.queryFloat('DBIN? 0,%d' % binNumber)
                            A = sr785.queryFloat('DSPY? 0,%d' % binNumber) # should maybe try doing binary and then try making it into a float
                            B = sr785.queryFloat('DSPY? 1,%d' % binNumber)
                        except:
                            print "Bailing out"
                            break
                        self.dataAvailable.emit(Freq, A, B, binNumber)
                        if bool(binNumber == self.nrOfPoints-1):
                            binNumber = 0
                        elif self.stopRequested:
                            break
                        else:
                            binNumber += 1
            if self.stopRequested:
                break
            self.msleep(200)

# Are print statements needed any more?

from Visa.VisaSetting import Setting

class SR785_SineSweepWidget(QWidget, SR785_SineSweep3Ui.Ui_Form):
    display1 = np.empty([1,])
    display2 = np.empty([1,])
    freqPoints = np.empty([1,])
    deviceNumber = int
    runNumber = str
    sequenceString = str

    def __init__(self, sr785, parent=None):
        QWidget.__init__(self, parent)
        SR785_SineSweep3Ui.Ui_Form.__init__(self)
        self.sr785 = sr785
        self.setupUi(self)
        self.dlg = fileGeneratorDialog.fileGenerator(self)

        inputLayout = QVBoxLayout(self.inputPage)
        self.inputChannelGbA = SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'A')
        inputLayout.addWidget(self.inputChannelGbA)
        self.inputChannelGbB = SR785_GUI.SR785_InputChannelGroupBox(self.sr785, 'B')
        inputLayout.addWidget(self.inputChannelGbB) 

        self.fileDialog = QtGui.QFileDialog()
        self.fileDialogPb.clicked.connect(self.fileInfo)
        self.sampleInfoPb.clicked.connect(self.sampleInfo)
        self.startPb.clicked.connect(self.startMeasurement)
        self.pausePb.clicked.connect(self.pauseMeasurement)

        # Disabling all buttons but the File Generator button
#        self.startPb.setDisabled(True)
        self.pausePb.setDisabled(True)
        self.stopPb.setDisabled(True)
#        self.sampleInfoPb.setDisabled(True)
#        self.sampleInfoPb.setToolTip('Currently Disabled')
        self.fileDialogPb.setDisabled(True)

        # Frequency Menu
        self.sr785.sweptSine.startFrequency.bindToSpinBox(self.startFrequencySb)
        self.sr785.sweptSine.stopFrequency.bindToSpinBox(self.stopFrequencySb)
        #Potential issue with the repeat feature. Not sure how many times it repeats and I am not sure that it will work with getting more data due to how measurements are read in.
        self.sr785.sweptSine.repeat.bindToEnumComboBox(self.repeatCombo)
        self.sr785.sweptSine.sweepType.bindToEnumComboBox(self.typeCombo)
        self.sr785.sweptSine.autoResolution.bindToEnumComboBox(self.autoResolutionCombo)
        self.sr785.sweptSine.numberOfPoints.bindToSpinBox(self.numberOfPointsSb)
        self.sr785.sweptSine.maximumStepSize.bindToSpinBox(self.maximumStepSizeSb)
        self.sr785.sweptSine.fasterThreshold.bindToSpinBox(self.fasterThresholdSb)
        self.sr785.sweptSine.slowerThreshold.bindToSpinBox(self.slowerThresholdSb)
        self.sr785.sweptSine.autoResolution.changed.connect(self.autoResolutionEnable)

        # Source Menu
        self.sr785.sweptSine.amplitude.bindToSpinBox(self.amplitudeSb)
        self.sr785.sweptSine.autoLevelReference.bindToEnumComboBox(self.autoLvlReferCombo)
        self.sr785.sweptSine.idealReference.bindToSpinBox(self.idealReferSb)
        self.sr785.sweptSine.sourceRamping.bindToEnumComboBox(self.sourceRampCombo)
        self.sr785.sweptSine.sourceRampRate.bindToSpinBox(self.sourceRampRateSb)
        self.sr785.sweptSine.referenceUpperLimit.bindToSpinBox(self.referUpperLimitSb)
        self.sr785.sweptSine.referenceLowerLimit.bindToSpinBox(self.referLowerLimitSb)
        self.sr785.sweptSine.maximumSourceLevel.bindToSpinBox(self.maxSourceLvlSp)
        self.sr785.source.sineOffset.bindToSpinBox(self.offsetSb) # One odd-ball here
        self.sr785.sweptSine.autoLevelReference.changed.connect(self.autoLevelReferenceEnable)

        # Average Menu
        self.sr785.sweptSine.settleTime.bindToSpinBox(self.settleTimeSb)
        self.sr785.sweptSine.settleCycles.bindToSpinBox(self.settleCycleSb)
        self.sr785.sweptSine.integrationTime.bindToSpinBox(self.integrationTimeSb)
        self.sr785.sweptSine.integrationCycles.bindToSpinBox(self.integrationCyclesSb)

        self.measurementProgressBar
        self.numberOfPointsSb.valueChanged.connect(self.measurementProgressBar.setMaximum)
        self.measurementProgressBar.setMinimum(1)
        self.display1Plot
        self.display2Plot
        
        self.ownFilenameCheck.stateChanged.connect(self.filenameNeeded)
        self.restoreSettings()
        
    def saveSettings(self):
        s = QtCore.QSettings()
        s.setValue('pathName', self.pathnameLe.text())
        s.setValue('fileName', self.fileNameLe.text())
        self.dlg.saveSettings(s)


# Is there a way to make it so that the header information is sent to the dialog upon start up? Or is this not something that would be useful?
#        s.setValue('header info', self.dlg.data())

    def restoreSettings(self):
        s = QtCore.QSettings()
        self.pathnameLe.setText(s.value('pathName', '', type=QtCore.QString))
        self.fileNameLe.setText(s.value('fileName', '', type=QtCore.QString))
#        self.deviceNumber = s.value('device number').toInt()[0]
#        self.runNumber = s.value('run number', '', type=QtCore.QString)
#        self.sequenceString = s.value('sequence', '', type=QtCore.QString)
#        while len(self.sequenceString) < 4:
#            self.sequenceString = '0%s' %self.sequenceString
#        # Is swp the correct file extension? Or do we want the one for transfer functions?
#        self.fileNameLe.setText('%s%s%s.swp' %(s.value('device number', '', type=QtCore.QString),s.value('run number','',type=QtCore.QString),self.sequenceString))

# Dialog Information
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
        self.sr785.sweptSine.readAll()
        self.inputChannelGbA.restoreSettings(0)
        self.inputChannelGbB.restoreSettings(1)
        self.dlg.restoreSettings(s)

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
        filename = self.fileDialog.getSaveFileName(self,'Save File as', '%s' %self.pathnameLe.text())       
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
            self.fileNameLe.setText('%d%s%s.swp' %(self.deviceNumber,self.runNumber,self.sequenceString))

            print data['device number']
            os.chdir("%s" %self.pathnameLe.text())

            # Not the right place to write this stuff!
            dataFile = open("%s" %self.fileNameLe.text(),"a")
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
        self.saveSettings()

    def autoResolutionEnable(self):
        print "Switching autoresolution to " , self.autoResolutionCombo.currentText()

        if self.autoResolutionCombo.currentText() == 'off':
            self.fasterThresholdSb.setEnabled(False)
            self.slowerThresholdSb.setEnabled(False)
            self.maximumStepSizeSb.setEnabled(False)
        elif self.autoResolutionCombo.currentText() == 'on':
            self.fasterThresholdSb.setEnabled(True)
            self.slowerThresholdSb.setEnabled(True)
            self.maximumStepSizeSb.setEnabled(True)

    def autoLevelReferenceEnable(self):
        if self.autoLvlReferCombo.currentText() == 'off':
            self.amplitudeSb.setEnabled(True)
            self.idealReferSb.setEnabled(False)
            self.referUpperLimitSb.setEnabled(False)
            self.referLowerLimitSb.setEnabled(False)
            self.maxSourceLvlSp.setEnabled(False)
        else:
            self.amplitudeSb.setEnabled(False)
            self.idealReferSb.setEnabled(True)
            self.referUpperLimitSb.setEnabled(True)
            self.referLowerLimitSb.setEnabled(True)
            self.maxSourceLvlSp.setEnabled(True)

    def startMeasurement(self):
        self.measurementProgressBar.setValue(1)
        self.measurementProgressBar.setMaximum(self.numberOfPointsSb.value())
        self.thread = MeasurementThread(self.sr785, self.numberOfPointsSb.value(), self.repeatCombo.currentText(), self)
        self.thread.dataAvailable.connect(self.collectData)
        self.thread.progress.connect(self.measurementProgressBar.setValue)
        self.thread.finished.connect(self.measurementFinished)
        self.stopPb.clicked.connect(self.thread.stop)
        self.thread.start()
        self.enableSomeParameters(False)
        self.display1 = np.empty([self.numberOfPointsSb.value(),])
        self.display2 = np.empty([self.numberOfPointsSb.value(),])
        self.freqPoints = np.empty([self.numberOfPointsSb.value(),])
        self.initPlots()
#        if self.typeCombo.currentText() == 'linear':
#            self.freqPoints = np.linspace(self.startFrequencySb.value(),self.stopFrequencySb.value(),self.numberOfPointsSb.value())
#        elif self.typeCombo.currentText() == 'log':
#            self.freqPoints = np.logspace(np.log10(self.startFrequencySb.value()),np.log10(self.stopFrequencySb.value()),self.numberOfPointsSb.value())
        os.chdir("%s" %self.pathnameLe.text())
        dataFile = open("%s" %self.fileNameLe.text(),"a")
        dataFile.write("%s\%s\n" %(self.pathnameLe.text(),self.fileNameLe.text()))
        dataFile.write("Date and Time of Measurement: %s\n" % strftime("%Y-%m-%d %H:%M:%S"))
        for name, item in self.sr785.sweptSine:
            if isinstance(item, Setting):
                dataFile.write('#SR785/SweptSine/%s=%s\n' % ( name, item.string ))
                
        for channel in range(2):
            for name, item in self.sr785.inputs[channel]:
                if isinstance(item, Setting):
                    dataFile.write('#SR785/Channel%d/%s=%s\n' % ( channel, name, item.string ))

        dataFile.write('#SR785/Source/Offset=%s\n' % self.sr785.source.sineOffset.string)
            
        dataFile.write("Frequency (Hz)\tMagnitude\tPhase (%s)\n" % self.sr785.queryString('UNIT? 1'))
        dataFile.close()

    def enableSomeParameters(self, enable):
        self.startPb.setEnabled(enable)
        self.numberOfPointsSb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)
        self.pausePb.setEnabled(not enable)

    def pauseMeasurement(self):
        self.startPb.setText('Restart Measurement')
        if self.pausePb.text() == 'Pause Measurement':
            self.sr785.pauseMeasurement()
            self.pausePb.setText('Continue Measurement')
        elif self.pausePb.text() == 'Continue Measurement':
            self.sr785.continueMeasurement()
            self.pausePb.setText('Pause Measurement')

    def measurementFinished(self):
        self.enableSomeParameters(True)
        print "Measurement finished"

    def initPlots(self):
# Clearing the previous plot
        self.display1Plot.clear()
        self.display2Plot.clear()
        # X axis labels
        self.display1Plot.setLabel('bottom', text='Frequency', units='Hz')
        self.display2Plot.setLabel('bottom', text='Frequency', units='Hz')
        # Y axis labels
        self.display1Plot.setLabel('left',text='Magnitude')
        self.display2Plot.setLabel('left',text='Phase', units=self.sr785.queryString('UNIT? 1'))
#        self.requestedViewPlot.setLabel('left',text='Magnitude')
# Setting the grid to be on
        self.display1Plot.showGrid(x=True,y=True)
        self.display2Plot.showGrid(x=True,y=True)
# Setting the log mode of the graph to be on
        self.display1Plot.setLogMode(x=True,y=True)
        self.display2Plot.setLogMode(x=True)
# Creating curves to be used later
        self.curve1 = self.display1Plot.plot([],[], pen='r', name='Magnitude')
        self.curve2 = self.display2Plot.plot([],[], pen='b', name='Phase')

    def collectData(self, Freq, A, B,binNumber):
        os.chdir("%s" %self.pathnameLe.text())
        dataFile = open("%s" %self.fileNameLe.text(),"a")
        print 'A,B', A, B
        self.freqPoints[binNumber] = Freq
#        self.freqPoints[binNumber] = self.sr785.frequencyOfBin(0, binNumber)
        self.display1[binNumber] = A
        self.display2[binNumber] = B
        self.measurementProgressBar.setValue(binNumber+1)
        dataFile.write("%f\t%g\t%g\n" %(self.freqPoints[binNumber],self.display1[binNumber],self.display2[binNumber]))
        if binNumber == self.numberOfPointsSb.maximum()-1:
            dataFile.write("Date and Time of Measurement: %s\n" %strftime("%Y-%m-%d %H:%M:%S"))
        dataFile.close()
        self.updatePlots(binNumber)

    def updatePlots(self, binNumber):
        x = self.freqPoints[0:binNumber+1]
        self.curve1.setData(x,self.display1[0:binNumber+1])
        self.curve2.setData(x,self.display2[0:binNumber+1])

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
    app.setApplicationName('SR785 Sine Sweep')

    visaAddress = 'GPIB1::10'
    sr785 = SR785(visaAddress)
#    sr785 = SR785(None)
    sr785.debug = True

    mainWindow = SR785_SineSweepWidget(sr785)
    mainWindow.show()
# Setting the measurement to swept sine
    sr785.commandString('MGRP 2, 3')
# Setting the measurement type to frequency response for both displays
    sr785.commandString('MEAS 0, 47')
    sr785.commandString('MEAS 1, 47')
# Setting the displays to the magnitude and phase of the frequency response
# For unwrapped phase, change the 5 to a 6 in the second view command
    sr785.commandString('VIEW 0, 1')
    sr785.commandString('VIEW 1, 5')
    sys.exit(app.exec_())

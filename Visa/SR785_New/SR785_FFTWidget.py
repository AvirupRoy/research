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

class MeasurementThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    dataAvailable = QtCore.pyqtSignal(float, float, int)

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
        # Should now work with continuous settings
        while binNumber <= self.nrOfPoints-1:
            status = sr785.queryInteger('DSPS?')
            if bool(status & 2**0) and bool(status & 2**8): ## Don't need to change these numbers because they ask if new data is available or not, not measurement specific
                i = self.sr785.sweptSine.measurementProgress()
                while binNumber <= i:
                    try:
                        A = sr785.queryFloat('DSPY? 0,%d' % binNumber)
                        B = sr785.queryFloat('DSPY? 1,%d' % binNumber)
                    except:
                        print "Bailing out"
                        break
                    self.dataAvailable.emit(A, B, binNumber)
                    binNumber += 1
                    if self.repeatType == 'continuous' & binNumber > self.nrOfPoints-1:
                        binNumber = 0
                    self.progress.emit(i)
            if self.stopRequested:
                break
            self.msleep(200)

class SR785_FFTWidget(QWidget, SR785_FFTUi.Ui_Form):
    def __init__(self, sr785, parent=None):
        QWidget.__init__(self, parent)
        SR785_FFTUi.Ui_Form.__init__(self)
        self.sr785 = sr785
        self.setupUi(self)

        # Frequency Menu
        # There are still other things to include in this
        self.sr785.fft.lines.bindToEnumComboBox(self.linesCombo)
        self.sr785.fft.baseFrequency.bindToEnumComboBox(self.baseFrequencyCombo)
        self.sr785.fft.startFrequency.bindToSpinBox(self.startFrequencySb)
        self.sr785.fft.centerFrequency.bindToSpinBox(self.centerFrequencySb)
        self.sr785.fft.endFrequency.bindToSpinBox(self.endFrequencySb)
#        self.settlePb.clicked.connect(self.sr785.fft.settle) ## Might want to create a function in here for settling

        # Average Menu
        self.sr785.fft.computeAverage.bindToEnumComboBox(self.computeAverageCombo)
        self.sr785.fft.averageType.bindToEnumComboBox(self.averageTypeCombo)
        self.sr785.fft.fftAverageType.bindToEnumComboBox(self.fftAverageTypeCombo)
        self.sr785.fft.numberOfAverages.bindToSpinBox(self.numberOfAveragesSb)
        self.sr785.fft.fftTimeRecordIncrement.bindToSpinBox(self.fftTimeRecordIncrementSb)
        self.sr785.fft.overloadReject.bindToEnumComboBox(self.overloadRejectCombo)
        self.sr785.fft.triggerAverageMode.bindToEnumComboBox(self.triggerAverageModeCombo)
        self.sr785.fft.averagePreview.bindToEnumComboBox(self.averagePreviewCombo)

        self.display1Plot
        self.display2Plot

        # Not sure if a start, pause, or stop button are needed

    def saveSettings(self):
        s = QtCore.QSettings()

    def restoreSettings(self):
        s = QtCore.QSettings()

    def startMeasurement(self):
        self.thread = MeasurementThread(self.sr785, self)
        self.thread.dataAvailable.connect(self.collectData)
        self.stopPb.clicked.connect(self.thread.stop)
        self.thread.start()
        self.pausePb.setEnabled(True)
        self.enableSomeParameters(False)
        self.startPb.setEnabled(False)
        self.stopPb.setEnabled(True)
#        self.display1 = np.empty([self.numberOfPointsSb.value(),])
#        self.display2 = np.empty([self.numberOfPointsSb.value(),])
        self.initPlots()
        os.chdir("%s" %self.pathnameLe.text())
        dataFile = open("%s" %self.fileNameLe.text(),"a")
        dataFile.write("%s\%s\n" %(self.pathnameLe.text(),self.fileNameLe.text()))
        dataFile.write("Date and Time of Measurement: %s\n" %strftime("%Y-%m-%d %H:%M:%S") )
        dataFile.write("LabView Time: %f\n" %self.labviewTime())

# Might want to go ahead and add the other things that are enabled/disabled in the start measurement function
    def enableSomeParameters(self, enable):
        self.startPb.setEnabled(enable)
        self.numberOfPointsSb.setEnabled(enable)
        self.stopPb.setEnabled(not enable)

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
        # One issue is that sometimes we get negative numbers which then give a warning when we try to convert to a log scale
        # X axis labels
        self.display1Plot.setLabel('bottom', text='Hz')
        self.display2Plot.setLabel('bottom', text='Hz')
        # Y axis labels
        self.display1Plot.setLabel('left',text='%s' %self.sr785.queryString('UNIT ? 0'))
        self.display2Plot.setLabel('left',text='%s' %self.sr785.queryString('UNIT ? 1'))
        self.display1Plot.setLogMode(x=True,y=True)
        self.display2Plot.setLogMode(x=True,y=True)
        self.display1Plot.showGrid(x=True,y=True)
        self.display2Plot.showGrid(x=True)
        self.curve1 = self.display1Plot.plot([],[], pen='r', name='Magnitude')
        self.curve2 = self.display2Plot.plot([],[], pen='b', name='Phase')
        # Should it be log-log for the phase plot as well?

    def collectData(self, A, B,binNumber):
        os.chdir("%s" %self.pathnameLe.text())
        dataFile = open("%s" %self.fileNameLe.text(),"a")
        print 'A,B', A, B
        self.freqPoints[binNumber] = self.sr785.frequencyOfBin(0, binNumber) # Do we need different frequencies for each display
        self.display1[binNumber] = A
        self.display2[binNumber] = B
        self.measurementProgressBar.setValue(binNumber+1)
        dataFile.write("%f\t%g\t%g\n" %(self.freqPoints[binNumber],self.display1[binNumber],self.display2[binNumber]))
        self.updatePlots(binNumber)

    def updatePlots(self, binNumber):
        x = self.freqPoints[0:binNumber+1]
        self.curve1.setData(x,self.display1[0:binNumber+1])
        self.curve2.setData(x,self.display2[0:binNumber+1])

if __name__ == '__main__':
    import sys
    from SR785 import SR785
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    app.setOrganizationName('McCammonLab')
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('SR785 FFT')

    visaAddress = 'GPIB0::10'
    sr785 = SR785(visaAddress)
#    sr785 = SR785(None)
    sr785.debug = True

    mainWindow = SR785_FFTWidget(sr785)
    mainWindow.show()
# Setting the measurement to fft
    sr785.commandString('MRGP 2, 0')
# Setting the measurement type to frequency response for both displays
    sr785.commandString('MEAS 0, 11')
    sr785.commandString('MEAS 1, 11')
# Setting the displays to the real and imaginary part of the frequency response
    sr785.commandString('VIEW 0, 1')
    sr785.commandString('VIEW 1, 5')
    sys.exit(app.exec_())

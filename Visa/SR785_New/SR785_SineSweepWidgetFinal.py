# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 19:03:30 2015

@author: jaeckel
"""
#from PyQt4.QtGui import QGroupBox

#include <Qtimer>

import SR785_SineSweep2Ui

from PyQt4.QtGui import QWidget

from PyQt4 import Qt, Qwt5, QtGui, QtCore

from time import strftime

import pyqtgraph

import numpy as np

import random # don't think this is necessary but maybe...

import os

class SR785_SineSweepWidget(QWidget, SR785_SineSweep2Ui.Ui_Form):
    def __init__(self, sr785, parent=None):
        QWidget.__init__(self, parent)
        SR785_SineSweep2Ui.Ui_Form.__init__(self)       
        self.sr785 = sr785
#        super(SR785_SineSweepWidget, self).__init__(self)
        self.setupUi(self)
        self.startPb.clicked.connect(self.startMeasurement)
        self.pausePb.setDisabled(True)        
        self.pausePb.clicked.connect(self.pauseMeasurement)
        
        # Frequency Menu
        self.sr785.sweptSine.startFrequency.bindToSpinBox(self.startFrequencySb)
        self.sr785.sweptSine.stopFrequency.bindToSpinBox(self.stopFrequencySb)
        self.sr785.sweptSine.repeat.bindToEnumComboBox(self.repeatCombo)        
        self.sr785.sweptSine.sweepType.bindToEnumComboBox(self.typeCombo)
        self.sr785.sweptSine.autoResolution.bindToEnumComboBox(self.autoResolutionCombo)        
        self.sr785.sweptSine.numberOfPoints.bindToSpinBox(self.numberOfPointsSb)
        self.sr785.sweptSine.maximumStepSize.bindToSpinBox(self.maximumStepSizeSb)
        self.sr785.sweptSine.fasterThreshold.bindToSpinBox(self.fasterThresholdSb)
        self.sr785.sweptSine.slowerThreshold.bindToSpinBox(self.slowerThresholdSb)
        
        # Source Menu
        self.sr785.sweptSine.autoLevelReference.bindToEnumComboBox(self.autoLvlReferCombo)
        self.sr785.sweptSine.idealReference.bindToSpinBox(self.idealReferSb)
        self.sr785.sweptSine.sourceRamping.bindToEnumComboBox(self.sourceRampCombo)
        self.sr785.sweptSine.sourceRampRate.bindToSpinBox(self.sourceRampRateSb)
        self.sr785.sweptSine.referenceUpperLimit.bindToSpinBox(self.referUpperLimitSb)
        self.sr785.sweptSine.referenceLowerLimit.bindToSpinBox(self.referLowerLimitSb)
        self.sr785.sweptSine.maximumSourceLevel.bindToSpinBox(self.maxSourceLvlSp)
        self.sr785.sweptSine.offset.bindToSpinBox(self.offsetSb)        
        
        # Average Menu        
        self.sr785.sweptSine.settleTime.bindToSpinBox(self.settleTimeSb)
        self.sr785.sweptSine.settleCycles.bindToSpinBox(self.settleCycleSb)
        self.sr785.sweptSine.integrationTime.bindToSpinBox(self.integrationTimeSb)
        self.sr785.sweptSine.integrationCycles.bindToSpinBox(self.integrationCyclesSb)
        
# Need to figure out a way to make sure that this gets changed if the number of points
# desired changes according to the spin box        
 
        self.measurementProgressBar
        self.numberOfPointsSb.valueChanged.connect(self.measurementProgressBar.setMaximum)
        self.measurementProgressBar.setMinimum(0)        
        self.channel1Plot
        self.channel2Plot
              
      
    def startMeasurement(self):
        ## Maybe enable a stop button and disable the start button
#        self.sr785.startMeasurement()
#        self.timer = QtCore.QTimer(self)
#        self.timer.timeout.connect(self.checkIfDone)
#        self.timer.start(1000)
        self.pausePb.setEnabled(True)
        if self.startPb.text() == 'Start Measurement':            
            self.startPb.setText('Restart Measurement')
        elif self.startPb.text() == 'Restart Measurement':
            self.startPb.setText('Restart Measurement')

    def pauseMeasurement(self):
        self.startPb.setText('Restart Measurement')
        if self.pausePb.text() == 'Pause Measurement':
#            self.sr785.pauseMeasurement()
            self.pausePb.setText('Continue Measurement')
        elif self.pausePb.text() == 'Continue Measurement':
#            self.sr785.continueMeasurement()
            self.pausePb.setText('Pause Measurement')
            

# Not liking something about this, unsupported operand type(s) for -: 'builtin_function_or_method' and 'int'     
#    def checkIfDone(self):
#        progress = sr785.measurementProgress()
#        self.measurementProgressBar.value(progress)
#        numPts = self.numberOfPointsSb.value()   #Doesn't like this and now doesn't like the retrieveData function...
#        if numPts-1 == progress:
#            self.timer.stop()
#            self.channel1PLot.setXRange(self.startFrequencySb.value(), self.stopFrequencySb.value())
#            self.channel2PLot.setXRange(self.startFrequencySb.value(), self.stopFrequencySb.value())
#            freqPoints = range(self.startFrequencySb.value(),self.stopFrequencySb.value(),(self.stopFrequencySb.value()-self.startFrequencySb.value())/self.numberOfPointsSb.value())
#            channel1 = sr785.display.retrieveData(0) # TypeError: unbound method retrieveData() must be called with Display instance as first argument (got int instance instead)
#            channel2 = sr785.display.retrieveData(1)
#            self.channel1Plot.plot(freqPoints,channel1)
#            self.channel2Plot.plot(freqPoints,channel2)
#            os.chdir("%s" %self.pathnameLe.text())
#            dataFile = open("%s" %self.fileNameLe.text(),"a")
#            dataFile.write("%s\%s" %(self.pathnameLe.text(),self.fileNameLe.text())
#            dataFile.write("Date and Time of Measurement: %s" %strftime("%Y-%m-%d %H:%M:%S") )
#            dataFile.write("Settle Time: %f\n" %self.settleTimeSb.value())
#            dataFile.write("Settle Cycles: %f\n" %self.settleCycleSb.value())
#            dataFile.write("Integration Time: %f\n" %self.integrationTimeSb.value())
#            dataFile.write("Integration Cycles: %f\n" %self.integrationCyclesSb.value())
#               for i in range(0,len(channel1)):
#                   dataFile.write("%f\t%f\t%f\n" %(freqPoints[i],channel1[i],channel2[i]))


if __name__ == '__main__':
    import sys
    from SR785 import SR785
    from PyQt4.QtGui import QApplication
    app = QApplication([])
#    visaAddress = 'GPIB0::10'
#    sr785 = SR785(visaAddress)
    sr785 = SR785(None)
    sr785.debug = True
        
    mainWindow = SR785_SineSweepWidget(sr785)
    mainWindow.show()
#    sr785.display.selectMeasurement(2,'frequency response')
#    display0 = sr785.display.retrieveData(0)
#    display1 = sr785.display.retrieveData(1)
#    mainWindow.mplwidget.axes.plot(display0, '-')
    #app.exec_()
    sys.exit(app.exec_())

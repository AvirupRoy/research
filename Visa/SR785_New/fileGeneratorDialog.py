# -*- coding: utf-8 -*-
"""
Created on Wed Jul 01 15:49:01 2015

@author: Cole Cook
"""

import fileGeneratorDialogUi

from PyQt4.QtGui import QDialog

from PyQt4 import QtCore

import os

from time import strftime

# Would it make more sense to have a line edit with the filename or would it make more sense to have a line edit with the run number
# and a spin box for the sequence?

class fileGenerator(QDialog, fileGeneratorDialogUi.Ui_Dialog):
    '''FileGenerator is a QDialog which helps you to collect run/device meta data to be stored with measurements

        Call data() to  retrieve a dictionary holding all the metadata.
    Usage:

    '''

#    pathName = QtCore.pyqtSignal(str)
#    fileName = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        fileGeneratorDialogUi.Ui_Dialog.__init__(self)
        self.setupUi(self)
#        self.generateFilePb.clicked.connect(self.generateFile)
#        self.buttonBox.OK.clicked.connect(self.generateFile)
#        self.generateFile.connect(self.buttonBox, QtCore.SIGNAL(accepted()))
#        self.buttonBox.addAction(self.generateFile)
#        self.buttonBox.clicked.connect(self.generateFile)

# Setting Maximums
        self.deviceLengthSb.setMaximum(1E6)
        self.deviceWidthSb.setMaximum(1E6)
        self.deviceThicknessSb.setMaximum(1E9)
        self.loadResistorSb.setMaximum(1E9)
# Setting suffixes
        self.deviceLengthSb.setSuffix(u' µm') # How to do Greek letters here?
        self.deviceWidthSb.setSuffix(u' µm')
        self.deviceThicknessSb.setSuffix(' nm')
        self.biasCurrentSb.setSuffix(' I')
        self.biasVoltageSb.setSuffix(' V')
        self.loadResistorSb.setSuffix(' Ohm')

        self.deviceNumberSb.valueChanged.connect(self.deviceOrRunNumberUpdateFilename)
        self.runNumberLe.textChanged.connect(self.deviceOrRunNumberUpdateFilename)
        self.sequenceNumberSb.valueChanged.connect(self.sequenceNumberUpdateFilename)

        self.buttonBox.accepted.connect(self.accept)
# Combo Box Stuff
# Note that mxf is an actual file type... Creates a video file I think...
#        self.fileTypeCb.addItems(["Liquid Helium Level: .lhe","Multiple Transfer Functions: .mxf","Noise: .nse","Swept Sine: .swp","Text: .txt","Transfer Function: .xfr"])

    def accept(self):
        # Ask all controls for their data and save it for later
#        self._data = {'deviceNumber':self.deviceNumberSb.value(), 'device id':self.deviceIDLe.text()}
    # Might want to add the pathname and filename to the collection of data
#        self.pathName.emit("%s" %self.pathnameLe.text())
#        self.fileName.emit("%s.%s" %(self.filenameLe.text(),self.fileTypeCb.currentText().split(".")[1]))
        self._data = {'path name':self.pathnameLe.text(),'file name':self.filenameLe.text(),'device number':self.deviceNumberSb.value(),'device id':self.deviceIDLe.text(),'item description':self.itemDescriptionLe.text(),'item id':self.twoCharItemIDLe.text(),'secondary id':self.secondaryIDLe.text(),'device length':self.deviceLengthSb.value(),'device width':self.deviceWidthSb.value(),'device thickness':self.deviceThicknessSb.value(),'run number':self.runNumberLe.text(),'sequence number':self.sequenceNumberSb.value(),'load resistor':self.loadResistorSb.value(),'fet dc gain':self.fetDCGainSb.value(),'ac gain':self.acGainSb.value(),'internal divider ratio':self.internalDividerRatioSb.value(),'bias current':self.biasCurrentSb.value(),'bias voltage':self.biasVoltageSb.value(),'source x position':self.sourceXPositionSb.value(),'source y position':self.sourceYPositionSb.value(),'external gain':self.externalGainSb.value(),'cold plate temperature':self.coldPlateTemperatureSb.value()}
#        print self._data['deviceNumber']
        QDialog.accept(self) # Let super-class handle the rest

    def saveSettings(self, settings = None):
        if settings is None:
            settings = QtCore.QSettings()
        else:
            settings = settings
        settings.setValue('device id', self._data['device id'])
        settings.setValue('item description', self._data['item description'])
        settings.setValue('item id', self._data['item id'])
        settings.setValue('secondary id', self._data['secondary id'])
        settings.setValue('device length', self._data['device length'])
        settings.setValue('device width', self._data['device width'])
        settings.setValue('device thickness', self._data['device thickness'])
        settings.setValue('load resistor', self._data['load resistor'])
        settings.setValue('fet dc gain', self._data['fet dc gain'])
        settings.setValue('ac gain', self._data['ac gain'])
        settings.setValue('internal divider ratio', self._data['internal divider ratio'])
        settings.setValue('bias current', self._data['bias current'])
        settings.setValue('bias voltage', self._data['bias voltage'])
        settings.setValue('source x position', self._data['source x position'])
        settings.setValue('source y position', self._data['source y position'])
        settings.setValue('external gain', self._data['external gain'])
        settings.setValue('cold plate temperature', self._data['cold plate temperature'])
        settings.setValue('run number', self._data['run number'])
        settings.setValue('sequence', self._data['sequence number'])
        settings.setValue('device number', self._data['device number'])

    def restoreSettings(self, settings = None):
        if settings is None:
            settings = QtCore.QSettings()
        else:
            settings = settings
        self.pathnameLe.setText(self.pathnameLe.text())
        self.pathnameLe.setText(settings.value('pathName', '', type=QtCore.QString))
        self.filenameLe.setText(self.filenameLe.text())
        newSequenceNumber = settings.value('sequence number').toInt()[0] + 1
        sequenceString = '%d' %newSequenceNumber
        while len(sequenceString) < 4:
            sequenceString = '0%s' %sequenceString
# Good way to change filetype?

        self.filenameLe.setText('%s%s%s.dat' % (settings.value('device number', '', type=QtCore.QString),settings.value('run number','',type=QtCore.QString),sequenceString))

        self.deviceNumberSb.setValue(settings.value('device number').toInt()[0])
        self.deviceIDLe.setText(settings.value('device id','',type=QtCore.QString))
        self.itemDescriptionLe.setText(settings.value('item description','',type=QtCore.QString))
        self.twoCharItemIDLe.setText(settings.value('item id','',type=QtCore.QString))
        self.secondaryIDLe.setText(settings.value('secondary id','',type=QtCore.QString))
        self.deviceLengthSb.setValue(settings.value('device length').toFloat()[0])
        self.deviceWidthSb.setValue(settings.value('device width').toFloat()[0])
        self.deviceThicknessSb.setValue(settings.value('device thickness').toFloat()[0])
        self.runNumberLe.setText(settings.value('run number', '', type=QtCore.QString))
        self.sequenceNumberSb.setValue(newSequenceNumber)
        self.loadResistorSb.setValue(settings.value('load resistor').toInt()[0])
        self.fetDCGainSb.setValue(settings.value('fet dc gain').toInt()[0])
        self.acGainSb.setValue(settings.value('ac gain').toInt()[0])
        self.internalDividerRatioSb.setValue(settings.value('internal divider ratio').toFloat()[0])
        self.biasCurrentSb.setValue(settings.value('bias current').toFloat()[0])
        self.biasVoltageSb.setValue(settings.value('bias voltage').toFloat()[0])
        self.sourceXPositionSb.setValue(settings.value('source x position').toInt()[0])
        self.sourceYPositionSb.setValue(settings.value('source y position').toInt()[0])
        self.externalGainSb.setValue(settings.value('external gain').toFloat()[0])
        self.coldPlateTemperatureSb.setValue(settings.value('cold plate temperature').toFloat()[0])

    def deviceOrRunNumberUpdateFilename(self):
        self.filenameLe.setText('%s%s0001.dat' %(self.deviceNumberSb.value(),self.runNumberLe.text()))

    def sequenceNumberUpdateFilename(self):
        sequenceString = '%d' %self.sequenceNumberSb.value()
        while len(sequenceString) < 4:
            sequenceString = '0%s' %sequenceString
        self.filenameLe.setText('%s%s%s.dat' %(self.deviceNumberSb.value(),self.runNumberLe.text(),sequenceString))


    def data(self):
        '''Returns a dictionary with the meta-info'''
        return self._data

        # Not sure if I need the \n at the end of the string stuff
        # generateFile function is completely unnecessary now...
    def generateFile(self):
        '''Writes the meta info into our standard format file'''
# Create File
        os.chdir("%s" %self.pathnameLe.text())
        fileType = self.fileTypeCb.currentText()
        self.pathName.emit("%s" %self.pathnameLe.text())
        self.fileName.emit("%s.%s" %(self.filenameLe.text(),fileType.split(".")[1]))
        # Should a new file always be created or should it keep writing on a old file if an
        # old file name is used?
        dataFile = open("%s.%s" %(self.filenameLe.text(),fileType.split(".")[1]), "a")
        if fileType.split(".")[1] != "txt":
            dataFile.write("%s\%s.%s\n" %(self.pathnameLe.text(),self.filenameLe.text(),fileType.split(".")[1]))
    #        dataFile = open("text.txt", "a")
    #        dataFile.write("%s" %fileType)
            dataFile.write("Date and Time of Measurement: %s\n\n" %strftime("%Y-%m-%d %H:%M:%S") )
    ## Device Information
            dataFile.write("Device Information\n")
            dataFile.write("Device number: %d\n" %self.deviceNumberSb.value())
            dataFile.write("Device ID: %s\n" %self.deviceIDLe.text())
            dataFile.write("Item Description: %s\n" %self.itemDescriptionLe.text())
            dataFile.write("Item ID (2 chars): %s\n" %self.twoCharItemIDLe.text())
            dataFile.write("Secondary Id (8 chars): %s\n" %self.secondaryIDLe.text())
            dataFile.write("Device Length: %f\n" %self.deviceLengthSb.value())
            dataFile.write("Device Width: %f\n" %self.deviceWidthSb.value())
            dataFile.write("Device Thickness: %f\n\n" %self.deviceThicknessSb.value())
    # Channel Information
            dataFile.write("Channel Information\n")
            dataFile.write("Load Resistor: %d\n" %self.loadResistorSb.value())
            dataFile.write("FET DC Gain: %d\n" %self.fetDCGainSb.value())
            dataFile.write("AC Gain: %d\n" %self.acGainSb.value())
            dataFile.write("Internal Divider Ratio: %f\n\n" %self.internalDividerRatioSb.value())
    # General Operating Conditions
            dataFile.write("General Operating Conditions\n")
            dataFile.write("Bias Current: %f\n" %self.biasCurrentSb.value())
            dataFile.write("Bias Voltage: %f\n" %self.biasVoltageSb.value())
            dataFile.write("Source X Position: %d\n" %self.sourceXPositionSb.value())
            dataFile.write("Source Y Position: %d\n" %self.sourceYPositionSb.value())
            dataFile.write("External Gain: %f\n" %self.externalGainSb.value())
            dataFile.write("Cold Plate Temperature (GeA): %f\n\n" %self.coldPlateTemperatureSb.value())
     # Program Specific Parameters
            dataFile.write("Program Specific Parameters\n")
        dataFile.close()


if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    mainWindow = fileGenerator(None)
    mainWindow.show()
    sys.exit(app.exec_())
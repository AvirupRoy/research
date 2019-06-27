# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 19:03:30 2015

@author: jaeckel
"""
from PyQt4.QtGui import QGroupBox

import SR785_ChannelGroupBoxUi, SR785_SourceGroupBoxUi

class SR785_InputChannelGroupBox(QGroupBox, SR785_ChannelGroupBoxUi.Ui_GroupBox):
    def __init__(self, sr785, inputChannel, parent=None):
        super(SR785_InputChannelGroupBox, self).__init__(parent)
        self.setupUi(self)
        if isinstance(inputChannel, int):
            ch = inputChannel
        elif inputChannel == 'A':
            ch = 0
        elif inputChannel == 'B':
            ch = 1
        else:
            raise Exception('Unknown input channel')

        self.sr785 = sr785
        self.setTitle('Channel %d' % (ch+1))

        inp = sr785.inputs[ch]
        self.inp = inp
        inp.antiAliasing.bindToCheckBox(self.antiAliasingCb)
#        inp.autoRange.bindToCheckBox(self.autoRangingCb)
        inp.aWeighting.bindToCheckBox(self.aWeightingCb)
        inp.mode.bindToEnumComboBox(self.modeCombo)
        inp.coupling.bindToEnumComboBox(self.couplingCombo)
        inp.grounding.bindToEnumComboBox(self.groundingCombo)
        inp.autoRangeMode.bindToEnumComboBox(self.autoRangeTypeCombo)
        inp.inputRange.bindToEnumComboBox(self.rangeCombo)

#        self.rangeCombo.addItems(inp.InputRange())
#        self.rangeCombo.currentIndexChanged.connect(inp.setInputRange)
#        self.restoreSettings()

#    def setInputRange(self):
#        inp.setInputRange(ch, self.rangeCombo.currentText())
# Might want to restrict the scope of readAll, is what I have correct?
    def restoreSettings(self, ch):
        #sr785.readAll()
        self.inp.readAll()
#        find = '%s Vpk' % self.inp.getInputRange(ch+1)
#        index = self.rangeCombo.findText(find)
#        self.rangeCombo.setCurrentIndex(index)
#        print "Index:", self.rangeCombo.currentIndex()
#        print "String:", self.rangeCombo.currentText()

from LabWidgets.SilentWidgets import SilentGroupBox

class SR785_SourceGroupBox(SilentGroupBox, SR785_SourceGroupBoxUi.Ui_GroupBox):
    def __init__(self, sr785, parent=None):
        super(SR785_SourceGroupBox, self).__init__(parent)
        self.setupUi(self)
        self.sr785 = sr785

#What is the difference between a check box and a group box? I am not sure how to turn the signal on and off using a group box...
#        sr785.source.output.bindToCheckBox(self.isChecked)
        sr785.source.output.bindToCheckBox(self.sourceOnCheck)
        self.sourceTab.currentChanged.connect(self.tabChanged)
#        self.isChecked.connect(self.sourceOnOff)

#    def sourceOnOff(self):
#        if self.isChecked():
#            sr785.commandString('SRCO 1')
#        else:
#            sr785.commandString('SRCO 0')

        # Sine
        sine = sr785.source.sine
        sine[0].amplitude.bindToSpinBox(self.sineAmplitude1Sb)
        sine[1].amplitude.bindToSpinBox(self.sineAmplitude2Sb)
        sine[0].frequency.bindToSpinBox(self.sineFrequency1Sb)
        sine[1].frequency.bindToSpinBox(self.sineFrequency2Sb)
        sr785.source.sineOffset.bindToSpinBox(self.sineOffsetSb)

        # Chirp
        chirp = sr785.source.chirp
        # Need to finish getting amplitude setting on SR785 - not sure on if this is right, went off of the sine wave amplitude
        chirp.amplitude.bindToSpinBox(self.chirpAmplitudeSb)
        chirp.burstPercentage.bindToSpinBox(self.chirpBurstPercentageSb)
        chirp.display.bindToEnumComboBox(self.chirpSourceDisplayCb)

        # Noise
        noise = sr785.source.noise
        noise.amplitude.bindToSpinBox(self.noiseAmplitudeSb)
        noise.type.bindToEnumComboBox(self.noiseTypeCombo)
        noise.burstPercentage.bindToSpinBox(self.noiseBurstPercentageSb)
        noise.sourceDisplay.bindToEnumComboBox(self.noiseSourceDisplayCombo)

        # Arbitrary
        arbitrary = sr785.source.arbitrary
        arbitrary.amplitude.bindToSpinBox(self.arbitraryAmplitudeSb)
        arbitrary.playbackRate.bindToSpinBox(self.arbitraryPlaybackRateSb)
        arbitrary.buffer.bindToEnumComboBox(self.arbitrarySourceBufferCombo)

#        sr785.source.type.bindToEnumComboBox(self.sourceTypeCombo)
#        self.sourceTypeCombo.currentIndexChanged.connect(self.changeTab)
# This function isn't working
#    def changeTab(self):
#        sourceType = self.sourceTypeCombo.currentText()
#        if sourceType == 'sine':
#            self.sourceTab.setCurrentWidget(self.sourceTab.sineTab)
#        elif sourceType == 'chirp':
#            self.sourceTab.setCurrentWidget(self.sourceTab.chirpTab)
#        elif sourceType == 'noise':
#            self.sourceTab.setCurrentWidget(self.sourceTab.noiseTab)
#        elif sourceType == 'arbitrary':
#            self.sourceTab.setCurrentWidget(self.sourceTab.arbitraryTab)

    def tabChanged(self, index):
        text = self.sourceTab.tabText(index)
        if 'Sine' in text:
            self.sr785.source.type.code = self.sr785.source.type.SINE
        elif 'Chirp' in text:
            self.sr785.source.type.code = self.sr785.source.type.CHIRP
        elif 'Noise' in text:
            self.sr785.source.type.code = self.sr785.source.type.NOISE
        elif 'Arbitrary' in text:
            self.sr785.source.type.code = self.sr785.source.type.ARBITRARY

# Might want to restrict the scope of readAll because it might be too much
    def restoreSettings(self):
        #sr785.readAll()
        self.sr785.source.readAll()
# When does the above piece of code actually emit the command to use that type of source?

# Trying to disable tabs depending on what source type is requested. Might not be necessary if the above works well.
#    def tabsDisabled(self):
#        text = self.sourceTypeCombo.currentText()
#        if text == 'sine':
#            self.sourceTab.


if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    from SR785 import SR785
    #import sys

    visaResource = 'GPIB1::10'
    #visaResource = None
    sr785 = SR785(visaResource)
    #sr785 = None

    app = QApplication([])
    mainWindow = SR785_InputChannelGroupBox(sr785, 'B')
    #mainWindow = SR785_SourceGroupBox(sr785)
    mainWindow.show()
    sr785.readAll()
    app.exec_()
    #sys.exit(app.exec_())

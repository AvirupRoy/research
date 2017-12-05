# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 12:25:51 2017

@author: wisp10
"""
from __future__ import print_function
import textwrap
from PyQt4.QtGui import QWidget, QApplication, QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton, QComboBox, QCheckBox


def capitalizeFirst(string):
    r = string[0].upper() + string[1:]
    return r

def generateCode(boundWidgets):                
                
    code = ''
        
    for key in boundWidgets:
        name = key
        capName = capitalizeFirst(name)
        widget = boundWidgets[key]
        toolTip = str(widget.toolTip())
        if isinstance(widget, QDoubleSpinBox):
            unit = widget.suffix()
            minimum = widget.minimum()
            maximum = widget.maximum()
            decimals = widget.decimals()
            formatString = '%%.%df' % decimals
            minStr = formatString % minimum
            maxStr = formatString % maximum
            setterComment = 'Set the value of %s in units of%s (from %s to %s%s).' % (name, unit, minStr, maxStr, unit)
            getterComment = 'Get the value of %s (float).' % name
            elementType = 'setQuery'
        elif isinstance(widget, QSpinBox):
            minimum = widget.minimum()
            maximum = widget.maximum()
            setterComment = 'Set the value of %s (int from %d to %d).' % (name, minimum, maximum)
            getterComment = 'Get the value of %s (int).' % name
            elementType = 'setQuery'
        elif isinstance(widget, QLineEdit):
            setterComment = 'Set %s (string).' % (name)
            getterComment = 'Return the string for %s.' % (name)
            elementType = 'setQuery'
        elif isinstance(widget, QComboBox):
            choices = []
            setterComment = 'Select %s with choices of %s.' % (name, choices)
            getterComment = 'Return the choice for %s.' % (name)
            elementType = 'setQuery'
        elif isinstance(widget, QCheckBox):
            setterComment = 'Enable (or disable) %s.' % name
            getterComment = 'Return True if %s is enabled.' % name
            elementType = 'OnOff'
        elif isinstance(widget, QPushButton):
            setterComment = ''
            getterComment = ''
            elementType = 'button'
        else:
            print('Name:', name, 'has unsupported type', type(widget))
            continue
        
        if len(toolTip) > 0:
            setterComment += '\n\t\t\n'
            setterComment += "\t\tTooltip for %s:\n\t\t" % name
            toolTipLines = textwrap.wrap(toolTip, width=80-2*4)
            setterComment += '\n\t\t'.join(toolTipLines)
            #for line in toolTipLines:
            #    setterComment += '\t\t' + line + '\n'
    
        if elementType == 'setQuery':        
            code += "\tdef set%s(self, %s):\n" % (capName, name)
            code += "\t\t'''%s'''\n" % setterComment
            code += "\t\tself._setValue('%s', %s)\n" % (name, name)
            code += "\n"
            code += "\tdef %s(self):\n" % (name)
            code += "\t\t'''%s'''\n" % getterComment
            code += "\t\treturn self._queryValue('%s')\n" % (name)
            code += "\n"
        elif elementType == 'OnOff':
            code += "\tdef enable%s(self, enable=True):\n" % (capName)
            code += "\t\t'''%s'''\n" % setterComment
            code += "\t\tself._setValue('%s', enable)\n" % (name)
            code += "\n"
            code += "\tdef disable%s(self):\n" % (capName)
            code += "\t\t'''Disable %s'''\n" % (name)
            code += "\t\tself.enable%s(False)\n" % (capName)
            code += "\n"
            code += "\tdef is%s(self):\n" % (capName)
            code += "\t\t'''%s'''\n" % getterComment
            code += "\n"
        elif elementType == 'button':
            code += "\tdef %s(self):\n" % (name)
            code += "\t\t'''%s'''\n" % setterComment
            code += "\t\tself._clickButton('%s')\n" % (name)
            code += "\n"
            code += "\tdef is%s(self):\n" % (capName)
            code += "\t\t'''%s'''\n" % getterComment
            code += "\t\tself._isEnabled('%s')\n" % (name)
            code += "\n"
    return code

if __name__ == '__main__':
    import TES.MultiLockinUi as ui
    
    class DummyWidget(ui.Ui_Form, QWidget):
        def __init__(self, parent = None):
            super(DummyWidget, self).__init__(parent)
            self.setupUi(self)
            
    
    app = QApplication([])
    widget = DummyWidget()        
    
    self = widget
    boundWidgets = {'sample': self.sampleLe, 'comment': self.commentLe,
                    'samplingRate': self.sampleRateSb, 'decimation': self.inputDecimationCombo,
                    'rampRate': self.rampRateSb, 'offset':self.offsetSb,
                    'dcBw': self.dcBwSb, 'dcFilterOrder': self.dcFilterOrderSb,
                    'saveRawData': self.saveRawDataCb, 'saveRawDemod': self.saveRawDemodCb,
                    'aiChannel': self.aiChannelCombo, 'aiRange': self.aiRangeCombo,
                    'aiTerminalConfig': self.aiTerminalConfigCombo,
                    'start': self.startPb, 'stop': self.stopPb}
                    
    code = generateCode(boundWidgets)
    print('Generated code:')
    code.replace('\t', '     ')
    print(code)

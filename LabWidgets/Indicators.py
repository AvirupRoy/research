# -*- coding: utf-8 -*-
"""
Created on Wed Oct 07 14:29:32 2015

@author: wisp10
"""

from math import log10,pow,floor

from PyQt4.QtGui import QLineEdit, QSizePolicy, QFont
from PyQt4.QtCore import Qt, QSize, pyqtSignal

# @author Felix Jaeckel
# @email fxjaeckel@gmail.com

from PyQt4.QtCore import pyqtProperty, pyqtSignal, QSize, QString, QPoint, Qt
from PyQt4.QtGui import QWidget, QColor, QPixmap, QPixmapCache, QPainter, QRadialGradient, QPen

class LedIndicator(QWidget):
	valueChanged = pyqtSignal(bool)
	
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self._value = False
		self._color = QColor(Qt.red)
		
	@pyqtProperty(QColor)
	def color(self):
		return self._color
			
	#@color.setter
	def setColor(self, newColor):
		if (newColor == self._color):
			return
		oldKey = self.generateKey()
		QPixmapCache.remove(oldKey)
		self._color = QColor(newColor)
		self.update()
		
	def value(self):
		return self._value
		
	def setValue(self, newValue):
		if self._value != newValue:
			self._value = newValue;
			self.update()
			self.valueChanged.emit(self._value)
			
	def toggle(self):
		self.setValue(not self._value)
		
	def turnOn(self):
		self.setValue(True)
		
	def turnOff(self):
		self.setValue(False)

	def generateKey(self):
		# Because of the centering code below, both w and h are characteristics for the pixmap.
		return QString("QlxLed:%1:%2:%3:%4").arg(self._color.name()).arg(self.width()).arg(self.height()).arg(self._value)
	
	def sizeHint(self):
		return QSize(24, 24)
	
	def minimumSizeHint(self):
		return QSize(12, 12)
		
	def heightForWidth(self, width):
		return width

	def paintEvent(self, event):
		w = self.width();
		h = self.height();
		s = min(w, h);

		key = self.generateKey();
		pixmap = QPixmapCache.find(key)
		if not pixmap:
#			print "Generating pixmap"
			pixmap = QPixmap(w,h);
			pixmap.fill(self, QPoint(0,0)) # Fill pixmap with widget background

			pixPainter = QPainter(pixmap)
			pixPainter.setRenderHint(QPainter.Antialiasing)

			# Offsets for centering
			ox = int(0.5*(w-s))
			oy = int(0.5*(h-s));

			insideColor = self._color
			if not self._value:
				insideColor = insideColor.darker(250);
			gradient = QRadialGradient(ox+0.5*s, oy+0.5*s, 0.5*s);
			gradient.setColorAt(0.2, insideColor);
			gradient.setColorAt(0.6, insideColor.darker(120));
			gradient.setColorAt(1.0, insideColor.darker(160));
			pixPainter.setBrush(gradient);
			pixPainter.setPen(QPen(Qt.black,2));
			pixPainter.drawEllipse(1+ox, 1+oy, s-2, s-2);
			pixPainter.end()
			QPixmapCache.insert(key, pixmap)
		
		p = QPainter()
		p.begin(self)
		p.drawPixmap(QPoint(0,0), pixmap)
		p.end()

#class QlxLedPlugin(QPyDesignerCustomWidgetPlugin):
#	def __init__(self, parent = None):
#		QPyDesignerCustomWidgetPlugin.__init__(self)
#		self.initialized = False

#	def initialize(self, formEditor):
#		if self.initialized:
#			return
#	self.initialized = True

#	def createWidget(self, parent):
#		return QlxLed(parent)

#	def name(self):
#		return "QlxLed"

#	def includeFile(self):
#		return "QlxWidgets.QlxLed"


class Indicator(QLineEdit):
    def __init__(self, *args, **kwargs):
        QLineEdit.__init__(self, *args, **kwargs)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignRight)
        self.setValue(None)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        font = QFont("Courier New",12, QFont.Bold,False)
        self.setFont(font)


    def sizeHint(self):
        fm = self.fontMetrics()
        h = QLineEdit.sizeHint(self).height()
        w = fm.width(self.sizeHintString())
        return QSize(w+10, h+6)

class TextIndicator(Indicator):
    def sizeHintString(self):
        return 'ABCDEFGHIJKLMOPQRST'

    def setValue(self, text):
        if text is None:
            text = 'N/A'
        self.setText(text)

class FloatIndicator(Indicator):
    def __init__(self, *args, **kwargs):
        self.setFormatString('%.4f')
        Indicator.__init__(self, *args, **kwargs)

    def setValue(self, value):
        self.setText(self.stringForValue(value))

    def sizeHintString(self):
        return self.stringForValue(-1E7/3)

    def setFormatString(self, string):
        self.formatString = string

    def stringForValue(self, value):
        if value is None:
            value = float('nan')
        return self.formatString % value

class MixedUnitsIndicator(Indicator):
    pass

class EngineeringIndicator(Indicator):
    def __init__(self, *args, **kwargs):
        Indicator.__init__(self, *args, **kwargs)
        self.unit = ''
        self.precision = 3

    def sizeHintString(self):
        return self.stringForValue(-999E6)

    def setPrecision(self, precision):
        self.precision = precision

    def setUnit(self, unit):
        self.unit = unit

    def enableSign(self, enable=True):
        self.sign = True

    def stringForValue(self, value):
        if value is None:
            return 'N/A'
        SI = {-8:'y', -7:'z',-6:'a',-5:'f', -4:'p',-3:'n',-2:u'μ', -1:'m', 0:' ',1: 'k', 2: 'M', 3: 'G', 4:'T', 5:'P', 6:'E', 7:'Z', 8:'Y'}
        if value != 0:
            decade = int(floor(log10(abs(value))/3))
        else:
            decade = 0
        if SI.has_key(decade):
            prefix = SI[decade]
            formatString = '%%.%df %s%s' % (self.precision, prefix, self.unit)
            return formatString % (value*pow(10,-decade*3))
        else:
            formatString = '%%.%dg' % (self.precision)
            return formatString % value


    def setValue(self, value):
        self.setText(self.stringForValue(value))

class TemperatureIndicator(Indicator):
    def __init__(self, *args, **kwargs):
        Indicator.__init__(self, *args, **kwargs)
        self.setUnit('K')
        self.precision = 3
        self.setKelvin(None)

    def setUnit(self, unit):
        if unit == 'C':
            self.suffix = u' °C'
        elif unit == 'K':
            self.suffix = ' K'
        elif unit == 'F':
            self.suffix = ' °F'
        else:
            raise Exception('Unsupported unit')
        self.unit = unit

    def enableConversion(self, enable=True):
        self.conversion = enable

    def setPrecision(self, precision):
        self.precision = precision

    def setCelsius(self, celsius):
        if celsius is None:
            self.setKelvin(None)
        else:
            self.setKelvin(celsius+273.15)

    def setValue(self, kelvin):
        self.setKelvin(kelvin)

    def setKelvin(self, kelvin):
        self.setText(self.stringForValue(kelvin))

    def sizeHintString(self):
        return self.formatCelsius(-300.5616434)

    def stringForValue(self, kelvin):
        if kelvin is None:
            return 'N/A'
        if self.unit == 'K':
            return self.formatKelvin(kelvin)
        elif self.unit == 'C':
            return self.formatCelsius(kelvin)
        elif self.unit == 'F':
            return self.formatFahrenheit(kelvin)

    def formatCelsius(self, kelvin):
        celsius = kelvin-273.15
        formatString = u'%%+.%df °C' % self.precision
        return formatString % celsius

    def formatFahrenheit(self, kelvin):
        fahrenheit = kelvin*9./5.-459.67
        formatString = u'%%+.%df °F' % self.precision
        return formatString % fahrenheit

    def formatKelvin(self, kelvin):
        if kelvin < 1E-6:
            suffix = 'nK'
            mult = 1E9
        elif kelvin < 1E-3:
            suffix = u'μK'
            mult = 1E6
        elif kelvin < 1:
            suffix = 'mK'
            mult = 1E3
        else:
            suffix = ' K'
            mult = 1.
        formatString = '%%.%df %s' % (self.precision, suffix)
        return formatString % (mult*kelvin)

class PercentIndicator(Indicator):
    def __init__(self, *args, **kwargs):
        Indicator.__init__(self, *args, **kwargs)
        self.setPrecision(1)
        self.setReadOnly(True)
        self.setPercentage(None)
        self.setAlignment(Qt.AlignRight)

    def sizeHintString(self):
        return self.stringForValue(800.1251)

    def setPrecision(self, precision):
        self.precision = precision
        self.formatString = '%%.%df %%%%' % precision

    def stringForValue(self, percent):
        if percent is None:
            return 'N/A'
        else:
            return self.formatString % percent

    def setValue(self, percent):
        self.setPercentage(percent)

    def setPercentage(self, percent):
        self.setText(self.stringForValue(percent))

    def setFraction(self, fraction):
        self.setPercentage(1E2*fraction)

import re
from PyQt4.QtGui import QValidator,QDoubleSpinBox

_float_re = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')

def valid_float_string(string):
    match = _float_re.search(string)
    return match.groups()[0] == string if match else False


class FloatValidator(QValidator):

    def validate(self, string, position):

        string=str(string)

        if valid_float_string(string):

            return (QValidator.Acceptable, position)
        if string == "" or string[position-1] in 'e.-+':
            return (QValidator.Intermediate, position)

        return(QValidator.Invalid, position)

    def fixup(self, text):
        match = _float_re.search(text)
        return match.groups()[0] if match else ""

class MixedUnitsDoubleSpinBox(QDoubleSpinBox):
    valueChangedSI = pyqtSignal(float)

    def __init__(self, toSIFactor=1):
        super(MixedUnitsDoubleSpinBox,self).__init__(*args, **kwargs)
        self.toSIFactor = toSIFactor
        self.valueChanged.connect(self._valueChanged)

    def setToSIFactor(self, toSIFactor):
        self.toSIFactor = toSIFactor

    def _valueChanged(self, value):
        self.valueChangedSI = value * self.toSIFactor

    def valueSI(self):
        return self.value() * self.toSIFactor

    def setValueSI(self, valueSI):
        self.setValue(value*self.scaleFactor)


class ScientificDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super(ScientificDoubleSpinBox,self).__init__(*args, **kwargs)
        self.setMinimum(1.e-18)
        self.setMaximum(1.e+18)
        self.validator = FloatValidator()
        self.setDecimals(1000)

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        return float(text)

    def textFromValue(self, value):
        return format_float(value)

    def stepBy(self, steps):
        text = self.cleanText()
        groups = _float_re.search(text).groups()
        decimal = float(groups[1])
        decimal += steps
        new_string = "{:g}".format(decimal) + (groups[3] if groups[3] else "")
        self.lineEdit().setText(new_string)

def format_float(value):
    """Modified form of the 'g' format specifier."""
    string = "{:g}".format(value).replace("e+", "e")
    string = re.sub("e(-?)0*(\d+)", r"e\1\2", string)
    return string

from PyQt4 import QtGui
from PyQt4.QtCore import QSettings, QString

class LabWidget(object):
    '''This is obsolete.'''
#    def __init__(self, parent=None):
#        QMainWindow.__init__(self, parent)
    def restoreSettings(self):
        s = QSettings()
        self.restoreGeometry(s.value("geometry").toByteArray())
        #self.restoreState(s.value("windowState").toByteArray())
        self._doRestoreSettings(s, self)

    def _doRestoreSettings(self, s, widget):
        print "Looking at children of:", widget
        children = widget.children()
        print children
        for child in children:
            print "Working on:", child
            name = child.objectName()
            if isinstance(child, QtGui.QAbstractSlider) or isinstance(child, QtGui.QSpinBox):
                child.setValue( s.value(name, child.value(), type=int) )
            elif isinstance(child, QtGui.QDoubleSpinBox):
                child.setValue( s.value(name, child.value(), type=float) )
            elif isinstance(child, QtGui.QPlainTextEdit):
                child.setPlainText( s.value(name, child.toPlainText(), type=QString) )
            elif isinstance(child, QtGui.QTextEdit) or isinstance(child, QtGui.QLineEdit):
                child.setText( s.value(name, child.text(), type=QString) )
            elif isinstance(child, QtGui.QComboBox):
                i = child.findText( s.value(name, child.currentText(), type=QString) )
                child.setCurrentIndex(i)
            elif isinstance(child, QtGui.QAbstractButton):
                child.setChecked( s.value(name, child.isChecked(), type=bool) )
            elif isinstance(child, QtGui.QGroupBox):
                child.setChecked( s.value(name, child.isChecked(), type=bool) )
                self._doRestoreSettings(s, child)
            elif isinstance(child, QtGui.QWidget):
                self._doRestoreSettings(s, child)
            else:
                print"Can't deal with %s" % child
                continue

    def saveSettings(self):
        s = QSettings()
        s.setValue("geometry", self.saveGeometry())
        #s.setValue("windowState", self.saveState())
        self._doSaveSettings(s, self)

    def _doSaveSettings(self, s, widget):
        print "Looking at children of:", widget
        children = widget.children()
        print children
        for child in children:
            name = child.objectName()
            if isinstance(child, QtGui.QAbstractSlider) or isinstance(child, QtGui.QAbstractSpinBox):
                s.setValue(name, child.value())
            elif isinstance(child, QtGui.QPlainTextEdit):
                s.setValue(name, child.toPlainText())
            elif isinstance(child, QtGui.QTextEdit) or isinstance(child, QtGui.QLineEdit):
                s.setValue(name, child.text())
            elif isinstance(child, QtGui.QComboBox):
                s.setValue(name, child.currentText())
            elif isinstance(child, QtGui.QAbstractButton):
                s.setValue(name, child.isChecked())
            elif isinstance(child, QtGui.QGroupBox):
                s.setValue(name, child.isChecked())
                self._doSaveSettings(s, child)
            elif isinstance(child, QtGui.QWidget):
                self._doSaveSettings(s, child)
            else:
                print"Can't deal with %s" % child

    def closeEvent(self, event):
        self.saveSettings()
        print "SUper:", super(LabWidget, self)
        #super(LabWidget,self).closeEvent(event)

if __name__ == '__main__':
    import sys
    from PyQt4.QtCore import QTimer
    from PyQt4.QtGui import *

    app = QApplication(sys.argv)
    dialog = QDialog()

    layout = QVBoxLayout()
    scientificSb = ScientificDoubleSpinBox()
    scientificSb.setMinimum(-1E24)
    scientificSb.setMaximum(1E24)
    layout.addWidget(scientificSb)
    engineeringIndicator = EngineeringIndicator()
    engineeringIndicator.setUnit(u'Ω')
    layout.addWidget(engineeringIndicator)
    percentIndicator = PercentIndicator()
    layout.addWidget(percentIndicator)

    temperatureIndicator = TemperatureIndicator()
    temperatureIndicator.setUnit('K')
    layout.addWidget(temperatureIndicator)

    led1 = LedIndicator()
    led1.setColor(Qt.green)
    led1.turnOn()
    led2 = LedIndicator()
    led2.setColor(Qt.red)
    led2.turnOff()
    layout.addWidget(led1)
    layout.addWidget(led2)

        
    
    timer = QTimer()
    timer.timeout.connect(led1.toggle)
    timer.timeout.connect(led2.toggle)
    timer.start(100)

    subLayout = QGridLayout()
    columns = 25
    rows = 29
    for i in range(columns*rows):
        led = LedIndicator()
        led.setValue(bool(i%2))
        column = i % columns
        row = int(i/columns)
        led.setColor(QColor((row+1)*int(255./rows), 255-i%255, (columns-column)*int(255./columns)))
        subLayout.addWidget(led, row, column)
        timer.timeout.connect(led.toggle)
    layout.addLayout(subLayout)

    scientificSb.valueChanged.connect(percentIndicator.setPercentage)
    scientificSb.valueChanged.connect(engineeringIndicator.setValue)
    scientificSb.valueChanged.connect(temperatureIndicator.setKelvin)

    dialog.setLayout(layout)
    dialog.show()
    sys.exit(app.exec_())

# -*- coding: utf-8 -*-
"""
Created on Thu Dec 03 12:03:11 2015
Collection of Settings classes that facilitate mapping of instrument settings to
Python classes supporting signal emission on change, automated binding to GUI elements
@author: wisp10
"""

from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
from LabWidgets.SilentWidgets import EnumComboBox, SilentCheckBox, SilentGroupBox, SilentSpinBox, SilentDoubleSpinBox
import weakref
class Setting(QObject):
    '''Base class for all settings, providing basic caching interface'''
    def __init__(self, instrument, caching=False):
        QObject.__init__(self, parent = instrument)
#        super(Setting, self).__init__()
        self._instrument = weakref.ref(instrument)
        self.caching = caching

    @property
    def instrument(self):
        return self._instrument()
        
    @property
    def caching(self):
        return self._caching

    @caching.setter
    def caching(self, enable):
        self._caching = enable

    def __str__(self):
        return "Setting(bound to %s)" % str(self.instrument)        

import re

class EnumSetting(Setting):
    '''Represents enumerated settings, like e.g. input coupling settings.'''
    
    changed = pyqtSignal(float, bool)

    def __init__(self, command, longName, choices, instrument = None, queryString = None, caching=False, toolTip = None):
        #super(EnumSetting, self).__init__(instrument, caching)
        Setting.__init__(self, instrument, caching)
        self.command = command
        if queryString is None:
            self.queryString = '%s?' % self.command
        else:
            self.queryString = queryString
        self.longName = longName
        self.codes = [x[0] for x in choices]
        self.strings = [x[1] for x in choices] # @todo This is not right
        self.toolTip = toolTip
        self._code = None
        for choice in choices:
            print "Choice:", choice
            code = choice[0]
            if len(choice) > 2:
                label = choice[2]
            else:
                label = re.sub('\W|^(?=\d)','_', choice[1]).upper()
            setattr(self, label, code)

    @property
    def code(self):
        if not self.caching or self._code is None:
            if self.instrument is None:
                raise Exception("Unable to execute query!")
            self._code = self.instrument.queryInteger(self.queryString)
        self.changed.emit(self._code, False)
        return self._code

    @code.setter
    def code(self, newCode):
        if newCode in self.codes:
            if self.instrument:
                self.instrument.commandInteger(self.command, newCode)
            else:
                raise Exception("No instrument object->can't execute command...")
            self._code = newCode
            self.changed.emit(newCode, True)
        else:
            raise Exception("Unsupported code")

    @pyqtSlot(float)
    def change(self, newCode):
        self.code = newCode

    @property
    def string(self):
        return self.strings[self.code]
        
    def populateEnumComboBox(self, enumCombo):
        enumCombo.clear()
        for i,code in enumerate(self.codes):
            enumCombo.addItem(self.strings[i], code)

    def bindToEnumComboBox(self, enumCombo, allowWrite=True):
        if not isinstance(enumCombo, EnumComboBox):
            raise Exception('Need an instance of EnumComboBox')
        self.changed.connect(enumCombo.setCurrentCodeSilently)
        self.populateEnumComboBox(enumCombo)
        enumCombo.currentCodeChanged.connect(self.change)
        if self.toolTip != None:
            enumCombo.setToolTip(self.toolTip)

    def __str__(self):
        return "%s EnumSetting (bound to %s)" % (self.longName, str(self.instrument))

            
import numpy as np
class NumericEnumSetting(EnumSetting):
    def __init__(self, command, longName, valueChoices, instrument = None, unit='', caching=False, toolTip = None):
#        super(EnumSetting, self).__init__(command, longName, [], instrument, caching)
        self.toolTip = toolTip
        stringChoices = []
        self.values = {}
        values = []
        for choice in valueChoices:
            code = choice[0]
            value = choice[1]
            string = '%g %s' % (value, unit)
            stringChoices.append( (code, string) )
            self.values[code] = value
            values.append(value)
        EnumSetting.__init__(self, command=command, longName=longName, choices=stringChoices, instrument=instrument, caching=caching, toolTip=toolTip)
        self.min = np.min(values)
        self.max = np.max(values)
        
    @property        
    def value(self):
        return self.values[self.code]
        
    @property
    def string(self):
        return str(self.value)

class NumericSetting(Setting):
    '''Base class for numeric settings. Don't normally use directly.'''
    
    def __init__(self, command, longName, minimum, maximum, unit = '', instrument = None, queryString = None, toolTip = None, caching=True):
        '''Construct a numberic setting with a specified command, minimum and maximum values, a unit label.
            command: The basic command that should be exectued on the VISA instrument. By default, the query command will be "command?"
        
        Optional arguments are:
            queryString: You can specify this if the query command for the instrument is not the usual "command?"
            toolTip:     Tool-tip to be associated with widget.
        '''
        super(NumericSetting, self).__init__(instrument, caching)
#        Setting.__init__(self, instrument)
        self.min = minimum
        self.max = maximum
        self.unit = unit
        self.longName = longName
        self.commandTemplate = '%s %%d' % command
        self.toolTip = toolTip
        if queryString is None:
            self.queryTemplate = '%s?' % command
        else:
            self.queryTemplate = queryString
        self._value = None

    @property
    def value(self):
        if not self.caching or self._value is None:
            if self.instrument is None:
                raise Exception("Unable to execute query!")
            self._value = self.instrument.queryInteger(self.queryTemplate)
            self.changed.emit(self._value, False)
        return self._value

    @value.setter
    def value(self, newValue):
        '''Set this property to a new value'''
        if newValue < self.min or newValue > self.max:
            raise Exception('Parameter %s out of range' % self.longName)
        if self.instrument is None:
            raise Exception('No instrument, cannot execute command...')

        self.instrument.commandString(self.commandTemplate % newValue)
        self._value = newValue # FJ added 2016-06-27

    @pyqtSlot()
    def maximize(self):
        '''Set this setting to its maximum value'''
        self.value = self.max

    @pyqtSlot()
    def minimize(self):
        '''Set this setting to its minimum value'''
        self.value = self.min

    @property
    def string(self):
        return str(self.value)

    def __str__(self):
        return "%s NumericSetting (bound to %s)" % (self.longName, str(self.instrument))


class IntegerSetting(NumericSetting):
    '''A numeric setting that will only accept integer values. This will bind to QSpinBox.'''
    changed = pyqtSignal(int, bool)
    '''Signal emitted when the value of this setting has changed.'''

    def configureSpinBox(self, spinBox):
        spinBox.setMinimum(self.min)
        spinBox.setMaximum(self.max)
        spinBox.setSuffix(self.unit)
        if self.toolTip != None:
            spinBox.setToolTip(self.toolTip)

    @pyqtSlot(int)
    def change(self, value):
        self.value = value

    def bindToSpinBox(self, spinBox):
        self.configureSpinBox(spinBox)
        if not spinBox.isReadOnly():
            spinBox.valueChanged.connect(self.change)
        if isinstance(spinBox, SilentSpinBox):
            self.changed.connect(spinBox.setValueSilently)

    def __str__(self):
        return "%s IntegerSetting (bound to %s)" % (self.longName, str(self.instrument))

from numpy import deg2rad, rad2deg

class AngleSetting(Setting):
    '''Base class for numeric settings. Don't normally use directly.'''
    changedRadians = pyqtSignal(float, bool)
    changedDegrees = pyqtSignal(float, bool)
    
    def __init__(self, command, longName, instrumentUnits = 'deg', step = 0.1, decimals=2, instrument = None, queryString = None, toolTip = None, caching=True):
        '''Construct a numberic setting with a specified command, minimum and maximum values, a unit label.
            command: The basic command that should be exectued on the VISA instrument. By default, the query command will be "command?"
        
        Optional arguments are:
            queryString: You can specify this if the query command for the instrument is not the usual "command?"
            toolTip:     Tool-tip to be associated with widget.
        '''
        super(NumericSetting, self).__init__(instrument, caching)
#        Setting.__init__(self, instrument)
        if 'rad' in instrumentUnits:
            self._instrumentRad = True
        elif 'deg' in instrumentUnits:
            self._instrumentRad = False
        else:
            raise Exception('Unknown instrument units')
        self.longName = longName
        self.commandTemplate = '%s %%f' % command
        self.toolTip = toolTip
        self.decimals = decimals
        self.step = step
        if queryString is None:
            self.queryTemplate = '%s?' % command
        else:
            self.queryTemplate = queryString
        self._value = None

    @property
    def value(self):
        '''Return the angle in instrument units'''
        if not self.caching or self._value is None:
            if self.instrument is None:
                raise Exception("Unable to execute query!")
            self._value = self.instrument.queryFloat(self.queryTemplate)
            if self._instrumentRad:
                rad = self._value
                deg = rad2deg(rad)
            else:
                deg = self._value
                rad = deg2rad(deg)
            self.changedRadians.emit(rad, False)
            self.changedDegrees.emit(deg, False)
        return self._value

    @value.setter
    def value(self, newValue):
        '''Set the angle in instrument units'''
        if newValue < self.min or newValue > self.max:
            raise Exception('Parameter %s out of range' % self.longName)
        if self.instrument is None:
            raise Exception('No instrument, cannot execute command...')

        self.instrument.commandString(self.commandTemplate % newValue)
        if self._instrumentRad:
            rad = newValue
            deg = rad2deg(rad)
        else:
            deg = newValue
            rad = deg2rad(deg)
        self.changedRadians.emit(rad, True)
        self.changedDegrees.emit(deg, True)
                
    @property
    def radian(self):
        if self._instrumentRad:
            return self.value
        else:
            return rad2deg(self.value)
            
    @radian.setter
    def radian(self, newAngle):
        if self._instrumentRad:
            self.value = newAngle
        else:
            self.value = rad2deg(newAngle)
    
    @property
    def degree(self):
        if self._instrumentRad:
            return rad2deg(self.value)
        else:
            return self.value
    
    @degree.setter
    def degree(self, newAngle):
        if self._instrumentRad:
            self.value = deg2rad(newAngle)
        else:
            self.value = newAngle

    @pyqtSlot(float)
    def changeDegree(self, value):
        self.degree = value

    @pyqtSlot(float)
    def changeRadians(self, value):
        self.radians = value

    def bindToSpinBox(self, spinBox, rad=False):
        '''Bind this setting to a QDoubleSpinBox and set minimum and maximum
        values, as well as resolution and tool-tip (if given). 
        The scale parameter is currently ignored, but could be used if the GUI
        element would have different units than the instrument.'''
        if rad:
            unit = 'rad'
            maximum = 2*np.pi
        else:
            unit = 'deg'
            maximum = 360
        spinBox.setSuffix(' %s' % unit)
        
        spinBox.setMaximum(maximum)
        spinBox.setMinimum(-maximum)

        spinBox.setWrapping(True)
        
        if self.decimals is not None:
            spinBox.setDecimals( self.decimals )
            
        spinBox.setSingleStep(self.step)
        if not spinBox.isReadOnly():
            if rad:
                spinBox.valueChanged.connect(self.changeRadians)
            else:
                spinBox.valueChanged.connect(self.changeDegree)
            
        if isinstance(spinBox, SilentDoubleSpinBox):
            if rad:
                self.changedRadians.connect(spinBox.setValueSilently)
            else:
                self.changedDegrees.connect(spinBox.setValueSilently)
                
        if self.toolTip != None:
            spinBox.setToolTip(self.toolTip)

    def __str__(self):
        return "%s AngleSetting (bound to %s)" % (self.longName, str(self.instrument))

class FloatSetting(NumericSetting):
    '''A numeric setting that will accept floating point values. This will bind to QDoubleSpinBox.'''
    changed = pyqtSignal(float, bool)
    '''Signal emitted when the value of this setting has changed.'''

    def __init__(self, command, longName, minimum, maximum, unit, step, decimals, instrument = None, queryString = None, toolTip = None):
        super(FloatSetting, self).__init__(command, longName, minimum, maximum, unit, instrument, queryString, toolTip)
#        NumericSetting.__init__(self, command, longName, minimum, maximum, unit, instrument, queryString, toolTip)
        self.min = minimum
        self.max = maximum
        self.unit = unit
        self.step = step
        self.decimals = decimals
        self.commandTemplate = '%s %%f' % command
        self.toolTip = toolTip

        self._value = None

    @property
    def value(self):
        if not self.caching or self._value is None:
            if self.instrument is None:
                raise Exception("Unable to execute query!")
            self._value = self._queryValue()
            self.changed.emit(self._value, False)
        return self._value

    def _queryValue(self):
        return self.instrument.queryFloat(self.queryTemplate)

    @value.setter
    def value(self, newValue):
        if newValue < self.min or newValue > self.max:
            raise Exception('Parameter %s out of range' % self.longName)
        if self.instrument is None:
            raise Exception('No instrument, cannot execute command...')

        print "instrument:", self.instrument, type(self.instrument)
        self.instrument.commandString(self.commandTemplate % newValue)
        self._value = newValue
        self.changed.emit(newValue, True)
        
    def configureSpinBox(self, spinBox):
        spinBox.setMinimum(self.min)
        spinBox.setMaximum(self.max)
        if self.decimals is not None:
            spinBox.setDecimals( self.decimals )
        spinBox.setSingleStep(self.step)
        if len(self.unit):
            spinBox.setSuffix(' %s' % self.unit)
        if self.toolTip != None:
            spinBox.setToolTip(self.toolTip)

    @pyqtSlot(float)
    def change(self, value):
        self.value = value

    def bindToSpinBox(self, spinBox, scale=1.):
        '''Bind this setting to a QDoubleSpinBox and set minimum and maximum
        values, as well as resolution and tool-tip (if given). 
        The scale parameter is currently ignored, but could be used if the GUI
        element would have different units than the instrument.'''
        self.configureSpinBox(spinBox)
        if not spinBox.isReadOnly():
            spinBox.valueChanged.connect(self.change)
        if isinstance(spinBox, SilentDoubleSpinBox):
            self.changed.connect(spinBox.setValueSilently)

    def __str__(self):
        return "%s FloatSetting (bound to %s)" % (self.longName, str(self.instrument))

class OnOffSetting(Setting):
    '''A enabled/disabled type setting.'''
    changed = pyqtSignal(bool, bool)
    '''Signal emitted when this setting has been changed.
    The first parameter indicates the new state. The second parameter is 
    False if this signal was emitted as the result of a "read" operation on the
    instrument. If it results from a write, it is True.'''
    
    def __init__(self, command, longName, instrument = None, queryString = None, caching=False, toolTip = None):
        Setting.__init__(self, instrument, caching)
        self.command = command
        self.longName = longName
        self.toolTip = toolTip
        self._enabled = None
        if queryString is None:
            self.queryString = '%s?' % self.command
        else:
            self.queryString = queryString

    @property
    def enabled(self):
        if not self.caching or self._enabled is None:
            self._enabled = self.instrument.queryBool('%s' % self.queryString)
        self.changed.emit(self._enabled, False)
        return self._enabled

    @enabled.setter
    def enabled(self, enable):
        self.instrument.commandBool(self.command, enable)
        self.changed.emit(enable, True)
        self._enabled = enable

    @property
    def disabled(self):
        return ~self.enabled

    @disabled.setter
    def disabled(self, disable):
        self.enabled = ~disable

    @pyqtSlot(bool)
    def enable(self, enable=True):
        self.enabled = enable

    @pyqtSlot(bool)
    def disable(self, disable=True):
        self.enabled = ~disable
        
    @property
    def string(self):
        return str(self.enabled)

    def bindToCheckBox(self, checkableWidget, allowWrite=True):
        if not (isinstance(checkableWidget, SilentCheckBox) or isinstance(checkableWidget, SilentGroupBox)):
            raise Exception('Need a SilentCheckBox')
        self.changed.connect(checkableWidget.setChecked)
        if allowWrite:
            checkableWidget.checkStateChanged.connect(self.enable)

    def __str__(self):
        return "%s OnOffSetting (bound to %s)" % (self.longName, str(self.instrument))

class SettingCollection(object):
    '''A class to group together multiple Settings. Use this if you want
    to perform logic groupling of your settings, like e.g. in the SR785, where
    source, input, etc. are grouped together.
    Provides functionality to iterate through the settings tree. Perhaps this
    can be simplified eliminated or generalized in the future'''
    def __iter__(self):
        for attr, value in self.__dict__.iteritems():
            yield attr, value

    @property
    def caching(self):
        pass

    @caching.setter
    def caching(self, enable):
        if enable:
            text = "Enabling"
        else:
            text = "Disabling"
        for name,i in self:
            if isinstance(i, Setting):
                print "%s caching on:" % text, i
                i.caching = enable
            elif isinstance(i, SettingCollection):
                i.caching = enable
                print "Entering collection:", i

    def readAll(self):
        for name,i in self:
            if isinstance(i, NumericSetting):
                i.value
            elif isinstance(i, EnumSetting):
                i.code
            elif isinstance(i, OnOffSetting):
                i.enabled
            elif isinstance(i, SettingCollection):
                i.readAll()
            elif isinstance(i, list):
                for k in i:
                    if isinstance(k, SettingCollection):
                        k.readAll()

#from Visa.SR785.VisaInstrument import VisaInstrument

class InstrumentWithSettings():
    def __iter__(self):
        for attr, value in self.__dict__.iteritems():
            yield attr, value

    def enableCaching(self, enable=True):
        print "Iterating..."
        if enable:
            text = "Enabling"
        else:
            text = "Disabling"
        for name,i in self:
            if isinstance(i, Setting):
                print "%s caching on:" % text, i
                i.caching = enable
            elif isinstance(i, SettingCollection):
                print "Entering collection:", i
                i.caching = enable
            else:
                print i, type(i)

    def allSettingValues(self):
        '''This currently only works for flat classes'''
        r = {}
        for name,item in self:
            if isinstance(item, Setting):
                r[name] = item.string
        return r
        
    def disableCaching(self):
        self.enableCaching(False)

if __name__ == '__main__':
    class TestInstrument:
        pass
    enum = EnumSetting('ENUMCMD', 'testCommand', [(1, 'on'), (2, 'off')], None)
    nEnum = NumericEnumSetting('ENUMCMD', 'tesCommand', [(1,10.), (2, 0.1), (3, 0.2)], unit='g', caching=True, toolTip='Bla')
    nEnum
    
    
    
#class Test(QObject):
#    changed = pyqtSignal(int, bool)
#
#    @property
#    def code(self):
#        if not self.caching or self._code is None:
#            try:
#                self._code = self.instrument.queryInt('%s?' % self.command)
#            except:
#                self._code = None
#        self.changed.emit(self._code, False)
#        return self._code
#
#    @code.setter
#    def code(self, code):
#        if code in self.codes:
#            if self.instrument:
#                self.instrument.commandInteger(self.command, code)
#            else:
#                raise "No instrument object->can't execute query..."
#            self._code = code
#            print "Code now:", self._code
#            self.changed.emit(code, True)
#        else:
#            raise "Unsupported code"
#
#    @pyqtSlot(int)
#    def change(self, code):
#        self._code = code
#
#    @property
#    def string(self):
#        return self.strings[self.code]
#
#    def __init__(self, command, longName, choices, instrument = None, caching=False):
#        QObject.__init__(self, instrument)
#        self.command = command
#        self.longName = longName
#        self.codes = [x[0] for x in choices]
#        self.strings = [x[1] for x in choices]
#        self.instrument = instrument
#        self.caching = caching
#        self._code = None
#        for choice in choices:
#            print "Choice:", choice
#            code = choice[0]
#            if len(choice) > 2:
#                label = choice[2]
#            else:
#                label = re.sub('\W|^(?=\d)','_', choice[1]).upper()
#            setattr(self, label, code)
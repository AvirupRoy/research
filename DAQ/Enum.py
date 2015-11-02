# -*- coding: utf-8 -*-
#  Copyright (C) 2012 Felix Jaeckel <fxjaeckel@gmail.com> and Randy Lafler <rlafler@unm.edu>

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Mon Nov 26 13:30:42 2012

@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

from collections import OrderedDict


def SettingEnum(dictionary):
    """ This function generates non-value based enumeration from a dictionary containing the codes as keys, and for each value a tuple with the enum name and a descriptive string  """
    codes = dictionary.keys()
    vals = dictionary.values()
    names = [x[0] for x in vals]
    strings = [x[1] for x in vals]

    class EnumType(object):
        def __init__(self, *enumValues):
            self._codeDict = OrderedDict()
            self._nameDict = OrderedDict()
            self._stringDict = OrderedDict()
            for v in enumValues:
                setattr(self, v.Name, v)
                self._codeDict[v.Code] = v
                self._nameDict[v.Name] = v
                self._stringDict[v.String] = v

        def names(self):
            return self._nameDict.keys()

        def strings(self):
            return self._stringDict.keys()

        def fromCode(self, code):
            return self._codeDict[code]

        def fromName(self, name):
            return self._nameDict[name]

        def fromString(self, string):
            return self._stringDict[string]

        def __getitem__(self, i):   # Allow indexing with [i] for convenience
            return self.fromCode(i)

        __call__ = __getitem__  # Allow indexing also with (i)


    class EnumValue(object):
        __slots__ = ('__index','__code', '__name', '__string')
        def __init__(self, index, code, name, string):
            self.__index = index
            self.__code = code
            self.__name = name
            self.__string = string
        Code = property(lambda self: self.__code)
        Name = property(lambda self: self.__name)
        String = property(lambda self: self.__string)
        EnumType = property(lambda self: EnumType)
        def __hash__(self): return hash(self.__code)
        def __int__(self): return self.__code
        def __cmp__(self, other):
            assert self.EnumType is other.EnumType, "Only values from the same enum are comparable"
            return cmp(self.__code, other.__code)
        def __invert__(self): return constants[maximum - self.__index]
        def __nonzero__(self): return bool(self.__index)
        def __repr__(self): return str(names[self.__index])

    maximum = len(names) - 1
    constants = tuple(map(EnumValue, range(len(names)), codes, names, strings))
    return EnumType(*constants)

def ParameterEnum(dictionary):
    """ This function generates a value based enumeration from a dictionary containing the codes as keys, and for each value a tuple with the enum name, a descriptive string, and the numerical value  """
    codes = dictionary.keys()
    vals = dictionary.values()
    names = [x[0] for x in vals]
    strings = [x[1] for x in vals]
    values = [x[2] for x in vals]

    class EnumType(object):
        def __init__(self, *enumValues):
            self._codeDict = OrderedDict()
            self._nameDict = OrderedDict()
            self._stringDict = OrderedDict()
            self._valueDict = OrderedDict()
            for v in enumValues:
                setattr(self, v.Name, v)
                self._codeDict[v.Code] = v
                self._nameDict[v.Name] = v
                self._stringDict[v.String] = v
                self._valueDict[v.Value] = v
            self.Max = self.fromValue(max(self._valueDict.keys()))
            self.Min = self.fromValue(min(self._valueDict.keys()))

        def names(self):
            return self._nameDict.keys()

        def strings(self):
            return self._stringDict.keys()

        def fromCode(self, code):
            return self._codeDict[code]

        def fromName(self, name):
            return self._nameDict[name]

        def fromString(self, string):
            return self._stringDict[string]

        def fromValue(self, value):
            try:
                return self._valueDict[value]
            except KeyError:
                return self.findClosest(value)

        def findClosest(self, value):
                closest = min([(abs(value-x), x) for x in self._valueDict.keys()])[1]
                return self.fromValue(closest)

        def findGE(self, value):
                larger = min([ (x-value, x) for x in self._valueDict.keys() if x >= value] or [(0,None)]) [1]
                return self.fromValue(larger)

        def findSE(self, value):
                smaller = min([ (value-x, x) for x in self._valueDict.keys() if x <= value] or [(0,None)]) [1]
                return self.fromValue(smaller)

        def findGreater(self, value):
                larger = min([ (x-value, x) for x in self._valueDict.keys() if x > value] or [(0,None)]) [1]
                return self.fromValue(larger)

        def findSmaller(self, value):
                smaller = min([ (value-x, x) for x in self._valueDict.keys() if x < value] or [(0,None)]) [1]
                return self.fromValue(smaller)

        def increase(self, other):
            pass


        def __getitem__(self, i):   # Allow indexing with [i] for convenience
            return self.fromCode(i)

        __call__ = __getitem__  # Allow indexing also with (i)


    class EnumValue(object):
        __slots__ = ('__index','__code', '__name', '__string', '__value')
        def __init__(self, index, code, name, string, value):
            self.__index = index
            self.__code = code
            self.__name = name
            self.__string = string
            self.__value = value
        Code = property(lambda self: self.__code)
        Name = property(lambda self: self.__name)
        String = property(lambda self: self.__string)
        Value = property(lambda self: self.__value)
        EnumType = property(lambda self: EnumType)
        def increase(self): return EnumValue()
        def __hash__(self): return hash(self.__code)
        def __int__(self): return self.__code
        def __float__(self): return self.__value
        def __cmp__(self, other):   # Compare by value, not by code
            assert self.EnumType is other.EnumType, "Only values from the same enum are comparable"
            return cmp(self.__value, other.__value)
        def __invert__(self): return constants[maximum - self.__index]
        def __nonzero__(self): return bool(self.__index)
        def __repr__(self): return str(names[self.__index])

    maximum = len(names) - 1
    constants = tuple(map(EnumValue, range(len(names)), codes, names, strings, values))
    return EnumType(*constants)

if __name__ == '__main__':
    FeedbackResistor = ParameterEnum({0x0000:('R_1K',    '1 kOhm', 1E3),
                                      0x0002:('R_10K',  '10 kOhm', 1E4),
                                      0x0004:('R_100K','100 kOhm', 1E5),
                                      0x0006:('R_1M',    '1 MOhm', 1E6)})

    IntegratorCapacitor = ParameterEnum({0x0300:('C_1NF',    '1 nF', 1E-9),
                                         0x0200:('C_10NF',  '10 nF', 1E-8),
                                         0x0100:('C_100NF','100 nF', 1E-7)
                                         })
    TestSignalOptions = SettingEnum({0: ('TS_OFF', 'Off'),
                                     1: ('TS_ON', 'On'),
                                     2: ('TS_AUTO', 'Auto')})


    print FeedbackResistor.Min
    r = FeedbackResistor.fromCode(0x0002)
    print r
    print r.Code
    print r.Name
    print r.String
    print FeedbackResistor.names()
    print FeedbackResistor.strings()

    print IntegratorCapacitor.strings()

    t = TestSignalOptions.fromCode(0)
    print t
    t = TestSignalOptions.TS_AUTO

    print TestSignalOptions.names()
    print TestSignalOptions.strings()



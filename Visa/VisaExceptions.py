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

# -*- coding: utf-8 -*-

"""
Created on Thu Jun 21 09:45:24 2012
@summary: Error class for VISA instruments
@author: Felix Jaeckel and Randy Lafler
@contact: fxjaeckel@gmail.com
"""

class Error(Exception):
    """Base class for exceptions in the VISA module."""
    pass

class ParameterOutOfRange(Error):
    """Exception raised for numerical parameters that are out-of-range.

    Attributes:
        device   -- Device that caused the error
        item     -- Parameter that was out-of-range
        minValue -- Minimum allowed value
        maxValue -- Maximum allowed value
        units    -- Units of minValue and maxValue
    """
    def __init__(self, device, item, minValue, maxValue, units=''):
        self.device = device
        self.item = item
        self.minValue = minValue
        self.maxValue = maxValue
        self.units = units
        self.message = "%s: Parameter %s out of accepted range from %0.5f to %0.5f %s" % (self.device, self.item, self.minValue, self.maxValue, self.units)
        
class SettingInvalid(Error):
    """Exception raised for an invalid discrete setting .

    Attributes:
        device   -- Device that caused the error
        setting  -- Parameter that was out-of-range
    """
    def __init__(self, device, item):
        self.device = device
        self.item = item
        self.message = "%s: Illegal value for setting %s" % (self.device, self.item)

class CommunicationsError(Error):
    def __init__(self, device, item):
        self.device = device
        self.item = item
        self.message = "%s: Communication error %s" % (self.device, self.item)
        
class DeviceNotPresent(Error):
    
    def __init__(self, device, id):
        self.device = device
        self.id = id
        self.message = "%s: Device could not be identified (ID=%s)." % (self.device, self.id)
        

      
if __name__ == '__main__':
    err = ParameterOutOfRange("VISA::12", "Test", -10, 10, "V")
    try:
        raise err
    except Error as e:
        print(e.message)
        

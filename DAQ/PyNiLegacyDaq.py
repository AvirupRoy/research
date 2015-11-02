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
Created on Wed Sep 19 13:46:04 2012
Python interface to NI's traditional (legacy) DAQ API
Unfortunately, currently crashes machine
@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

import os
import ctypes.util
import ctypes as ct
import numpy as np
import warnings
from Enum import SettingEnum

import inspect

def whoIsCaller():
    return inspect.stack()[2][3]


if os.name=='nt':
    import _winreg as winreg
    regpath = r'SOFTWARE\National Instruments\NI-DAQ\CurrentVersion'
    reg6432path = r'SOFTWARE\Wow6432Node\National Instruments\NI-DAQ\CurrentVersion'
    libname = 'nidaq32'

    try:
        regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, regpath)
    except WindowsError:
        try:
            regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg6432path)
        except WindowsError:
            print('You need to install NI DAQ first.')
    nidaq_install = winreg.QueryValueEx(regkey, 'Path')[0]
    print "NIDAQ install:", nidaq_install

    lib = ctypes.util.find_library(libname)
    if lib is None:
        # try default installation path:
        lib = os.path.join(nidaq_install, r'lib\nidaq32.dll')
        if os.path.isfile(lib):
            print('You should add %r to PATH environment variable and reboot.' % (os.path.dirname (lib)))
        else:
            lib = None

else:
    # TODO: Find the location of the NIDAQmx.h automatically (eg by using the location of the library)
    include_nidaq_h = '/usr/local/include/NIDAQmx.h'
    libname = 'nidaq'
    lib = ct.util.find_library(libname)

libnidaq = None

if lib is None:
    warnings.warn('''Failed to find NI-DAQmx library. Make sure that lib%s is installed and its location is listed in PATH|LD_LIBRARY_PATH|. The functionality of libnidaqmx.py will be disabled.''' % (libname), ImportWarning)
else:
    if os.name=='nt':
        libnidaq = ct.windll.LoadLibrary(lib)
    else:
        libnidaq = ct.cdll.LoadLibrary(lib)

print "Loaded NI DAQmx library:", lib

i8 = ct.c_char
u8 = ct.c_byte
i16 = ct.c_int16
u16 = ct.c_uint16
i32 = ct.c_int32
u32 = ct.c_uint32
f32 = ct.c_float
f64 = ct.c_double
pointer = ct.c_void_p
byref = ct.byref
string = ct.c_char_p


def defineFunction(function, inputargs=None):
    f = function
    f.argtypes = inputargs
    f.restype = i16
    return f

#
#def decodeError(code):
#    bufferSize = 4096
#    buffer = ctypes.create_string_buffer('\000' * bufferSize)
#    r = _getExtendedErrorInfo(ct.byref(buffer), bufferSize)
#    if r != 0:
#        r = libnidaqmx.DAQmxGetErrorString(code, ct.byref(buffer), bufferSize)
#    return buffer.value
#
#def itemsFromBuffer(buffer):
#    items = buffer.value.split(',')
#    return([x.strip() for x in items])
#
#def itemsFromBufferStripPrefix(stringbuffer, prefix):
#    items = stringbuffer.value.split(',')
#    return [x.strip().lstrip(prefix) for x in items]
#
#Edge = SettingEnum({10171: ('FALLING', 'Falling Edge'), 10280: ('RISING', 'Rising Edge')})

class Error(Exception):
    def __init__(self, source, function, errorCode, reason = None):
        self.source = source
        self.function = function
        self.errorCode = errorCode
        message = "NI DAQmx error (function %s in %s):\n Error code %s\n Error message %s\n" % (function, source, errorCode, reason)
        super(Error,self).__init__(message)


def handleError(errorCode):
    if errorCode == 0:
        pass
    else:
        raise Exception("Error: %d" % errorCode)

_AI_Change_Parameter = defineFunction(libnidaq.AI_Change_Parameter, [i16, i16, u32, u32])

def aiChangeParameter(slot, channel, parameterId, parameterValue):
    ret = _AI_Change_Parameter(slot, channel, parameterId, parameterValue)
    return ret

_AI_Check = defineFunction(libnidaq.AI_Change_Parameter)

def aiCheck(slot):
    status = i16(0)
    value = i16(0)
    ret = _AI_Check(i16(slot), ct.byref(status), ct.byref(value))
    handleError(ret)
    return status, value

_AI_Clear = defineFunction(libnidaq.AI_Clear, [i16])

def aiClear(slot):
    ret = _AI_Clear(i16(slot))
    handleError(ret)

_AI_Read = defineFunction(libnidaq.AI_Read, [i16, i16, i16, ct.c_void_p])
_AI_Read32 = defineFunction(libnidaq.AI_Read32, [i16, i16, i16, ct.c_void_p])
_AI_VRead = defineFunction(libnidaq.AI_VRead, [i16, i16, i16, ct.c_void_p])

def aiRead(slot, channel, gain):
    value = i16()
    ret = _AI_Read(slot, channel, gain, ct.byref(value))
    handleError(ret)
    return value

def aiRead32(slot, channel, gain):
    value = i32()
    ret = _AI_Read(slot, channel, gain, ct.byref(value))
    handleError(ret)
    return value

def aiVRead(slot, channel, gain):
    volts = f64()
    ret = _AI_VRead(slot, channel, gain, byref(volts))
    handleError(ret)
    return volts.value

_AI_Setup = defineFunction(libnidaq.AI_Setup, [i16, i16, i16])

def aiSetup(slot, channel, gain):
    ret = _AI_Setup(slot, channel, gain)
    handleError(ret)

_Get_NI_DAQ_Version = defineFunction(libnidaq.Get_NI_DAQ_Version, [pointer])

def niDaqVersion():
    version = u32()
    ret = _Get_NI_DAQ_Version(ct.byref(version))
    handleError(ret)
    return version.value

_Get_DAQ_Device_Info = defineFunction(libnidaq.Get_DAQ_Device_Info, [i16, u32, pointer])

def getDaqDeviceInfo(slot, infoType):
    infoVal = u32()
    ret = _Get_DAQ_Device_Info(slot, infoType, byref(infoVal))
    handleError(ret)
    return infoVal.value

_AO_Configure = defineFunction(libnidaq.AO_Configure, [i16, i16, i16, i16, f64, i16])

def aoConfigure(slot, channel, outputPolarity, intOrExtRef, refVoltage, updateMode):
    ret = _AO_Configure(slot, channel, outputPolarity, intOrExtRef, refVoltage, updateMode)
    handleError(ret)

_AO_VWrite = defineFunction(libnidaq.AO_VWrite, [i16, i16, f64])

Pointer = ct.c_void_p

# i16 WINAPI DAQ_Config (i16 slot, 	i16 startTrig, i16 extConv);
_DAQ_Config = defineFunction(libnidaq.DAQ_Config, [i16, i16, i16])

# i16 WINAPI DAQ_Start (i16 slot, i16 chan, i16 gain, i16 FAR * buffer, u32 cnt, i16 timebase, u16 sampInt);
_DAQ_Start = defineFunction(libnidaq.DAQ_Start, [i16, i16, i16, Pointer, u32, i16, u16])

# i16 WINAPI DAQ_Check (i16 slot, i16 FAR * progress, u32 FAR *retrieved);
_DAQ_Check = defineFunction(libnidaq.DAQ_Check, [i16, ct.POINTER(i16), ct.POINTER(u32)])

# i16 WINAPI DAQ_Clear (i16 slot);
_DAQ_Clear = defineFunction(libnidaq.DAQ_Clear, [i16])

# i16 WINAPI DAQ_to_Disk (i16 slot, i16 chan, i16 gain, i8 FAR * fileName, u32 cnt, f64 sampleRate,	i16 concat);
_DAQ_ToDisk = defineFunction(libnidaq.DAQ_to_Disk, [i16, i16, i16, string, u32, f64, i16])

# i16 WINAPI DAQ_Op (i16 slot, i16 chan, i16 gain, i16 FAR * buffer, u32 cnt, f64 sampleRate);
_DAQ_Op = defineFunction(libnidaq.DAQ_to_Disk, [i16, i16, i16, ct.POINTER(i16), u32, f64, i32])

class UpdateMode:
    IMMEDIATE = 0
    DELAYED = 1
    EXTERNAL = 2

class Device():

    class TimeBase:
        CLK_20MHz = -3
        CLK_5MHz = -1
        CLK_EXT = 0
        CLK_1MHz = 1
        CLK_100kHz = 2
        CLK_10kHz = 3
        CLK_1kHz = 4
        CLK_100Hz = 5


    def __init__(self, slot):
        self.slot = slot

    def serialNumber(self):
        return getDaqDeviceInfo(self.slot, InfoType.ND_DEVICE_SERIAL_NUMBER)

    def deviceType(self):
        return getDaqDeviceInfo(self.slot, InfoType.ND_DEVICE_TYPE_CODE)

    def aiSetup(self, channel, gain):
        aiSetup(self.slot, channel, gain)

    def aiReadVoltage(self, channel, gain):
        return aiVRead(self.slot, channel, gain)

    def aoConfigure(self, channel, bipolar = True, extRef=False, refVoltage = +10.0, updateMode = UpdateMode.IMMEDIATE):
        if bipolar:
            outputPolarity = 0
        else:
            outputPolarity = 1

        if extRef:
            intOrExtRef = 1
        else:
            intOrExtRef = 0
        aoConfigure(self.slot, channel, outputPolarity, intOrExtRef, refVoltage, updateMode)

    def aoWriteVoltage(self, channel, voltage):
        ret = _AO_VWrite(self.slot, channel, voltage)
        handleError(ret)

    def daqConfig(self):
        ret = _DAQ_Config(self.slot, 0, 0)
        handleError(ret)

    def daqStart(self, channel, gain, buffer, timeBase, sampleInterval):
        #print "Starting DAQ to", buffer.data.ctypes.data

        #bufferPointer = buffer.data.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
        #print "BufferPointer:", bufferPointer
        print "Size:", buffer.size
        bufferPointer = buffer.data
        ret = _DAQ_Start(self.slot, channel, gain, bufferPointer, buffer.size, timeBase, sampleInterval)
        handleError(ret)

    def daqToDisk(self, channel, gain, fileName, count, rate, concat):
        ret = _DAQ_ToDisk(self.slot, channel, gain, fileName, count, rate, concat)
        handleError(ret)

    def daqOp(self, channel, gain, count, rate):
        #buffer = ct.create_string_buffer(count*4)
        buffer = (ct.c_int16 * (count * 2))(0)
        dummy = 0
        ret = _DAQ_Op(self.slot, channel, gain, buffer, count, rate, dummy)
        handleError(ret)
        return buffer

    def daqCheck(self):
        progress = i16()
        retrieved = u32()
        ret = _DAQ_Check(self.slot, byref(progress), byref(retrieved))
        handleError(ret)
        return progress.value, retrieved.value

    def daqClear(self):
        ret = _DAQ_Clear(self.slot)
        handleError(ret)

class Buffer():
    def __init__(self, size=1024):
        self.size = size
        #self.data = np.zeros((2*size,),dtype=np.int16, order = 'C')
        self.data = ct.create_string_buffer(size*2)

class InfoType:
    ND_DEVICE_SERIAL_NUMBER = 15280
    ND_DEVICE_TYPE_CODE = 15300

if __name__ == '__main__':
    import time
    #aiClear(3)
    x = niDaqVersion()
    print "NI-DAQ version:", x
    d = Device(1)
    print "Serial # %X" % d.serialNumber()
    print "Device type code", d.deviceType()
    gain = 0
#    d.aiSetup(0, 0)
#    d.aiSetup(1, 0)
#    for i in range(20):
#        print d.aiReadVoltage(0,0)


    #fileName = 'D:\\Users\\FJ\\testDaq.txt'
    #print "Filename:", fileName
    #d.daqToDisk(0, gain, fileName, 10000, 10000, 0)

    d.daqOp(0, gain, count=1000, rate=10E3)
    print buffer.data

#    d.daqConfig()
#    buffer = Buffer(2048)
#    d.daqStart(0, gain, buffer, d.TimeBase.CLK_100kHz, 10)
#    while(True):
#        time.sleep(0.2)
#        print "Checking on progress"
#        progress, retrieved = d.daqCheck()
#        print "Progress, retrieved:", progress, retrieved
#        if progress > 0:
#            break
#
#    print "Data:", buffer.data
#    d.daqClear()

 #   d.aoConfigure(0)
 #   d.aoWriteVoltage(0, 1)


#    d = Device(2)
#    print "Serial # %X" % d.serialNumber()
#    print "Device type code", d.deviceType()
#    print d.aiReadVoltage(2, 0)

#    info = getDaqDeviceInfo(2, InfoType.ND_DEVICE_SERIAL_NUMBER)
#    print info
    #print aiRead(2, 1, 0)
    #print aiCheck(1)
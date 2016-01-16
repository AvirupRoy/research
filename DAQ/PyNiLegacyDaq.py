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
Main purpose is to talk to NI PCI-4452.
The NI PXI-4351 24-bit DAQ device is something different again and has its own API (sigh!).
Unfortunately, currently crashes machine
@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

import os
import ctypes.util
#from numpy.ctypeslib import ndpointer
import ctypes as ct
import numpy as np
import warnings

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
    # TODO: Find the location of the nidaq.h automatically (eg by using the location of the library)
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
dataPointer = np.ctypeslib.ndpointer(dtype=np.int32, ndim=1, flags='aligned,writeable,C_CONTIGUOUS')
arrayDataPointer = np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='aligned,writeable,F_CONTIGUOUS')

def defineFunction(function, inputargs=None):
    f = function
    f.argtypes = inputargs
    f.restype = i16
    return f
    
class Error(Exception):
    def __init__(self, source, function, errorCode, reason = None):
        self.source = source
        self.function = function
        self.errorCode = errorCode
        message = "NI DAQmx error (function %s in %s):\n Error code %s\n Error message %s\n" % (function, source, errorCode, reason)
        super(Error,self).__init__(message)

def handleError(errorCode):
    if errorCode != 0:
        try:
            from PyNiLegacyData import ErrorCodes
            errorType, errorMessage = ErrorCodes[errorCode]
            message = "NI legacy DAQ error %d (%s): %s" % (errorCode, errorType, errorMessage)
        except:
            message = '"NI legacy DAQ error %d: No description available' % errorCode
        raise Exception(message)

## Utility
#extern i16 WINAPI Timeout_Config (i16 slot, i32 numTicks);

_Timeout_Config = defineFunction(libnidaq.Timeout_Config, [i16, i32])
'''Establishes a timeout limit synchronous functions use to ensure that these functions eventually return control to your application. Examples of synchronous functions are DAQ_Op, DAQ_DB_Transfer, and WFM_from_Disk.'''

def configureTimeout(slot, seconds):
    '''Configure a timeout limit for synchronous functions.'''
    ticks = int(seconds*18) # 18 ticks per second
    ret = _Timeout_Config(slot, ticks)
    handleError(ret)

## General
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

## One-shot ("sample-on-demand") operations, not supported by the DSA device
# Analog input
_AI_Setup = defineFunction(libnidaq.AI_Setup, [i16, i16, i16])
def aiSetup(slot, channel, gain):
    ret = _AI_Setup(slot, channel, gain)
    handleError(ret)


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
def aiRead(slot, channel, gain):
    value = i16()
    ret = _AI_Read(slot, channel, gain, ct.byref(value))
    handleError(ret)
    return value

_AI_Read32 = defineFunction(libnidaq.AI_Read32, [i16, i16, i16, ct.c_void_p])
def aiRead32(slot, channel, gain):
    value = i32()
    ret = _AI_Read(slot, channel, gain, ct.byref(value))
    handleError(ret)
    return value

_AI_VRead = defineFunction(libnidaq.AI_VRead, [i16, i16, i16, ct.c_void_p])
def aiVRead(slot, channel, gain):
    volts = f64()
    ret = _AI_VRead(slot, channel, gain, byref(volts))
    handleError(ret)
    return volts.value

# Analog Out
_AO_Configure = defineFunction(libnidaq.AO_Configure, [i16, i16, i16, i16, f64, i16])
def aoConfigure(slot, channel, outputPolarity, intOrExtRef, refVoltage, updateMode):
    ret = _AO_Configure(slot, channel, outputPolarity, intOrExtRef, refVoltage, updateMode)
    handleError(ret)

_AO_VWrite = defineFunction(libnidaq.AO_VWrite, [i16, i16, f64])

# Analog In
#i16 WINAPI AI_Configure (i16 slot, i16 chan, i16 inputMode, i16 inputRange, i16 polarity, 	i16 driveAIS)
_AI_Configure = defineFunction(libnidaq.AI_Configure, [i16, i16, i16, i16, i16, i16])

_AI_Change_Parameter = defineFunction(libnidaq.AI_Change_Parameter, [i16, i16, u32, u32])
def aiChangeParameter(slot, channel, parameterId, parameterValue):
    ret = _AI_Change_Parameter(slot, channel, parameterId, parameterValue)
    return ret


## Data acquisition functions
# i16 WINAPI DAQ_Config (i16 slot, i16 startTrig, i16 extConv);
_DAQ_Config = defineFunction(libnidaq.DAQ_Config, [i16, i16, i16])
'''Stores configuration information for subsequent DAQ operations.'''

# i16 WINAPI DAQ_Start (i16 slot, i16 chan, i16 gain, i16 FAR * buffer, u32 cnt, i16 timebase, u16 sampInt);
_DAQ_Start = defineFunction(libnidaq.DAQ_Start, [i16, i16, i16, dataPointer, u32, i16, u16])
'''Initiates an asynchronous, single-channel DAQ operation and stores its input in an array.'''

# i16 WINAPI DAQ_Check (i16 slot, i16 FAR * progress, u32 FAR *retrieved);
_DAQ_Check = defineFunction(libnidaq.DAQ_Check, [i16, ct.POINTER(i16), ct.POINTER(u32)])
'''Checks whether the current DAQ operation is complete and returns the status and the number of samples acquired to that point.'''

# i16 WINAPI DAQ_Clear (i16 slot);
_DAQ_Clear = defineFunction(libnidaq.DAQ_Clear, [i16])
'''Cancels the current DAQ operation (both single-channel and multiple-channel scanned) and reinitializes the DAQ circuitry.'''

_DAQ_Rate = defineFunction(libnidaq.DAQ_Rate, [f64, i16, ct.POINTER(i16), ct.POINTER(u16)])
'''Converts a DAQ rate into the timebase and sample-interval values needed to produce the rate you want.'''


## Single channel functions
# i16 WINAPI DAQ_to_Disk (i16 slot, i16 chan, i16 gain, i8 FAR * fileName, u32 cnt, f64 sampleRate, i16 concat);
_DAQ_ToDisk = defineFunction(libnidaq.DAQ_to_Disk, [i16, i16, i16, ct.c_char_p, u32, f64, i16])
'''Synchronous, single-channel DAQ to file operation.'''

# i16 WINAPI DAQ_Op (i16 slot, i16 chan, i16 gain, i16 FAR * buffer, u32 cnt, f64 sampleRate);
_DAQ_Op = defineFunction(libnidaq.DAQ_Op, [i16, i16, i16, dataPointer, u32, f64])
'''Performs a synchronous, single-channel DAQ operation. DAQ_Op does not return until Traditional NI-DAQ (Legacy) has acquired all the data or an acquisition error has occurred.'''

## Multi-channel
# i16 WINAPI SCAN_Op (i16 slot, i16 numChans, i16 FAR * chans, i16 FAR * gains, i16 FAR * buffer, 	u32 cnt, f64 sampleRate, f64 scanRate)
_SCAN_Op = defineFunction(libnidaq.SCAN_Op, [i16, i16, ct.POINTER(i16), ct.POINTER(i16), arrayDataPointer, u32, f64, f64])

# i16 WINAPI SCAN_Setup (i16 slot, i16 num_chans, i16 FAR * chans, 	i16 FAR * gains)
_SCAN_Setup = defineFunction(libnidaq.SCAN_Setup, [i16, i16, ct.POINTER(i16), ct.POINTER(i16)])

# i16 WINAPI SCAN_Start (i16 slot, i16 FAR * buffer, u32 cnt, i16 tb1, u16 si1, i16 tb2, u16 si2);
_SCAN_Start = defineFunction(libnidaq.SCAN_Start, [i16, arrayDataPointer, u32, i16, u16, i16, u16])

## Double buffering functions
# i16 WINAPI DAQ_DB_Config (i16 slot, i16 dbMode);
_DAQ_DB_Config = defineFunction(libnidaq.DAQ_DB_Config, [i16, i16])
'''Enable or disable double buffering'''

# i16 WINAPI DAQ_DB_HalfReady (i16 slot, i16 FAR * halfReady, i16 FAR * daqStopped)
_DAQ_DB_HalfReady = defineFunction(libnidaq.DAQ_DB_HalfReady, [i16, ct.POINTER(i16), ct.POINTER(i16)])
'''Check whether the next buffer is ready in a double-buffered acquisition. If so,
use DAQ_DB_Transfer to retrieve data from the buffer.'''

# i16 WINAPI DAQ_DB_Transfer (i16 slot, i16 FAR * hbuffer, u32 FAR * ptsTfr, i16 FAR * status)
_DAQ_DB_Transfer = defineFunction(libnidaq.DAQ_DB_Transfer, [i16, dataPointer, ct.POINTER(u32), ct.POINTER(i16)])
'''Transfers half the data from the buffer being used for double-buffered data acquisition to another buffer, which is passed to the function, and waits until the data to be transferred is available before returning.'''


#i16 WINAPI DAQ_Set_Clock (i16 slot, u32 whichClock, f64 desiredRate, u32 units, f64 FAR * actualRate)
_DAQ_Set_Clock = defineFunction(libnidaq.DAQ_Set_Clock, [i16, u32, f64, u32, ct.POINTER(f64)])
'''Sets the scan rate for a group of channels (44XX devices and 45XX devices only).'''

#i16 WINAPI DAQ_Monitor (i16 slot, i16 chan, i16 seq, u32 monitorCnt, i16 FAR * monitorBuf, u32 FAR * newestIndex, i16 FAR * status)
_DAQ_Monitor = defineFunction(libnidaq.DAQ_Monitor, [i16, i16, i16, u32, dataPointer, ct.POINTER(u32), ct.POINTER(i16)])
'''Returns data from an asynchronous data acquisition in progress. During a multiple-channel acquisition,
 you can retrieve data from a single channel or from all channels being scanned.
 An oldest/newest mode provides for return of sequential (oldest) blocks of data or return of the most recently
 acquired (newest) blocks of data.'''

## Trigger functions
#i16 WINAPI Configure_HW_Analog_Trigger (i16 deviceNumber, u32 onOrOff, i32 lowValue, i32 highValue, u32 mode, u32 trigSource)
_Configure_HW_Analog_Trigger  = defineFunction(libnidaq.Configure_HW_Analog_Trigger, [i16, u32, i32, i32, u32, u32])

## Calibration
# i16 WINAPI Calibrate_E_Series (i16 deviceNumber, u32 calOp, u32 setOfCalConst, f64 calRefVolts);
# i16 WINAPI Calibrate_59xx (i16 deviceNumber, u32 operation, f64 refVoltage);
# i16 WINAPI Calibrate_DSA (	i16 deviceNumber, u32 operation, f64 refVoltage);
_Calibrate_DSA = defineFunction(libnidaq.Calibrate_DSA, [i16, u32, f64])

class UpdateMode:
    IMMEDIATE = 0
    DELAYED = 1
    EXTERNAL = 2
    
class InputMode:
    DIFF = 0
    RSE  = 1
    NRSE = 2

from PyNiLegacyData import ND
from PyNiLegacyData import DeviceInfo

class GenericDevice():
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
        self._isDsa = None
        self.doubleBuffered = False
        
    def __del__(self):
        self.terminate()
        
    def terminate(self):
        if self.slot is not None:
            try:
                self.daqClear()
            except:
                pass

    @property
    def serialNumber(self):
        return getDaqDeviceInfo(self.slot, DeviceInfo.SERIAL_NUMBER)

    @property
    def deviceType(self):
        devType = getDaqDeviceInfo(self.slot, DeviceInfo.TYPE_CODE)
        return devType

    @property
    def model(self):
        from PyNiLegacyData import DeviceTypes
        return DeviceTypes[self.deviceType]
        
    def isDsa(self):
        if self._isDsa is None:
            self._isDsa = self.deviceType in [233,234,235,236]
        return self._isDsa
        
    def configureTimeout(self, seconds):
        '''Configure the time-out for synchronous function calls.'''
        configureTimeout(self.slot, seconds)


class AnalogStreamingMixin():        
    def enableDoubleBuffering(self, enable):
        '''Enable double buffering for continous acquisition.'''
        if enable:
            ret = _DAQ_DB_Config(self.slot, 1)
        else:
            ret = _DAQ_DB_Config(self.slot, 0)
        handleError(ret)
        self.doubleBuffered = True
                        
    def halfReady(self):
        '''Check if next buffer is ready during double-buffered operation.
        Returns two booleans, the first indicating whether next buffer is ready,
        the second indicating whether the DAQ operation is completed.'''
        ready = ct.c_int16(False)
        stopped = ct.c_int16(False)
        ret = _DAQ_DB_HalfReady(self.slot, ct.byref(ready), ct.byref(stopped))
        handleError(ret)
        return bool(ready.value), bool(stopped.value)
        
    def fetchFromDoubleBuffer(self):
        '''Retrieve the next available data buffer for a continuous, double buffered acquisition.'''
        #count = int(0.5*self.dataBuffer.size)
        #data = np.zeros((count,),dtype=self.NativeDType, order = 'C')
        pointsTransferred = ct.c_uint32(0)
        status = ct.c_int16(0)
        ret = _DAQ_DB_Transfer(self.slot, self.dataBuffer, ct.byref(pointsTransferred), ct.byref(status))
        handleError(ret)
        assert(pointsTransferred.value == count)
        return self.aiData()

class CounterDevice():
    pass

class AiMixin():
    def aiSetup(self, channel, gain):
        '''Apply a gain setting to a specified channel.'''
        aiSetup(self.slot, channel, gain)
    
    def setAiCoupling(self, channel, coupling='AC'):
        if coupling == 'AC':
            value = ND.AC
        else:
            value = ND.DC
        aiChangeParameter(self.slot, channel, parameterId = ND.AI_COUPLING, parameterValue=value)
    
    def aiConfigure(self, channel, inputMode='SE'):
        _AI_Configure(self.slot, 0)
        pass

    def configureAnalogTrigger(self, enable, lowValue, highValue, mode, source):
        pass

    def daqConfig(self, softwareTrigger = True, externalConversionClock = 0):
        if softwareTrigger:
            startTrigger = 0
        else:
            startTrigger = 1
        ret = _DAQ_Config(self.slot, startTrigger, externalConversionClock)
        handleError(ret)

    def daqToDisk(self, channel, gain, fileName, count=1000, rate=1000.0, append=False):
        '''Performs a synchronous, single-channel DAQ operation and saves the acquired data in a disk file. '''
        ret = _DAQ_ToDisk(self.slot, channel, gain, fileName, count, rate, append)
        handleError(ret)

    def daqOp(self, channel, gain, count, rate):
        '''Start a single channel synchronous, finite acquisition. The data will be returned in a numpy integer array.
        This function does not return until all samples have been collected or a time-out occurs.
        Therefore, make sure you specify an appropriate time-out with configureTimeout() first.'''
        #self.dataBuffer = np.zeros((count,),dtype=self.NativeDType, order = 'C')
        self.dataBuffer = self.makeDataBuffer(count)
        ret = _DAQ_Op(self.slot, channel, gain, self.dataBuffer, self.dataBuffer.size, rate)
        handleError(ret)
        return self.aiData()
        
    def daqStart(self, channel, gain, timeBase = GenericDevice.TimeBase.CLK_100kHz, sampleInterval=2, bufferSize=1000):
        '''Start a single-channel asynchronous acquisition.
             channel: Specify any AI channel number
             gain:
             timeBase: Select from DAQ.TimeBase (ignored for DSA devices)
             sampleInterval: Number of clock-cycles between samples (ignored for DSA devices)
           For DSA device use setClock() to configure the timing.
        '''
#        self.dataBuffer = np.zeros((bufferSize,),dtype=self.NativeDType, order = 'C')
        self.dataBuffer = self.makeDataBuffer(bufferSize)
        ret = _DAQ_Start(self.slot, channel, gain, self.dataBuffer, self.dataBuffer.size, timeBase, sampleInterval)
        handleError(ret)

    def daqCheck(self):
        '''Checks whether the current DAQ operation is complete and returns the status and the number of samples acquired to that point.'''
        stopped = i16(0)
        retrieved = u32(0)
        ret = _DAQ_Check(self.slot, byref(stopped), byref(retrieved))
        handleError(ret)
        return stopped.value, retrieved.value

    def daqClear(self):
        print "Clearing DAQ device"
        ret = _DAQ_Clear(self.slot)
        handleError(ret)

    def scanSetup(self, channels, gains):
        '''Initializes circuitry for a scanned (multi-channel) data acquisition
        operation. Initialization includes storing a table of the channel sequence
        and gain setting for each channel to be digitized (MIO and AI devices only).'''
        assert(len(channels) == len(gains))
        self.activeAiChannels = np.asarray(channels, dtype=np.int16)
        self.activeAiGains = np.asarray(gains, dtype=np.int16)
        nChannels = len(channels)
        ret = _SCAN_Setup(self.slot, nChannels, self.activeAiChannels.ctypes.data_as(ct.POINTER(ct.c_int16)), self.activeAiGains.ctypes.data_as(ct.POINTER(ct.c_int16)))
        self.nChannels = nChannels
        handleError(ret)

    @property        
    def numberOfAiChannels(self):
        return len(self.activeAiChannels)
        
    def makeDataBuffer(self, samplesPerChannel):
        return np.zeros((self.numberOfAiChannels,samplesPerChannel),dtype=self.NativeDType, order = 'F')
        
    def scanStart(self, samplesPerChannel, sampleTimeBase = 0, sampleInterval = 0, scanTimeBase = 0, scanInterval = 0):
        '''Initiates a multiple-channel scanned data acquisition operation, with or without interval scanning.
        For double-buffered acquisitions, count specifies the size of the buffer.
        On DSA devices, sampleTimebase, sampleInterval, scanTimeBase, and scanInterval are all ignored.
        Instead, use setAiClock to set the sample rate.'''
        nChannels = self.numberOfAiChannels
        self.dataBuffer = self.makeDataBuffer(samplesPerChannel)
        if self.doubleBuffered:
            self.dataDoubleBuffer = self.makeDataBuffer(samplesPerChannel*2)
            dataBuffer = self.dataDoubleBuffer
#            count = 2 * nChannels * samplesPerChannel
        else:
            dataBuffer = self.dataBuffer
#            count = nChannels * samplesPerChannel
        ret = _SCAN_Start(self.slot, dataBuffer, dataBuffer.size, sampleTimeBase, sampleInterval, scanTimeBase, scanInterval)
        handleError(ret)
        
    def aiData(self):
        if self.nChannels > 1:
            return self.dataBuffer.reshape((self.numberOfAiChannels,-1), order='F')
        else:
            return self.dataBuffer
        
    def scanOp(self, channels, gains, samplesPerChannel, sampleRate, scanRate):
        '''Performs a synchronous, multiple-channel scanned data acquisition operation.
        SCAN_Op does not return until Traditional NI-DAQ (Legacy) acquires all the data
        or an acquisition error occurs (MIO, AI, and DSA devices only).
        Simultaneous sampling devices do not use the sampleRate parameter.
        Because these devices use simultaneous sampling of all channels, the scanRate
        parameter controls the acquisition rate.'''
        assert(len(channels) == len(gains))
        self.activeAiChannels = np.asarray(channels, dtype=np.int16)
        self.activeAiGains = np.asarray(gains, dtype=np.int16)
        self.dataBuffer = self.makeDataBuffer(samplesPerChannel)
        ret = _SCAN_Op(self.slot, len(channels), self.activeAiChannels.ctypes.data_as(ct.POINTER(ct.c_int16)), self.activeAiGains.ctypes.data_as(ct.POINTER(ct.c_int16)), self.dataBuffer, self.dataBuffer.size, sampleRate, scanRate)
        handleError(ret)
        return self.aiData()

class AoMixin():
    def aoConfigure(self, channel, bipolar = True, extRef=False, refVoltage = +10.0, updateMode = UpdateMode.IMMEDIATE):
        '''Confiugre the analog output.'''
        if bipolar:
            outputPolarity = 0
        else:
            outputPolarity = 1

        if extRef:
            intOrExtRef = 1
        else:
            intOrExtRef = 0
        aoConfigure(self.slot, channel, outputPolarity, intOrExtRef, refVoltage, updateMode)


class AiSinglePointMixin():
    def aiReadVoltage(self, channel, gain):
        '''Single shot voltage reading on a given channel.'''
        return aiVRead(self.slot, channel, gain)

class AoSinglePointMixin():
    def aoWriteVoltage(self, channel, voltage):
        '''Single shot voltage update on the analog output.'''
        ret = _AO_VWrite(self.slot, channel, voltage)
        handleError(ret)


class ESeriesDevice(GenericDevice, AnalogStreamingMixin, AiMixin, AiSinglePointMixin):
    pass    

            
class DsaDevice(GenericDevice, AnalogStreamingMixin, AiMixin, AoMixin):
    NativeDType = np.int32
    def setAiClock(self, rate):
        '''Sets the scan rate for a group of channels (44XX devices and 45XX devices only).'''
        actualRate = ct.c_double(0)
        ret = _DAQ_Set_Clock(self.slot, 0, rate, 0, ct.byref(actualRate))
        handleError(ret)
        return actualRate.value

    def selfCalibrate(self):
        '''Initiate the interal self calibration.
        If you calibrate your PCI-4451/4452 while it is connected to a BNC-2140 accessory,
        set each input channel to SE and connect each channel + terminal to a channel – terminal
        through a BNC shunt. In addition, make sure that ICP  power is turned off on the BNC-2140 to 
        avoid affecting the reference voltage reading. If you calibrate your PCI-4453/4454
        while it is connected to the BNC-2142 accessory, connect each + terminal to its shield
        through a BNC shunt. You can also calibrate your PCI-445X by removing the external cable
        connected to the BNC-214X accessory.'''
        ret = _Calibrate_DSA(self.slot, ND.SELF_CALIBRATE, 0)
        handleError(ret)

    def aiData(self):
        if self.numberOfAiChannels > 1:
            d = self.dataBuffer.reshape((self.numberOfAiChannels,-1), order='F')
        else:
            d = self.dataBuffer
        return np.right_shift(d, 16).astype(np.int16)
        
    def aiVoltages(self):
        V = self.aiData().astype(np.float32)
        for i in range(self.numberOfAiChannels):
            V[i,:] *= self.scaleForAiGain(self.activeAiGains[i])
        return V
                
    def restoreFactoryCalibration(self):
        '''Restore device to factory calibration data.'''
        ret = _Calibrate_DSA(self.slot, ND.RESTORE_FACTORY_CALIBRATION, 0)
        handleError(ret)
    
    def calibrateToExternalReference(self, referenceVoltage):
        assert referenceVoltage>=1.0
        assert referenceVoltage<=9.99
        ret = _Calibrate_DSA(self.slot, ND.EXTERNAL_CALIBRATE, referenceVoltage)
        handleError(ret)
        
class Pci4452(DsaDevice):
    aiChannels = 4
    aoChannels = 0
    sampleRateSpan = (5E3, 204.8E3)
    AiGainsAndRanges = {-20:42.4, -10:31.6, 0:10.0, 10: 3.16, 20: 1.00, 30:0.316, 40:0.100, 50: 0.0316, 60: 0.0100}
    AiGainsAndFullScale = {-20:100.0, -10:31.6, 0:10.0, 10: 3.16, 20: 1.00, 30:0.316, 40:0.100, 50: 0.0316, 60: 0.0100}
    
    def scaleForAiGain(self, gain):
        '''Return the scaling factor to convert from integer ADC code to voltage'''
        fullScale = self.AiGainsAndFullScale[gain]
        scale = fullScale / (2**15)
        return scale
        

DeviceTypeMap = {234: Pci4452}

def Device(slot=0):
    '''Factory function to make the right kind of device'''
    devType = getDaqDeviceInfo(slot, DeviceInfo.TYPE_CODE)
    try:
        device = DeviceTypeMap[devType](slot)
        return device
    except:
        pass
    
    if devType in [233,234,235,236]:
        return DsaDevice(slot)
    else:
        return GenericDevice(slot)
    


if __name__ == '__main__':
    import time
    #aiClear(3)
    x = niDaqVersion()
    print "NI-DAQ version:", x
    d = Device(1)
    try:
        print "Serial #: %X" % d.serialNumber
        print "Device type:", d.deviceType
        print "Model:", d.model
        print "DSA:", d.isDsa()
        gain = -20
        for channel in range(4):
            d.setAiCoupling(channel, 'DC')
        
        d.configureTimeout(30)
#        print "Starting self-calibration"
#        d.selfCalibrate()
#        print "Done"
#        raise Exception("Done")
#        print "Restoring factory calibration"
#        d.restoreFactoryCalibration()
#        print "Done"
#        raise Exception("Done")
#        print "Calibrate to external reference"
#        d.calibrateToExternalReference(9.000)
#        print "Done"
        
    
    #    d.aiSetup(0, 0)
    #    d.aiSetup(1, 0)
    #    for i in range(20):
    #        print d.aiReadVoltage(0,0)
    
        #test = 'continuousAi'
        test = 'syncFiniteAiMulti'
        #test = 'asyncFiniteAiMulti'
        #test = 'continuousAiMulti'
        import matplotlib.pyplot as mpl
        
        channel = 0
        count = 50000
        rate = 5000
        if test == 'diskAi':
            print "Demonstrating direct streaming to disk."
            d.configureTimeout(15)
            fileName = 'testDaq2.txt'
            print "Filename:", fileName
            d.daqToDisk(channel=channel, gain=gain, fileName=fileName, count=count, rate=rate, append=False)
            print "Done"
        elif test == 'syncFiniteAi':
            print "Demonstrating finite synchronous acquisition, please wait until all samples are collected."
            d.configureTimeout(15)
            data = d.daqOp(channel=channel, gain=gain, count=count, rate=rate)
            print "Done! Total samples:", len(data)
            data = data.astype(np.float32)*d.scaleForAiGain(gain)
            mpl.plot(data)
            mpl.show()
        elif test == 'asyncFiniteAi':
            print "Demonstrating finite asynchronous single-channel acquisition"
            d.setAiClock(rate)
            print "Starting"
            data = d.daqStart(channel, gain, bufferSize=count) # @Toto: maybe rename bufferSize to samplesPerChannel?
            while True:
                print "Waiting..."
                time.sleep(0.2)
                complete, nSamples = d.daqCheck()
                print "Samples...", nSamples
                if complete:
                    break
            print "Done! Total samples:", d.daqCheck()[1]
            data = data.astype(np.float32)*d.scaleForAiGain(gain)
            mpl.plot(data)
            mpl.show()
        elif test == 'continuousAi':
            print "Demonstrating continuous asynchronous single-channel acquisition"
            d.configureTimeout(0.1)
            rate = d.setAiClock(rate)
            print "Actual data rate:", rate
            d.enableDoubleBuffering(True)
            print "Starting"
            buffer = d.daqStart(channel, gain, bufferSize=int(0.5*rate))
            data = np.zeros((0,), dtype=np.int32)
            while True:
                ready,complete = d.halfReady()
                if ready:
                    newData = d.retrieveBufferedData()
                    data = np.hstack([data, newData])
                    print "Total:", data.shape[-1]
                if complete or data.shape[-1] >= 2.*count:
                    break
            print "Done! Total samples:", data.shape[-1]
            data = data.astype(np.float32)*d.scaleForAiGain(gain)
            mpl.plot(data[:10000])
            mpl.plot(data[-10000:])
            mpl.show()
        elif test == 'continuousAiMulti':
            print "Demonstrating continuous asynchronous multi-channel acquisition"
            d.configureTimeout(0.1)
            rate = d.setAiClock(rate)
            print "Actual data rate:", rate
            d.enableDoubleBuffering(True)
            print "Starting"
            channels = [0, 1, 2, 3]
            gains = [gain, gain, gain, gain]
            d.configureTimeout(15)
            d.setAiClock(rate)
            d.scanSetup(channels, gains)
            d.scanStart(samplesPerChannel = count)
            data = np.zeros((len(channels), 0), dtype=np.int32)
            while True:
                ready,complete = d.halfReady()
                if ready:
                    newData = d.retrieveBufferedData()
                    data = np.hstack([data, newData])
                    print "Total:", data.shape[-1]
                if complete or data.shape[-1] >= 30.*count:
                    break
            print "Done! Total samples:", data.shape[-1]
            for channel in channels:
                mpl.plot(data[channel][:10000].astype(np.float32)*d.scaleForAiGain(gains[channel]), label='Channel %d' % channel)
            mpl.legend()
            mpl.show()
            
        elif test == 'syncFiniteAiMulti':
            channels = [0, 1, 2, 3]
            gains = [gain, gain, gain, gain]
            d.configureTimeout(15)
            data = d.scanOp(channels, gains, samplesPerChannel=count, sampleRate=0, scanRate = rate)
            print "Data shape:", data.shape
            print "Done!"
            for i,channel in enumerate(channels):
                mpl.plot(data[i].astype(np.float32)*d.scaleForAiGain(gains[i]), label='Channel %d' % channel)
            mpl.legend()
            mpl.show()
            
        elif test == 'asyncFiniteAiMulti':
            channels = [0, 1, 2]
            gains = [gain, gain, gain]
            d.configureTimeout(15)
            d.setAiClock(rate)
            d.scanSetup(channels, gains)
            d.scanStart(samplesPerChannel = count)
            while True:
                print "Waiting..."
                time.sleep(0.2)
                complete, nSamples = d.daqCheck()
                print "Samples...", nSamples
                if complete:
                    break
            print "Done! Total samples:", nSamples
            data = d.aiData()            
            for i,channel in enumerate(channels):
                mpl.plot(data[i].astype(np.float32)*d.scaleForAiGain(gains[i]), label='Channel %d' % channel)
            mpl.legend()
            mpl.show()
        else:
            print "Unknown test sequence"
    finally:
        del d
 
# -*- coding: utf-8 -*-
#  Copyright (C) 2012-2015 Felix Jaeckel <fxjaeckel@gmail.com>

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
Python interface to NI's DaqMx API for data acquistion
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
    regpath = r'SOFTWARE\National Instruments\NI-DAQmx\CurrentVersion'
    reg6432path = r'SOFTWARE\Wow6432Node\National Instruments\NI-DAQmx\CurrentVersion'
    libname = 'nicaiu'

    try:
        regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, regpath)
    except WindowsError:
        try:
            regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg6432path)
        except WindowsError:
            print('You need to install NI DAQmx first.')
    nidaqmx_install = winreg.QueryValueEx(regkey, 'Path')[0]
    include_nidaqmx_h = os.path.join(nidaqmx_install, r'include\NIDAQmx.h')
    if not os.path.isfile(include_nidaqmx_h): # from Issue 23
        include_nidaqmx_h = os.path.join(nidaqmx_install, r'DAQmx ANSI C Dev\include\NIDAQmx.h')

    ansi_c_dev = os.path.join(nidaqmx_install, r'National Instruments\NI-DAQ\DAQmx ANSI C Dev')
    if not os.path.isdir(ansi_c_dev): # from Issue 23
        ansi_c_dev = os.path.join(nidaqmx_install, r'DAQmx ANSI C Dev')
        regkey.Close()

    lib = ctypes.util.find_library(libname)
    if lib is None:
        # try default installation path:
        lib = os.path.join(ansi_c_dev, r'lib\nicaiu.dll')
        if os.path.isfile(lib):
            print('You should add %r to PATH environment variable and reboot.' % (os.path.dirname (lib)))
        else:
            lib = None

else:
    # TODO: Find the location of the NIDAQmx.h automatically (eg by using the location of the library)
    include_nidaqmx_h = '/usr/local/include/NIDAQmx.h'
    libname = 'nidaqmx'
    lib = ct.util.find_library(libname)

libnidaqmx = None
if lib is None:
    warnings.warn('''Failed to find NI-DAQmx library. Make sure that lib%s is installed and its location is listed in PATH|LD_LIBRARY_PATH|. The functionality of libnidaqmx.py will be disabled.''' % (libname), ImportWarning)
else:
    if os.name=='nt':
        print "WinDLL"
        libnidaqmx = ct.windll.LoadLibrary(lib)
    else:
        print "C DLL"
        libnidaqmx = ct.cdll.LoadLibrary(lib)

print "Loaded NI DAQmx library:", lib

int8 = ct.c_int8
uInt8 = ct.c_uint8
int16 = ct.c_int16
uInt16 = ct.c_uint16
int32 = ct.c_int32
TaskHandle = bool32 = uInt32 = ct.c_uint32
int64 = ct.c_int64
uInt64 = ct.c_uint64

float32 = ct.c_float
float64 = ct.c_double
void_p = ct.c_void_p

def defineFunction(function, inputargs=None):
    f = function
    f.argtypes = inputargs
    f.restype = int32
    return f

_getExtendedErrorInfo = defineFunction(libnidaqmx.DAQmxGetExtendedErrorInfo)
_getErrorString = defineFunction(libnidaqmx.DAQmxGetErrorString)


def decodeError(code):
    bufferSize = 4096
    buffer = ctypes.create_string_buffer('\000' * bufferSize)
    r = _getExtendedErrorInfo(ct.byref(buffer), bufferSize)
    if r != 0:
        r = libnidaqmx.DAQmxGetErrorString(code, ct.byref(buffer), bufferSize)
    return buffer.value

def itemsFromBuffer(buffer):
    items = buffer.value.split(',')
    return([x.strip() for x in items])

def itemsFromBufferStripPrefix(stringbuffer, prefix):
    items = stringbuffer.value.split(',')
    return [x.strip().lstrip(prefix) for x in items]

Edge = SettingEnum({10171: ('FALLING', 'Falling Edge'), 10280: ('RISING', 'Rising Edge')})

class Error(Exception):
    def __init__(self, source, function, errorCode, reason = None):
        self.source = source
        self.function = function
        self.errorCode = errorCode
        message = "NI DAQmx error (function %s in %s):\n Error code %s\n Error message %s\n" % (function, source, errorCode, reason)
        super(Error,self).__init__(message)

class System(object):
    """This interface class provides access to the system-wide properties of the NI DAQmx installation."""
    bufSize = 1024
    _getDaqMajorVersion = defineFunction(libnidaqmx.DAQmxGetSysNIDAQMajorVersion)
    _getDaqMinorVersion = defineFunction(libnidaqmx.DAQmxGetSysNIDAQMinorVersion)
    _getDaqUpdateVersion = defineFunction(libnidaqmx.DAQmxGetSysNIDAQUpdateVersion)
    _getSysDevNames = defineFunction(libnidaqmx.DAQmxGetSysDevNames)

    def __init__(self):
        self.driverVersion()

    def handleError(self, errorCode):
        if not errorCode:
            pass
        else:
            caller = whoIsCaller()
            raise Error(source=self, function=caller, errorCode=errorCode, reason=decodeError(errorCode))

    def driverVersion(self):
            major = uInt32(0)
            minor = uInt32(0)
            update = uInt32(0)
            result = self._getDaqMajorVersion(ct.byref(major))
            self.handleError(result)
            result = self._getDaqMinorVersion(ct.byref(minor))
            self.handleError(result)
            result = self._getDaqUpdateVersion(ct.byref(update))
            self.handleError(result)
            self.version = "%d.%d.%d" % (major.value, minor.value, update.value)
            return (major.value, minor.value, update.value)

    def findDevices(self):
        buffer = ct.create_string_buffer('\000' * self.bufSize)
        result = self._getSysDevNames(ct.byref(buffer), self.bufSize)
        self.handleError(result)
        return itemsFromBuffer(buffer)

class Range(object):
    def __init__(self, min, max):
        self.min = min
        self.max = max
    def __repr__(self):
        return "Range(%f,%f)" % (self.min, self.max)

class Device(object):
    _getDevProductType = defineFunction(libnidaqmx.DAQmxGetDevProductType)
    _getDevSerialNumber = defineFunction(libnidaqmx.DAQmxGetDevSerialNum)
    _getAoPhysicalChannels = defineFunction(libnidaqmx.DAQmxGetDevAOPhysicalChans)
    _getAiPhysicalChannels = defineFunction(libnidaqmx.DAQmxGetDevAIPhysicalChans)
    _getAiVoltageRanges = defineFunction(libnidaqmx.DAQmxGetDevAIVoltageRngs)
    _getAoVoltageRanges = defineFunction(libnidaqmx.DAQmxGetDevAOVoltageRngs)
    _getAiCouplings = defineFunction(libnidaqmx.DAQmxGetDevAICouplings)
    _getAiResolution = defineFunction(libnidaqmx.DAQmxGetAIResolution)
    _resetDevice = defineFunction(libnidaqmx.DAQmxResetDevice)
    _isSimulated = defineFunction(libnidaqmx.DAQmxGetDevIsSimulated)
    _isSimultaneousSamplingSupported = defineFunction(libnidaqmx.DAQmxGetDevAISimultaneousSamplingSupported)
    _getDigitalInputLines = defineFunction(libnidaqmx.DAQmxGetDevDILines)
    _getDigitalInputPorts = defineFunction(libnidaqmx.DAQmxGetDevDIPorts)
    _getCounterInputChannels = defineFunction(libnidaqmx.DAQmxGetDevCIPhysicalChans)
    _getCounterOutputChannels = defineFunction(libnidaqmx.DAQmxGetDevCOPhysicalChans)
    _getTerminals = defineFunction(libnidaqmx.DAQmxGetDevTerminals)


    bufferSize = 2048

    _getDigitalOutputLines = defineFunction(libnidaqmx.DAQmxGetDevDOLines);
    _getDigitalOutputPorts = defineFunction(libnidaqmx.DAQmxGetDevDOPorts);

#DAQmxGetDevCOPhysicalChans(const char device[], char *data, uInt32 bufferSize);

#DAQmxGetDevAOTrigUsage(const char device[], int32 *data)
#1 	Device supports advance triggers
#2 	Device supports pause triggers
#4 	Device supports reference triggers
#8 	Device supports start triggers
#16 	Device supports handshake triggers
#32 	Device supports arm start triggers
#DAQmxGetDevAOMaxRate(const char device[], float64 *data)
#DAQmxGetDevAOMinRate(const char device[], float64 *data)


    def __init__(self, identifier):
        '''Create a device object for the given identifier, e.g. "Dev1", "Dev2", and so on. Find valid identifiers using System.findDevices()'''
        self._id = identifier

    def reset(self):
        result = self._resetDevice(self._id) # DAQmxResetDevice(const char deviceName[])
        self.handleError(result)

    def simultaneousSamplingSupported(self):
        simul = bool32(0)
        #DAQmxGetDevAISimultaneousSamplingSupported(const char device[], bool32 *data)
        result = self._isSimultaneousSamplingSupported(self._id, ct.byref(simul))
        self.handleError(result)
        return bool(simul.value)

    def isSimulated(self):
        simulated = bool32(0)
        result = self._isSimulated(self._id, ct.byref(simulated))    # DAQmxGetDevIsSimulated(const char device[], bool32 *data)
        self.handleError(result)
        return bool(simulated.value)

    def handleError(self, errorCode):
        if not errorCode:
            pass
        else:
            caller = whoIsCaller()
            raise Error(source=self, function=caller, errorCode=errorCode, reason=decodeError(errorCode))

    def serialNumber(self):
        serial = uInt32(0)
        result = self._getDevSerialNumber(self._id, ct.byref(serial))
        self.handleError(result)
        return serial.value

    def productType(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        result = self._getDevProductType(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return buffer.value

    def findDiLines(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        #DAQmxGetDevDILines(const char device[], char *data, uInt32 bufferSize);
        result = self._getDigitalInputLines(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return itemsFromBufferStripPrefix(buffer, self._id + '/')

    def findDiPorts(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        #DAQmxGetDevDIPorts(const char device[], char *data, uInt32 bufferSize)
        result = self._getDigitalInputPorts(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return buffer.value.split(',')

    def findDoLines(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        #DAQmxGetDevDOLines(const char device[], char *data, uInt32 bufferSize);
        result = self._getDigitalOutputLines(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return buffer.value.split(',')

    def findDoPorts(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        #DAQmxGetDevDOPorts(const char device[], char *data, uInt32 bufferSize);
        result = self._getDigitalOutputPorts(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return itemsFromBufferStripPrefix(buffer, self._id + '/')

    def findCiChannels(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        #DAQmxGetDevCIPhysicalChans(const char device[], char *data, uInt32 bufferSize)
        result = self._getCounterInputChannels(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return itemsFromBufferStripPrefix(buffer, self._id + '/')

    def findCoChannels(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        #DAQmxGetDevCOPhysicalChans(const char device[], char *data, uInt32 bufferSize)
        result = self._getCounterOutputChannels(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return itemsFromBufferStripPrefix(buffer, self._id + '/')

    def findTerminals(self):
        #DAQmxGetDevTerminals(const char device[], char *data, uInt32 bufferSize);
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        result = self._getTerminals(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return itemsFromBufferStripPrefix(buffer, self._id + '/')

    def findAoChannels(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        result = self._getAoPhysicalChannels(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return itemsFromBufferStripPrefix(buffer, self._id + '/')

    def findAiChannels(self):
        buffer = ct.create_string_buffer('\000' * self.bufferSize)
        result = self._getAiPhysicalChannels(self._id, ct.byref(buffer), self.bufferSize);
        self.handleError(result)
        return itemsFromBufferStripPrefix(buffer, self._id + '/')

    def findAiCouplings(self):
        couplings = uInt32(0)
        result = self._getAiCouplings(self._id, ct.byref(couplings))
        self.handleError(result)
        aiCouplings = list()
        couplings = couplings.value
        if (couplings & 2):
            aiCouplings.append('DC')
        if (couplings & 1):
            aiCouplings.append('AC')
        if (couplings & 4):
            aiCouplings.append('GND')
        if (couplings & 8):
            aiCouplings.append('HF reject')
        if (couplings & 16):
            aiCouplings.append('LF reject')
        if (couplings & 32):
            aiCouplings.append('Noise reject')
        return aiCouplings

    def voltageRangesAi(self):
        data = np.zeros((128,2),dtype=np.float64, order='C')
        result = self._getAiVoltageRanges(self._id, data.ctypes.data, data.size)
        self.handleError(result)
        rs = list()
        for range in data:
            min = range[0]
            max = range[1]
            if (min == max):
                break   # apparently the end
            else:
                rs.append(Range(min, max))
        return rs
    def voltageRangesAo(self):
        data = np.zeros((128,2),dtype=np.float64, order='C')
        result = self._getAoVoltageRanges(self._id, data.ctypes.data, data.size)
        self.handleError(result)
        rs = list()
        for range in data:
            min = range[0]
            max = range[1]
            if (min == max):
                break   # apparently the end
            else:
                rs.append(Range(min, max))
        return rs


class Task(object):
    _createTask = defineFunction(libnidaqmx.DAQmxCreateTask)
    _startTask = defineFunction(libnidaqmx.DAQmxStartTask)
    _stopTask = defineFunction(libnidaqmx.DAQmxStopTask)
    _isTaskDone = defineFunction(libnidaqmx.DAQmxIsTaskDone)
    _controlTask = defineFunction(libnidaqmx.DAQmxTaskControl)
    _clearTask = defineFunction(libnidaqmx.DAQmxClearTask)
    _digitalEdgeStartTrigger = defineFunction(libnidaqmx.DAQmxCfgDigEdgeStartTrig)
    _digitalEdgeReferenceTrigger = defineFunction(libnidaqmx.DAQmxCfgDigEdgeRefTrig)
    _analogEdgeStartTrigger = defineFunction(libnidaqmx.DAQmxCfgAnlgEdgeStartTrig)
    _analogWindowStartTrigger = defineFunction(libnidaqmx.DAQmxCfgAnlgWindowStartTrig)
    _getMaxSampleClockRate = defineFunction(libnidaqmx.DAQmxGetSampClkMaxRate)

    # Values for the Mode parameter of DAQmxTaskControl
    TASK_START = 0
    TASK_STOP = 1
    TASK_VERIFY = 2
    TASK_COMMIT = 3
    TASK_RESERVE = 4
    TASK_UNRESERVE = 5
    TASK_ABORT = 6

    GROUP_BY_CHANNEL = False    # DAQmx_Val_GroupByChannel
    GROUP_BY_SAMPLE = True      # DAQmx_Val_GroupByScanNumber

    #DAQmxGetSampClkMaxRate(TaskHandle taskHandle, float64 *data)
    #DAQmxSetSampClkRate(TaskHandle taskHandle, float64 data)

    WindowTrigger = SettingEnum({10163: ('ENTERING', 'Entering window'), 10208: ('LEAVING', 'Leaving window')})

    def __init__(self, name):
        '''Create a task object with specified name. The name is basically an arbitrary string, but required to be unique.'''
        self.name = name
        self._handle = int32(0)
        result = self._createTask(name, ct.byref(self._handle))   # DAQmxCreateTask(const char taskName[], TaskHandle *taskHandle)
        self.handleError(result)
        self.channels = list()
        self.timeOut = 2.0

    def __del__(self):
        if self._handle:
            self.clear()

    def handleError(self, errorCode):
        if not errorCode:
            pass
        else:
            caller = whoIsCaller()
            raise Error(source=self, function=caller, errorCode=errorCode, reason=decodeError(errorCode))

    def setTimeOut(self, timeOut = 1.0):
        self.timeOut = timeOut

    def handle(self):
        return self._handle

    def start(self):
        result = self._startTask(self._handle)   # DAQmxStartTask(TaskHandle taskHandle);
        self.handleError(result)

    def stop(self):
        result = self._stopTask(self._handle)    # DAQmxStopTask(TaskHandle taskHandle)
        self.handleError(result)

    def isDone(self):
        done = bool32(0)
        result = self._isTaskDone(self._handle, ct.byref(done))  # DAQmxIsTaskDone(TaskHandle taskHandle, bool32 *isTaskDone)
        self.handleError(result)
        return bool(done.value)

    def control(self, action):
        result = self._controlTask(self._handle, int32(action))  # DAQmxTaskControl(TaskHandle taskHandle, int32 action)
        self.handleError(result)

    def verify(self):
        self.control(self.TASK_VERIFY)

    def commit(self):
        self.control(self.TASK_COMMIT)

    def clear(self):
        result = self._clearTask(self._handle)    # DAQmxClearTask(TaskHandle taskHandle)
        self._handle = None
        self.handleError(result)
        self.channels = list()
        print "Task cleared"

    def reserveResources(self):
        self.control(self.TASK_RESERVE)

    def unreserveResources(self):
        self.control(self.TASK_UNRESERVE)

    def abort(self):
        self.control(self.TASK_ABORT)

    def configureTiming(self, timing):
        result = timing.applyToTask(self)
        self.handleError(result)

    def maxSampleClockRate(self):
        rate = float64(0)
        result = self._getMaxSampleClockRate(self._handle, ct.byref(rate))
        self.handleError(result)
        return rate.value

    #DAQmxSetStartTrigDelay(TaskHandle taskHandle, float64 data)
    #DAQmxSetStartTrigRetriggerable(TaskHandle taskHandle, bool32 data)

    def digitalEdgeStartTrigger(self, source, edge=Edge.RISING):
        #DAQmxCfgDigEdgeStartTrig(TaskHandle taskHandle, const char triggerSource[], int32 triggerEdge)
        result = self._digitalEdgeStartTrigger(self._handle, source, int32(edge.Code))
        self.handleError(result)

    def digitalEdgeReferenceTrigger(self, source, preTriggerSamples, edge=Edge.FALLING):
        #DAQmxCfgDigEdgeRefTrig (TaskHandle taskHandle, const char triggerSource[], int32 triggerEdge, uInt32 pretriggerSamples)
        result = self._digitalEdgeReferenceTrigger(self._handle, source, int32(edge.Code), uInt32(preTriggerSamples))
        self.handleError(result)

    def analogEdgeStartTrigger(self, source, edge=Edge.RISING, level = 0.0):
        #DAQmxCfgAnlgEdgeStartTrig(TaskHandle taskHandle, const char triggerSource[], int32 triggerSlope, float64 triggerLevel)
        result = self._analogEdgeStartTrigger(self._handle, source, int32(edge.Code), float64(level))
        self.handleError(result)

    #DAQmxSetAnlgEdgeStartTrigHyst(TaskHandle taskHandle, float64 data);
    #DAQmxSetAnlgEdgeStartTrigDigFltrEnable(TaskHandle taskHandle, bool32 data)
    #DAQmxSetAnlgEdgeStartTrigDigFltrMinPulseWidth(TaskHandle taskHandle, float64 data)

    def analogWindowStartTrigger(self, source, triggerCondition, bottom=-1.0, top=+1.0):
        # DAQmxCfgAnlgWindowStartTrig(TaskHandle taskHandle, const char triggerSource[], int32 triggerWhen, float64 windowTop, float64 windowBottom)
        if (top < bottom):
            c = top
            top = bottom
            bottom = c

        result = self._analogWindowStartTrigger(self._handle, source, int32(triggerCondition.Code), float64(top), float64(bottom))
        self.handleError(result)
    #DAQmxSetAnlgWinStartTrigDigFltrEnable(TaskHandle taskHandle, bool32 data)
    # DAQmxSetAnlgWinStartTrigDigFltrMinPulseWidth

class OutputTask(Task):
    _configureOutputBuffer = defineFunction(libnidaqmx.DAQmxCfgOutputBuffer)

    def configureOutputBuffer(self, samplesPerChannel):
        result = self._configureOutputBuffer(self._handle, ct.c_uint32(samplesPerChannel)) # DAQmxCfgOutputBuffer(TaskHandle taskHandle, uInt32 numSampsPerChan)
        self.handleError(result)

class InputTask(Task):
    _samplesAvailable = defineFunction(libnidaqmx.DAQmxGetReadAvailSampPerChan)
    _configureInputBuffer = defineFunction(libnidaqmx.DAQmxCfgInputBuffer)

    def configureInputBuffer(self, samplesPerChannel):
        result = self._configureInputBuffer(self._handle, ct.c_uint32(samplesPerChannel))  # DAQmxCfgInputBuffer(TaskHandle taskHandle, uInt32 numSampsPerChan)
        self.handleError(result)

    def samplesAvailable(self):
        samples = uInt32(0)
        #DAQmxGetReadAvailSampPerChan(TaskHandle taskHandle, uInt32 *data)
        result = self._samplesAvailable(self._handle, ct.byref(samples))
        self.handleError(result)
        return samples.value
    #DAQmxGetReadTotalSampPerChanAcquired(TaskHandle taskHandle, uInt64 *data)


class AoTask(OutputTask):
    _writeAnalogF64 = defineFunction(libnidaqmx.DAQmxWriteAnalogF64)
#    _setWriteAttribute = defineFunction(libnidaqmx.DAQmxSetWriteAttribute)

    _setWriteRegenMode = defineFunction(libnidaqmx.DAQmxSetWriteRegenMode)
    ATTRIBUTE_WRITE_REGENMODE = int32(0x1453)
    ATTRIBUTE_WRITE_OFFSET =  int32(0x190D)

    REGENERATION_ALLOW = int32(10097)
    REGENERATION_DONOTALLOW = int32(10158)

    def writeData(self, data, autoStart = False):
        samplesWritten = int32(0)
        data = np.asarray(data, dtype = np.float64, order = 'C')
        nChannels = len(self.channels)
        if nChannels != 1:
            if not data.shape[0] == nChannels:
                raise Error(self, 'writeData', 0, 'Size of data (%d) does not match number of channels' % (data.shape[0], nChannels))
            if len(data.shape) > 1:
                samplesPerChannel = data.shape[1]
            else:
                samplesPerChannel = 1
        else:
            samplesPerChannel = data.shape[0]
        #DAQmxWriteAnalogF64(TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, float64 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
        result = self._writeAnalogF64(self._handle, int32(samplesPerChannel), bool32(autoStart), float64(self.timeOut), bool32(self.GROUP_BY_CHANNEL), data.ctypes.data, ct.byref(samplesWritten), None)
        self.handleError(result)

    def addChannel(self, channel):
        if not isinstance(channel, AoChannel):
            raise TypeError, "Channel must be an AoChannel"
        channel.attachToTask(self)
        self.channels.append(channel)

    def disableRegeneration(self):
        self.enableRegeneration(False)

    def enableRegeneration(self, enable = True):
        if enable:
            self._setWriteRegenMode(self._handle, self.REGENERATION_ALLOW)
            #self._setWriteAttribute(self._handle, self.ATTRIBUTE_WRITE_REGENMODE, self.REGENERATION_ALLOW)
        else:
            self._setWriteRegenMode(self._handle, self.REGENERATION_DONOTALLOW)
            #self._setWriteAttribute(self._handle, self.ATTRIBUTE_WRITE_REGENMODE, self.REGENERATION_DONOTALLOW)

class DoTask(OutputTask):
    _writeDigitalLines = defineFunction(libnidaqmx.DAQmxWriteDigitalLines)

    def addChannel(self, channel):
        if not isinstance(channel, DoChannel):
            raise TypeError, "Channel must be a DoChannel"
        channel.attachToTask(self)
        self.channels.append(channel)

    def writeData(self, data, autoStart = False):
        samplesWritten = int32(0)
        data = np.asarray(data, dtype = np.uint8, order = 'C')
        nChannels = len(self.channels)
        if nChannels != 1:
            if not data.shape[0] == nChannels:
                raise Error
            if len(data.shape) > 1:
                samplesPerChannel = data.shape[1]
            else:
                samplesPerChannel = 1;
        else:
            samplesPerChannel = data.shape[0]
        #DAQmxWriteDigitalLines       (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout, bool32 dataLayout, uInt8 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
        result = self._writeDigitalLines(self._handle, int32(samplesPerChannel), bool32(autoStart), float64(self.timeOut), bool32(self.GROUP_BY_CHANNEL), data.ctypes.data, ct.byref(samplesWritten), None)
        self.handleError(result)

class DiTask(InputTask):
    _readDigitalLines = defineFunction(libnidaqmx.DAQmxReadDigitalLines)

    def addChannel(self, channel):
        if not isinstance(channel, DiChannel):
            raise TypeError, "Channel must be a DiChannel"
        channel.attachToTask(self)
        self.channels.append(channel)

    def readData(self, samplesPerChannel=None):
        nChannels = len(self.channels)
        if samplesPerChannel == None:
            samplesPerChannel = self.samplesAvailable()
        else:
            samplesPerChannel = int(samplesPerChannel)

        data = np.zeros((nChannels, samplesPerChannel),dtype=np.uint8, order = 'C')
        samplesPerChannelRead = int32(0)
        #DAQmxReadDigitalLines (TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, uInt8 readArray[], uInt32 arraySizeInBytes, int32 *sampsPerChanRead, int32 *numBytesPerSamp, bool32 *reserved);
        result = self._readDigitalLines(self._handle, int32(samplesPerChannel), float64(self.timeOut), bool32(self.GROUP_BY_CHANNEL), data.ctypes.data, ct.byref(samplesPerChannelRead), None)
        self.handleError(result)
        samplesPerChannelRead = samplesPerChannelRead.value
        if samplesPerChannelRead < samplesPerChannel:   # If we didn't get as much data as we wanted,
            return data[:,0:samplesPerChannelRead]      # trim the array down
        else:
            return data

class AiTask(InputTask):
    _readAnalogF64 = defineFunction(libnidaqmx.DAQmxReadAnalogF64)
    #DAQmxGetReadOverloadedChansExist(TaskHandle taskHandle, bool32 *data)

    def readData(self, samplesPerChannel=None):
        nChannels = len(self.channels)
        assert nChannels > 0
        if samplesPerChannel == None:
            samplesPerChannel = self.samplesAvailable()
        else:
            samplesPerChannel = int(samplesPerChannel)

        data = np.zeros((nChannels, samplesPerChannel),dtype=np.float64, order = 'C')
        samplesPerChannelRead = int32(0)
        # DAQmxReadAnalogF64(TaskHandle taskHandle, int32 numSampsPerChan, float64 timeout, bool32 fillMode, float64 readArray[], uInt32 arraySizeInSamps, int32 *sampsPerChanRead, bool32 *reserved);
        result = self._readAnalogF64(self._handle, int32(samplesPerChannel), float64(self.timeOut), bool32(self.GROUP_BY_CHANNEL), data.ctypes.data, data.size, ct.byref(samplesPerChannelRead), None)
        self.handleError(result)
        samplesPerChannelRead = samplesPerChannelRead.value

        if samplesPerChannelRead < samplesPerChannel:
            return data[:,0:samplesPerChannelRead]
        else:
            return data

    def addChannel(self, channel):
        if not isinstance(channel, AiChannel):
            raise TypeError, "Channel must be an AnalogInputChannel"
        channel.attachToTask(self)
        self.channels.append(channel)

class Timing(object):
    _configureSampleClockTiming = defineFunction(libnidaqmx.DAQmxCfgSampClkTiming)

    SampleMode = SettingEnum({10178: ('FINITE', 'Finite samples'), 10123: ('CONTINUOUS', 'Continuos Samples'), 12522: ('HWTIMED_SP', 'Hardware timed, single point')})

    def __init__(self, rate = 1000, samplesPerChannel = 1000, activeEdge = Edge.RISING):
        self.rate = rate
        self.samplesPerChannel = samplesPerChannel
        self.sampleMode = Timing.SampleMode.CONTINUOUS
        self.activeEdge = activeEdge
        self.source = 'OnboardClock'

    def setClockSource(self, source = 'OnboardClock'):
        self.source = source

    def setSamplesPerChannel(self, samplesPerChannel):
        self.samplesPerChannel = int(samplesPerChannel)

    def setRate(self, rate):
        self.rate = rate

    def setActiveEdge(self, activeEdge):
        self.activeEdge = activeEdge

    def setSampleMode(self, sampleMode):
        self.sampleMode = sampleMode

    def applyToTask(self, task):
        # DAQmxCfgSampClkTiming(TaskHandle taskHandle, const char source[], float64 rate, int32 activeEdge, int32 sampleMode, uInt64 sampsPerChan);
        return self._configureSampleClockTiming(task.handle(), self.source, float64(self.rate), int32(self.activeEdge.Code), int32(self.sampleMode.Code), uInt64(self.samplesPerChannel))

class ImplicitTiming(object):
    _configureImplicitTiming = defineFunction(libnidaqmx.DAQmxCfgImplicitTiming)
    SampleMode = SettingEnum({10178: ('FINITE', 'Finite samples'), 10123: ('CONTINUOUS', 'Continuous Samples'), 12522: ('HWTIMED_SP', 'Hardware timed, single point')})
    def __init__(self, sampleMode = None, numberOfPulses=0):
        self._numberOfPulses = int(numberOfPulses)
        if sampleMode is not None:
            self._sampleMode = sampleMode
        elif numberOfPulses > 0:
            self._sampleMode = ImplicitTiming.SampleMode.FINITE
        else:
            self._sampleMode = ImplicitTiming.SampleMode.CONTINUOUS

    def applyToTask(self, task):
        # int32 DAQmxCfgImplicitTiming (TaskHandle taskHandle, int32 sampleMode, uInt64 sampsPerChanToAcquire);
        return self._configureImplicitTiming(task.handle(), int32(self._sampleMode.Code), uInt64(self._numberOfPulses))

class Channel(object):
    def __init__(self, physicalChannel):
        self.physicalChannel = physicalChannel
    def handleError(self, errorCode):
        if not errorCode:
            pass
        else:
            caller = whoIsCaller()
            raise Error(source=self, function=caller, errorCode=errorCode, reason=decodeError(errorCode))

class CounterOutputTask(OutputTask):
    def addChannel(self, channel):
        if not isinstance(channel, CounterOutputChannel):
            raise TypeError, "Channel must be a CounterOutputChannel"
        channel.attachToTask(self)
        self.channels.append(channel)


class DigitalChannel(Channel):
    DAQmx_Val_ChanPerLine = 0
    DAQmx_Val_ChanForAllLines = 1
    pass

class DoChannel(DigitalChannel):
    _createDigitalOutputChannel = defineFunction(libnidaqmx.DAQmxCreateDOChan)
    def __init__(self, lines, names=None, lineGrouping = DigitalChannel.DAQmx_Val_ChanPerLine):
        self.lines = lines
        self.names = names
        self.lineGrouping = lineGrouping

    def attachToTask(self, task):
        self.taskHandle = task.handle()
        #int32 DAQmxCreateDOChan (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
        result = self._createDigitalOutputChannel(self.taskHandle, str(self.lines), self.names, int32(self.lineGrouping))
        self.handleError(result)


class DiChannel(DigitalChannel):
    _createDigitalInputChannel = defineFunction(libnidaqmx.DAQmxCreateDIChan)
    def __init__(self, lines, names=None, lineGrouping = DigitalChannel.DAQmx_Val_ChanPerLine):
        self.lines = lines
        self.names = names
        self.lineGrouping = lineGrouping
    def attachToTask(self, task):
        self.taskHandle = task.handle()
        #int32 DAQmxCreateDIChan (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
        result = self._createDigitalInputChannel(self.taskHandle, self.lines, self.names, int32(self.lineGrouping))
        self.handleError(result)


class AnalogChannel(Channel):
    VOLTS = 10348   # DAQmx_Val_Volts
    def __init__(self, physicalChannel, minimum, maximum, assignedName):
        super(AnalogChannel, self).__init__(physicalChannel)
        self.minimum = minimum
        self.maximum = maximum
        self.assignedName = assignedName

class AiChannel(AnalogChannel):
    _createAiVoltageChannel = defineFunction(libnidaqmx.DAQmxCreateAIVoltageChan)

    TerminalConfiguration = SettingEnum({-1:('DEFAULT', 'Default'), 10083:('RSE', 'RSE'), 10078:('NRSE', 'NRSE'), 10106:('DIFF', 'Differential'), 12529:('PSEUDO_DIFF', 'Pseudo-differential')})

    def __init__(self, physicalChannel, minimum, maximum, assignedName = None):
        super(AiChannel, self).__init__(physicalChannel, minimum, maximum, assignedName)
        self.terminalConfiguration = AiChannel.TerminalConfiguration.DEFAULT

    def setTerminalConfiguration(self, terminalConfiguration):
        self.terminalConfiguration = terminalConfiguration

    def attachToTask(self, task):
        # DAQmxCreateAIVoltageChan (TaskHandle taskHandle, const char physicalChannel[], const char nameToAssignToChannel[], int32 terminalConfig, float64 minVal, float64 maxVal, int32 units, const char customScaleName[]
        self.taskHandle = task.handle()
        result = self._createAiVoltageChannel(self.taskHandle, self.physicalChannel, self.assignedName, int32(self.terminalConfiguration.Code), float64(self.minimum), float64(self.maximum), int32(self.VOLTS), None)
        self.handleError(result)

    def aiResolution(self):  # Only when associated with task
        resolution = float64(0)
        # DAQmxGetAIResolution(TaskHandle taskHandle, const char channel[], float64 *data)
        result = self._getAiResolution(self.taskHandle, self.physicalChannel, ct.byref(resolution))
        self.handleError(result)
        return resolution.value

class AoChannel(AnalogChannel):
    _createAoVoltageChannel = defineFunction(libnidaqmx.DAQmxCreateAOVoltageChan)

    #define DAQmx_Val_RSE                                                     10083 // RSE
    #define DAQmx_Val_Diff                                                    10106 // Differential
    #define DAQmx_Val_PseudoDiff                                              12529 // Pseudodifferential
    #TerminalConfiguration = SettingEnum({10083:('RSE', 'RSE'), 10106: ('DIFF', 'Differential'), 12529:('PSEUDO_DIFF', 'Pseudo-differential')})

    def __init__(self, physicalChannel, minimum, maximum, assignedName = None):
        '''Create an analog output channel, specified by name. You also need to specify minimum and maximum voltages.'''
        super(AoChannel, self).__init__(physicalChannel, minimum, maximum, assignedName)

    def attachToTask(self, task):
        self.taskHandle = task.handle()
        # DAQmxCreateAOVoltageChan(TaskHandle taskHandle, const char physicalChannel[], const char nameToAssignToChannel[], float64 minVal, float64 maxVal, int32 units, const char customScaleName[])
        result = self._createAoVoltageChannel(self.taskHandle, self.physicalChannel, self.assignedName, float64(self.minimum), float64(self.maximum), self.VOLTS, None)
        self.handleError(result)


class IdleStates:
    HIGH = 10192    # DAQmx_Val_High
    LOW  = 10214    # DAQmx_Val_Low



class CounterOutputChannel(Channel):
    _getPulseIdleState = defineFunction(libnidaqmx.DAQmxGetCOPulseIdleState)
    _setPulseIdleState = defineFunction(libnidaqmx.DAQmxSetCOPulseIdleState)

    DAQmx_Val_Seconds = 10364
    DAQmx_Val_Ticks   = 10304

    def __init__(self, physicalChannel, idleState = False, initialDelay=0, assignedName = None):
        super(CounterOutputChannel, self).__init__(physicalChannel)
        self._initalDelay = float(initialDelay)
        self._idleState = idleState
        self.assignedName = assignedName

    def setPulseIdleState(self, high):
        #int32 __CFUNC DAQmxSetCOPulseIdleState(TaskHandle taskHandle, const char channel[], int32 data)
        if high:
            v = IdleStates.HIGH
        else:
            v = IdleStates.LOW
        result = self._setPulseIdleState(self.taskHandle, self.physicalChannel, int32(v))
        self.handleError(result)
        self._idleState = high

    def pulseIdleState(self):
        idleState = int32(0)
        result = self._getPulseIdleState(self.taskHandle, self.physicalChannel, ct.byref(idleState))
        self.handleError(result)
        if idleState.value == IdleStates.HIGH:
            return True
        elif idleState.value == IdleStates.LOW:
            return False
        else:
            raise "Unknown idle state"

class CoChannelFrequency(CounterOutputChannel):
    _getPulseDutyCycle = defineFunction(libnidaqmx.DAQmxGetCOPulseDutyCyc)
    _setPulseDutyCycle = defineFunction(libnidaqmx.DAQmxSetCOPulseDutyCyc)
    _getPulseFrequency = defineFunction(libnidaqmx.DAQmxGetCOPulseFreq)
    _setPulseFrequency = defineFunction(libnidaqmx.DAQmxSetCOPulseFreq)

    def __init__(self, physicalChannel, frequency, dutyCycle, idleState = False, initialDelay=0,  assignedName = None):
        super(CoChannelTime, self).__init__(physicalChannel, idleState, initialDelay, assignedName)
        self._frequency = float(frequency)
        self._dutyCycle = float(dutyCycle)

    def setPulseDutyCycle(self, percent):
        '''Change the duty cycle of a (running) pulse train. Note: You have to update pulseFrequency afterwards in order for this to take effect.'''
        # int32 __CFUNC DAQmxSetCOPulseDutyCyc(TaskHandle taskHandle, const char channel[], float64 data)
        result = self._setPulseDutyCycle(self.taskHandle, self.physicalChannel, float64(percent))
        self.handleError(result)

    def pulseDutyCycle(self):
        dc = float64(0)
        # int32 __CFUNC DAQmxGetCOPulseDutyCyc(TaskHandle taskHandle, const char channel[], float64 *data)
        result = self._getPulseDutyCycle(self.taskHandle, self.physicalChannel, ct.byref(dc))
        self.handleError(result)
        return dc.value

    def setPulseFrequency(self, Hz):
        # int32 __CFUNC DAQmxSetCOPulseFreq(TaskHandle taskHandle, const char channel[], float64 data)
        result = self._setPulseFrequency(self.taskHandle, self.physicalChannel, float64(Hz))
        self.handleError(result)

    def pulseFrequency(self):
        f = float64(0)
        # int32 __CFUNC DAQmxGetCOPulseFreq(TaskHandle taskHandle, const char channel[], float64 *data)
        result = self._getPulseFrequency(self.taskHandle, self.physicalChannel, ct.byref(f))
        self.handleError(result)
        return f.value

    def attachToTask(self, task):
        print "Not implemented"


class CoChannelTime(CounterOutputChannel):
    _createCoPulseChannelTime = defineFunction(libnidaqmx.DAQmxCreateCOPulseChanTime)
    _getPulseHighTime = defineFunction(libnidaqmx.DAQmxGetCOPulseHighTime)
    _setPulseHighTime = defineFunction(libnidaqmx.DAQmxSetCOPulseHighTime)
    _getPulseLowTime = defineFunction(libnidaqmx.DAQmxGetCOPulseLowTime)
    _setPulseLowTime = defineFunction(libnidaqmx.DAQmxSetCOPulseLowTime)

    def __init__(self, physicalChannel, lowTime, highTime, idleState = False, initialDelay=0,  assignedName = None):
        super(CoChannelTime, self).__init__(physicalChannel, idleState, initialDelay, assignedName)
        self._lowTime = float(lowTime)
        self._highTime = float(highTime)
    def setPulseHighTime(self, seconds):
        '''Update the time period that the pulse will be held high'''
        # int32 __CFUNC DAQmxSetCOPulseHighTime(TaskHandle taskHandle, const char channel[], float64 data)

        result = self._setPulseHighTime(self.taskHandle, self.physicalChannel, float64(seconds))
        self.handleError(result)
        self._highTime = seconds

    def pulseHighTime(self):
        t = float64(0)
        # int32 __CFUNC DAQmxGetCOPulseHighTime(TaskHandle taskHandle, const char channel[], float64 *data);
        result = self._getPulseHighTime(self.taskHandle, self.physicalChannel, ct.byref(t))
        self.handleError(result)
        self._pulseHighTime = t.value
        return t.value

    def setPulseLowTime(self, seconds):
        '''Update the time period that the pulse will be held high'''
        # int32 __CFUNC DAQmxSetCOPulseLowTime(TaskHandle taskHandle, const char channel[], float64 data)
        result = self._setPulseLowTime(self.taskHandle, self.physicalChannel, float64(seconds))
        self.handleError(result)
        self._lowTime = seconds

    def pulseLowTime(self):
        t = float64(0)
        # int32 __CFUNC DAQmxGetCOPulseLowTime(TaskHandle taskHandle, const char channel[], float64 *data);
        result = self._getPulseLowTime(self.taskHandle, self.physicalChannel, ct.byref(t))
        self.handleError(result)
        self._pulseLowTime = t.value
        return t.value

    def attachToTask(self, task):
        self.taskHandle = task.handle()
        #int32 DAQmxCreateCOPulseChanTime (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], int32 units, int32 idleState, float64 initialDelay, float64 lowTime, float64 highTime);
        if self._idleState:
            v = IdleStates.HIGH
        else:
            v = IdleStates.LOW
        result = self._createCoPulseChannelTime(self.taskHandle, self.physicalChannel, self.assignedName, int32(self.DAQmx_Val_Seconds), int32(v), float64(self._initalDelay), float64(self._lowTime), float64(self._highTime))
        self.handleError(result)

if __name__ == '__main__':
    import time
    sys = System()
    print "DAQmx version:", sys.version
    devs = sys.findDevices()
    print "Number of devices:", len(devs)
    print "Devices: ", devs


    dev = Device('Dev4')
    print "SimultaneousSampling: ", dev.simultaneousSamplingSupported()
    print "AI channels:", dev.findAiChannels()

    print "DI lines: ", dev.findDiLines()
    print "DI ports: ", dev.findDiPorts()
    print "CI channels: ", dev.findCiChannels()
    print "CO channels: ", dev.findCoChannels()
    print "Terminals", dev.findTerminals()
    coChannel0 = CoChannelTime('/Dev4/ctr0', 10, 10)
    coChannel1 = CoChannelTime('/Dev4/ctr1', 45E-6, 5.00005E-6)
    coTask = CounterOutputTask('COTASK')
    coTask.addChannel(coChannel0)
    coTask.addChannel(coChannel1)
    coTiming = ImplicitTiming(ImplicitTiming.SampleMode.CONTINUOUS)
    coTask.configureTiming(coTiming)
    coTask.start()
    print 'Pulse high-time 0:', coChannel0.pulseHighTime()
    print 'Pulse low-time 0:', coChannel0.pulseLowTime()
    print 'Pulse high-time 1:', coChannel1.pulseHighTime()
    print 'Pulse low-time 1:', coChannel1.pulseLowTime()
    print 'Idle state:', coChannel0.pulseIdleState()
    time.sleep(5)
    coTask.stop()
    print "Done pulsing"
    sys.exit()

    do1 = DoChannel('/Dev4/port0/line0')
    do2 = DoChannel('/Dev4/port0/line1')
    doTask = DoTask("DO")
    doTask.addChannel(do1)
    doTask.addChannel(do2)
    for i in range(0,10):
        doTask.writeData((True, True), autoStart=True)
        print "On"
        time.sleep(2)
        doTask.writeData((False, False), autoStart=True)
        print "Off"
        time.sleep(2)

    print "Is task done?", doTask.isDone()
    doTask.stop()


    dev = Device('Dev4')
    print "SimultaneousSampling: ", dev.simultaneousSamplingSupported()
    print "DI ports: ", dev.findDiPorts()
    print "DO ports: ", dev.findDoPorts()
    print "DI lines: ", dev.findDiLines()
    print "DO lines: ", dev.findDoLines()
    print "CI channels: ", dev.findCiChannels()
    print "CO channels: ", dev.findCoChannels()
    print "Terminals", dev.findTerminals()
    ao = AoChannel('Dev3/ao0', -3.5, 3.5)
    timing = Timing()
    timing.setRate(96000)
    #timing.setSampleMode(Timing.SampleMode.FINITE)
    #timing.setActiveEdge(Timing.ActiveEdge.RISING)
    timing.setSamplesPerChannel(1250)
    otask = AoTask('Output')
    otask.addChannel(ao)
    otask.configureTiming(timing)
    sineWave = 3.5 * np.sin(np.arange(1250, dtype=np.float64)*2*np.pi/1250)
    otask.digitalEdgeStartTrigger('/Dev3/ai/StartTrigger')
    otask.writeData(sineWave)
    otask.start()

    ai1 = AiChannel('Dev3/ai1', -10,+10)
    ai2 = AiChannel('Dev3/ai2', -10,+10)
    itask = AiTask('Input')
    itask.addChannel(ai1)
    itask.addChannel(ai2)
    itask.configureTiming(timing)
    itask.start()
    for i in range(10):
        #print itask.samplesAvailable()
        samples = itask.readData()
        print samples.shape
        if itask.isDone() or otask.isDone():
            break
    itask.stop()
    otask.stop()

#Supported output clock-rates for NI-4431:
#800.000000,  1.250000e3,  1.500000e3,  1.600000e3,  2.500000e3,
#3.0e3,  3.200000e3,  5.0e3,  6.0e3,  6.400000e3,  10.0e3,  12.0e3,
#12.800000e3,  20.0e3,  24.0e3,  25.600000e3,  40.0e3,  48.0e3,  51.200000e3,
#80.0e3,  96.0e3
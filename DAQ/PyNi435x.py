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
Python interface to NI's 435x data acquisition card
Unfortunately currently crashes machine, perhaps due to 32/64 bit mismatch?

@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

import ctypes as ct

libName = 'C:\\Program Files\\IVI Foundation\\VISA\\WinNT\\Bin\\ni435x_32.dll'

lib = ct.windll.LoadLibrary(libName)
print lib

ViUInt16 = ct.c_uint16
ViUInt32 = ct.c_uint32
ViInt16 = ct.c_int16
ViInt32 = ct.c_int32
ViReal64 = ct.c_double
ViString = ct.c_char_p

ViBoolean = ViUInt16
ViSession = ViUInt32
ViStatus = ViInt32
ViRsrc = ViString
Pointer = ct.c_void_p
byref = ct.byref

import numpy as np

def defineFunction(function, inputargs=None):
    f = function
    f.argtypes = inputargs
    f.restype = ViStatus
    return f


# ViStatus _VI_FUNC NI435X_init (ViRsrc resourceName, ViBoolean IDQuery, ViBoolean resetDevice, ViPSession DAQsession);
_NI435X_Init = defineFunction(lib.NI435X_init, [ViRsrc, ViBoolean, ViBoolean, Pointer])
# ViStatus _VI_FUNC NI435X_Set_Range (ViSession DAQsession, ViChar _VI_FAR channelString[], ViReal64 lowLimits, ViReal64  highLimits);
_NI435X_SetScanList = defineFunction(lib.NI435X_Set_Scan_List, [ViSession, ViString])
# ViStatus _VI_FUNC NI435X_Set_Number_Of_Scans (ViSession DAQsession, ViInt32 numberOfScans);
_NI435X_SetRange = defineFunction(lib.NI435X_Set_Range, [ViSession, ViString, ViReal64, ViReal64])
# ViStatus _VI_FUNC NI435X_Set_Powerline_Frequency (ViSession DAQsession, ViInt16 powerlineFrequency);
_NI435X_SetPowerline_Frequency = defineFunction(lib.NI435X_Set_Powerline_Frequency, [ViSession, ViInt16])
# ViStatus _VI_FUNC NI435X_Set_Auto_Zero (ViSession DAQsession, ViBoolean autoZero);
_NI435X_SetAutoZero = defineFunction(lib.NI435X_Set_Auto_Zero, [ViSession, ViBoolean])
# ViStatus _VI_FUNC NI435X_Set_Gnd_Ref (ViSession DAQsession, ViChar _VI_FAR channelString[], ViInt16 groundReference);
_NI435X_SetGndRef = defineFunction(lib.NI435X_Set_Gnd_Ref, [ViSession, ViString, ViInt16])
# ViStatus _VI_FUNC NI435X_Set_Reading_Rate (ViSession DAQsession, ViInt16 readingRate);
_NI435X_SetReadingRate = defineFunction(lib.NI435X_Set_Reading_Rate, [ViSession, ViInt16])
# ViStatus _VI_FUNC NI435X_Set_Scan_List (ViSession DAQsession, ViChar _VI_FAR channelString[]);
_NI435X_SetNumberOfScans = defineFunction(lib.NI435X_Set_Number_Of_Scans, [ViSession, ViInt32])
# ViStatus _VI_FUNC NI435X_Get_Number_Of_Channels (ViSession DAQsession, ViUInt16 *numberOfChannels);
_NI435X_GetNumberOfChannels = defineFunction(lib.NI435X_Get_Number_Of_Channels, [ViSession, Pointer])
# ViStatus _VI_FUNC NI435X_Check_And_Read (ViSession DAQsession, ViReal64 timeout, ViInt32 *scansRead, ViReal64 _VI_FAR scansBuffer[]);
_NI435X_CheckAndRead = defineFunction(lib.NI435X_Check_And_Read, [ViSession, ViReal64, Pointer, np.ctypeslib.ndpointer(dtype=np.float64, ndim=1, flags='aligned,writeable,C_CONTIGUOUS')])
#_NI435X_CheckAndRead = defineFunction(lib.NI435X_Check_And_Read, [ViSession, ViReal64, Pointer, ct.POINTER(ViReal64)])
# ViStatus _VI_FUNC NI435X_Read (ViSession DAQsession, ViInt32 numerOfScans, ViReal64 timeout, ViReal64 _VI_FAR scansRead[]);
_NI435X_Read = defineFunction(lib.NI435X_Read, [ViSession, ViInt32, ViReal64, Pointer])
# ViStatus _VI_FUNC NI435X_Acquisition_StartStop (ViSession DAQsession, ViInt16 control);
_NI435X_AcquisitionStartStop = defineFunction(lib.NI435X_Acquisition_StartStop, [ViSession, ViInt16])
# ViStatus _VI_FUNC NI435X_Check (ViSession DAQsession, ViPInt32 scansAvailable, ViPBoolean overflow);
_NI435X_Check = defineFunction(lib.NI435X_Check, [ViSession, Pointer, Pointer])
# ViStatus _VI_FUNC NI435X_reset (ViSession DAQsession);
_NI435X_Reset = defineFunction(lib.NI435X_reset, [ViSession])
# ViStatus _VI_FUNC NI435X_self_test (ViSession DAQsession, ViPInt16 selfTestResult, ViChar _VI_FAR selfTestMessage[]);
_NI435X_SelfTest = defineFunction(lib.NI435X_self_test, [ViSession, Pointer, ViString])
# ViStatus _VI_FUNC NI435X_revision_query (ViSession DAQsession, ViChar _VI_FAR instrumentDriverRevision[], ViChar _VI_FAR firmwareRevision[]);
_NI435X_RevisionQuery = defineFunction(lib.NI435X_revision_query, [ViSession, ViString, ViString])
# ViStatus _VI_FUNC NI435X_error_query (ViSession DAQsession, ViPInt32 errorCode, ViChar _VI_FAR errorMessage[]);
_NI435X_ErrorQuery = defineFunction(lib.NI435X_error_query, [ViSession, Pointer, ViString])
# ViStatus _VI_FUNC NI435X_error_message (ViSession DAQsession, ViStatus errorCode, ViChar _VI_FAR errorMessage[]);
_NI435X_ErrorMessage = defineFunction(lib.NI435X_error_message, [ViSession, ViStatus, Pointer])
# ViStatus _VI_FUNC NI435X_close (ViSession DAQsession);
_NI435X_Close = defineFunction(lib.NI435X_close, [ViSession])
# ViStatus _VI_FUNC NI435X_system_query (ViSession DAQsession, ViChar _VI_FAR nidaqVer[]);
_NI435X_SystemQuery = defineFunction(lib.NI435X_system_query, [ViSession, ViString])
# ViStatus _VI_FUNC NI435X_Set_Auto_Zero_Mode (ViSession DAQsession, ViInt16 autoZeroMode);
_NI435X_SetAutoZeroMode = defineFunction(lib.NI435X_Set_Auto_Zero_Mode, [ViSession, ViInt16])

class NI345X():

    WARNING_CODES = [-1302, -1303, -1304, -1311, -1320]
    NI435X_START = 0
    NI435X_STOP  = 1

    NI435X_OFF = ViInt16(0)
    NI435X_ON  = ViInt16(1)


    class PowerlineFrequency:
        F50Hz = ViInt16(0)
        F60Hz = ViInt16(1)

    class ReadingRate:
        FAST = ViInt16(0)
        SLOW = ViInt16(1)

    class AutoZeroMode:
        ZERO_AT_START  = ViInt16(1)
        ZERO_EACH_SCAN = ViInt16(2)

    def __init__(self, resourceName='DAQ::1', idQuery=True, resetDevice=False):
        self.session = None
        session = ViSession()
        ret = _NI435X_Init(resourceName, idQuery, resetDevice, byref(session))
        self.handleError(ret)
        self.session = session

    def setScanList(self, channels):
        self.channels = channels
        ret = _NI435X_SetScanList(self.session, self.channelString)
        self.handleError(ret)

    @property
    def channelString(self):
        return ','.join(map(str, self.channels))

    def setRange(self,lowLimit, highLimit):
        ret = _NI435X_SetRange(self.session, self.channelString, lowLimit, highLimit)
        self.handleError(ret)

    def setPowerLineFrequency(self, frequency):
        if frequency == 50:
            frequency = self.PowerlineFrequency.F50Hz
        elif frequency == 60:
            frequency = self.PowerlineFrequency.F60Hz
        ret = _NI435X_SetPowerline_Frequency(self.session, frequency)
        self.handleError(ret)

    def enableAutoZero(self, enable=True):
        ret = _NI435X_SetAutoZero(self.session, enable)
        self.handleError(ret)

    def disableAutoZero(self):
        self.enableAutoZero(False)

    def setAutoZeroMode(self, mode):
        ret = _NI435X_SetAutoZeroMode(self.session, mode)
        self.handleError(ret)

    def enableGroundReference(self, channels, enable=True):
        channelString = ','.join(map(str, channels))
        if enable:
            ret = _NI435X_SetGndRef(self.session, channelString, self.NI435X_ON)
        else:
            ret = _NI435X_SetGndRef(self.session, channelString, self.NI435X_OFF)
        self.handleError(ret)

    def disableGroundReference(self):
        self.enableGroundReference(False)

    def setReadingRate(self, rate):
        ret = _NI435X_SetReadingRate(self.session, rate)
        self.handleError(ret)

    def setNumberOfScans(self, numberOfScans):
        ret = _NI435X_SetNumberOfScans(self.session, numberOfScans)
        self.handleError(ret)

    def numberOfChannels(self):
        numberOfChannels = ViUInt16()
        ret = _NI435X_GetNumberOfChannels(self.session, byref(numberOfChannels))
        self.handleError(ret)
        return numberOfChannels.value

    def check(self):
        scansAvailable = ViInt32()
        backlog = ViBoolean()
        ret = _NI435X_Check(self.session, byref(scansAvailable), byref(backlog))
        self.handleError(ret)
        return scansAvailable.value, backlog.value

    def checkAndRead(self, scansToRead = 1000, timeOut = 1.):
        samples = scansToRead * self.numberOfChannels()
        scansBuffer = np.zeros((samples,), dtype=float)
        scansToRead = ViInt32(scansToRead)
        print "Samples:", samples
#        scansBufferType = ViReal64*samples
#        scansBuffer = scansBufferType()
        ret = _NI435X_CheckAndRead(self.session, timeOut, byref(scansToRead), scansBuffer )
        print "Scans actually read:", scansToRead.value
        self.handleError(ret)
        print "scansBuffer:", scansBuffer
        return scansBuffer

    def read(self):
        #ret = _NI435X_Read(self.session, )
        #self.handleError(ret)
        pass

    def startAcquisition(self, start=True):
        if start:
            ret = _NI435X_AcquisitionStartStop(self.session, self.NI435X_START)
        else:
            ret = _NI435X_AcquisitionStartStop(self.session, self.NI435X_STOP)

        self.handleError(ret)

    def stopAcquisition(self):
        self.startAcquisition(False)

    def errorMessage(self, errorCode):
        errorMessage = ct.create_string_buffer(256)
        _NI435X_ErrorMessage(self.session, errorCode, byref(errorMessage))
        return errorMessage.value

    def close(self):
        if self.session is not None:
            ret = _NI435X_Close(self.session)
            self.handleError(ret)
            self.session = None

    def revisionQuery(self):
        instrumentDriverRev = ct.create_string_buffer(256)
        firmwareRev = ct.create_string_buffer(256)
        ret = _NI435X_RevisionQuery(self.session, instrumentDriverRev, firmwareRev)
        self.handleError(ret)
        return instrumentDriverRev.value, firmwareRev.value

    def handleError(self, errorCode):
        if errorCode == 0:
            return
        else:
            message = self.errorMessage(errorCode)
        if errorCode in self.WARNING_CODES:
            print 'NI345X warning (code %d): %s' % (errorCode, message)
        else:
            raise Exception('NI345X warning (code %d): %s' % (errorCode, message))


if __name__ == '__main__':
    import time
    daq = NI345X('DAQ::2')
    #driverRev, firmwareRev = daq.revisionQuery()
    #print "Driver:", driverRev
    #print "FW:", firmwareRev
    daq.setScanList([3,5,8,9])
    #daq.disableAutoZero()
    daq.setPowerLineFrequency(daq.PowerlineFrequency.F60Hz)
    daq.enableGroundReference([3,5])
    daq.setReadingRate(daq.ReadingRate.SLOW)
    daq.setRange(-15.,+15.)
    daq.setNumberOfScans(2)
    print "Number of channels:", daq.numberOfChannels()
    print "Starting..."
    daq.startAcquisition()
    print "Waiting..."
    time.sleep(5)
    d = daq.checkAndRead(10)
    daq.stopAcquisition()
    daq.close()

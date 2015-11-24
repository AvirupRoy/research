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
import os, time
import numpy as np

libName = 'C:\\Program Files\\IVI Foundation\\VISA\\WinNT\\Bin\\ni435x_32.dll'

lib = ct.windll.LoadLibrary(libName)

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
_NI435X_CheckAndRead = defineFunction(lib.NI435X_Check_And_Read, [ViSession, ViReal64, Pointer, np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='aligned,writeable,F_CONTIGUOUS')])
# ViStatus _VI_FUNC NI435X_Read (ViSession DAQsession, ViInt32 numberOfScans, ViReal64 timeout, ViReal64 _VI_FAR scansRead[]);
_NI435X_Read = defineFunction(lib.NI435X_Read, [ViSession, ViInt32, ViReal64, np.ctypeslib.ndpointer(dtype=np.float64, ndim=2, flags='aligned,writeable,F_CONTIGUOUS')])
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

    def __init__(self, resourceName='DAQ::1', idQuery=True, resetDevice=False, drives = ['C:\Users\WISP10', 'D:']):
        self._session = None
        self._running = False
        for drive in drives:
            self.fileSystemGuard('%s\PyNi435x_Guard.txt' % drive)
        time.sleep(1)
        session = ViSession()
        ret = _NI435X_Init(resourceName, idQuery, resetDevice, byref(session))
        self.handleError(ret)
        self._session = session
        
    def fileSystemGuard(self, fileName):
        f = open( fileName, 'w+' )
        f.write("Guard File")
        f.flush()
        os.fsync(f.fileno())
        f.close()
        
    def __del__(self):
        print "Deleting NI435x"
        self.close()

    def setScanList(self, channels):
        self._channels = channels
        ret = _NI435X_SetScanList(self._session, self.channelString)
        self.handleError(ret)

    def scanList(self):
        return self._channels

    @property
    def channelString(self):
        return ','.join(map(str, self._channels))

    def setRange(self,lowLimit, highLimit):
        ret = _NI435X_SetRange(self._session, self.channelString, lowLimit, highLimit)
        self.handleError(ret)

    def setPowerLineFrequency(self, frequency):
        if frequency == 50:
            frequency = self.PowerlineFrequency.F50Hz
        elif frequency == 60:
            frequency = self.PowerlineFrequency.F60Hz
        ret = _NI435X_SetPowerline_Frequency(self._session, frequency)
        self.handleError(ret)

    def enableAutoZero(self, enable=True):
        ret = _NI435X_SetAutoZero(self._session, enable)
        self.handleError(ret)

    def disableAutoZero(self):
        self.enableAutoZero(False)

    def setAutoZeroMode(self, mode):
        ret = _NI435X_SetAutoZeroMode(self._session, mode)
        self.handleError(ret)

    def enableGroundReference(self, channels, enable=True):
        channelString = ','.join(map(str, channels))
        if enable:
            ret = _NI435X_SetGndRef(self._session, channelString, self.NI435X_ON)
        else:
            ret = _NI435X_SetGndRef(self._session, channelString, self.NI435X_OFF)
        self.handleError(ret)

    def disableGroundReference(self):
        self.enableGroundReference(False)

    def setReadingRate(self, rate):
        ret = _NI435X_SetReadingRate(self._session, rate)
        self.handleError(ret)

    def setNumberOfScans(self, numberOfScans):
        ret = _NI435X_SetNumberOfScans(self._session, numberOfScans)
        self.handleError(ret)

    def numberOfChannels(self):
        numberOfChannels = ViUInt16()
        ret = _NI435X_GetNumberOfChannels(self._session, byref(numberOfChannels))
        self.handleError(ret)
        return numberOfChannels.value

    def check(self):
        '''Checks for available data and returns scans available in the buffer and whether or not there is unread data in the buffer.'''
        scansAvailable = ViInt32()
        backlog = ViBoolean()
        ret = _NI435X_Check(self._session, byref(scansAvailable), byref(backlog))
        self.handleError(ret)
        return scansAvailable.value, bool(backlog.value)

    def checkAndRead(self, scansToRead = 1000, timeOut = 1.):
        '''Reads the number of measurements available unless a timeout occurs. Returns measurements from the instrument based upon its current configuration.'''
        nChannels = self.numberOfChannels()
        scansBuffer = np.ones((nChannels,scansToRead), dtype=float, order='F')*np.nan
        scansToRead = ViInt32(scansToRead)
        ret = _NI435X_CheckAndRead(self._session, timeOut, byref(scansToRead), scansBuffer )
        self.handleError(ret)
        return scansBuffer[:,0:scansToRead.value]

    def read(self, scansToRead = 1, timeOut = 1.):
        '''Reads the number of measurements specified in scansToRead unless a timeout occurs, and returns measurements from the device based upon its current configuration.'''
        nChannels = self.numberOfChannels()
        scansBuffer = np.ones((nChannels,scansToRead), dtype=float, order='F')*np.nan
        scansToRead = ViInt32(scansToRead)
        ret = _NI435X_Read(self._session, scansToRead, timeOut, scansBuffer)
        self.handleError(ret)
        return scansBuffer

    def startAcquisition(self, start=True):
        if start:
            ret = _NI435X_AcquisitionStartStop(self._session, self.NI435X_START)
            self.handleError(ret)
            self._running = True
        else:
            ret = _NI435X_AcquisitionStartStop(self._session, self.NI435X_STOP)
            self.handleError(ret)
            self._running = False

    def stopAcquisition(self):
        self.startAcquisition(False)

    def errorMessage(self, errorCode):
        errorMessage = ct.create_string_buffer(256)
        _NI435X_ErrorMessage(self._session, errorCode, byref(errorMessage))
        return errorMessage.value

    def close(self):
        if self._session is not None:
            if self._running:
                print "Stopping NI435x acquisition"
                self.stopAcquisition()
            print "Closing NI435x session"
            ret = _NI435X_Close(self._session)
            self.handleError(ret)
            self._session = None

    def revisionQuery(self):
        instrumentDriverRev = ct.create_string_buffer(256)
        firmwareRev = ct.create_string_buffer(256)
        ret = _NI435X_RevisionQuery(self._session, instrumentDriverRev, firmwareRev)
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


def testShuo():
    import time
    import numpy as np
    daq = NI345X('DAQ::2')
    #driverRev, firmwareRev = daq.revisionQuery()
    #print "Driver:", driverRev
    #print "FW:", firmwareRev
    daq.setScanList([3])
    #daq.disableAutoZero()
    daq.setPowerLineFrequency(daq.PowerlineFrequency.F60Hz)
    daq.enableGroundReference([3,5])
    daq.setReadingRate(daq.ReadingRate.FAST)
    daq.setRange(-15.,+15.)
    nScans = 20
    
    daq.setNumberOfScans(nScans)
    print "Number of channels:", daq.numberOfChannels()
    print "Starting..."
    daq.startAcquisition()
    nSamples = 0
#    d = []
    dx = []
    d1 = []
    while nSamples < nScans:
        #print "Check:", daq.check()
        d = daq.checkAndRead(timeOut=0.)
        newSamples = d.shape[1]
        d1 = d[0]
        dx.extend(d1)
        if newSamples:
            print "Result:", d
#        time.sleep(0.1)
        nSamples += newSamples
#
    stdd = np.std(dx)
    dmean = np.mean(dx)
    print dmean, stdd
    daq.stopAcquisition()
    daq.close()


def testSingleChannel():
    import time
    import matplotlib.pyplot as mpl
    daq = NI345X('DAQ::2')
    driverRev, firmwareRev = daq.revisionQuery()
    print "Driver:", driverRev
    print "FW:", firmwareRev
    daq.setScanList([3])
    #daq.disableAutoZero()
    daq.setPowerLineFrequency(daq.PowerlineFrequency.F60Hz)
    daq.enableGroundReference([3])
    daq.setReadingRate(daq.ReadingRate.FAST)
    daq.setRange(-15.,+15.)
    nScans = 100

    
    daq.setNumberOfScans(nScans)
    print "Number of channels:", daq.numberOfChannels()
    print "Starting..."
    daq.startAcquisition()
    t1 = time.time()
    nSamples = 0
    trace = []
    while nSamples < nScans:
        #print "Check:", daq.check()
        d = daq.checkAndRead(timeOut=0.)
        newSamples = d.shape[1]
        if newSamples:
            trace = np.append(trace, d[0])
            t2 = time.time()
            print "Result:", d, 'at t=', t2-t1
#        time.sleep(0.1)
        nSamples += newSamples
    #daq.stopAcquisition()
    #daq.close()
    mpl.plot(trace)
    mpl.show()
    
def testMultipleChannels():
    import time
    daq = NI345X('DAQ::2')
    driverRev, firmwareRev = daq.revisionQuery()
    print "Driver:", driverRev
    print "FW:", firmwareRev
    channels = [3, 5, 7, 10, 11]
    daq.setScanList(channels)
    #daq.disableAutoZero()
    daq.setPowerLineFrequency(daq.PowerlineFrequency.F60Hz)
    daq.enableGroundReference(channels)
    daq.setReadingRate(daq.ReadingRate.FAST)
    daq.setRange(-15.,+15.)
    nScans = 20
    daq.setNumberOfScans(nScans)
    print "Number of channels:", daq.numberOfChannels()
    print "Starting..."
    daq.startAcquisition()
    t1 = time.time()
    nSamples = 0
    trace = np.zeros(shape=(daq.numberOfChannels(),0), dtype=float)
    while nSamples < nScans:
        #print "Check:", daq.check()
        d = daq.checkAndRead(timeOut=0.)
        newSamples = d.shape[1]
        if newSamples:
            t2 = time.time()
            trace = np.append(trace, axis=0)
            print "Result:", d, 'at t=', t2-t1
#        time.sleep(0.1)
        nSamples += newSamples
    print 
    daq.stopAcquisition()
    #daq.close()
    print trace

if __name__ == '__main__':
    testSingleChannel()
    #testMultipleChannels()
    

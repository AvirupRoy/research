# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 15:10:57 2015

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

DeviceTypes = {
      1: 'Not a National Instruments DAQ device',
      7: 'PC-DIO-24',
      8: 'AT-DIO-32F',
     12: 'PC-DIO-96',
     13: 'PC-LPM-16',
     15: 'AT-AO-6',
     25: 'AT-MIO-16E-2',
     26: 'AT-AO-10',
     32: 'NEC-MIO-16E-4',
     35: 'DAQCard DIO-24',
     36: 'AT-MIO-16E-10',
     37: 'AT-MIO-16DE-10',
     38: 'AT-MIO-64E-3',
     39: 'AT-MIO-16XE-50',
     40: 'NEC-AI-16E-4',
     41: 'NEC-MIO-16XE-50',
     42: 'NEC-AI-16XE-50',
     44: 'AT-MIO-16E-1',
     50: 'AT-MIO-16XE-10',
     51: 'AT-AI-16XE-10',
     52: 'DAQCard-AI-16XE-50',
     53: 'DAQCard-AI-16E-4',
     65: 'PC-DIO-24/PnP',
     66: 'PC-DIO-96/PnP',
     67: 'AT-DIO-32HS',
     68: 'DAQCard-6533',
     75: 'DAQPad-6507',
     75: 'DAQPad-6508',
     76: 'DAQPad-6020E for USB',
     88: 'DAQCard-6062E',
     89: 'DAQCard-6715',
     90: 'DAQCard-6023E',
     91: 'DAQCard-6024E',
    200: 'PCI-DIO-96',
    201: 'PCI-',
    202: 'PCI-MIO-16XE-50',
    203: 'PCI-5102',
    204: 'PCI-MIO-16XE-10',
    205: 'PCI-MIO-16E-1',
    206: 'PCI-MIO-16E-4',
    207: 'PXI-6070E',
    208: 'PXI-6040E',
    209: 'PXI-6030E',
    210: 'PXI-6011E',
    211: 'PCI-DIO-32HS',
    215: 'PXI-6533',
    216: 'PCI-6534',
    218: 'PXI-6534',
    220: 'PCI-6031E (MIO-64XE-10)',
    221: 'PCI-6032E (AI-16XE-10)',
    222: 'PCI-6033E (AI-64XE-10)',
    223: 'PCI-6071E (MIO-64E-1)',
    232: 'PCI-6602',
    233: 'NI 4451 for PCI',
    234: 'NI 4452 for PCI',
    235: 'NI 4551 for PCI',
    236: 'NI 4552 for PCI',
    237: 'PXI-6602',
    240: 'PXI-6508',
    241: 'PCI-6110',
    244: 'PCI-6111',
    256: 'PCI-6503',
    257: 'PXI-6503',
    258: 'PXI-6071E',
    259: 'PXI-6031E',
    261: 'PCI-6711',
    262: 'PCI-6711',
    263: 'PCI-6713',
    264: 'PXI-6713',
    265: 'PCI-6704',
    266: 'PXI-6704',
    267: 'PCI-6023E',
    268: 'PXI-6023E',
    269: 'PCI-6024E',
    270: 'PXI-6024E',
    271: 'PCI-6025E',
    272: 'PXI-6025E',
    273: 'PCI-6052E',
    274: 'PXI-6052E',
    275: 'DAQPad-6070E (for 1394)',
    276: 'DAQPad-6052E for 1394 (mass termination)',
    285: 'PCI-6527',
    286: 'PXI-6527',
    307: 'PXI-4351',
    308: 'PCI-6601',
    311: 'PCI-6703',
    314: 'PCI-6034E',
    315: 'PXI-6034E',
    316: 'PCI-6035E',
    317: 'PXI-6035E',
    318: 'PXI-6703',
    319: 'PXI-6608',
    321: 'NI 4454 for PCI',
    327: 'PCI-6608',
    329: 'NI 6222 for PCI',
    330: 'NI 6222 for PXI',
    331: 'NI 6224 for Ethernet',
    332: 'DAQPad-6052E for USB',
    335: 'NI 4472 for PXI/CompactPCI',
    338: 'PCI-6115',
    339: 'PXI-6115',
    340: 'PCI-6120',
    341: 'PXI-6120',
    342: 'NI 4472 for PCI',
    348: 'DAQCard-6036E',
    348: 'NI 6036E for PCI',
    349: 'NI 6731 for PCI',
    350: 'NI 6733 for PCI',
    351: 'NI 6731 for PXI/Compact PCI',
    352: 'NI 6733 for PXI/Compact PCI',
    353: 'PCI-4474',
    354: 'PXI-4474',
    361: 'DAQPad-6052E for 1394 (BNC)',
    366: 'PCI-6013',
    367: 'PCI-6014'}

ErrorCodes = {
    -10001: ('syntaxError', 'An Error was detected in the input string; the arrangement or ordering of the characters in the string is not consistent with the expected ordering'),
    -10002: ('semanticsError', 'An Error was detected in the input string; the syntax of the string is correct, but certain values specified in the string are inconsistent with other values specified in the string'),
    -10003: ('invalidValueError', 'The value of a numeric parameter is invalid'),
    -10004: ('valueConflictError', 'The value of a numeric parameter is inconsistent with another one, and therefore the combination is invalid'),
    -10005: ('badDeviceError', 'The device is invalid'),
    -10006: ('badLineError', 'The line is invalid'),
    -10007: ('badChanError', 'A channel, port, or counter is out of range for the device type or device configuration; or the combination of channels is not allowed; or the scan order must be reversed (0 last)'),
    -10008: ('badGroupError', 'The group is invalid'),
    -10009: ('badCounterError', 'The counter is invalid'),
    -10010: ('badCountError', 'The count is too small or too large for the specified counter, or the given I/O transfer count is not appropriate for the current buffer or channel configuration'),
    -10011: ('badIntervalError', 'The analog input scan rate is too fast for the number of channels and the channel clock rate; or the given clock rate is not supported by the associated counter channel or I/O channel'),
    -10012: ('badRangeError', 'The analog input or analog output voltage or current range is invalid for the specified channel, or you are writing an invalid voltage or current to the analog output'),
    -10013: ('badErrorCodeError', 'The driver returned an unrecognized or unlisted Error code'),
    -10014: ('groupTooLargeError', 'The group size is too large for the device'),
    -10015: ('badTimeLimitError', 'The time limit is invalid'),
    -10016: ('badReadCountError', 'The read count is invalid'),
    -10017: ('badReadModeError', 'The read mode is invalid'),
    -10018: ('badReadOffsetError', 'The offset is unreachable'),
    -10019: ('badClkFrequencyError', 'The frequency is invalid'),
    -10020: ('badTimebaseError', 'The timebase is invalid'),
    -10021: ('badLimitsError', 'The limits are beyond the range of the device'),
    -10022: ('badWriteCountError', 'Your data array contains an incomplete update, or you are trying to write past the end of the internal buffer, or your output operation is continuous and the length of your array is not a multiple of one half of the internal buffer size'),
    -10023: ('badWriteModeError', 'The write mode is out of range or is disallowed'),
    -10024: ('badWriteOffsetError', 'Adding the write offset to the write mark places the write mark outside the internal buffer'),
    -10025: ('limitsOutOfRangeError', "The requested input limits exceed the device's capability or configuration. Alternative limits were selected"),
    -10026: ('badBufferSpecificationError', 'The requested number of buffers or the buffer size is not allowed. For example, the buffer limit for Lab and devices is 64K samples, or the device does not support multiple buffers'),
    -10027: ('badDAQEventError', 'For DAQEvents 0 and 1 general value A must be greater than 0 and less than the internal buffer size. If DMA is used for DAQEvent 1, general value A must divide the internal buffer size evenly, with no remainder. If the TIO-10 is used for DAQEvent 4, general value A must be 1 or 2.'),
    -10028: ('badFilterCutoffError', 'The cutoff frequency specified is not valid for this device'),
    -10029: ('obsoleteFunctionError', 'The function you are calling is no longer supported in this version of the driver'),
    -10030: ('badBaudRateError', 'The specified baud rate for communicating with the serial port is not valid on this platform'),
    -10031: ('badChassisIDError', 'The specified SCXI chassis does not correspond to a configured SCXI chassis'),
    -10032: ('badModuleSlotError', 'The SCXI module slot that was specified is invalid or corresponds to an empty slot'),
    -10033: ('invalidWinHandleError', 'The window handle passed to the function is invalid'),
    -10034: ('noSuchMessageError', 'No configured message matches the one you tried to delete'),
    -10035: ('irrelevantAttributeError', 'The specified attribute is not relevant'),
    -10036: ('badYearError', 'The specified year is invalid'),
    -10037: ('badMonthError', 'The specified month is invalid'),
    -10038: ('badDayError', 'The specified day is invalid'),
    -10039: ('stringTooLongError', 'The specified input string is too long. For instance, DAQScope 5102 devices can only store a string up to 32 bytes in length on the calibration EEPROM. In that case, please shorten the string'),
    -10040: ('badGroupSizeError', 'The group size is invalid'),
    -10041: ('badTaskIDError', 'The specified task ID is invalid. For instance, you may have connected a taskID from an Analog Input VI to a Digital I/O VI'),
    -10042: ('inappropriateControlCodeError', 'The specified control code is inappropriate for the current configuration or state'),
    -10043: ('badDivisorError', 'The specified divisor is invalid'),
    -10044: ('badPolarityError', 'The specified polarity is invalid'),
    -10045: ('badInputModeError', 'The specified input mode is invalid'),
    -10046: ('badExcitationError', 'The excitation value specified is not valid for this device'),
    -10047: ('badConnectionTypeError', 'The type of SCXI channel connection specified is not valid for this module'),
    -10048: ('badExcitationTypeError', 'The excitation type specified is not valid for this device'),
    -10050: ('badChanListError', 'There is more than one channel name in the channel list that corresponds to the same hardware channel'),
    -10079: ('badTrigSkipCountError', 'The trigger skip count is invalid'),
    -10080: ('badGainError', 'The gain or gain adjust is invalid'),
    -10081: ('badPretrigCountError', 'The pretrigger sample count is invalid'),
    -10082: ('badPosttrigCountError', 'The posttrigger sample count is invalid'),
    -10083: ('badTrigModeError', 'The trigger mode is invalid'),
    -10084: ('badTrigCountError', 'The trigger count is invalid'),
    -10085: ('badTrigRangeError', 'The trigger range or trigger hysteresis window is invalid'),
    -10086: ('badExtRefError', 'The external reference is invalid'),
    -10087: ('badTrigTypeError', 'The trigger type is invalid'),
    -10088: ('badTrigLevelError', 'The trigger level is invalid'),
    -10089: ('badTotalCountError', 'The total count is inconsistent with the buffer size and pretrigger scan count or with the device type'),
    -10090: ('badRPGError', 'The individual range, polarity, and gain settings are valid but the combination is not allowed'),
    -10091: ('badIterationsError', 'You have attempted to use an invalid setting for the iterations parameter. The iterations value must be 0 or greater. Your device might be limited to only two values, 0 and 1'),
    -10092: ('lowScanIntervalError', 'Some devices require a time gap between the last sample in a scan and the start of the next scan. The scan interval you have specified does not provide a large enough gap for the device. See your documentation for an explanation'),
    -10093: ('fifoModeError', 'FIFO mode waveform generation cannot be used because at least one condition is not satisfied'),
    -10094: ('badCalDACconstError', 'The calDAC constant passed to the function is invalid'),
    -10095: ('badCalStimulusError', 'The calibration stimulus passed to the function is invalid'),
    -10096: ('badCalibrationConstantError', 'The specified calibration constant is invalid'),
    -10097: ('badCalOpError', 'The specified calibration operation is invalid'),
    -10098: ('badCalConstAreaError', 'The specified calibration constant area is invalid. For instance, the specified calibration constant area contains constants which cannot be modified outside the factory'),
    -10100: ('badPortWidthError', 'The requested digital port width is not a multiple of the hardware port width or is not attainable by the DAQ hardware'),
    -10120: ('gpctrBadApplicationError', 'Invalid application used'),
    -10121: ('gpctrBadCtrNumberError', 'Invalid counterNumber used'),
    -10122: ('gpctrBadParamValueError', 'Invalid paramValue used'),
    -10123: ('gpctrBadParamIDError', 'Invalid paramID used'),
    -10124: ('gpctrBadEntityIDError', 'Invalid entityID used'),
    -10125: ('gpctrBadActionError', 'Invalid action used'),
    -10126: ('gpctrSourceSelectError', 'Invalid source selected'),
    -10127: ('badCountDirError', 'The specified counter does not support the specified count direction'),
    -10128: ('badGateOptionError', 'The specified gating option is invalid'),
    -10129: ('badGateModeError', 'The specified gate mode is invalid'),
    -10130: ('badGateSourceError', 'The specified gate source is invalid'),
    -10131: ('badGateSignalError', 'The specified gate signal is invalid'),
    -10132: ('badSourceEdgeError', 'The specified source edge is invalid'),
    -10133: ('badOutputTypeError', 'The specified output type is invalid'),
    -10134: ('badOutputPolarityError', 'The specified output polarity is invalid'),
    -10135: ('badPulseModeError', 'The specified pulse mode is invalid'),
    -10136: ('badDutyCycleError', 'The specified duty cycle is invalid'),
    -10137: ('badPulsePeriodError', 'The specified pulse period is invalid'),
    -10138: ('badPulseDelayError', 'The specified pulse delay is invalid'),
    -10139: ('badPulseWidthError', 'The specified pulse width is invalid'),
    -10140: ('badFOUTportError', 'The specified frequency output (FOUT or FREQ_OUT) port is invalid'),
    -10141: ('badAutoIncrementModeError', 'The specified autoincrement mode is invalid'),
    -10150: ('CfgInvalidatedSysCalError', 'Hardware configuration has changed since last system calibration'),
    -10151: ('sysCalOutofDateError', 'system calibration is out of date'),
    -10180: ('badNotchFilterError', 'The specified notch filter is invalid'),
    -10181: ('badMeasModeError', 'The specified measurement mode is invalid'),
    -10200: ('EEPROMreadError', 'Unable to read data from EEPROM'),
    -10201: ('EEPROMwriteError', 'Unable to write data to EEPROM'),
    -10202: ('EEPROMwriteProtectionError', u'You cannot write into this location or area of your EEPROM because it is write–protected. You may be trying to store calibration constants into a write–protected area; if this is the case, you should select user area of the EEPROM instead'),
    -10203: ('EEPROMinvalidLocationError', 'The specified EEPROM location is invalid'),
    -10204: ('EEPROMinvalidPasswordError', 'The password for accessing the EEPROM is incorrect'),
    -10240: ('noDriverError', 'The driver interface could not locate or open the driver'),
    -10241: ('oldDriverError', 'One of the driver files or the configuration utility is out of date, or a particular feature of the Channel Wizard is not supported in this version of the driver'),
    -10242: ('functionNotFoundError', 'The specified function is not located in the driver'),
    -10243: ('configFileError', 'The driver could not locate or open the configuration file, or the format of the configuration file is not compatible with the currently installed driver'),
    -10244: ('deviceInitError', 'The driver encountered a hardware-initialization Error while attempting to configure the specified device'),
    -10245: ('osInitError', 'The driver encountered an operating-system Error while attempting to perform an operation, or the operating system does not support an operation performed by the driver'),
    -10246: ('communicationsError', 'The driver is unable to communicate with the specified external device'),
    -10247: ('cmosConfigError', 'The CMOS configuration-memory for the device is empty or invalid, or the configuration specified does not agree with the current configuration of the device, or the EISA system configuration is invalid'),
    -10248: ('dupAddressError', 'The base addresses for two or more devices are the same; consequently, the driver is unable to access the specified device'),
    -10249: ('intConfigError', 'The interrupt configuration is incorrect given the capabilities of the computer or device'),
    -10250: ('dupIntError', 'The interrupt levels for two or more devices are the same'),
    -10251: ('dmaConfigError', 'The DMA configuration is incorrect given the capabilities of the computer/DMA controller or device'),
    -10252: ('dupDMAError', 'The DMA channels for two or more devices are the same'),
    -10253: ('jumperlessBoardError', 'Unable to find one or more jumperless devices you have configured using the Measurement & Automation Explorer'),
    -10254: ('DAQCardConfError', 'Cannot configure the DAQCard because 1) the correct version of the card and socket services software is not installed; 2) the card in the PCMCIA socket is not a DAQCard; or 3) the base address and/or interrupt level requested are not available according to the card and socket services resource manager. Try different settings or use AutoAssign in the Measurement & Automation Explorer'),
    -10256: ('comPortOpenError', 'There was an Error in opening the specified COM port'),
    -10257: ('baseAddressError', 'Bad base address specified in Measurement & Automation Explorer'),
    -10258: ('dmaChannel1Error', 'Bad DMA channel 1 specified in Measurement & Automation Explorer or by the operating system'),
    -10259: ('dmaChannel2Error', 'Bad DMA channel 2 specified in Measurement & Automation Explorer or by the operating system'),
    -10260: ('dmaChannel3Error', 'Bad DMA channel 3 specified in Measurement & Automation Explorer or by the operating system'),
    -10261: ('userModeToKernelModeCallError', 'The user mode code failed when calling the kernel mode code'),
    -10340: ('noConnectError', 'No RTSI or PFI signal/line is connected, or the specified signal and the specified line are not connected, or your connection to an RDA server either cannot be made or has been terminated'),
    -10341: ('badConnectError', 'The RTSI or PFI signal/line cannot be connected as specified'),
    -10342: ('multConnectError', 'The specified RTSI signal is already being driven by a RTSI line, or the specified RTSI line is already being driven by a RTSI signal'),
    -10343: ('SCXIConfigError', 'The specified SCXI configuration parameters are invalid, or the function cannot be executed with the current SCXI configuration'),
    -10347: ('chassisCommunicationError', 'There was an Error in sending a packet to the remote chassis. Check your serial port cable connections'),
    -10349: ('SCXIModuleTypeConflictError', 'The module ID read from the SCXI module conflicts with the configured module type'),
    -10350: ('CannotDetermineEntryModuleError', 'Neither an SCXI entry module (i.e.: the SCXI module cabled to the measurement device that performs the acquisition/control operation) has been specified by the user, nor can Traditional NI-DAQ (Legacy) uniquely determine the entry module for the current SCXI configuration'),
    -10360: ('DSPInitError', 'The DSP driver was unable to load the kernel for its operating system'),
    -10370: ('badScanListError', 'The scan list is invalid; for example, you are mixing AMUX-64T channels and onboard channels, scanning SCXI channels out of order, or have specified a different starting channel for the same SCXI module. Also, the driver attempts to achieve complicated gain distributions over SCXI channels on the same module by manipulating the scan list and returns this Error', 'if it fails'),
    -10380: ('invalidSignalSrcError', 'The specified signal source is invalid for the selected signal name'),
    -10381: ('invalidSignalNameError', 'The specified signal name is invalid'),
    -10382: ('invalidSrcSpecError', 'The specified source specification is invalid for the signal source or signal name'),
    -10383: ('invalidSignalDestError', 'The specified signal destination is invalid'),
    -10390: ('routingError', 'The routing manager was unable to complete the request due to a lack of resources, or because the required resources are reserved'),
    -10391: ('pfiBadLineError', 'The routing manager was unable to complete the request due to an invalid PFI line number'),
    -10392: ('pfiGPCTRNotRoutedError', 'The specified General Purpose Counter Output and/or Up/Down signal(s) are not routed to any PFI lines'),
    -10393: ('pfiDefaultLineUndefinedError', 'A default PFI line does not exist for the given signal. You must specify the PFI line either explicitly in the VI, or through the PFI line configuration VI'),
    -10394: ('pfiDoubleRoutingError', 'Given PFI line is already reserved for a different signal, or given signal has already reserved a different PFI line'),
    -10400: ('userOwnedRsrcError', 'The specified resource is owned by the user and cannot be accessed or modified by the driver'),
    -10401: ('unknownDeviceError', 'The specified device is not a National Instruments product, the driver does not support the device (for example, the driver was released before the device was supported), or the device has not been configured using the Measurement & Automation Explorer'),
    -10402: ('deviceNotFoundError', 'No device is located in the specified slot or at the specified address'),
    -10403: ('deviceSupportError', 'The specified device does not support the requested action (the driver recognizes the device, but the action is inappropriate for the device)'),
    -10404: ('noLineAvailError', 'No line is available'),
    -10405: ('noChanAvailError', 'No channel is available'),
    -10406: ('noGroupAvailError', 'No group is available'),
    -10407: ('lineBusyError', 'The specified line is in use'),
    -10408: ('chanBusyError', 'The specified channel is in use'),
    -10409: ('groupBusyError', 'The specified group is in use'),
    -10410: ('relatedLCGBusyError', 'A related line, channel, or group is in use; if the driver configures the specified line, channel, or group, the configuration, data, or handshaking lines for the related line, channel, or group will be disturbed'),
    -10411: ('counterBusyError', 'The specified counter is in use'),
    -10412: ('noGroupAssignError', 'No group is assigned, or the specified line or channel cannot be assigned to a group'),
    -10413: ('groupAssignError', 'A group is already assigned, or the specified line or channel is already assigned to a group'),
    -10414: ('reservedPinError', 'The selected signal requires a pin that is reserved and configured only by Traditional NI-DAQ (Legacy). You cannot configure this pin yourself'),
    -10415: ('externalMuxSupportError', 'This function does not support your DAQ device when an external multiplexer (such as an AMUX–64T or SCXI) is connected to it'),
    -10440: ('sysOwnedRsrcError', 'The specified resource is owned by the driver and cannot be accessed or modified by the user'),
    -10441: ('memConfigError', 'No memory is configured to support the current data-transfer mode, or the configured memory does not support the current data-transfer mode. (If block transfers are in use, the memory must be capable of performing block transfers'),
    -10442: ('memDisabledError', 'The specified memory is disabled or is unavailable given the current addressing mode'),
    -10443: ('memAlignmentError', 'The transfer buffer is not aligned properly for the current data-transfer mode. For example, the buffer is at an odd address, is not aligned to a 32-bit boundary, is not aligned to a 512-bit boundary, and so on. Alternatively, the driver is unable to align the buffer because the buffer is too small. For DSA devices, buffer should be an array of i32. These devices return the data in a 32-bit format in which the data bits are in the most significant bits. The buffer must be aligned on a 4-byte boundary. If the buffer is allocated as an array of i32s, it must be typecast to an i16 pointer when passing its address to DAQ_Op. If the buffer is allocated as a double-sized array of i16s, the user must check that the buffer is aligned on a 4-byte boundary before passing the buffer to DAQ_Op'),
    -10444: ('memFullError', 'No more system memory is available on the heap, or no more memory is available on the device, or insufficient disk space is available'),
    -10445: ('memLockError', 'The transfer buffer cannot be locked into physical memory. On PC AT machines, portions of the DMA data acquisition buffer may be in an invalid DMA region, for example, above 16 megabytes'),
    -10446: ('memPageError', 'The transfer buffer contains a page break; system resources may require reprogramming when the page break is encountered'),
    -10447: ('memPageLockError', 'The operating environment is unable to grant a page lock'),
    -10448: ('stackMemError', 'The driver is unable to continue parsing a string input due to stack limitations'),
    -10449: ('cacheMemError', 'A cache-related Error occurred, or caching is not supported in the current mode'),
    -10450: ('physicalMemError', 'A hardware Error occurred in physical memory, or no memory is located at the specified address'),
    -10451: ('virtualMemError', 'The driver is unable to make the transfer buffer contiguous in virtual memory and therefore cannot lock it into physical memory; thus, the buffer cannot be used for DMA transfers'),
    -10452: ('noIntAvailError', 'No interrupt level is available for use'),
    -10453: ('intInUseError', 'The specified interrupt level is already in use by another device'),
    -10454: ('noDMACError', 'No DMA controller is available in the system'),
    -10455: ('noDMAAvailError', 'No DMA channel is available for use'),
    -10456: ('DMAInUseError', 'The specified DMA channel is already in use by another device'),
    -10457: ('badDMAGroupError', 'DMA cannot be configured for the specified group because it is too small, too large, or misaligned. Consult the device documentation to determine group ramifications with respect to DMA'),
    -10458: ('diskFullError', 'The storage disk you specified is full'),
    -10459: ('DLLInterfaceError', 'The Traditional NI-DAQ (Legacy) DLL could not be called due to an interface error'),
    -10460: ('interfaceInteractionError', 'You have mixed VIs from the DAQ library and the _DAQ compatibility library (LabVIEW 2.2 style VIs). You may switch between the two libraries only by running the DAQ VI Device Reset before calling _DAQ compatibility VIs or by running the compatibility VI Board Reset before calling DAQ VIs'),
    -10461: ('resourceReservedError', 'The specified resource is unavailable because it has already been reserved by another entity'),
    -10462: ('resourceNotReservedError', 'The specified resource has not been reserved, so the action is not allowed'),
    -10463: ('mdResourceAlreadyReservedError', 'Another entity has already reserved the requested resource'),
    -10464: ('mdResourceReservedError', 'Attempted to access a reserved resource that requires the usage of a key'),
    -10465: ('mdResourceNotReservedError', 'Attempting to lift a reservation off a resource that previously had no reservation'),
    -10466: ('mdResourceAccessKeyError', 'The requested operation cannot be performed because the key supplied is invalid'),
    -10467: ('mdResourceNotRegisteredError', 'The resource requested is not registered with the minidriver'),
    -10480: ('muxMemFullError', 'The scan list is too large to fit into the mux-gain memory of the device'),
    -10481: ('bufferNotInterleavedError', 'You must provide a single buffer of interleaved data, and the channels must be in ascending order. You cannot use DMA to transfer data from two buffers; however, you may be able to use interrupts'),
    -10482: ('waveformBufferSizeError', 'You have specified channels with different waveform lengths. To fix the problem, ensure that the waveform data for every channel has the same number of array elements'),
    -10540: ('SCXIModuleNotSupportedError', 'At least one of the SCXI modules specified is not supported for the operation'),
    -10541: ('TRIG1ResourceConflict CTRB1 will drive COUTB1, however CTRB1 will also drive TRIG1. This may cause unpredictable results when scanning the chassis'),
    -10542: ('matrixTerminalBlockError', 'This function requires that no Matrix terminal block is configured with the SCXI module'),
    -10543: ('noMatrixTerminalBlockError', 'This function requires that some matrix terminal block is configured with the SCXI module'),
    -10544: ('invalidMatrixTerminalBlockError', 'The type of matrix terminal block configured will not allow proper operation of this function with the given parameters'),
    -10560: ('invalidDSPHandleError', 'The DSP handle input is not valid'),
    -10561: ('DSPDataPathBusyError', 'Either DAQ or WFM can use a PC memory buffer, but not both at the same time'),
    -10600: ('noSetupError', 'No setup operation has been performed for the specified resources. Or, some resources require a specific ordering of calls for proper setup'),
    -10601: ('multSetupError', 'The specified resources have already been configured by a setup operation'),
    -10602: ('noWriteError', 'No output data has been written into the transfer buffer'),
    -10603: ('groupWriteError', 'The output data associated with a group must be for a single channel or must be for consecutive channels'),
    -10604: ('activeWriteError', 'Once data generation has started, only the transfer buffers originally written to may be updated. If DMA is active and a single transfer buffer contains interleaved channel-data, new data must be provided for all output channels currently using the DMA channel'),
    -10605: ('endWriteError', 'No data was written to the transfer buffer because the final data block has already been loaded'),
    -10606: ('notArmedError', 'The specified resource is not armed'),
    -10607: ('armedError', 'The specified resource is already armed'),
    -10608: ('noTransferInProgError', 'No transfer is in progress for the specified resource'),
    -10609: ('transferInProgError', 'A transfer is already in progress for the specified resource, or the operation is not allowed because the device is in the process of performing transfers, possibly with different resources'),
    -10610: ('transferPauseError', 'A single output channel in a group may not be paused if the output data for the group is interleaved'),
    -10611: ('badDirOnSomeLinesError', 'Some of the lines in the specified channel are not configured for the transfer direction specified. For a write transfer, some lines are configured for input. For a read transfer, some lines are configured for output'),
    -10612: ('badLineDirError', 'The specified line does not support the specified transfer direction'),
    -10613: ('badChanDirError', 'The specified channel does not support the specified transfer direction, or you have performed an operation on a digital port or line configured for the opposite direction'),
    -10614: ('badGroupDirError', 'The specified group does not support the specified transfer direction'),
    -10615: ('masterClkError', 'The clock configuration for the clock master is invalid'),
    -10616: ('slaveClkError', 'The clock configuration for the clock slave is invalid'),
    -10617: ('noClkSrcError', 'No source signal has been assigned to the clock resource'),
    -10618: ('badClkSrcError', 'The specified source signal cannot be assigned to the clock resource'),
    -10619: ('multClkSrcError', 'A source signal has already been assigned to the clock resource'),
    -10620: ('noTrigError', 'No trigger signal has been assigned to the trigger resource'),
    -10621: ('badTrigError', 'The specified trigger signal cannot be assigned to the trigger resource'),
    -10622: ('preTrigError', 'The pretrigger mode is not supported or is not available in the current configuration, or no pretrigger source has been assigned'),
    -10623: ('postTrigError', 'No posttrigger source has been assigned'),
    -10624: ('delayTrigError', 'The delayed trigger mode is not supported or is not available in the current configuration, or no delay source has been assigned'),
    -10625: ('masterTrigError', 'The trigger configuration for the trigger master is invalid'),
    -10626: ('slaveTrigError', 'The trigger configuration for the trigger slave is invalid'),
    -10627: ('noTrigDrvError', 'No signal has been assigned to the trigger resource'),
    -10628: ('multTrigDrvError', 'A signal has already been assigned to the trigger resource'),
    -10629: ('invalidOpModeError', 'The specified operating mode is invalid, or the resources have not been configured for the specified operating mode'),
    -10630: ('invalidReadError', 'The parameters specified to read data were invalid in the context of the acquisition. For example, an attempt was made to read 0 bytes from the transfer buffer, or an attempt was made to read past the end of the transfer buffer'),
    -10631: ('noInfiniteModeError', 'Continuous input or output transfers are not allowed in the current operating mode, or continuous operation is not allowed for this type of device'),
    -10632: ('someInputsIgnoredError', 'Certain inputs were ignored because they are not relevant in the current operating mode'),
    -10633: ('invalidRegenModeError', 'The specified analog output regeneration mode is not allowed for this device'),
    -10634: ('noContTransferInProgressError', 'No continuous (double buffered) transfer is in progress for the specified resource'),
    -10635: ('invalidSCXIOpModeError', 'Either the SCXI operating mode specified in a configuration call is invalid, or a module is in the wrong operating mode to execute the function call'),
    -10636: ('noContWithSynchError', 'You cannot start a continuous (double-buffered) operation with a synchronous function call'),
    -10637: ('bufferAlreadyConfigError', 'Attempted to configure a buffer after the buffer had already been configured. You can configure a buffer only once'),
    -10638: ('badClkDestError', 'The clock cannot be assigned to the specified destination'),
    -10670: ('rangeBadForMeasModeError', 'The input range is invalid for the configured measurement mode'),
    -10671: ('autozeroModeConflictError', 'Autozero cannot be enabled for the configured measurement mode'),
    -10680: ('badChanGainError', 'All channels of this device must have the same gain'),
    -10681: ('badChanRangeError', 'All channels of this device must have the same range'),
    -10682: ('badChanPolarityError', 'All channels of this device must be the same polarity'),
    -10683: ('badChanCouplingError', 'All channels of this device must have the same coupling'),
    -10684: ('badChanInputModeError', 'All channels of this device must have the same input mode'),
    -10685: ('clkExceedsBrdsMaxConvRateError', "The clock rate exceeds the device's recommended maximum rate"),
    -10686: ('scanListInvalidError', 'A configuration change has invalidated the scan list'),
    -10687: ('bufferInvalidError', 'A configuration change has invalidated the acquisition buffer, or an acquisition buffer has not been configured'),
    -10688: ('noTrigEnabledError', 'The number of total scans and pretrigger scans implies that a triggered start is intended, but triggering is not enabled'),
    -10689: ('digitalTrigBError', 'Digital trigger B is illegal for the number of total scans and pretrigger scans specified'),
    -10690: ('digitalTrigAandBError', 'This device does not allow digital triggers A and B to be enabled at the same time'),
    -10691: ('extConvRestrictionError', 'This device does not allow an external sample clock with an external scan clock, start trigger, or stop trigger'),
    -10692: ('chanClockDisabledError', 'The acquisition cannot be started because the channel clock is disabled'),
    -10693: ('extScanClockError', 'You cannot use an external scan clock when doing a single scan of a single channel'),
    -10694: ('unsafeSamplingFreqError', 'The scan rate is above the maximum or below the minimum for the hardware, gains, and filters used'),
    -10695: ('DMAnotAllowedError', 'You have set up an operation that requires the use of interrupts. DMA is not allowed. For example, some DAQ events, such as messaging and LabVIEW occurrences, require interrupts'),
    -10696: ('multiRateModeError', 'Multi-rate scanning cannot be used with the AMUX-64, SCXI, or pretriggered acquisitions'),
    -10697: ('rateNotSupportedError', 'Unable to convert your timebase/interval pair to match the actual hardware capabilities of this device'),
    -10698: ('timebaseConflictError', 'You cannot use this combination of scan and sample clock timebases for this device'),
    -10699: ('polarityConflictError', 'You cannot use this combination of scan and sample clock source polarities for this operation and device'),
    -10700: ('signalConflictError', 'You cannot use this combination of scan and convert clock signal sources for this operation and device'),
    -10701: ('noLaterUpdateError', 'The call had no effect because the specified channel had not been set for later internal update'),
    -10710: ('noHandshakeModeError', 'The specified port has not been configured for handshaking'),
    -10720: ('noEventCtrError', 'The specified counter is not configured for event-counting operation'),
    -10740: ('SCXITrackHoldError', 'A signal has already been assigned to the SCXI track-and-hold trigger line, or a control call was inappropriate because the specified module is not configured for one-channel operation'),
    -10780: ('sc2040InputModeError', 'When you have an SC2040 attached to your device, all analog input channels must be configured for differential input mode'),
    -10781: ('outputTypeMustBeVoltageError', 'The polarity of the output channel cannot be bipolar when outputting currents'),
    -10782: ('sc2040HoldModeError', 'The specified operation cannot be performed with the SC-2040: (configured in hold mode'),
    -10783: ('calConstPolarityConflictError', 'Calibration constants in the load area have a different polarity from the current configuration. Therefore, you should load constants from factory'),
    -10784: ('masterDeviceNotInPXISlot2 Your master device must be PXI slot number 2 in order to route clocks to slave devices. PXI slot 2 is the STAR trigger controller slot. Only modules in slot 2 can drive the STAR trigger lines'),
    -10800: ('timeOutError', 'The operation could not complete within the time limit'),
    -10801: ('calibrationError', 'An Error occurred during the calibration process. Possible reasons for this Error include incorrect connection of the stimulus signal, incorrect value of the stimulus signal, or malfunction of your DAQ device'),
    -10802: ('dataNotAvailError', 'The requested amount of data has not yet been acquired'),
    -10803: ('transferStoppedError', 'The on-going transfer has been stopped. This is to prevent regeneration for output operations, or to reallocate resources for input operations'),
    -10804: ('earlyStopError', 'The transfer stopped prior to reaching the end of the transfer buffer'),
    -10805: ('overRunError', 'The clock rate is faster than the hardware can support. An attempt to input or output a new data point was made before the hardware could finish processing the previous data point. This condition may also occur when glitches are present on an external clock signal'),
    -10806: ('noTrigFoundError', 'No trigger value was found in the input transfer buffer'),
    -10807: ('earlyTrigError', 'The trigger occurred before sufficient pretrigger data was acquired'),
    -10808: ('LPTcommunicationError', 'An Error occurred in the parallel port communication with the DAQ device'),
    -10809: ('gateSignalError', 'Attempted to start a pulse width measurement with the pulse in the phase to be measured (e.g., high phase for high-level gating)'),
    -10810: ('internalDriverError', 'An unexpected Error occurred inside the driver when performing this given operation'),
    -10811: ('frequencyMeasurementError', "The input signal's frequency could not be measured. The input signal's frequency may be outside the expected frequency range, or the threshhold and hysteresis values may not be being crossed"),
    -10840: ('softwareError', 'The contents or the location of the driver file was changed between accesses to the driver'),
    -10841: ('firmwareError', 'The firmware does not support the specified operation, or the firmware operation could not complete due to a data-integrity problem'),
    -10842: ('hardwareError', 'The hardware is not responding to the specified operation, or the response from the hardware is not consistent with the functionality of the hardware'),
    -10843: ('underFlowError', 'Because of system and/or bus-bandwidth limitations, the driver could not write data to the device fast enough to keep up with the device throughput; the onboard device memory reported an underflow error. This Error', 'may be returned erroneously when an overrun Error', 'has occurred'),
    -10844: ('underWriteError', 'Your application was unable to deliver data to the background generation buffer fast enough so new data could not be delivered to the device. To prevent this error, you might increase the size of the background generation buffer, increase the amount of data you write to it per call to the write function/VI, slow down your generation rate, or reduce the number of tasks your computer is performing'),
    -10845: ('overFlowError', 'Because of system and/or bus-bandwidth limitations, the driver could not read data from the device fast enough to keep up with the device throughput; the onboard device memory reported an overflow error'),
    -10846: ('overWriteError', 'Your application was unable to retrieve data from the background acquisition buffer fast enough so the unretrieved data was overwritten with new data. To prevent this error, you might increase the size of the background acquisition buffer, increase the amount of data you read from it per call to the read function/VI, slow down your acquisition rate, or reduce the number of tasks your computer is performing'),
    -10847: ('dmaChainingError', 'New buffer information was not available at the time of the DMA chaining interrupt; DMA transfers will terminate at the end of the currently active transfer buffer'),
    -10848: ('noDMACountAvailError', 'The driver could not obtain a valid reading from the transfer-count register in the DMA controller'),
    -10849: ('OpenFileError', 'The configuration file or DSP kernel file could not be opened'),
    -10850: ('closeFileError', 'Unable to close a file'),
    -10851: ('fileSeekError', 'Unable to seek within a file'),
    -10852: ('readFileError', 'Unable to read from a file'),
    -10853: ('writeFileError', 'Unable to write to a file'),
    -10854: ('miscFileError', 'An Error', 'occurred accessing a file'),
    -10855: ('osUnsupportedError', 'Traditional NI-DAQ (Legacy) does not support the current operation on this particular version of the operating system'),
    -10856: ('osError', 'An unexpected Error', 'occurred from the operating system while performing the given operation'),
    -10857: ('internalKernelError', 'An unexpected Error', 'occurred inside the kernel of the device while performing this operation'),
    -10858: ('hardwareConfigChangedError', 'The system has reconfigured the device and has invalidated the existing configuration. The device requires reinitialization to be used again'),
    -10880: ('updateRateChangeError', 'A change to the update rate is not possible at this time because 1) when waveform generation is in progress, you cannot change the interval timebase or 2) when you make several changes in a row, you must give each change enough time to take effect before requesting further changes'),
    -10881: ('partialTransferCompleteError', 'You cannot do another transfer after a successful partial transfer'),
    -10884: ('pretrigReorderError', 'Could not rearrange data after a pretrigger acquisition completed'),
    -10885: ('overLoadError', 'The input signal exceeded the input range of the ADC'),
    -10920: ('gpctrDataLossError', 'One or more data points may have been lost during buffered GPCTR operations due to speed limitations of your system') }

class ND:
	ABOVE_HIGH_LEVEL			= 11020
	ABOVE_LEVEL_A			= 11021
	ABOVE_LEVEL_A_HYSTERESIS	= 11022
	AC					= 11025
	ACK_REQ_EXCHANGE_GR1		= 11030
	ACK_REQ_EXCHANGE_GR2		= 11035
	ACTIVE				= 11037
	ADC_RESOLUTION			= 11040
	AI_CALDAC_COUNT			= 11050
	AI_CHANNEL_COUNT			= 11060
	AI_COUPLING				= 11055
	AI_FIFO_INTERRUPTS		= 11600
	ANALOG_FILTER			= 11065
	AO48XDC_SET_POWERUP_STATE	= 42100
	AO_CALDAC_COUNT			= 11070
	AO_CHANNEL_COUNT			= 11080
	AO_EXT_REF_CAPABLE		= 11090
	AO_UNIPOLAR_CAPABLE		= 11095
	ARM					= 11100
	ARMED					= 11200
	ATC_OUT				= 11250
	ATTENUATION				= 11260
	AUTOINCREMENT_COUNT		= 11300
	AUTOMATIC				= 11400
	AVAILABLE_POINTS			= 11500

	BASE_ADDRESS			= 12100
	BELOW_LEVEL_A			= 12110
	BELOW_LEVEL_A_HYSTERESIS	= 12115
	BELOW_LOW_LEVEL			= 12130
	BETWEEN_LEVEL_A_LEVEL_B	= 12135
	BOARD_CLOCK				= 12170
	BUFFERED_EVENT_CNT		= 12200
	BUFFERED_PERIOD_MSR		= 12300
	BUFFERED_PULSE_WIDTH_MSR	= 12400
	BUFFERED_SEMI_PERIOD_MSR	= 12500
	BURST					= 12600
	BURST_INTERVAL			= 12700

	CAL_CONST_AUTO_LOAD		= 13050
	CALIBRATION_ENABLE		= 13055
	CALIBRATION_FRAME_SIZE		= 13060
	CALIBRATION_FRAME_PTR		= 13065
	CJ_TEMP                    	= 0x8000
	CALGND                     	= 0x8001
	P_POS_0                    	= 0x4000
	P_POS_1                    	= 0x4001
	P_POS_2                    	= 0x4002
	P_POS_3                    	= 0x4003
	P_POS_4                    	= 0x4004
	P_POS_5                    	= 0x4005
	P_POS_6                    	= 0x4006
	P_POS_7                    	= 0x4007
	P_NEG_0                    	= 0x2000
	P_NEG_1                    	= 0x2001
	P_NEG_2                    	= 0x2002
	P_NEG_3                    	= 0x2003
	P_NEG_4                    	= 0x2004
	P_NEG_5                    	= 0x2005
	P_NEG_6                    	= 0x2006
	P_NEG_7                    	= 0x2007
	CLEAN_UP				= 13100
	CLOCK_REVERSE_MODE_GR1		= 13120
	CLOCK_REVERSE_MODE_GR2		= 13130
	CONFIG_MEMORY_SIZE		= 13150
	CONTINUOUS				= 13160
	COUNT					= 13200

	COUNTER_0				= 13300
	COUNTER_1				= 13400
	COUNTER_2				= 13310
	COUNTER_3				= 13320
	COUNTER_4				= 13330
	COUNTER_5				= 13340
	COUNTER_6				= 13350
	COUNTER_7				= 13360

	COUNTER_1_SOURCE			= 13430
	COUNT_AVAILABLE			= 13450
	COUNT_DOWN				= 13465
	COUNT_UP				= 13485
	COUNT_1				= 13500
	COUNT_2				= 13600
	COUNT_3				= 13700
	COUNT_4				= 13800
	CURRENT_OUTPUT			= 40200

	DAC_RESOLUTION			= 13950
	DATA_TRANSFER_CONDITION	= 13960
	DATA_XFER_MODE_AI			= 14000
	DATA_XFER_MODE_AO_GR1		= 14100
	DATA_XFER_MODE_AO_GR2		= 14200
	DATA_XFER_MODE_DIO_GR1		= 14300
	DATA_XFER_MODE_DIO_GR2		= 14400
	DATA_XFER_MODE_DIO_GR3		= 14500
	DATA_XFER_MODE_DIO_GR4		= 14600
	DATA_XFER_MODE_DIO_GR5		= 14700
	DATA_XFER_MODE_DIO_GR6		= 14800
	DATA_XFER_MODE_DIO_GR7		= 14900
	DATA_XFER_MODE_DIO_GR8		= 15000

	DATA_XFER_MODE_GPCTR0		= 15100
	DATA_XFER_MODE_GPCTR1		= 15200
	DATA_XFER_MODE_GPCTR2		= 15110
	DATA_XFER_MODE_GPCTR3		= 15120
	DATA_XFER_MODE_GPCTR4		= 15130
	DATA_XFER_MODE_GPCTR5		= 15140
	DATA_XFER_MODE_GPCTR6		= 15150
	DATA_XFER_MODE_GPCTR7		= 15160
	DATA_XFER_MODE_GPCTR8		= 15165
	DATA_XFER_MODE_GPCTR9		= 15170
	DATA_XFER_MODE_GPCTR10		= 15175
	DATA_XFER_MODE_GPCTR11		= 15180

	DC					= 15250
	DDS_BUFFER_SIZE			= 15255
	DEVICE_NAME				= 15260
	DEVICE_POWER			= 15270
	DEVICE_SERIAL_NUMBER		= 15280
	DEVICE_STATE_DURING_SUSPEND_MODE	= 15290
	DEVICE_TYPE_CODE				= 15300
	DIGITAL_FILTER				= 15350
	DIGITAL_RESTART				= 15375
	DIO128_GET_PORT_THRESHOLD		= 41200
	DIO128_SELECT_INPUT_PORT		= 41100
	DIO128_SET_PORT_THRESHOLD		= 41300
	DISABLED					= 15400
	DISARM					= 15450
	DIVIDE_DOWN_SAMPLING_SUPPORTED	= 15475
	DMA_A_LEVEL					= 15500
	DMA_B_LEVEL					= 15600
	DMA_C_LEVEL					= 15700
	DONE						= 15800
	DONT_CARE					= 15900
	DONT_KNOW					= 15950

	EDGE_SENSITIVE				= 16000
	ENABLED				= 16050
	END				= 16055
	EXTERNAL				= 16060
	EXTERNAL_CALIBRATE				= 16100

	FACTORY_CALIBRATION_EQUIP				= 16210
	FACTORY_EEPROM_AREA				= 16220
	FIFO_EMPTY				= 16230
	FIFO_HALF_FULL_OR_LESS				= 16240
	FIFO_HALF_FULL_OR_LESS_UNTIL_FULL				= 16245
	FIFO_NOT_FULL				= 16250
	FIFO_TRANSFER_COUNT				= 16260
	FILTER_CORRECTION_FREQ				= 16300
	FOREGROUND				= 16350
	FREQ_OUT				= 16400
	FSK				= 16500
	EDGE_BASED_FSK				= 16500

	GATE				= 17100
	GATE_POLARITY				= 17200

	GPCTR0_GATE				= 17300
	GPCTR0_OUTPUT				= 17400
	GPCTR0_SOURCE				= 17500

	GPCTR1_GATE				= 17600
	GPCTR1_OUTPUT				= 17700
	GPCTR1_SOURCE				= 17800

	GPCTR2_GATE				= 17320
	GPCTR2_OUTPUT				= 17420
	GPCTR2_SOURCE				= 17520

	GPCTR3_GATE				= 17330
	GPCTR3_OUTPUT				= 17430
	GPCTR3_SOURCE				= 17530

	GPCTR4_GATE				= 17340
	GPCTR4_OUTPUT				= 17440
	GPCTR4_SOURCE				= 17540

	GPCTR5_GATE				= 17350
	GPCTR5_OUTPUT				= 17450
	GPCTR5_SOURCE				= 17550

	GPCTR6_GATE				= 17360
	GPCTR6_OUTPUT				= 17460
	GPCTR6_SOURCE				= 17660

	GPCTR7_GATE				= 17370
	GPCTR7_OUTPUT				= 17470
	GPCTR7_SOURCE				= 17570





	GROUND_DAC_REFERENCE				= 17900

	HARDWARE				= 18000
	HI_RES_SAMPLING				= 18020
	HIGH				= 18050
	HIGH_HYSTERESIS				= 18080
	HIGH_TO_LOW				= 18100
	HW_ANALOG_TRIGGER				= 18900

	IMPEDANCE				= 19000
	INACTIVE				= 19010
	INITIAL_COUNT				= 19100
	INIT_PLUGPLAY_DEVICES				= 19110
	INSIDE_REGION				= 19150
	INTERNAL				= 19160
	INTERNAL_100_KHZ				= 19200
	INTERNAL_10_MHZ				= 19300
	INTERNAL_1250_KHZ				= 19320
	INTERNAL_20_MHZ				= 19400
	INTERNAL_25_MHZ				= 19410
	INTERNAL_2500_KHZ				= 19420
	INTERNAL_5_MHZ				= 19450
	INTERNAL_7160_KHZ				= 19460
	INTERNAL_TIMER				= 19500
	INTERRUPTS				= 19600
	INTERRUPT_A_LEVEL				= 19700
	INTERRUPT_B_LEVEL				= 19800
	INTERRUPT_TRIGGER_MODE				= 19850
	IN_CHANNEL_CLOCK_TIMEBASE				= 19900
	IN_CHANNEL_CLOCK_TB_POL				= 20000
	IN_CONVERT				= 20100
	IN_CONVERT_POL				= 20200
	IN_DATA_FIFO_SIZE				= 20250
	IN_EXTERNAL_GATE				= 20300
	IN_EXTERNAL_GATE_POL				= 20400
	IN_SCAN_CLOCK_TIMEBASE				= 20500
	IN_SCAN_CLOCK_TB_POL				= 20600
	IN_SCAN_IN_PROG				= 20650
	IN_SCAN_START				= 20700
	IN_SCAN_START_POL				= 20800
	IN_START_TRIGGER				= 20900
	IN_START_TRIGGER_POL	=	21000
	IN_STOP_TRIGGER	=	21100
	IN_STOP_TRIGGER_POL	=	21200
	INT_AI_GND	=	21210
	INT_AO_CH_0	=	21230
	INT_AO_CH_0_VS_REF_5V	=	21235
	INT_AO_CH_1	=	21240
	INT_AO_CH_1_VS_AO_CH_0	=	21245
	INT_AO_CH_1_VS_REF_5V	=	21250
	INT_AO_CH_2	=	21220
	INT_AO_CH_3		=	21221
	INT_AO_CH_4		=	21222
	INT_AO_CH_5		=	21223
	INT_AO_CH_6		=	21224
	INT_AO_CH_7		=	21225
	INT_AO_GND		=	21260
	INT_AO_GND_VS_AI_GND				= 21265
	INT_CM_REF_5V				= 21270
	INT_DEV_TEMP				= 21280
	INT_REF_5V				= 21290
	INT_REF_EXTERN				= 21296
	INT_CAL_BUS				= 21295
	INT_MUX_BUS				= 21305

	INT_AI_GND_AMP_0				= 21211
	INT_AI_GND_AMP_1				= 21212
	INT_AI_GND_AMP_2				= 21213
	INT_AI_GND_AMP_3				= 21214
	INT_AI_GND_AMP_4				= 21215
	INT_AI_GND_AMP_5				= 21216
	INT_AI_GND_AMP_6				= 21217
	INT_AI_GND_AMP_7				= 21218

	INT_AO_CH_0_AMP_0				= 21231
	INT_AO_CH_0_AMP_1				= 21232
	INT_AO_CH_0_AMP_2				= 21233
	INT_AO_CH_0_AMP_3				= 21234
	INT_AO_CH_1_AMP_0				= 21241
	INT_AO_CH_1_AMP_1				= 21242
	INT_AO_CH_1_AMP_2				= 21243
	INT_AO_CH_1_AMP_3				= 21244
	INT_AO_CH_0_VS_REF_AMP_0				= 21236
	INT_AO_CH_0_VS_REF_AMP_1				= 21237
	INT_AO_CH_0_VS_REF_AMP_2				= 21238
	INT_AO_CH_0_VS_REF_AMP_3				= 21239
	INT_AO_CH_1_VS_REF_AMP_0				= 21251
	INT_AO_CH_1_VS_REF_AMP_1				= 21252
	INT_AO_CH_1_VS_REF_AMP_2				= 21253
	INT_AO_CH_1_VS_REF_AMP_3				= 21254
	INT_AO_GND_VS_AI_GND_AMP_0				= 21266
	INT_AO_GND_VS_AI_GND_AMP_1				= 21267
	INT_AO_GND_VS_AI_GND_AMP_2				= 21268
	INT_AO_GND_VS_AI_GND_AMP_3				= 21269
	INT_CM_REF_AMP_0				= 21271
	INT_CM_REF_AMP_1				= 21272
	INT_CM_REF_AMP_2				= 21273
	INT_CM_REF_AMP_3				= 21274
	INT_REF_AMP_0				= 21291
	INT_REF_AMP_1				= 21292
	INT_REF_AMP_2				= 21293
	INT_REF_AMP_3				= 21294
	INT_REF_AMP_4				= 21301
	INT_REF_AMP_5				= 21302
	INT_REF_AMP_6				= 21303
	INT_REF_AMP_7				= 21304
	ROUTE_INT_REFERENCE				= 21299

	INTERRUPT_EVERY_SAMPLE				= 11700
	INTERRUPT_HALF_FIFO				= 11800
	IO_CONNECTOR				= 21300

	LEVEL_A				= 21410
	LEVEL_B				= 21420
	LEVEL_SENSITIVE				= 24000
	LINK_COMPLETE_INTERRUPTS				= 24010
	LOW				= 24050
	LOW_HYSTERESIS				= 24080
	LOW_TO_HIGH				= 24100
	LPT_DEVICE_MODE				= 24200

	MARKER				= 24500
	MARKER_QUANTUM				= 24550
	MAX_ARB_SEQUENCE_LENGTH				= 24600
	MAX_FUNC_SEQUENCE_LENGTH				= 24610
	MAX_LOOP_COUNT				= 24620
	MAX_NUM_WAVEFORMS				= 24630
	MAX_SAMPLE_RATE				= 24640
	MAX_WFM_SIZE				= 24650
	MEMORY_TRANSFER_WIDTH				= 24700
	MIN_SAMPLE_RATE				= 24800
	MIN_WFM_SIZE				= 24810

	NEGATIVE				= 26100
	NEW				= 26190
	NI_DAQ_SW_AREA				= 26195
	NO				= 26200
	NO_STRAIN_GAUGE				= 26225
	NO_TRACK_AND_HOLD				= 26250
	NONE				= 26300
	NOT_APPLICABLE				= 26400
	NUMBER_DIG_PORTS				= 26500

	OFF				= 27010
	OFFSET				= 27020
	ON				= 27050
	OTHER				= 27060
	OTHER_GPCTR_OUTPUT				= 27300
	OTHER_GPCTR_TC				= 27400
	OUTSIDE_LEVEL_A_LEVEL_B				= 27065
	OUT_DATA_FIFO_SIZE				= 27070
	OUT_EXTERNAL_GATE				= 27080
	OUT_EXTERNAL_GATE_POL				= 27082
	OUT_START_TRIGGER				= 27100
	OUT_START_TRIGGER_POL				= 27102
	OUT_UPDATE				= 27200
	OUT_UPDATE_POL				= 27202
	OUT_UPDATE_CLOCK_TIMEBASE				= 27210
	OUT_UPDATE_CLOCK_TB_POL				= 27212
	OUTPUT_ENABLE				= 27220
	OUTPUT_MODE				= 27230
	OUTPUT_POLARITY				= 27240
	OUTPUT_STATE				= 27250
	OUTPUT_TYPE				= 40000

	DIGITAL_PATTERN_GENERATION				= 28030
	PAUSE				= 28040
	PAUSE_ON_HIGH				= 28045
	PAUSE_ON_LOW				= 28050
	PFI_0				= 28100
	PFI_1				= 28200
	PFI_2				= 28300
	PFI_3				= 28400
	PFI_4				= 28500
	PFI_5				= 28600
	PFI_6				= 28700
	PFI_7				= 28800
	PFI_8				= 28900
	PFI_9				= 29000
	PFI_10				= 50280
	PFI_11				= 50290
	PFI_12				= 50300
	PFI_13				= 50310
	PFI_14				= 50320
	PFI_15				= 50330
	PFI_16				= 50340
	PFI_17				= 50350
	PFI_18				= 50360
	PFI_19				= 50370
	PFI_20				= 50380
	PFI_21				= 50390
	PFI_22				= 50400
	PFI_23				= 50410
	PFI_24				= 50420
	PFI_25				= 50430
	PFI_26				= 50440
	PFI_27				= 50450
	PFI_28				= 50460
	PFI_29				= 50470
	PFI_30				= 50480
	PFI_31				= 50490
	PFI_32				= 50500
	PFI_33				= 50510
	PFI_34				= 50520
	PFI_35				= 50530
	PFI_36				= 50540
	PFI_37				= 50550
	PFI_38				= 50560
	PFI_39				= 50570

	PLL_REF_FREQ				= 29010
	PLL_REF_SOURCE				= 29020
	PRE_ARM				= 29050
	POSITIVE				= 29100
	PREPARE				= 29200
	PROGRAM				= 29300
	PULSE				= 29350
	PULSE_SOURCE				= 29500
	PULSE_TRAIN_GNR				= 29600
	PXI_BACKPLANE_CLOCK				= 29900

	REGLITCH				= 31000
	RESERVED				= 31100
	RESET				= 31200
	RESUME				= 31250
	RETRIG_PULSE_GNR				= 31300
	REVISION				= 31350
	RTSI_0				= 31400
	RTSI_1				= 31500
	RTSI_2				= 31600
	RTSI_3				= 31700
	RTSI_4				= 31800
	RTSI_5				= 31900
	RTSI_6				= 32000
	RTSI_CLOCK				= 32100
	PXI_STAR				= 32200
	PXI_STAR_3				= 32210
	PXI_STAR_4				= 32220
	PXI_STAR_5				= 32230
	PXI_STAR_6				= 32240
	PXI_STAR_7				= 32250
	PXI_STAR_8				= 32260
	PXI_STAR_9				= 32270
	PXI_STAR_10				= 32280
	PXI_STAR_11				= 32290
	PXI_STAR_12				= 32300
	PXI_STAR_13				= 32310
	PXI_STAR_14				= 32320
	PXI_STAR_15				= 32330

	SCANCLK				= 32400
	SCANCLK_LINE				= 32420
	SC_2040_MODE				= 32500
	SC_2043_MODE				= 32600
	SELF_CALIBRATE				= 32700
	SET_DEFAULT_LOAD_AREA				= 32800
	RESTORE_FACTORY_CALIBRATION				= 32810
	SET_POWERUP_STATE				= 42100
	SIGNAL_CONDITIONING_SPEC				= 32900
	SIMPLE_EVENT_CNT				= 33100
	SINGLE				= 33150
	SINGLE_PERIOD_MSR				= 33200
	SINGLE_PULSE_GNR				= 33300
	SINGLE_PULSE_WIDTH_MSR				= 33400
	SINGLE_TRIG_PULSE_GNR				= 33500
	SOURCE				= 33700
	SOURCE_POLARITY				= 33800
	STABLE_10_MHZ				= 33810
	STEPPED				= 33825
	STRAIN_GAUGE				= 33850
	STRAIN_GAUGE_EX0				= 33875
	SUB_REVISION				= 33900
	SYNC_DUTY_CYCLE_HIGH				= 33930
	SYNC_OUT				= 33970

	TC_REACHED				= 34100
	THE_AI_CHANNEL				= 34400
	TOGGLE				= 34700
	TOGGLE_GATE				= 34800
	TRACK_AND_HOLD				= 34850
	TRIG_PULSE_WIDTH_MSR				= 34900
	TRIGGER_SOURCE				= 34930
	TRIGGER_MODE				= 34970

	UI2_TC				= 35100
	UP_DOWN				= 35150
	UP_TO_1_DMA_CHANNEL				= 35200
	UP_TO_2_DMA_CHANNELS				= 35300
	USE_CAL_CHAN				= 36000
	USE_AUX_CHAN				= 36100
	USER_EEPROM_AREA				= 37000
	USER_EEPROM_AREA_2				= 37010
	USER_EEPROM_AREA_3				= 37020
	USER_EEPROM_AREA_4				= 37030
	USER_EEPROM_AREA_5				= 37040

	DSA_RTSI_CLOCK_AD				= 44000
	DSA_RTSI_CLOCK_DA				= 44010
	DSA_OUTPUT_TRIGGER				= 44020
	DSA_INPUT_TRIGGER				= 44030
	DSA_SHARC_TRIGGER				= 44040
	DSA_ANALOG_TRIGGER				= 44050
	DSA_HOST_TRIGGER				= 44060
	DSA_EXTERNAL_DIGITAL_TRIGGER				= 44070
	DSA_EXCITATION				= 44080

	VOLTAGE_OUTPUT				= 40100
	VOLTAGE_REFERENCE				= 38000

	VXI_SC                     	= 0x2000
	PXI_SC                     	= 0x2010
	WALRUS_SCXI_HV_BACKPLANE   	= 0x2011
	WALRUS_SCXI_LV_BACKPLANE   	= 0x2012
	VXIMIO_SET_ALLOCATE_MODE				= 43100
	VXIMIO_USE_ONBOARD_MEMORY_AI				= 43500
	VXIMIO_USE_ONBOARD_MEMORY_AO				= 43600
	VXIMIO_USE_ONBOARD_MEMORY_GPCTR				= 43700
	VXIMIO_USE_PC_MEMORY_AI				= 43200
	VXIMIO_USE_PC_MEMORY_AO				= 43300
	VXIMIO_USE_PC_MEMORY_GPCTR				= 43400

	WFM_QUANTUM				= 45000

	YES				= 39100
	ND_3V_LEVEL				= 43450

	WRITE_MARK				= 50000
	READ_MARK				= 50010
	BUFFER_START				= 50020
	TRIGGER_POINT				= 50025
	BUFFER_MODE				= 50030
	DOUBLE				= 50050
	QUADRATURE_ENCODER_X1				= 50070
	QUADRATURE_ENCODER_X2				= 50080
	QUADRATURE_ENCODER_X4				= 50090
	TWO_PULSE_COUNTING				= 50100
	LINE_FILTER				= 50110
	SYNCHRONIZATION				= 50120
	ND_5_MICROSECONDS				= 50130
	ND_1_MICROSECOND				= 50140
	ND_500_NANOSECONDS				= 50150
	ND_100_NANOSECONDS				= 50160
	ND_1_MILLISECOND				= 50170
	ND_10_MILLISECONDS				= 50180
	ND_100_MILLISECONDS				= 50190


	OTHER_GPCTR_SOURCE				= 50580
	OTHER_GPCTR_GATE				= 50590
	AUX_LINE				= 50600
	AUX_LINE_POLARITY				= 50610
	TWO_SIGNAL_EDGE_SEPARATION_MSR				= 50630
	BUFFERED_TWO_SIGNAL_EDGE_SEPARATION_MSR				= 50640
	SWITCH_CYCLE				= 50650
	INTERNAL_MAX_TIMEBASE				= 50660
	PRESCALE_VALUE				= 50670
	MAX_PRESCALE				= 50690
	INTERNAL_LINE_0				= 50710
	INTERNAL_LINE_1				= 50720
	INTERNAL_LINE_2				= 50730
	INTERNAL_LINE_3				= 50740
	INTERNAL_LINE_4				= 50750
	INTERNAL_LINE_5				= 50760
	INTERNAL_LINE_6				= 50770
	INTERNAL_LINE_7				= 50780
	INTERNAL_LINE_8				= 50790
	INTERNAL_LINE_9				= 50800
	INTERNAL_LINE_10				= 50810
	INTERNAL_LINE_11				= 50820
	INTERNAL_LINE_12				= 50830
	INTERNAL_LINE_13				= 50840
	INTERNAL_LINE_14				= 50850
	INTERNAL_LINE_15				= 50860
	INTERNAL_LINE_16				= 50862
	INTERNAL_LINE_17				= 50864
	INTERNAL_LINE_18				= 50866
	INTERNAL_LINE_19				= 50868
	INTERNAL_LINE_20				= 50870
	INTERNAL_LINE_21				= 50872
	INTERNAL_LINE_22				= 50874
	INTERNAL_LINE_23				= 50876





	START_TRIGGER				= 51150
	START_TRIGGER_POLARITY				= 51151



	COUNTING_SYNCHRONOUS				= 51200
	SYNCHRONOUS				= 51210
	ASYNCHRONOUS				= 51220
	CONFIGURABLE_FILTER				= 51230
	ENCODER_TYPE				= 51240
	Z_INDEX_ACTIVE				= 51250
	Z_INDEX_VALUE				= 51260
	SNAPSHOT				= 51270
	POSITION_MSR				= 51280
	BUFFERED_POSITION_MSR				= 51290
	SAVED_COUNT				= 51300
	READ_MARK_H_SNAPSHOT				= 51310
	READ_MARK_L_SNAPSHOT				= 51320
	WRITE_MARK_H_SNAPSHOT				= 51330
	WRITE_MARK_L_SNAPSHOT				= 51340
	BACKLOG_H_SNAPSHOT				= 51350
	BACKLOG_L_SNAPSHOT				= 51360
	ARMED_SNAPSHOT				= 51370
	EDGE_GATED_FSK				= 51371
	SIMPLE_GATED_EVENT_CNT				= 51372

	VIDEO_TYPE				= 51380
	PAL_B				= 51390
	PAL_G				= 51400
	PAL_H				= 51410
	PAL_I				= 51420
	PAL_D				= 51430
	PAL_N				= 51440
	PAL_M				= 51450
	NTSC_M				= 51460
	COUNTER_TYPE				= 51470
	NI_TIO				= 51480
	AM9513				= 51490
	STC				= 51500
	ND_8253				= 51510
	A_HIGH_B_HIGH				= 51520
	A_HIGH_B_LOW				= 51530
	A_LOW_B_HIGH				= 51540
	A_LOW_B_LOW				= 51550
	Z_INDEX_RELOAD_PHASE				= 51560
	UPDOWN_LINE				= 51570
	DEFAULT				= 51575
	DEFAULT_PFI_LINE				= 51580
	BUFFER_SIZE				= 51590
	ELEMENT_SIZE				= 51600
	NUMBER_GP_COUNTERS				= 51610
	BUFFERED_TIME_STAMPING				= 51620
	TIME_0_DATA_32				= 51630
	TIME_8_DATA_24				= 51640
	TIME_16_DATA_16				= 51650
	TIME_24_DATA_8				= 51660
	TIME_32_DATA_32				= 51670
	TIME_48_DATA_16				= 51680
	ABSOLUTE				= 51690
	RELATIVE				= 51700
	TIME_DATA_SIZE				= 51710
	TIME_FORMAT				= 51720
	HALT_ON_OVERFLOW				= 51730
	OVERLAY_RTSI_ON_PFI_LINES				= 51740
	STOP_TRIGGER				= 51750
	TS_INPUT_MODE				= 51760
	BOTH_EDGES				= 51770

	CLOCK_0				= 51780
	CLOCK_1				= 51790
	CLOCK_2				= 51800
	CLOCK_3				= 51810
	SYNCHRONIZATION_LINE				= 51820
	TRANSFER_METHOD				= 51830
	SECONDS				= 51840
	PRECISION				= 51850
	NANO_SECONDS				= 51860
	SYNCHRONIZATION_METHOD				= 51870
	PULSE_PER_SECOND				= 51880
	IRIG_B				= 51890
	SIMPLE_TIME_MSR				= 51900
	SINGLE_TIME_MSR				= 51910
	BUFFERED_TIME_MSR				= 51920
	DMA				= 51930
	INTERNAL_SYNCHRONIZATION				= 51940
	INITIAL_SECONDS				= 51950
	INITIAL_SECONDS_ENABLE				= 51951
	EXTERNAL_CALIBRATION				= 51990
	INTERNAL_CALIBRATION				= 51200
	ABORT_CALIBRATION				= 51210
	STORE_CALIBRATION				= 51220

	MEASUREMENT_MODE				= 51230
	CURRENT				= 51240
	FREQUENCY				= 52250
	VOLTAGE				= 52260
	OHMS				= 52270

	EXCITATION_CURRENT				= 52280
	FREQ_STARTING_EDGE				= 52290
	FREQ_TRIG_LOW				= 52300
	FREQ_TRIG_HIGH				= 52310
	FREQ_NUM_OF_CYCLES				= 52320
	FREQ_TIME_BASE				= 52330
	FREQ_LOW_LIMIT				= 52340

	AVERAGING_NUM_OF_SAMPLES				= 52350
	AVERAGING_FREQUENCY				= 52360
	OFFSET_COMP_MODE				= 52370

	DIGITAL_LINE				= 52380
	DIGITAL_PORT				= 52390
	GPCTR0_UP_DOWN				= 52400
	GPCTR1_UP_DOWN				= 52410
	DIGITAL_LINE_0				= 52420
	DIGITAL_LINE_1				= 52430
	DIGITAL_LINE_2				= 52440
	DIGITAL_LINE_3				= 52450
	DIGITAL_LINE_4				= 52460
	DIGITAL_LINE_5				= 52470
	DIGITAL_LINE_6				= 52480
	DIGITAL_LINE_7				= 52490
	SCARAB_A_MEMORY_SIZE				= 52510
	SCARAB_B_MEMORY_SIZE				= 52520
	PATTERN_GENERATION_LOOP_ENABLE				= 52530
	MEASUREMENT_TYPE				= 52540
	DIFFERENTIAL				= 52550
	NRSE				= 52560
	ND_4WIRE				= 52570
	READ_MARK_H_SNAPSHOT_GR1				= 52580
	READ_MARK_L_SNAPSHOT_GR1				= 52590
	READ_MARK_H_SNAPSHOT_GR2				= 52600
	READ_MARK_L_SNAPSHOT_GR2				= 52610
	WRITE_MARK_H_SNAPSHOT_GR1				= 52620
	WRITE_MARK_L_SNAPSHOT_GR1				= 52630
	WRITE_MARK_H_SNAPSHOT_GR2				= 52640
	WRITE_MARK_L_SNAPSHOT_GR2				= 52650

	PARAM_SCXI_SETTLING_TIME				= 52710
	PARAM_USER_DEFINED_SETTLING_TIME				= 52720
	PARAM_SCXI_SCAN_INFO				= 52730
	PARAM_SCXI_MODULE_CODE				= 52740
	PARAM_SCXI_DUMMY				= 52750
	PARAM_CHANNEL_NAME				= 52760
	PARAM_TASKID				= 52770
	PARAM_CJC				= 52780
	PARAM_CHANNEL_CLOCK_TIMEBASE				= 52790
	PARAM_CHANNEL_CLOCK_INTERVAL				= 52800
	PARAM_CHANNEL_CLOCK_FREQUENCY				= 52810
	PARAM_CHANNEL_CLOCK_SOURCE				= 52820
	PARAM_CHANNEL_CLOCK_DEFAULT				= 52830
	PARAM_SCAN_CLOCK_TIMEBASE				= 52840
	PARAM_SCAN_CLOCK_INTERVAL				= 52850
	PARAM_SCAN_CLOCK_FREQUENCY				= 52860
	PARAM_SCAN_CLOCK_SOURCE				= 52870
	PARAM_SCAN_CLOCK_DEFAULT				= 52880
	PARAM_NUM_CHANNELS				= 52890

class TriggerMode:
    BELOW_LOW_LEVEL  = ND.BELOW_LOW_LEVEL
    ABOVE_HIGH_LEVEL = ND.ABOVE_HIGH_LEVEL
    INSIDE_REGION    = ND.INSIDE_REGION
    HIGH_HYSTERESIS  = ND.HIGH_HYSTERESIS
    LOW_HYSTERESIS   = ND.LOW_HYSTERESIS
    
class TriggerSource:
    THE_AI_CHANNEL = ND.THE_AI_CHANNEL
    PFI0           = ND.PFI_0
    PFI1           = ND.PFI_1
    AI0            = 0 # Only for DSA
    AI1            = 1 # Only for DSA
    AI2            = 2 # Only for DSA
    AI3            = 3 # Only for DSA
    

class AiSignal:
    ATC_OUT       = ND.ATC_OUT # For DSA devices
    START_TRIGGER = ND.IN_START_TRIGGER
    STOP_TRIGGER  = ND.IN_STOP_TRIGGER
    SCAN_START    = ND.IN_SCAN_START
    SCAN_CLOCK_TIMEBASE = ND.IN_SCAN_CLOCK_TIMEBASE
    CONVERT       = ND.IN_CONVERT
    EXTERNAL_GATE = ND.IN_EXTERNAL_GATE
    CHANNEL_CLOCK_TIMEBASE = ND.IN_CHANNEL_CLOCK_TIMEBASE
    
class AoSignal:
    START_TRIGGER = ND.OUT_START_TRIGGER
    UPDATE        = ND.OUT_UPDATE
    EXTERNAL_GATE = ND.OUT_EXTERNAL_GATE
    UPDATE_CLOCK_TIMEBASE = ND.OUT_UPDATE_CLOCK_TIMEBASE

class Transition:
    LOW_TO_HIGH = ND.LOW_TO_HIGH
    HIGH_TO_LOW = ND.HIGH_TO_LOW
    DONT_CARE   = ND.DONT_CARE

class DeviceInfo:
    SERIAL_NUMBER = ND.DEVICE_SERIAL_NUMBER
    TYPE_CODE = ND.DEVICE_TYPE_CODE


if __name__ == '__main__':
    print ErrorCodes[-10884]

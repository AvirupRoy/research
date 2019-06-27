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
Created on Fri Jun 29 10:39:44 2012
@summary: Interface class for Agilent 33220A function generator
@author: Felix Jaeckel and Randy Lafler
@contact: fxjaeckel@gmail.com
"""
from PyQt4.QtCore import QObject

from Visa.VisaSetting import EnumSetting, IntegerSetting, FloatSetting, OnOffSetting, SettingCollection, InstrumentWithSettings
            
class SR785UnitFloatSetting(FloatSetting):
    '''A specialization of FloatSetting to deal with the circumstance that the SR785 allows to specify a scale in conjunction with a float setting.'''
    def _queryValue(self):
            r = self.instrument.queryString(self.queryTemplate)
            if ',' in r:
                d = r.split(',')
                units = int(d[1])
                mult = self.unitScale[units]
                value = float(d[0])*mult
            else:
                value = float(r)
            return value

class AmplitudeFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E-3, 1:1., 2:1}

class SineAmplitudeFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E-3, 1:1E-3, 2:1E-3, 3:1., 4:1.}

class FrequencyFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E3, 1:1., 2:1E-3, 3:1E-6}

class TimeFloatSetting(SR785UnitFloatSetting):
    unitScale = {0:1E-3, 1:1., 2:1}

class SR785InputRangeFloatEnumSetting(EnumSetting):
    @property
    def code(self):
        if not self.caching or self._code is None:
            if self.instrument is None:
                raise Exception("Unable to execute query!")
            r = self.instrument.queryString(self.queryString)
            if ',' in r:
                d = r.split(',')
                units = int(d[1])
                rawValue = int(d[0])
                if units == 0:
                    value = rawValue
                else:
                    raise Exception("Unsupported unit...")
            else:
                value = int(r)
#            value = '%d dBVpk' %value
            gains = np.linspace(-50,34,43)
            self._code = np.where(value == gains)[0][0]
            print "Code:", self._code
        self.changed.emit(self._code, False)
        return self._code
        
    @code.setter
    def code(self, newCode):
        if newCode in self.codes:
            if self.instrument:
                gains = np.linspace(-50,34,43)
                self.instrument.commandString('%s %d' %(self.command, gains[newCode]))
            else:
                raise Exception("No instrument object->can't execute command...")
            self._code = newCode
            self.changed.emit(newCode, True)
        else:
            raise Exception("Unsupported code")    


import struct
import numpy as np

from VisaInstrument import VisaInstrument


class SR785(VisaInstrument, InstrumentWithSettings, QObject):
    SCREEN_GRAPHS = 0
    SCREEN_MENU = 1
    SCREEN_STATUS = 2
    SCREEN_ALL = 3

    MenuKeyMap = [('Freq',33,'A'), ('Display\nSetup',34,'B'), ('Display\nOptions',35,'C'), ('Marker',36,'D'), ('Source',41,'H'), ('Input',42,'I'), ('Trigger',43,'J'), ('Average',44,'K'), ('User\nMath',49,'O'), ('Window',50,'P'), ('Water\nFall',51,'Q'), ('Capture',52,'R'), ('Analysis',57,'V'), ('Disk',58,'W'), ('Output',59,'X'), ('System',60,'Y')]
    SoftKeyMap = {1:0, 2:12, 3:11, 4:10, 5:9, 6:8, 7:16, 8:24, 9:32, 10:40}
    EntryKeyMap = [('Alt', 7), ('<-', 6), ('EXP', 5), ('7',2), ('8',3), ('9',4), ('4', 13), ('5',14), ('6', 15), ('1', 21), ('2', 22), ('3', 23), ('0', 29), ('.',30), ('-', 31)]
    ControlKeyMap = [('Start\nReset', 17), ('Start\ncapture', 18), ('Active\nDisplay', 19), ('Print\nScreen',20), ('Pause\nCont',25), ('Stop\nCapture', 26), ('Link',14), ('Help\nLocal',28)]
    FunctionKeyMap = [('Auto\nScale A',37,'E'), ('Auto\nRange Ch1',38,'F'), ('Marker\nRef',39,'G'), ('Auto\nScale B',45,'L'), ('AutoRange\nCh2',46,'M'), ('Display\nRef', 47,'N'), ('Span\nUp',53,'S'), ('Marker\nMax', 54,'T'), ('Marker\nCenter',55,'U'), ('Span\nDown',61,'Z'), ('Marker\nMin',62,'\\'), ('Show\nSetup',63,' ')]

    class Display(SettingCollection):
        NEWA = 2**0
        AVGA = 2**1
        SSA  = 2**4
        SSB  = 2**12

        def __init__(self, instrument):
            self.measurementGroup = EnumSetting('MGRP 2,', 'measurement group', [(0,'FFT'),(1,'correlation'),(2,'octave analysis'),(3,'swept sine')], instrument, 'MGRP? 1')
            self.instrument = instrument

        def selectMeasurement(self, display, measurement):
            group = self.measurementGroup.code
            print "Group:", group
            available = self.choicesForMeasurementGroup(group)
            print "Available:", available
            if measurement in available:
                for i,m in enumerate(available):
                    if m == measurement:
                        break
                self.instrument.commandString('MEAS %d,%d' % (display, i))
            else:
                raise Exception('Illegal measurement %s for group' % measurement)

        def choicesForMeasurementGroup(self, group):
            if group == self.measurementGroup.FFT:
                choices = ['linear','power spectrum','time record', 'time record (windowed)', 'orbit', 'cross spectrum', 'frequency response', 'coherence', 'capture']
            elif group == self.measurementGroup.CORRELATION:
                raise Exception('Not implemented!')
            elif group == self.measurementGroup.SWEPT_SINE:
                choices = ['spectrum', 'normalized variance', 'cross spectrum', 'frequency response']
            else:
                raise Exception('Not implemented!')
            return choices

        def retrieveData(self, display):
            raw = self.instrument.binaryTransfer('DSPB? %d' % display)
            l = len(raw)
            if l % 4 != 0:
                raise Exception('Incorrect length (%d) for binary response.' % l)
            n = l / 4
            data = struct.unpack('%df' % n, raw)
            return np.asarray(data)

#        def retrieveData2(self,display):
#            self.instrument.commandString('ACTD %d' %display)
#            raw = self.instrument.commandString('DUMP')
#            l = len(raw)
#            if l % 4 != 0:
#                raise Exception('Incorrect length (%d) for binary response.' % l)
#            n = l / 4
#            data = struct.unpack('%df' % n, raw)
#            return np.asarray(data)

    class Input(SettingCollection):
        def __init__(self, number, instrument):
            self.mode = EnumSetting('I%dMD' % number , 'input mode', [(0,'A'),(1,'A-B')], instrument,
                                      toolTip = "'A' is single-ended and 'A-B' is differential.\nIn general, when looking at very small signals, connect A to ghe signal source and B to the signal ground and use 'A-B'.\nFor more information, see page 285 of the User Manual pdf.")
            self.coupling = EnumSetting('I%dCP' % number, 'input coupling', [(0, 'DC'), (1, 'AC'), (2, 'ICP')], instrument,
                                         toolTip = "The 3dB bandwidth of the AC coupling is 0.16Hz.\nICP coupling connects a 5mA current source (26 VDC open current) to the center conductor of the A input connect.\nFor more information, see page 286 of the User Manual pdf.")
            self.grounding = EnumSetting('I%dGD' % number, 'input shield grounding', [(0, 'floating'), (1, 'grounded')], instrument,
                                          toolTip = "Float connects the shields to chassis ground through 1MOhm+0.01microF.\nGround connects the shields to chassis ground with 50Ohm.\nIn Ground mode, do not exceed 3V on the shields.\nFor more information, see pages 285-286 of the User Manual pdf.")
            self.autoRange = OnOffSetting('A%dRG' % number, 'auto ranging', instrument,
                                          toolTip = "Auto Range responds to all frequencies present at the input (except those attenuated by AC coupling), not just those withing the measurement span.\nFor more information, see page 192 of the User Manual pdf.")
            self.antiAliasing = OnOffSetting('I%dAF' % number, 'anti-alias filter', instrument,
                                             toolTip = "The anti-aliasing filter should generally be left On.\nFrequency domain measurements may have spurious alias signals if the filter is Off.\nFor more information, see pages 286-287 of the User Manual pdf.")
            self.aWeighting = OnOffSetting('I%dAW' % number, 'A-weighting', instrument,
                                           toolTip = "The A-Weighting filter simluates the hearing response of the human ear and is often used with Octave Analysis measurements.\nFor more information, see page 287 of the User Manual pdf.")
#            self.inputRange = EnumSetting('I%dRG' % number, 'input range', instrument,
#                                          toolTip = ")
            self.autoRangeMode = EnumSetting('I%dAR' % number, 'auto range mode', [(0,'up only'),(1,'tracking')], instrument, 'I%dAR?' % number,
                                                toolTip = "In Up Only, only overload causes the Input Range to change and thus, the Input Range only moves up.\nIn Tracking Mode, the Input Range moves up for overloads and down when the signal falls below half scale.\nDo not use Tracking Mode in cases with low frequency noise as this can cause the Input Range to osciallte.\nFor more information, see page 287 of the User Manual pdf.")
#            self.inputRange = SR785InputRangeFloatEnumSetting('I%dRG' % number, 'input range', [(i,'%d dBVpk' %(-50+2*i)) for i in range(43)], instrument, 'I%dRG?' % number,
            self.inputRange = SR785InputRangeFloatEnumSetting('I%dRG' % number, 'input range', [(i,'%f Vpk' %(10**(float(-50+2*i)/20))) for i in range(43)], instrument, 'I%dRG?' % number,
                                                                toolTip = "The input range is the full scale signal input just before overload.\nNote dBVpk=20log(Vpk) where log is base 10 so 20dBVpk=10Vpk.\nFor more information, see page 286 of the User Manual pdf.")


#        def InputRange(self):
#            return ['%f Vpp' %x for x in 10**(np.linspace(-50,34,42)/20)]
#
#        def setInputRange(self, display, inRange):
#            self.instrument.commandString('I%dRG %s' %(display, inRange))
#
#        # Note that the display has to be 1 or 2 not 0 or 1 like the others...
#        def getInputRange(self, display):
#            return self.instrument.queryString('I%dRG?' %display)

    class Source(SettingCollection):
        class Sine(SettingCollection):
            def __init__(self, number, instrument):
                # Need another amplitude setting for this because they are crazy
                self.amplitude = SineAmplitudeFloatSetting('S%dAM' % number, 'amplitude', 0, 5.0, 'V', 1E-4, 4, instrument,
                                              toolTip = "The sine output is the sum of two tones (sine waves) and the offset (constant).\nTo generate a single tone, set the amplitude of one of the tones to zero.\nNote that the sume of the amplitudes of Tone 1, Tone 2, and the absolute value of the offset cannot exceed 5V.\For more information, see page 267 of the User Manual pdf.")
                self.frequency = FrequencyFloatSetting('S%dFR' % number, 'frequency', 0, 102.4E3, 'Hz', 0.001, 3, instrument,
                                              toolTip = "The sine output is the sum of two tones (sine waves).\nRemember, the output is periodic over the FFT time record only if the frequency is an exact multiple of the Linewidth.\nFor more information, see page 267 of the User Manual pdf.")
                self.offset = AmplitudeFloatSetting('SOFF', 'sine source offset',-5, 5, 'V', 1E-4, 4, instrument, 'SOFF?',
                                           toolTip = "The sine output is the sum of two tones (sine waves) and the offset (constant).\nNote that the sum of the amplitudes of Tone 1, Tone 2 adn the absolute value of the offset cannot exceed 5V.\nUsing large offsets with small tone amplitudes will degrade the distortion performance of the sine source.\nFor more information, see page 268 of the User Manual pdf.")


        class Chirp(SettingCollection):
            def __init__(self, instrument):
                # Not sure on the amplitude value. I am guessing based on what the sine amplitude can be...
                self.amplitude = AmplitudeFloatSetting('CAMP', 'chirp amplitude', 0, 5.0, 'V', 1E-4, 4, instrument, 'CAMP?',
                                                       toolTip = "The peak output level is approximate due to the ripple in the source output reconstruction filter.\nThe input dynamic range of the measurement is reduced when using the chirp source.\nFor more information, see page 269 of the User Manual pdf.") # Don't know min and max
                self.burstPercentage = FloatSetting('CBUR', 'chirp burst percentage', 0.1, 100, '%', 0.1, 1, instrument, 'CBUR?',
                                                    toolTip = "The chirp waveform is output over a percentage of the FFT time record of the display selected as the Source Display.\nFor a continuous output, use 100% burst with continuous Trigger Source or Source Trigger.\nWith External Trigger, the chirp waveform is triggered along with the FFT time record.\nDo not use Ch1 or Ch2 input trigger since the output will not start until a trigger is received.\nFor more information, see pages 269-270 of the User Manual pdf.")
                self.display = EnumSetting('CSRC', 'source display', [(0,'display a'),(1,'display b')], instrument, 'CSRC?',
                                              toolTip = "The Source Display is the display which deteremines the burst period (FFT time record) and the bandwidth for bandlimited noise and chirp (FFT Span).\nThere is a single Source Display for both Chirp and Noise outputs.\nIf the other display has a different span, the chirp will not be appropriate for that span.\nFor more information, see page 270 of the User Manual pdf.")

        class Noise(SettingCollection):
            def __init__(self, instrument):
                # amplitude
                self.amplitude = AmplitudeFloatSetting('NAMP', 'noise amplitude', 0, 100, '%', 0.1, 1, instrument,
                                                       toolTip = "The source output will overshoot this amplitude by as much as 100% a small percentage of the time.\nBecause of the nature of noise, the peak amplitude is not perfectly defined.\nFor more information, see page 271 of the User Manual pdf.") # Not sure
                self.type = EnumSetting('NTYP', 'noise type', [(0,'bandlimited white'),(1,'white'),(2,'pink')],instrument,
                                        toolTip = 'White noise provides equal noise density from 0 to 102.4 kHz (regardless of the measurement bandwidth of the displays).\nThe spectrum of white noise appears flat in an FFT spectrum.\nPink noise rolls off at 3dB/oct providing equal energy per octave and extends beyond 102 kHz.\nBandlimiting restricts the noise bandwidth to the measurement span of the Source Display.\nFor more information, see page 271 of the User Manual')
                self.burstPercentage = FloatSetting('NBUR', 'noise burst percentage',0.1,100,'%',0.1,1,instrument,'NBUR?',
                                                    toolTip = "The noise waveform is output for a percentage of the FFT time record of the display selected as the Source Display.\nFor a continuous output, use 100% burst.\nWhen the burst percentage is less than 100%, the burst noise source is triggerd by Exernal triggers.\nDo not use Ch1 or Ch2 input trigger since the output will not start until a trigger is received.\nFor more information, see page 272 of the User Manual pdf.")
                self.sourceDisplay = EnumSetting('CSRC', 'source display', [(0,'display a'),(1,'display b')], instrument, 'CSRC?',
                                                    toolTip = 'This command is valid only when the Source Type is Chirp or Noise and the Measurement Group is FFT.\nFor more information, see page 272 of the User Manual pdf.')
                #self.burstSourcePeriod

        class Arbitrary(SettingCollection):
            def __init__(self, instrument):
                # Probably need to change this to a float setting
                self.amplitude = FloatSetting('AAMP', 'arbitrary source amplitude', 0, 500, '%', 0.0001, 4, instrument, 'AAMP?',
                                                toolTip = "The amplitude of the arbitrary source is relative to 1V.\nThe maximum output is 5V.\nFor more information, see page 274 of the User Manual pdf.")
                self.playbackRate = FloatSetting('ARAT', 'arbitrary source playback rate', 0, 19, '', 0.01,2, instrument, 'ARAT?', # @fixme @bug @TODO Figure out what ARAT this really is
                                                   toolTip = 'The maximum rate is divided by 2 to this power to obtain a rate.\nFor more information, see page 275 of the User Manual pdf.')
                self.buffer = EnumSetting('ASRC', 'arbitrary source buffer', [(0,'arbitrary waveform memory'),(1,'channel 1 capture'),(2,'channel 2 capture')], instrument, 'ASRC?',
                                                      toolTip = 'For more information, see page 275 of the User Manual pdf.')
                #self.startPoint = # Not sure what is going on here
                #self.length = # Not sure how to deal with this. Can only be an even number
                # See page 457 of the user manual to see if this is useful

        def __init__(self, instrument):
            self.type = EnumSetting('STYP', 'source type', [(0,'sine'), (1,'chirp'), (2,'noise'), (3,'arbitrary')], instrument,
                                        toolTip = "For information on the different source types, see pages 263-266 of the User Manual pdf.")
            self.output = OnOffSetting('SRCO', 'output enable', instrument,
                                       toolTip = "If the source is off, the output is held at 0V.\nFor more information, see page 263 of the User Manual pdf.")
            self.sine = [self.Sine(1, instrument), self.Sine(2, instrument)]
            self.sineOffset = AmplitudeFloatSetting('SOFF', 'sine offset', -5., +5., 'V', 1E-4, 4, instrument,
                                                    toolTip = '[-5..5V]\nThe offset resolution is 0.1mV.\nNote that the sum of the offset and Amplitude (if Auto Level Reference is off) or Maximum Source (if Auto Level Reference is on) cannot exceed 5V.\nFor more information, see page 282 of the User Manual.')
            self.noise = self.Noise(instrument)
            self.chirp = self.Chirp(instrument)
            self.arbitrary = self.Arbitrary(instrument)

    class FFT(SettingCollection):
        def __init__(self, instrument):
            self.instrument = instrument
            # Frequency Menu
            # Not sure on a lot of these. It doesn't give a range so I figured it must be the same as in swept sine
            # Should the different displays be able to have different settings?
            # Frequency Span is discrete and see the help files
            # Should get rid of start and end frequency and only use span and center, need to set base frequency first
#            self.frequencySpan = # What is going on here?... I think it can go from 0 to 102.4kHz
#            self.frequencySpan = FrequencyFloatSetting('FSPN 2,','frequency span', 0, 102.4E3, 'Hz', 1E-3, 3, instrument, 'FSPN? 1', toolTip = 'Note that frequency span will update to give the nearest possible frequency span.')
            self.lines = EnumSetting('FLIN 2,', 'lines (resolution)', [(0,'100 lines'),(1,'200 lines'),(2,'400 lines'),(3,'800 lines')],instrument, 'FLIN? 1',
                                     toolTip = "Fewer lines means wider linewidths (poorer resolution) but faster measurements.\nMore lines means narrower linewidths (better resolution) but slower measurements.\nChanging the FFT Resolution does not change the Span.\nThe Acquisition Time is changed (FFT Resolution/Span).\n For more information, see page 205 of the User Manual pdf.")
            self.baseFrequency = EnumSetting('FBAS 2,', 'base frequency', [(0,'100.0 kHz'),(1,'102.4 kHz')],instrument,'FBAS? 1',
                                              toolTip = "The Base Frequency sets the Full Span bandwidth for FFT measurements.\nAll spans are derived from the base frequency by dividing by powers of 2.\nChanging the FFT Base Frequency affects ALL of the FFT frequency parameters as well as the source frequency.\nFor more information, see page 205 of the User Manual pdf.")
            # The below should probably be implemented at some point but it is going to take some work
            #self.frequencySpan = EnumSetting('FSPN 2,', 'frequency span', list(enumerate(np.arange(self.baseFrequency))))
#            self.frequencySpan102 = EnumSetting('FSPN 2,', 'frequency span', [(x,'%f Hz' %x) for x in 102.4E3*np.logspace(-19,0,20,base=2)],instrument,'FSPN? 1')
#            [(x,'%f Hz' %x) for x in 102.4E3*np.logspace(-19,0,20,base=2)]
#            self.frequencySpan100 = EnumSetting('FSPN 2,', 'frequency span', enumerate(list(100E3*np.logspace(-19,0,20,base=2))),instrument,'FSPN? 1')
# Trying something with the lists
#            self.frequencySpan100 = EnumSetting('FSPN 2,', 'frequency span', [(x,'%f Hz' %x) for x in 100E3*np.logspace(-19,0,20,base=2)],instrument,'FSPN? 1')
#            self.frequencySpan102 = EnumSetting('FSPN 2,', 'frequency span', [(0, '0.195313 Hz'), (1, '0.390625 Hz'), (2, '0.78125 Hz'), (3, '1.5625 Hz'), (4, '3.125 Hz'), (5, '6.25 Hz'), (6, '12.5 Hz'), (7, '25.0 Hz'), (8, '50.0 Hz'), (9, '100.0 Hz'), (10, '200.0 Hz'), (11, '400.0 Hz'), (12, '800.0 Hz'), (13, '1600.0 Hz'), (14, '3200.0 Hz'), (15, '6400.0 Hz'), (16, '12800.0 Hz'), (17, '25600.0 Hz'), (18, '51200.0 Hz'), (19, '102400.0 Hz')],instrument,'FSPN? 1',useCode=False)
#            self.frequencySpan100 = EnumSetting('FSPN 2,', 'frequency span', [(0, '0.190735 Hz'), (1, '0.381470 Hz'), (2, '0.76294 Hz'), (3, '1.52588 Hz'), (4, '3.05176 Hz'), (5, '6.10352 Hz'), (6, '12.2070 Hz'), (7, '24.4141 Hz'), (8, '48.8281 Hz'), (9, '97.6563 Hz'), (10, '195.313 Hz'), (11, '390.625 Hz'), (12, '781.25 Hz'), (13, '1562.5 Hz'), (14, '3125.0 Hz'), (15, '6250.0 Hz'), (16, '12500.0 Hz'), (17, '25000.0 Hz'), (18, '50000.0 Hz'), (19, '100000.0 Hz')],instrument,'FSPN? 1', useCode=False)
# These two below should work for reading them back. I think the decimal places are correct so that it will work with the restore settings function
            #self.frequencySpan102 = EnumSetting('FSPN 2,', 'frequency span', [(0, '0.195313 Hz'), (1, '0.390625 Hz'), (2, '0.78125 Hz'), (3, '1.5625 Hz'), (4, '3.125 Hz'), (5, '6.25 Hz'), (6, '12.5 Hz'), (7, '25.0 Hz'), (8, '50.0 Hz'), (9, '100.0 Hz'), (10, '200.0 Hz'), (11, '400.0 Hz'), (12, '800.0 Hz'), (13, '1600.0 Hz'), (14, '3200.0 Hz'), (15, '6400.0 Hz'), (16, '12800.0 Hz'), (17, '25600.0 Hz'), (18, '51200.0 Hz'), (19, '102400.0 Hz')],instrument,'FSPN? 1',useCode=False)
            #self.frequencySpan100 = EnumSetting('FSPN 2,', 'frequency span', [(0, '0.190735 Hz'), (1, '0.38147 Hz'), (2, '0.762939 Hz'), (3, '1.525879 Hz'), (4, '3.051758 Hz'), (5, '6.103516 Hz'), (6, '12.207031 Hz'), (7, '24.414063 Hz'), (8, '48.828125 Hz'), (9, '97.65625 Hz'), (10, '195.3125 Hz'), (11, '390.625 Hz'), (12, '781.25 Hz'), (13, '1562.5 Hz'), (14, '3125.0 Hz'), (15, '6250.000000 Hz'), (16, '12500.0 Hz'), (17, '25000.0 Hz'), (18, '50000.0 Hz'), (19, '100000.0 Hz')],instrument,'FSPN? 1', useCode=False)

#            self.frequencySpan102 = EnumSetting('FSPN 2,', 'frequency span', [(0, '0.1953125 Hz'), (1, '0.390625 Hz'), (2, '0.78125 Hz'), (3, '1.5625 Hz'), (4, '3.125 Hz'), (5, '6.25 Hz'), (6, '12.5 Hz'), (7, '25.0 Hz'), (8, '50.0 Hz'), (9, '100.0 Hz'), (10, '200.0 Hz'), (11, '400.0 Hz'), (12, '800.0 Hz'), (13, '1600.0 Hz'), (14, '3200.0 Hz'), (15, '6400.0 Hz'), (16, '12800.0 Hz'), (17, '25600.0 Hz'), (18, '51200.0 Hz'), (19, '102400.0 Hz')],instrument,'FSPN? 1',useCode=False)
#            self.frequencySpan100 = EnumSetting('FSPN 2,', 'frequency span', [(0, '0.19073486328125 Hz'), (1, '0.3814697265625 Hz'), (2, '0.762939453125 Hz'), (3, '1.52587890625 Hz'), (4, '3.0517578125 Hz'), (5, '6.103515625 Hz'), (6, '12.20703125 Hz'), (7, '24.4140625 Hz'), (8, '48.828125 Hz'), (9, '97.65625 Hz'), (10, '195.3125 Hz'), (11, '390.625 Hz'), (12, '781.25 Hz'), (13, '1562.5 Hz'), (14, '3125.0 Hz'), (15, '6250.0 Hz'), (16, '12500.0 Hz'), (17, '25000.0 Hz'), (18, '50000.0 Hz'), (19, '100000.0 Hz')],instrument,'FSPN? 1', useCode=False)
            self.startFrequency = FrequencyFloatSetting('FSTR 2,', 'start frequency', 1E-3, 102.4E3, 'Hz', 1E-3, 3, instrument, 'FSTR? 1')
            self.centerFrequency = FrequencyFloatSetting('FCTR 2,', 'center frequency', 1E-3, 102.4E3, 'Hz', 1E-3, 3, instrument, 'FCTR? 1',
                                                         toolTip = "The Center frequency is the center of the measurement span.\nFor more information, see page 206 of the User Manual pdf.")
            self.endFrequency = FrequencyFloatSetting('FEND 2,', 'end frequency', 1E-3, 102.4E3, 'Hz', 1E-3, 3, instrument, 'FEND? 1')
#            self.settle = self.instrument.commandString('UNST 2') # Not sure if this makes sense or not, settle both displays?

            # Average Commands
            self.computeAverage = OnOffSetting('FAVG 2, ', 'compute average', instrument, 'FAVG? 1', toolTip = "If Compute Averages is off, no averaged quantites will be computed or displayed.\nAlthough this results in a slight improvement in the speed of some measurements, for normal operation Compute Averages should be left On.\nFor more information, see page 303 of the User Manual pdf.") #Should probably include...
            self.averageType = EnumSetting('FAVM 2, ', 'average type', [(0,'none'),(1,'vector'),(2,'rms'),(3,'peak hold')], instrument, 'FAVM? 1',
                                            toolTip = "Vector averaging averages the real and imaginary parts of the instanteous FFT measurements seperately.\nSince signed values are combined in the mean, random signals tend to average to zero.\nFor single channel measurements, vector averaging requires a trigger.\nThe Time Record Increment should be set to 100% when vector averaged measurements are being used.\mFor FFT measurements, RMS averaging is real and has zero phase.\nRMS averaging reduces fluctuations in the data but does not reduce the actual noise floor.\nPeak hold averaging is similar to RMS averaging, in that the RMS measurement quantities are calculated.\nHowever, instead of averaging the RMS measurements together, in peak-hold averaging the new data is compared to the old data and the maximum value is kept.\nFor more information, see pages 305-307 in the User Manual pdf.")
            self.fftAverageType = EnumSetting('FAVT 2, ', 'fft average type', [(0,'linear/fixed length'),(1,'exponential/continuous')], instrument, 'FAVT? 1',
                                               toolTip = "Linear weighting combines N (Number of Averages) measurements with equal weighting in either RMS or Vector averaging.\nWhen used with peak hold averaging, linear length weighting becomes fixed lenght averaging in that a fixed number, N, of measurements are compared to determining the peak.\nExponential weighting weights new data more than old data.\nExponential weighting reaches a steady state after approximately 5N measurements.\nMake sure that the number of averages is not so large as to eliminate changes in the data which might be important.\n When used with peak hold averaging, exponential weighting becomes continuous weighting in that new measurements are continually being compared to the current maximum to determing the new peak.\nFor more information, see page 304 of the User Manual pdf.")
            self.numberOfAverages = IntegerSetting('FAVN 2, ', 'number of averages', 2, 32767, '', instrument, 'FAVN? 1',
                                                   toolTip = "The Number of Averages specifies the number of measurements for Linear/Fixed Length averages or the weighting of new data in Exponential/Continuous average.\nFore more information, see page 305 of the User Manual pdf.")
            self.fftTimeRecordIncrement = FloatSetting('FOVL 2, ', 'fft time record increment', 0, 300, '%', 0.01, 2, instrument, 'FOVL? 1',
                                                       toolTip = "The Time Record Increment is how far the start of each time record is advanced between measurements (as a percentage of time record length.)\nIf the increment is 100%, the start of the next time record is exactly one time record advanced from the start of the previous time record.\nIf the increment is 25%, then the next time record starts 1/4 of a time record advanced from the start of the previous time record.\nWhen the Time Record Increment is less than or equal to 100%, the measurement is said to be 'real time'.\nWhen the Time Record Increment is greater than 100%, then the measurement is not 'real time' and some time points do not contribute to a measurement.\nTime Record Increment is set to 100% when vector averaged measurments are being used.\nFor more information, see page 307 of the User Manual pdf.")
# Might want to change overload reject to a check box and then add the toolTip
            self.overloadReject = EnumSetting('FREJ 2, ', 'overload reject', [(0,'off'),(1,'on')], instrument, 'FREJ? 1',)
            self.triggerAverageMode = EnumSetting('TAVM 2', 'trigger average mode', [(0,'time records'),(1,'averages')], instrument, 'TAVM? 1',
                                                     toolTip = "Normally, when Trigger Average Mode is set to Time Record each trigger triggers a single time record in each of these measurement groups.\nWhen Trigger Average Mode is set to Start Average, the first trigger will trigger ther first time record, and subsequent time records will be acquired as quickly as possible until the linear average is complete.\nFor more information, see page 309 of the User Manual pdf.") # Might need a display here, see page 469 of User Manual
            #self.averagePreview = EnumSetting('PAVO 2, ', 'average preview', [(0,'off'),(1,'manual'),(2,'timed')], instrument, 'PAVO? 1') # Might want to look at this one too...
#            self.previewTime = # not sure the min and max here
            # Not sure what to do about PAVA and PAVR - not needed

            # Windowing Commands
            self.windowType = EnumSetting('FWIN 2,', 'window type', [(0,'uniform'),(1,'flattop'),(2,'hanning'),(3,'bmh'),(4,'kaiser'),(5,'force/exponential')], instrument, 'FWIN? 1',
                                            toolTip = "Uniform means the time record is used with no windowing.\nUniform windowing provides amplitude accuracy only for exact bin frequencies and very poor frequency selectivity and is a poor choice for continuous signals.\nThe Hanning window has an amplitude variation of about 1.5dB for off-bin signals and provides only reasonable selectivity.\nThe Hanning window can limit the performance of the analyzer when looking at signals close together in frequency and very different in amplitude.\nThe Flattop window has the best amplitude accuracy of any window with an off-bin amplitude variation of about 0.02dB.\nThe Flattop window is the best window to use for accurate amplitude measurements.\nBMH window has reasonable off-bin amplitude accuracy (about 0.8dB).\n BMH is a good window to use for measurements requiring a large dynamic range.\nThe Kaiser window has the lowest side-lobes and least broadening for non-bin frequencies.\nThe Kaiser window is the best window to use for measurements requiring a large dynamic range.\nThe Force window is uniform over the beginning of the time record and zero over the remainder.\nThe Force window is used to isolate impulsive signals from noise and other oscillations later in the time record.\nThe Exponential window attenuates the time record with a decaying exponential time constant.\nThe Exponential window is often used in impact testing on the response channel to remover oscillations which last longer than the time record.\nFor more information, see pages 327-328 in the User Manual pdf.") # Can be used for FFT, Correlation, or Order measurements
            self.forceOrExponential1 = EnumSetting('W1FE', 'channel 1 force or exponetial', [(0,'force window'),(1,'exponetial window')], instrument, 'W1FE?',
                                                     toolTip = "The Force window is uniform over the beginning of the time record and zero over the remainder.\nThe Force window is used to isolate impulsive signals from noise and other oscillations later in the time record.\nThe Exponential window attenuates the time record with a decaying exponential time constant.\nThe Exponential window is often used in impact testing on the response channel to remover oscillations which last longer than the time record.\nFor more information, see pages 328-329 in the User Manual pdf.")
            self.forceOrExponential2 = EnumSetting('W2FE', 'channel 2 force or exponetial', [(0,'force window'),(1,'exponetial window')], instrument, 'W2FE?',
                                                     toolTip = "The Force window is uniform over the beginning of the time record and zero over the remainder.\nThe Force window is used to isolate impulsive signals from noise and other oscillations later in the time record.\nThe Exponential window attenuates the time record with a decaying exponential time constant.\nThe Exponential window is often used in impact testing on the response channel to remover oscillations which last longer than the time record.\nFor more information, see pages 328-329 in the User Manual pdf.")
            self.expoWindowTimeConstant = FloatSetting('FWTC 2,', 'expo window time constant', 5, 1000, '%', 0.1, 1, instrument, 'FWTC? 1',
                                                       toolTip = "The Exponential Window Time Constant is the percentage of the FFT time record where the window function reaches 1/e.\nFor more information, see page 329 of the User Manual pdf.")
            self.forceLength = FloatSetting('FWFL 2, ', 'force length', 0, 1E5, '', 0.01, 2, instrument, 'FWFL? 1',
                                              toolTip = "Points in the time record up to the Force Length are unmodified.\nPoints in the time record past the Force Length are zeroed.\nThe maximum value that can be entered is the length of the FFT time record.\nFor more information, see page 329 of the User Manual pdf.")
# Change computeAverage to a OnOffSetting
#        def isComputeAverage(self):
#            return self.instrument.commandString('FAVG? 1')
#
#        def setComputeAverage(self, onOff):
#            self.instrument.commandString('FAVG 2, %d' %onOff)
#
#        def computeAverageToolTip(self):
#            return "If Compute Averages is off, no averaged quantites will be computed or displayed.\nAlthough this results in a slight improvement in the speed of some measurements, for normal operation Compute Averages should be left On.\nFor more information, see page 303 of the User Manual pdf."
# Add toolTip for settleMeasurement
        def settleMeasurement(self):
            self.instrument.commandString('UNST 2')

        def setFrequencySpan(self, span): # Use this to actually set the span
            self.instrument.commandString('FSPN 2, %s' %span)
#            if self.baseFrequency.code == 0:
#                pass
#                # deal with it
#            elif self.baseFrequency.code == 1:
#                pass

        def frequencySpan(self): # Might want to first find the index with this value and then set the index to that value so that it doesn't add something to it, use findText function
            return self.instrument.queryFloat('FSPN? 1')

        def availableFrequencySpans(self, baseFreq): # Use this to send the available values to the combo box
            if baseFreq == '100.0 kHz':
                return ['0.190735 Hz', '0.38147 Hz', '0.762939 Hz', '1.525879 Hz', '3.051758 Hz', '6.103516 Hz', '12.207031 Hz', '24.414063 Hz', '48.828125 Hz', '97.65625 Hz', '195.3125 Hz', '390.625 Hz', '781.25 Hz', '1562.5 Hz', '3125.0 Hz', '6250.0 Hz', '12500.0 Hz', '25000.0 Hz', '50000.0 Hz', '100000.0 Hz']
                # deal with it
            elif baseFreq == '102.4 kHz':
                return ['0.195313 Hz', '0.390625 Hz', '0.78125 Hz', '1.5625 Hz', '3.125 Hz', '6.25 Hz', '12.5 Hz', '25.0 Hz', '50.0 Hz', '100.0 Hz', '200.0 Hz', '400.0 Hz', '800.0 Hz', '1600.0 Hz', '3200.0 Hz', '6400.0 Hz', '12800.0 Hz', '25600.0 Hz', '51200.0 Hz', '102400.0 Hz']

        def frequencySpanToolTip(self):
            return "The frequency span ranges from the FFT Base Frequency to 2^-19 times the Base Frequency in factors of 2.\nChanging the Span will change the Linewidth (Span/FFT Resolution) and Acquistion Time (FFT Resolution/Span).\nFor more information, see pages 203-204 of the User Manual pdf."

        def measurementSelect(self, display):
             # Measurement Types
            self.type = EnumSetting('MEAS %d, ' %display, 'measurement type', [(0,'fft 1'),(1,'fft 2'),(2,'power spectrum 1'),(3,'power spectrum 2'),(4,'time 1'),(5,'time 2'),(6,'windowed time 1'),(7,'windowed time 2'),(8,'orbit'),(9,'coherence'),(10,'cross spectrum'),(11,'frequency response'),(12,'capture buffer 1'),(13,'capture buffer 2'),(14,'fft user function 1'),(15,'fft user function 2'),(16,'fft user function 3'),(17,'fft user function 4'),(18,'fft user function 5')], instrument, 'MEAS? %d' %display)
            self.view = EnumSetting('VIEW %d, ' %display, 'measurement view', [(0,'log magnitude'),(1,'linear magnitude'),(2,'magnitude squared'),(3,'real part'),(4,'imaginary part'),(5,'phase'),(6,'unwrapped phase'),(7,'nyquist'),(8,'nichols')], instrument, 'VIEW? %d' %display)

# Probably can make so that only one windowing type per display
#        def windowCommands(self, display):
#            self.windowType = EnumSetting('FWIN %d, ' %display, 'window type', [(0,'uniform'),(1,'flattop'),(2,'hanning'),(3,'bmh'),(4,'kaiser'),(5,'force/expoential')], instrument, 'FWIN? %d' %display) # Can be used for FFT, Correlation, or Order measurements
#            # Next two functions only applicable when windowType is force/exponetial
#            self.forceOrExponential1 = EnumSetting('W1FE', 'channel 1 force or exponetial', [(0,'force window'),(1,'exponetial window')], instrument, 'W1FE?')
#            self.forceOrExponential2 = EnumSetting('W2FE', 'channel 2 force or exponetial', [(0,'force window'),(1,'exponetial window')], instrument, 'W2FE?')
#            # Might need a new setting type for the below
##            self.forceWindowLength =
#            self.expoWindowTimeConstant = IntegerSetting('FWTC %d, ' %display, 'expo window time constant', 0, 100, '%', instrument, 'FWTC? %d' %display)
#            # Do I want any of the trace stuff?
#            # Do I want any of the stuff about user functions?




    class SweptSine(SettingCollection):
        def __init__(self, instrument):
            self.instrument = instrument
            # Measurement Types, need to add in the display since each could be different...
            # Is there a clever way to do this?
            self.measurementType1 = EnumSetting('MEAS 0,', 'measurement type', [(42,'spectrum 1'),(43, 'spectrum 2'),(44,'normalized variance 1'),(45,'normalized variance 2'),(46,'cross spectrum'),(47,'frequency response')],instrument,'MEAS? 0')
            self.measurementType2 = EnumSetting('MEAS 1,', 'measurement type', [(42,'spectrum 1'),(43, 'spectrum 2'),(44,'normalized variance 1'),(45,'normalized variance 2'),(46,'cross spectrum'),(47,'frequency response')],instrument,'MEAS? 1')
            self.measurementView1 = EnumSetting('VIEW 0,', 'measurement view', [(0,'log'),(1,'linear'),(2,'magnitude squared'),(3,'real'),(4,'imaginary'),(5,'phase'),(6,'unwrapped phase'),(7,'nyquist'),(8,'nichols')],instrument,'VIEW? 0')
            self.measurementView2 = EnumSetting('VIEW 1,', 'measurement view', [(0,'log'),(1,'linear'),(2,'magnitude squared'),(3,'real'),(4,'imaginary'),(5,'phase'),(6,'unwrapped phase'),(7,'nyquist'),(8,'nichols')],instrument,'VIEW? 1')

            # Frequency Menu
            self.startFrequency = FrequencyFloatSetting('SSTR 2,', 'start frequency', 1E-3, 102.4E3, 'Hz', 1E-3, 3, instrument, 'SSTR? 1',
                                                        '[1mHz.. 102.4kHz]\nNote that measurements at frequencies less than 1 Hz take a significant amount of time.\nIf the Start frequency is changed during a sweep, the sweep will be reset.\nFor more information, see page 211 of the User Manual.')
            self.stopFrequency = FrequencyFloatSetting('SSTP 2,', 'stop frequency', 1E-3, 102.4E3, 'Hz', 1E-3, 3, instrument, 'SSTP? 1',
                                                       '[1mHz.. 102.4kHz]\nNote that measurements at frequencies less than 1 Hz take a significant amount of time.\nIf the Stop frequency is changed during a sweep, the sweep will be reset.\nFor more information, see page 211 of the User Manual.')
            self.repeat = EnumSetting('SRPT 2,', 'sweep repeat', [(0, 'single shot'), (1, 'continuous')], instrument, 'SRPT? 1',
                                      toolTip = 'In Single Shot mode, the measurement is paused at the completion of the sweep and the source ramps off.\nIn Continuous mode, the measurement is repeated at the completion of each sweep.\nThe source moves immediately to the Start frequency and begins the sweep again.\nFor more imformation, see page 212 of the User Manual.')
            self.sweepType = EnumSetting('SSTY 2,', 'sweep type', [(0, 'linear'), (1, 'log')], instrument, 'SSTY? 1',
                                         toolTip ='Linear sweep computes the measurement points in a linear progression from the start to the stop frequency.\nLog sweep uses a logarithmic progression of points from the start to the stop frequency.\nFor more information, see page 212 of the User Manual.')
            self.autoResolution = EnumSetting('SARS 2', 'auto resolution', [(0, 'off'), (1, 'on')], instrument, 'SARS? 1',
                                              toolTip = 'If Auto Resolution is off, all points in the sweep are measured.\nThis also disables Maximum Step Size, Faster Threshold, and Slower Threshold.\nAuto Resolution On allows the sweep to skip points if sequentail points do not vary by more than a specified amount.\nFor more imformation, see page 212 of the User Manual.')
            self.numberOfPoints = IntegerSetting('SNPS 2,', 'number of points', 10, 2048, '', instrument, 'SNPS? 1',
                                                 '[10..2048]\nThe points are in a Linear or Logarithmic progression as set by the Sweep Type.\nIf the Number of Points is changed during a sweep, the sweep will be reset.\nFor more information, see page 213 of the User Manual.')
            self.maximumStepSize = IntegerSetting('SSKP 2', 'maximum step size', 2, 256, '', instrument, 'SSKP? 1',
                                                  '[2..256]\nWhen Auto Resolution is On, each successive time the Faster Threshold condition is met (on BOTH channels), the frequency step size is increased until the Maximum Step Size is reached.\nGenerally, this number should not exceed 5% of the Number of Points in the sweep.\nFor more information, see page 213 of the User Manual.')
            self.fasterThreshold = FloatSetting('SFST 2', 'faster threshold', 1E-2, 3, 'dB', 1E-2, 2, instrument, 'SFST? 1',
                                                '[0.01..3dB]\nOnly enabled if Auto Resolution is On.\nIf the newest measurement is within the Faster Threshold of the previous measurement for BOTH channels, then the sweep will take larger steps, skipping frequency points.\nFor more information, see page 213 of the User Manual.')
            self.slowerThreshold = FloatSetting('SSLO 2', 'slower threshold', 5E-2, 6, 'dB', 1E-2, 2, instrument, 'SSLO? 1',
                                                '[0.05..6dB]\nOnly enabled if Auto Resolution is On.\nIf Auto Resolution is skipping points and a measurement differs from the previous measurement by more than the Slower Threshold for EITHER channel, then the sweep returns to the previously measured point and moves to the very next frequency point in the sweep (with no skipping).\nFor more information, see page 214 of the User Manual.')

            # Source Menu
            self.autoLevelReference = EnumSetting('SSAL', 'auto level reference', [(0, 'off'), (1, 'channel 1'), (2, 'channel 2')], instrument, 'SSAL ?',
                                                  toolTip = 'Auto Level Off maintains the source amplitude at a constant level at all frequencies during the swept sine sweep.\nThis usually works best for transfer functions which are fairly flat.\nAuto Level Channel 1 or 2 will adjust the source level to maintain a constant level, called the Ideal Reference, at the Channel 1 or 2 input.\nGenerally, this is useful for frequency response functions with substantial gain as well as attenuation.\nFor more information, see page 279 of the User Manual.')
            self.amplitude = AmplitudeFloatSetting('SSAM', 'sine amplitude', 0, 5, 'V', 1E3, 3, instrument, 'SSAM?',
                                                   '[0..5000mV]\nThis parameter is adjustable only if Auto Level Reference is Off.\nThe amplitude may be changed at any time during a sweep.\nFor more information, see page 279 of the User Manual.')
            self.idealReference = AmplitudeFloatSetting('SSRF', 'ideal reference', 0, 5, 'V', 1E3, 3, instrument, 'SSRF?',
                                                        '[0..5000mV]\nThis parameter is adjustable only if Auto Level Reference is set to Channel 1 or Channel 2.\nThe Ideal Reference is the signal level that the source maintains at the Reference Channel to within the Reference Limits.\nThe Ideal Reference may be changed at any time during a sweep.\nFor more information, see page 280 of the User Manual.')
            self.sourceRamping = EnumSetting('SRMP', 'source ramping', [(0, 'off'), (1, 'on')], instrument, 'SRMP?',
                                             toolTip = 'If Source Ramping is Off, source level changes are made instantly.\nIf Source Ramping is On, source level changes are made at the Source Ramp Rate.\nSettling starts after the source amplitude reaches the desired level.\nFor more information, see page 280 of the User Manual.')
            self.sourceRampRate = FloatSetting('SRAT', 'source ramp rate', 1E-3, 500, 'V/s', 1E-3, 3, instrument, 'SRAT?',
                                               '[0.001..500V/s]\nThe Source Ramp Rate is the rate at which the source amplitude changes when Source Ramping is On.\nIf Source Ramping is Off, source amplitude changes are made instantly.\nFor more information, see page 280 of the User Manual.')
            self.referenceUpperLimit = FloatSetting('SSUL', 'reference upper limit', 0.1, 30, 'dB', 0.1, 1, instrument, 'SSUL?',
                                                    '[0.1..30.0dB]\nThis parameter is only adjustable if Auto Level Reference is set to Channel 1 or Channel 2.\nWhen Auto Level is on, the Ideal Reference is the signal level the source will try to maintain at the Reference Channel.\nThe Reference Upper and Lower Limits are the allowable tolerances for the Reference Channel.\nThe Reference Upper Limit may be changed during a sweep.\nFor more information,see page 281 of the User Manual.')
            self.referenceLowerLimit = FloatSetting('SSLL', 'reference lower limit', -0.1, -30, 'dB', 0.1, 1, instrument, 'SSLL?',
                                                    '[-0.1..-30.0dB]\nThis parameter is adjustable only if Auto Level Refernce is set to Channel 1 or Channel 2.\nWhen Auto Level is on, the Ideal Reference is the signal level the source will try to maintain at the Reference Channel.\nThe Reference Upper and Lower Limits are all allowable tolerances for the Reference Channel.\nThe Reference Lower Limit may be changed during a sweep.\nFor more information, see page 281 of the User Manual.')
            self.maximumSourceLevel = AmplitudeFloatSetting('SMAX', 'maximum source level', 0, 5, 'V', 1E3, 3, instrument, 'SMAX?',
                                                            '[0..5000mV]\nThis parameter is adjustable only if Auto Level Reference is set to Channel 1 or Channel 2.\nThe Maximum Source Level is the largest allowed source amplitude.\nThe Maximum Source Level may be changed at any time during a sweep.\nFor more information, see page 281 of the User Manual.')
            #self.offset = FloatSetting('SOFF', 'DC offset', -5, 5, 'V', 1E-4, 4, instrument, 'SOFF?')

            # Average Menu
            self.settleTime = TimeFloatSetting('SSTM 2,', 'settle time', 3.906E-3, 1E3, 's', 3.906E-3, 4, instrument, 'SSTM? 1',
                                               '[7.8125ms..1ks]\nAt each frequency point, a settling time is allowed to pass before any measurement is made.\nThis allows the device under test to respond to the frequency change.\nThe actual settling time is the larger of the Settle Time and the Settle Cycles.\nChanges made to the Settle Time during a sweep take effect immediately.\nFor more information, see page 315 of the User Manual.')
            self.settleCycles = IntegerSetting('SSCY 2,', 'settle cycles', 1, 32767, 'cycles', instrument, 'SSCY? 1',
                                               '[1..32767]\nAt each frequency point, a settling time is allowed to pass before any measurement is made.\nThis allows the device under test to respond to the frequency change.\nThe actual settling time is the larger of the Settle Time and the Settle Cycles.\nChanges made to the number of Settle Cycles during a sweep take effect immediately.\nFor more information, see page 315 of the User Manual.')
            self.integrationTime = TimeFloatSetting('SITM 2,', 'integration time', 3.906E-3, 1E3, 's', 3.906E-3, 4, instrument, 'SITM? 1',
                                                    '[15.625ms..1ks]\nAt each frequency point, the inputs measure the signal at the source frequency.\nThe actual number of integration cycles is the larger of the Integration Time and the Integration Cycles.\nFor more information, see page 316 of the User Manual.')
            self.integrationCycles = IntegerSetting('SICY 2,', 'integration cycles', 1, 32767, 'cycles', instrument, 'SICY? 1',
                                                    '[1..32767]\nAt each frequency point, the inpust measure the signal at the source frequency.\nThe actual number of integration cycles is the larger of the Integration Time and the Integration Cycles.\nFor more information, see page 316 of the User Manual.')
#            self.progress = queryInteger('SSFR ?')

#        def measurementType(self,display):
#            self.measurementType = EnumSetting('MEAS %d' %display, 'measurement type', [(42,'spectrum 1'),(43, 'spectrum 2'),(44,'normalized variance 1'),(45,'normalized variance 2'),(46,'cross spectrum'),(47,'frequency response')],instrument,'MEAS?')


        def isFinished(self):
            x = self.instrument.displayStatus
            finished = bool(x & SR785.Display.SSA) and bool(x & SR785.Display.SSB)
            return finished

        def measurementProgress(self):
            return self.instrument.queryInteger('SSFR ?')

    def __init__(self, visaResource, instrument=None):
        VisaInstrument.__init__(self, visaResource)
#        InstrumentWithSettings.__init__(self)
        QObject.__init__(self, instrument)

        self.inputs = [SR785.Input(1, self), SR785.Input(2, self)]
        self.inputAutoOffset = OnOffSetting('IAOM', 'input auto-offset', self)
        self.sweptSine = SR785.SweptSine(self)
        self.source = SR785.Source(self)
        self.display = SR785.Display(self)
        self.fft = SR785.FFT(self)

    def readAll(self):
        self.source.readAll()
        self.display.readAll()
        self.sweptSine.readAll()
        self.fft.readAll()
        
        self.inputAutoOffset.enabled  # These are top level member and not a "SettingsCollection", so we have to handle them manually
        for inp in self.inputs:
            inp.readAll()

    def startMeasurement(self):
        self.commandString('STRT')

    def pauseMeasurement(self):
        self.commandString('PAUS')
#        self.paused = True
    def continueMeasurement(self):
#        if not self.paused:
#            raise Exception()
        self.commandString('CONT')

    def manualTrigger(self): # Perhaps move to Trigger class
        '''Send a manual trigger to the instrument'''
        self.commandString('TMAN')

    def frequencyOfBin(self, display, binNumber):
        return self.queryFloat('DBIN? %d, %d' %(display, binNumber))
        
    def configureScreenDump(self):
        self.commandInteger('POUT', 0) # Bitmap=0
        self.commandInteger('PDST', 3) # To GPIB=3
        self.commandInteger('PRTP', 4) # Type GIF=4 PCX_2BIT=2 PCX_8BIT=5
        
    def downloadScreen(self, screen=3):
        self.commandInteger('PSCR', screen)
        self.commandString('PRNT')
        data = self.readUnterminatedRawData(timeOut=1)
        return data

    def simulateKeyPress(self, keyCode):
        self.commandInteger('KEYP', keyCode)
        
    def rotateKnob(self, direction):
        self.commandInteger('KNOB', direction)

    @property
    def displayStatus(self):
        #r = self.queryString('DSPS? %d, %f, %s' % (125, 531.35, 'bala'))
        return self.queryInteger('DSPS?')



if __name__ == "__main__":

#    a = Test('BLA', 'BLUB', [(0, 'floating'), (1, 'grounded'), (2, 'spinning'), (3, 'crashing'), (4, 'exploding')])
#    a.code = 2
#    print a.code
#    print a.string

    #a = EnumSetting('BLA', 'BLUB', [(0, 'floating'), (1, 'grounded'), (2, 'spinning'), (3, 'crashing'), (4, 'exploding')])
#    print "A code:", a.code
#    print "A string:", a.string

    sr = SR785('GPIB1::10')
    sr.debug = True
    #sr.enableCaching()
    sr.disableCaching()
#    sr.inputs[0].autoRange.enabled = True
#    sr.inputs[0].coupling.code = sr.inputs[0].coupling.AC
#    sr.inputs[0].coupling.code = sr.inputs[0].coupling.ICP
#
#    sr.source.type.code = sr.source.type.SINE
#    sr.inputAutoOffset.disabled = False
#
#    print "Source:"
#    print "Type:", sr.source.type.code
#    #print type(sr.source.type.string)
#    #print "Type:", sr.source.type.string
##    print "
#
#
##    for i,input in enumerate(sr.inputs):
##        print "Input", i
##        print "Input coupling:", input.coupling.string
##        print "Input grounding:", input.grounding.code
##        print "Auto range:", input.autoRange.enabled
    #sr.display.measurementGroup.code = sr.display.measurementGroup.SWEPT_SINE
#    sr.display.selectMeasurement(2, 'spectrum')
#
#    sr.sweptSine.settleCycles.value = 2
#    print "settle cycles:", sr.sweptSine.settleCycles.value
#    sr.sweptSine.settleTime.value = 10E-3
#    print "settle time:", sr.sweptSine.settleTime.value
#    sr.sweptSine.integrationTime.value = 10E-3
#    sr.sweptSine.integrationCycles.value = 2
#
#    sr.sweptSine.numberOfPoints.value = 10
#    sr.sweptSine.sweepType.code = sr.sweptSine.sweepType.LINEAR
#    sr.sweptSine.startFrequency.value = 15.
#    print "swept sine start frequency:", sr.sweptSine.startFrequency.value
#    sr.sweptSine.stopFrequency.value = 20E3
#    sr.sweptSine.repeat.code = sr.sweptSine.repeat.SINGLE_SHOT
#
#    sr.startMeasurement()
#    sr.manualTrigger()
#
#    print "Display status:", sr.displayStatus
#    finishedA = False
#    finishedB = False
#    while True:
#        status = sr.displayStatus
#        if status & sr.display.SSA:
#            finishedA = True
#        if status & sr.display.SSB:
#            finishedB = True
#        if finishedA and finishedB:
#            break
#        else:
#            print "Still measuring:", finishedA, finishedB, status

#    display0 = sr.display.retrieveData(0)
#    display1 = sr.display.retrieveData(1)

 #   import matplotlib.pyplot as mpl
  #  mpl.subplot(2,1,1)
   # mpl.plot(display0, '-')
    #mpl.subplot(2,1,2)
    #mpl.plot(display1, '-')
    #mpl.show()

    #response = sr.queryString('ACTD 0; DUMP;')
    #print "We have data:", response

    #sr.commandString('PCIC 0')
    #print "PCIC?", sr.queryString('PCIC?')
    import time 
    sr.configureScreenDump()
    t1 = time.time()
    data = sr.downloadScreen(sr.SCREEN_MENU)
    t2 = time.time()
    #print "Length:", len(data)
    print "Time:", t2-t1
    print "Length:", len(data)
    #from hexdump import hexdump
    #print hexdump(data)
    fileName = 'MENU_.gif'
    with open(fileName, 'wb') as f:
        f.write(data)

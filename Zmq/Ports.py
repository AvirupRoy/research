# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 16:54:17 2015

@author: wisp10
"""

# The idea was that PubSubs will be odd-numbers, and RequestReplies will be PubSub+1 (i.e. even).
# This is no longer true, need to go through and sort the numbers

class PubSub:
    LockinThermometerRuOx2005 = 5540 # Bad
    LockinThermometerBox      = 5541
    Housekeeping              = 5553
    AdrTemperature            = 5555
    MagnetControl             = 5557
    LegacyDaqStreaming        = 5563
    TektronixScope            = 5565
    LockinThermometerAdr      = 5567
    TesBiasDAQ                = 5569
    FieldCoilBiasDAQ          = 5571
    
class RequestReply:
    LockinThermometerRuOx2005 = 5538
    LockinThermometerBox      = 5542
    MagnetControl             = 5558
    OpenSquid                 = 5560
    AdrPidControl             = 5562
    LegacyDaqStreaming        = 5564
    TektronixScope            = 5566
    LockinThermometerAdr      = 5568
    IvSweepsDaq               = 5570
    IvCurveDaq                = 5572 
    DaqAiSpectrum             = 5574
    MultitoneLockin           = 5576
    TransferFunction          = 5590
    SineSweepDaq              = 5598
    PiezoControl              = 5600
    PulseCollector            = 5602


LockInSockets = {'BusThermometer':(PubSub.LockinThermometerAdr,RequestReply.LockinThermometerAdr),
                 'RuOx2005Thermometer':(PubSub.LockinThermometerRuOx2005, RequestReply.LockinThermometerRuOx2005),
                 'BoxThermometer':(PubSub.LockinThermometerBox, RequestReply.LockinThermometerBox)}

def LockInPubSub(thermometerId):
    return LockInSockets[thermometerId][0]

def LockInRequestReply(thermometerId):
    return LockInSockets[thermometerId][1]

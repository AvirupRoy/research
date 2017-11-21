# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 16:54:17 2015

@author: wisp10
"""

class PubSub:
    AdrTemperature = 5555
    MagnetControl = 5557
    LegacyDaqStreaming = 5563
    TektronixScope = 5565
    LockinThermometerAdr = 5567
    LockinThermometerRuOx2005 = 5540
    LockinThermometerBox = 5541
    
class RequestReply:
    MagnetControl = 5558
    OpenSquid = 5560
    AdrPidControl = 5562
    LegacyDaqStreaming = 5564
    TektronixScope = 5566
    PiezoControl = 5568
    IvSweepsDaq = 5570
    IvCurveDaq = 5572
    TransferFunction = 5590
    SineSweepDaq = 5597
    DaqAiSpectrum = 5574

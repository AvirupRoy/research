# -*- coding: utf-8 -*-
"""
Created on Thu Dec 03 09:38:14 2015

@author: wisp10
"""

from AdrTemperatureControlPid import PidControlRemote

remote = PidControlRemote('test')

print "Ramp rate:", remote.rampRate()
print "Ramp target:", remote.rampTarget()
print "Ramp enabled:", remote.rampEnabled()

print "Setting ramp rate:", remote.setRampRate(1.0)
print "Setting target:", remote.setRampTarget(0.5732)
print "Enabling ramp:", remote.enableRamp(True)

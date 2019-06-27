# -*- coding: utf-8 -*-
"""
Created on Wed Sep 13 12:52:26 2017

@author: calorim
"""
from __future__ import print_function, division
import PyDaqMx as daq

system = daq.System()
print('Available devices:', system.findDevices())
dev = daq.Device('Dev1')
print('Available DO ports:', dev.findDoPorts())
print('Available DO lines:', dev.findDoLines())

channel = daq.DoChannel('Dev1/port0/line0')
task = daq.DoTask('DemoDO')
task.addChannel(channel)
data = [True, False,True]
task.writeData(data, autoStart = True)


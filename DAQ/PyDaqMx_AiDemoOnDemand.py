# -*- coding: utf-8 -*-
"""
Created on Wed Sep 13 12:52:26 2017

@author: calorim
"""
from __future__ import print_function, division
import PyDaqMx as daq
import time

system = daq.System()
print('Available devices:', system.findDevices())
dev = daq.Device('Dev1')
print('Available AI channels:', dev.findAiChannels())

channel = daq.AiChannel('Dev1/ai0', -10, +10)
task = daq.AiTask('DemoAI')
task.addChannel(channel)

nSamples = 1000
Vs = []
print('Selected channel:', channel)
print('Collecting %d on-demand samples...' % nSamples)

tStart = time.time()
for i in range(nSamples):
    V = task.readData(samplesPerChannel=1)
    Vs.append(V)
tStop = time.time()

print('Elapsed time:', tStop-tStart, 'Sample rate:', nSamples/(tStop-tStart))

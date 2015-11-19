# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 15:49:00 2015
Test the speed of sample-on-demand operations

@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

import PyDaqMx as daq

def makeAoTask(deviceName,aoChannel):
	#dev = daq.Device(deviceName)
	ao = daq.AoChannel('%s/%s' % (deviceName,aoChannel), -10, 10)
	otask = daq.AoTask('Output')
	otask.addChannel(ao)
	otask.start()   # No timing necessary for on-demand tasks
	return otask

def makeAiTask(deviceName,aiChannel):
	#dev = daq.Device(deviceName)
	ai = daq.AiChannel('%s/%s' % (deviceName,aiChannel), -10, 10)
	itask = daq.AiTask('Input')
	itask.addChannel(ai)
	itask.start()   # No timing necessary for on-demand tasks
	return itask


if __name__ == '__main__':
	sys = daq.System()
	print "DAQmx version:", sys.version
	devs = sys.findDevices()
	print "Number of devices:", len(devs)
	print "Devices: ", devs


	randomize = True
	deviceName = 'USB6002'
	aoChannel = 'ao1'
	aiChannel = 'ai2'

#	ai = daq.AiChannel('%s/%s' % (deviceName,aiChannel), -10, 10)
#	itask = daq.AiTask('Input')
#	itask.addChannel(ai)
#	itask.start()   # No timing necessary for on-demand tasks

	n= 10000
	import timeit
	t1 = timeit.Timer('otask.writeData([0])', setup = "from __main__ import makeAoTask; otask = makeAoTask('USB6002', 'ao1')")
	t2 = timeit.Timer('itask.readData(50)', setup = "from __main__ import makeAiTask; itask = makeAiTask('USB6002', 'ai1')")
	t3 = timeit.Timer('otask.writeData([0]); itask.readData(1)', setup = "from __main__ import makeAiTask, makeAoTask; itask = makeAiTask('USB6002', 'ai1');  otask = makeAoTask('USB6002', 'ao1')")
	print "AO:",t1.timeit(n)
	print "AI:",t2.timeit(n)
	print "AO+AI:",t3.timeit(n)




#	for i in range(100):
#		otask.writeData([Vcommand])
#		time.sleep(1)
#		#t = time.clock()
#		Vai = itask.readData(1000)[0]
#		#t2 = time.clock()
#		#print "T =", t2-t

	#otask.writeData([0])
	#otask.stop()

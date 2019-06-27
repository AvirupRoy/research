# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 15:49:00 2015
Some example code to test PyDaqMx: generates and digitizes analog output trough AO channel, trying to exhaust the code space.
Useful for check of linearity (differential or integral), offset, gain

@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""


if __name__ == '__main__':
    import PyDaqMx as daq
    import time
    sys = daq.System()
    print "DAQmx version:", sys.version
    devs = sys.findDevices()
    print "Number of devices:", len(devs)
    print "Devices: ", devs
    from Visa.Agilent34401A import Agilent34401A

    dmm = Agilent34401A('GPIB0::23')

    randomize = True
    deviceName = 'USB6002'
    aoChannel = 'ao0'
    aiChannel = 'ai0'
    dev = daq.Device(deviceName)
    print "SimultaneousSampling: ", dev.simultaneousSamplingSupported()
    print "AI channels:", dev.findAiChannels()
    ao = daq.AoChannel('%s/%s' % (deviceName,aoChannel), -10, 10)
    otask = daq.AoTask('Output')
    otask.addChannel(ao)
    otask.start()   # No timing necessary for on-demand tasks

    ai = daq.AiChannel('%s/%s' % (deviceName,aiChannel), -10, 10)
    itask = daq.AiTask('Input')
    itask.addChannel(ai)
    itask.start()   # No timing necessary for on-demand tasks

    fileName = '%s_%s_%s_%s.dat' % (deviceName, aoChannel, aiChannel, time.strftime('%Y%m%d-%H%M%S'))
    import numpy as np

    Vs= np.linspace(-10, 10, 65536)

    if randomize:
        np.random.shuffle(Vs)
    with open(fileName, 'w') as of:
        print "Output file:", fileName
        of.write("# TestDAQmx.py\n")
        of.write("# DMM:%s\n" % dmm.visaId())
        of.write('#'+'\t'.join(['Vcommand', 'Vdmm', 'Vai', 'VaiStd'])+'\n')
        #import matplotlib.pyplot as mpl
        for i,Vcommand in enumerate(Vs):
            otask.writeData([Vcommand])
            time.sleep(1)
            #t = time.clock()
            Vai = itask.readData(1000)[0]
            #t2 = time.clock()
            #print "T =", t2-t
            #mpl.figure()
            #mpl.plot(Vai)
            #mpl.show()
            #print Vai
            VaiMean = np.mean(Vai)
            VaiStd = np.std(Vai)
            Vdmm = dmm.voltageDc()
            print "Sample %5d: Vcommmand = %.7fV\tVdmm = %.7f\tVai = %.7f+-%.7fV" % (i, Vcommand, Vdmm, VaiMean, VaiStd)
            of.write('\t'.join(('%.7f' % x) for x in [Vcommand, Vdmm, VaiMean, VaiStd])+'\n')

    otask.writeData([0])
    otask.stop()

#    ai1 = AiChannel('Dev3/ai1', -10,+10)
#    ai2 = AiChannel('Dev3/ai2', -10,+10)
#    itask = AiTask('Input')
#    itask.addChannel(ai1)
#    itask.addChannel(ai2)
#    itask.configureTiming(timing)
#    itask.start()
#    for i in range(10):
#        #print itask.samplesAvailable()
#        samples = itask.readData()
#        print samples.shape
#        if itask.isDone() or otask.isDone():
#            break
#    itask.stop()
#    otask.stop()

# -*- coding: utf-8 -*-
"""
A simple forwarder to aggregate data from other publishers into a single publisher

Created on Tue Nov 21 14:34:29 2017
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

import zmq
from Ports import PubSub
import logging

try:
    context = zmq.Context()
    frontEnd = context.socket(zmq.SUB)
    frontEnd.setsockopt(zmq.SUBSCRIBE, '')
    ports = [PubSub.AdrTemperature, PubSub.LockinThermometerAdr, 
             PubSub.LockinThermometerBox, PubSub.LockinThermometerRuOx2005, PubSub.LockInThermometerUWGe5,
             PubSub.MagnetControl,
             PubSub.TesBiasDAQ, PubSub.FieldCoilBiasDAQ,PubSub.DiodeThermometers
             ]
    for port in ports:
        frontEnd.connect('tcp://127.0.0.1:%d' % port)
        
    outputPort = PubSub.Housekeeping
    backEnd = context.socket(zmq.PUB)
    backEnd.bind('tcp://*:%d' % outputPort)
    
    zmq.device(zmq.FORWARDER, frontEnd, backEnd)
except Exception as e:
    logging.error(e, exc_info=True)
finally:
    frontEnd.close()
    backEnd.close()
    context.term()

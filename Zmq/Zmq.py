# -*- coding: utf-8 -*-
"""
A set of easy-to-use classes for communications via ZeroMQ using the publish-subscribe and request-reply patterns.
Created on Thu Jun 25 10:52:53 2015
@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

import zmq
from PyQt4.QtCore import QThread, pyqtSignal, QObject
import logging
import time

LabviewEpoch = 2082844800.
LabviewThreshold = LabviewEpoch+time.time()-1 # Messages with a timestamp of this value or greater have a Labview timestamp

logger = logging.getLogger(__name__)

class ZmqException(Exception):
    pass

class ZmqBlockingRequestor():
    '''Send a ZeroMQ request, along with meta-information origin and timestamp. Will not return until a reply is actually received, so use with care!'''
    def __init__(self, port, host='127.0.0.1', origin='', timeOut=0.5):
        self.origin = origin
        self.host = host
        self.context = zmq.Context()
        self.requestSocket = self.context.socket(zmq.REQ)
        address = 'tcp://%s:%d' % (host, port)
        self.requestSocket.connect(address)
        self.requestSocket.setsockopt(zmq.RCVTIMEO,int(timeOut*1000))
        logging.info('ZmqBlockingRequestor connecting to %s', address)

    def request(self, query):
        '''Send a request through ZeroMQ, a time-stamp is automatically added.'''
        message = {'origin':self.origin, 'timeStamp': time.time(), 'request': query}
        logging.info('ZmqBlockingRequest sending request: %s', message)
        self.requestSocket.send_json(message)
        reply = self.requestSocket.recv_json()
        return reply

class ZmqRequest(QObject):
    sent = pyqtSignal(float)
    completed = pyqtSignal(int)
    def __init__(self, query):
        self.query = query

    def reply(self):
        return self._reply

    def provideReply(self, reply):
        self._reply = reply
        self.completed.emit()

import Queue

class ZmqAsyncRequestor(QThread):
    def __init__(self, host, port, origin='', parent = None):
        QThread.__init__(self, parent)
        self.host = host
        self.context = zmq.Context()
        self.requestSocket = self.context.socket(zmq.REQ)
        address = 'tcp://%s:%d' % (host, port)
        self.requestSocket.connect(address)
        logging.info('ZmqAsyncRequestor connecting to ', address)
        self.queue = Queue()

    def postRequest(self, request):
        self.queue.put(request)

    def stop(self):
        self.stopRequested = True

    def run(self):
        self.stopRequested = False
        while not self.stopRequested:
            request = self.queue.get()
            message = {'origin':self.origin, 'timeStamp': time.time(), 'request':request}
            self.requestSocket.send_json(message)
            request.sent.emit(time.time())
            reply = self.requestSocket.recv_json()
            request.provideReply(reply)

class ZmqRequestReplyThread(QThread):
    '''A QThread waiting for, and responding to ZMQ requests. By default, a requestReceived signal is emitted for each request, and the reply sent is "OK". Subclass and override processRequest as needed.'''
    requestReceived = pyqtSignal(str, float, str)   # Signal that a request has been received, parameters are origin, timestamp and request string

    def __init__(self, port, parent = None):
        super(ZmqRequestReplyThread,self).__init__(parent)
        self._port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.setsockopt(zmq.RCVTIMEO,500)
        address = 'tcp://*:%d' % self._port
        self.socket.bind(address)
        logger.info('ZmqRequestReplyThread listening at %s', address)
        self.replyPending = False

    def stop(self):
        self._stopRequested = True

    def processRequest(self, origin, timeStamp, request):
        '''Default request handler. By default the requestReceived signal is triggered. Override in subclasses as needed. Use send reply to send the reply (mandatory!).'''
        self.requestReceived.emit(origin, timeStamp, str(request))

    def sendReply(self, reply):
        '''Call here to send a reply. Note that you have to send a reply to each request!'''
        logger.info('ZmqRequestReply sending reply %s', reply)
        self.socket.send_json(reply)
        self.replyPending = False

    def run(self):
        self._stopRequested = False
        while not self._stopRequested:
            try:
                message = self.socket.recv_json()
            except:
                continue
            logger.log(logging.INFO, 'ZmqRequestReplyThread received request: %s' % message)
            try:
                timeStamp = message['timeStamp']
                origin = message['origin']
                request = message['request']
            except Exception,e:
                print "Exception:", e
                self.sendReply('Illegal request')
                continue

            self.replyPending = True
            self.processRequest(origin, timeStamp, request)
            i = 0
            while self.replyPending:
                self.msleep(10)
                i += 1
                if i > 100:
                    self.sendReply('No response')
                    break

class ZmqPublisher(QObject):
    '''Publish information via ZeroMQ publisher-subscriber architecture. A timestamp is automatically included.'''
    def __init__(self, origin, port, parent = None):
        QObject.__init__(self, parent)
        self.origin = origin
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        address = 'tcp://*:%d' % int(port)
        self.socket.bind(address)
        logger.info('ZmqPublisher % s at %s' % (origin, address))

    def publish(self, item, data):
        '''Publish a piece of data through the ZeroMQ socket, together with origin and timestamp information.'''
        message = { 'origin': self.origin,'timeStamp':time.time(), 'item': item, 'data': data }
        logger.log(logging.INFO, 'ZmqPublisher sending message: %s' % message)
        self.socket.send_json(message)

class ZmqSubscriber(QThread):
    floatReceived = pyqtSignal(str, str, float, float) # origin, item, value, timestamp
    intReceived = pyqtSignal(str, str, int, float)
    boolReceived = pyqtSignal(str, str, bool, float)
    stringReceived = pyqtSignal(str, str, str, float)

    def __init__(self, port, host='tcp://127.0.0.1', filterString = '', parent=None):
        QThread.__init__(self, parent)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect('%s:%d' % (host,port))
        self.socket.setsockopt(zmq.SUBSCRIBE,filterString)
        self.maxAge = 2.

    @property
    def maxAge(self):
        return self._maxAge

    @maxAge.setter
    def maxAge(self, seconds):
        self._maxAge = max(0, float(seconds))

    def stop(self):
        self.stopRequested = True

    def isExpired(self, tReceived, timeStamp):
        if timeStamp > LabviewThreshold: # Labview time-stamp
            timeStamp -= LabviewEpoch
        age = tReceived-timeStamp
        if self.maxAge > 0 and age > self._maxAge:
            logger.debug('Message too old (%f s)',age)
            return True
        else:
            return False

    def processMessage(self, message, tReceived):
        timeStamp = message['timeStamp']
        if self.isExpired(tReceived, timeStamp):
            return
        origin = message['origin']
        item = message['item']
        value = message['data']
        t = type(value)
        if t == float:
            self.floatReceived.emit(origin, item, value, timeStamp)
        elif t == int:
            self.intReceived.emit(origin, item, value, timeStamp)
        elif t == bool:
            self.boolReceived.emit(origin, item, value, timeStamp)
        elif t == str:
            self.stringReceived.emit(origin, item, value, timeStamp)
        else:
            logger.info('Unrecognized data type:%s', t)

    def run(self):
        logger.debug('Thread starting')
        self.stopRequested = False
        flags = zmq.NOBLOCK
        while not self.stopRequested:
            try:
                message = self.socket.recv_json(flags)
                tReceived = time.time()
            except:
                self.msleep(100)
                continue

            logger.debug('Message received at %s:%s', tReceived, message)
            self.processMessage(message, tReceived)
        logger.debug('Thread ending')

def testZmqSubscriber():
    port = 5556
    app = QCoreApplication([])
    sub = ZmqSubscriber(port)

    def received(origin, item, value, timeStamp):
        age = time.time()-timeStamp
        print "Received from", origin, "item=", item, "value=",value, "time stamp=", timeStamp, "age=", age, "s"

    sub.floatReceived.connect(received)

    timer = QTimer()
    timer.singleShot(1000, sub.start)
    timer.singleShot(20000, sub.stop)
    app.exec_()

def testZmqRequestReply():
    app = QCoreApplication([])
    server = ZmqRequestReplyThread(port = 7000)

    def received(origin, timeStamp, request):
        age = time.time()-timeStamp
        print "Received from", origin, "time stamp=", timeStamp, "age=", age, "s", "Request=", request

    server.requestReceived.connect(received)

    timer = QTimer()
    timer.singleShot(1000, server.start)
    timer.singleShot(20000, server.stop)
    app.exec_()


if __name__ == '__main__':
    from PyQt4.QtCore import QCoreApplication, QTimer
    logging.basicConfig(level=logging.DEBUG)
    testZmqRequestReply()
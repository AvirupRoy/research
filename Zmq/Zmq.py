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
import traceback

LabviewEpoch = 2082844800.
LabviewThreshold = LabviewEpoch+time.time()-1 # Messages with a timestamp of this value or greater have a Labview timestamp

logger = logging.getLogger(__name__)

class ZmqException(Exception):
    pass

class ZmqRequest(QObject):
    sent = pyqtSignal(float)
    '''Indicates that the request has been sent. The float parameters is a Unix
    time-stamp.'''
    
    completed = pyqtSignal(bool)
    '''Signal emitted when a reply has been received. 
    The boolean parameter indicates whether the request was successful (True) or not (False).'''
    
    def __init__(self, target = None, command = None, parameters = None, parent = None):
        super(ZmqRequest, self).__init__(parent)
        self.target = target
        self.command = command
        self.parameters = parameters
        self.reply = None
        
    def toDictionary(self):
        d = {'target': self.target, 'command': self.command, 'parameters': self.parameters}
        return d
        
    def __str__(self):
        return "Request:" + str(self.toDictionary())+ " Reply:"+str(self.reply)
        
    @classmethod        
    def fromDictionary(cls, d):
        target = d['target']
        command = d['command']
        parameters = d['parameters']
        return cls(target, command, parameters)

    def reply(self):
        return self._reply

    def provideReply(self, reply):
        '''Provide a reply to the request.'''
        self._reply = reply
        self.completed.emit(reply.ok())
        
class ZmqReply():
    class Status:
        OK = 1
        DENIED = 2
        ERROR = 3
        NETWORK_ERROR = 4
        
    def __init__(self, status = Status.OK, data=None, errorMessage = None):
        self.status = status
        self.data = data
        self.errorMessage = errorMessage
        
    @classmethod
    def Deny(cls, message=''):
        return cls(status=ZmqReply.Status.DENIED, errorMessage=message)
        
    @classmethod
    def Error(cls, message=''):
        return cls(status=ZmqReply.Status.ERROR, errorMessage=message)

    @classmethod
    def NetworkError(cls, message=''):
        return cls(status=ZmqReply.Status.NETWORK_ERROR, errorMessage=message)

    @classmethod        
    def fromDictionary(cls, d):
        status = d['status']
        data = d['data']
        errorMessage = d['errorMessage']
        return cls(status, data, errorMessage)
        
    def toDictionary(self):
        d = {'status': self.status, 'data': self.data, 'errorMessage': self.errorMessage}
        return d
        
    def ok(self):
        return self.status == ZmqReply.Status.OK
    
    def denied(self):
        return self.status == ZmqReply.Status.DENIED
        
    def failed(self):
        return not self.ok()
        
    def __str__(self):
        return str(self.toDictionary())

#class ZmqBlockingRequestor():
#    '''Send a ZeroMQ request, along with meta-information origin and timestamp. Will not return until a reply is actually received or time-out occurs, so use with care!'''
#    def __init__(self, port, host='127.0.0.1', origin='', timeOut=5.0):
#        self.origin = origin
#        self.host = host
#        self.context = zmq.Context()
#        self.requestSocket = self.context.socket(zmq.REQ)
#        self.address = 'tcp://%s:%d' % (host, port)
#        self.requestSocket.connect(self.address)
#        self.requestSocket.setsockopt(zmq.RCVTIMEO,int(timeOut*1000))
#        logger.info('ZmqBlockingRequestor connecting to %s', self.address)
#
#    def sendRequest(self, request):
#        '''Send a request through ZeroMQ, a time-stamp is automatically added. Request needs to be an object provinding two functions:
#        1) toDictionary() and
#        2) provideReply()
#        '''
#        message = {'origin':self.origin, 'timeStamp': time.time(), 'request': request.toDictionary()}
#        logger.info('ZmqBlockingRequest sending request to %s: %s', self.address, message)
#        try:
#            self.requestSocket.send_json(message)
#            r = self.requestSocket.recv_json()
#            reply = ZmqReply.fromDictionary(r)
#            logger.info('ZmqBlockingRequest reply received from %s:%s', self.address, str(reply))
#        except Exception,e:
#            reply = ZmqReply.NetworkError('ZMQ network error: %s' % str(e))
#            logger.debug('ZmqBlockingRequest encountered network error awaiting reply from %s: %s' , self.address, str(e))
#        request.provideReply(reply)
#        return reply

class ZmqBlockingRequestor():
    '''Send a ZeroMQ request, along with meta-information origin and timestamp. Will not return until a reply is actually received or time-out occurs, so use with care!'''
    def __init__(self, port, host='127.0.0.1', origin='', timeOut=5.0):
        self.origin = origin
        self.host = host
        self.address = 'tcp://%s:%d' % (host, port)
        self.poll = zmq.Poller()
        self._connect()
        self.timeOut = int(1000.*timeOut)
        
    def _connect(self):
        self.context = zmq.Context()
        self.requestSocket = self.context.socket(zmq.REQ)
        self.requestSocket.connect(self.address)
        self.poll.register(self.requestSocket, zmq.POLLIN)
        #self.requestSocket.setsockopt(zmq.RCVTIMEO,int(timeOut*1000))
        logger.info('ZmqBlockingRequestor connecting to %s', self.address)
        
    def _disconnect(self):
        self.requestSocket.setsockopt(zmq.LINGER, 0)
        self.requestSocket.close()
        self.poll.unregister(self.requestSocket)
        logger.info('ZmqBlockingRequestor disconnected from %s', self.address)

    def sendRequest(self, request, maxRetries = 3):
        '''Send a request through ZeroMQ, a time-stamp is automatically added. Request needs to be an object provinding two functions:
        1) toDictionary() and
        2) provideReply()
        '''
        message = {'origin':self.origin, 'timeStamp': time.time(), 'request': request.toDictionary()}
        logger.debug('ZmqBlockingRequest sending request to %s: %s', self.address, message)
        retries = 0
        while True:
            self.requestSocket.send_json(message)
            socks = dict(self.poll.poll(self.timeOut))
            if socks.get(self.requestSocket) == zmq.POLLIN:
                r = self.requestSocket.recv_json()
                reply = ZmqReply.fromDictionary(r)
                logger.debug('ZmqBlockingRequest reply received from %s:%s', self.address, str(reply))
                return reply
            else:
                logger.warn('ZmqBlockingRequest did not receive a reply. Retrying.')
                self._disconnect()
                if retries >= maxRetries:
                     reply = ZmqReply.NetworkError('Request abandoned')
                     request.provideReply(reply)
                     return reply
                self._connect()
            retries += 1

import Queue

class ZmqAsyncRequestor(QThread):
    '''A class to queue and send ZMQ requests and receive the replies asynchronously.'''
    def __init__(self, host, port, origin='', parent = None):
        QThread.__init__(self, parent)
        self.host = host
        self.context = zmq.Context()
        self.requestSocket = self.context.socket(zmq.REQ)
        address = 'tcp://%s:%d' % (host, port)
        self.requestSocket.connect(address)
        logger.info('ZmqAsyncRequestor connecting to ', address)
        self.queue = Queue()

    def sendRequest(self, request):
        self.queue.put(request)

    def stop(self):
        self.stopRequested = True

    def run(self):
        self.stopRequested = False
        while not self.stopRequested:
            request = self.queue.get()
            message = {'origin':self.origin, 'timeStamp': time.time(), 'request':request.toDictionary()}
            try:
                self.requestSocket.send_json(message)
                request.sent.emit(time.time())
                reply = ZmqReply.fromDictionary(self.requestSocket.recv_json())
            except Exception,e:
                reply = ZmqReply.NetworkError(str(e))
            request.provideReply(reply)

class ZmqRequestReplyThread(QThread):
    '''A QThread waiting for, and responding to ZMQ requests. 
    By default, a requestReceived signal is emitted for each request, and an "OK" reply is sent.
    Subclass and override processRequest to do your own processing and provide customized replies.
    Call start() to run the request-reply thread.'''
    
    def __init__(self, port, parent = None):
        super(ZmqRequestReplyThread,self).__init__(parent)
        self._port = port
        self.context = zmq.Context()
        address = 'tcp://*:%d' % self._port
        self.address = address
        self.injectRandomFailure = False
        self._bindToSocket()
        self.allowRequests()
        self.denyReason = ''
        self.failed = False
        
    def _bindToSocket(self):
        self.socket = self.context.socket(zmq.REP)
        self.socket.setsockopt(zmq.RCVTIMEO,500)
        self.socket.bind(self.address)
        logger.info('ZmqRequestReplyThread at %s bound to socket.', self.address)
        
    def _disconnect(self):
        logger.info('ZmqRequestReplyThread at %s disconnecting.', self.address)
        self.socket.close()

    def stop(self):
        self._stopRequested = True

    def allowRequests(self, allow=True):
        '''Allow incoming requests.'''
        self.requestsAllowed = allow

    def denyRequests(self, reason=''):
        '''Deny all incomming requests.'''
        self.allowRequests(False)
        self.denyReason = reason

    def processRequest(self, origin, timeStamp, request):
        '''Default request handler. By default the requestReceived signal is triggered.
        Override in subclasses as needed to provide a customized reply.'''
        return ZmqReply()

    def sendReply(self, reply):
        '''Call here to send a reply. Note that you have to send a reply to each request!'''
        if self.injectRandomFailure:
            import numpy as np
            if np.random.rand() < 0.1:
                logger.warn('ZmqRequestReplyThread %s: injected random failure. Not sending reply!' % self.address)
                return
        self.socket.send_json(reply.toDictionary())
        logger.debug('ZmqRequestReply %s sent reply %s.', self.address, str(reply))

    def run(self):
        self._stopRequested = False
        logger.info('ZmqRequestReplyThread %s: Waiting for requests.', self.address)
        while not self._stopRequested:
            try:
                message = self.socket.recv_json()
            except zmq.ZMQError, e:
                if e.errno == zmq.constants.EAGAIN: # Just a timeout (errno 11)
                    continue
                else:  # zmq.constants.EFSM (156384763): Operation cannot be accomplished in the current state
                    logger.warn('ZmqRequestReplyThread %s: Server socket has failed and will try to restart (exception %s)', self.address, str(e))
                    self._disconnect()
                    try:
                        self._bindToSocket()
                    except zmq.ZMQError, e:
                        logger.warn('ZmqRequestReplyThread %s: Unable to restart server socket  (exception %s). Thread will terminate.', self.address, str(e))
                        break
                    continue
            logger.debug('ZmqRequestReplyThread %s received request: %s', self.address, message)
            try:
                timeStamp = message['timeStamp']
                origin = message['origin']
                request = ZmqRequest.fromDictionary(message['request'])
            except Exception,e:
                logger.warn('Exception parsing request: %s', str(e))
                self.sendReply(ZmqReply.Error('Malformed request'))
                continue

            if not self.requestsAllowed:
                logger.warn('ZmqRequestReplyThread denied request')
                rep = ZmqReply.Deny(self.denyReason)
                self.sendReply(rep)
                continue
            
            reply = self.processRequest(origin, timeStamp, request)
            logger.debug("Reply ready: %s", reply)
            if reply is None:
                reply = ZmqReply.Error('No response available')
            try:
                self.sendReply(reply)
            except Exception as e:
                logger.warn('Exception during send: %s', e)
                logger.warn('Backtrace: %s', traceback.format_exc())
                break
            # End of while loop
            
        self._disconnect()
        logger.info('ZmqRequestReplyThread %s: Thread ended.' % self.address)
        
class RequestReplyRemote(QObject):
    '''Subclass this to provide convenient RequestReply client interfaces.'''
    error = pyqtSignal(str)
    def __init__(self, origin, port, host='tcp://127.0.0.1', blocking=True, parent = None):
        super(RequestReplyRemote, self).__init__(parent)
        self.retries = 3
        if blocking:
            self.requestor = ZmqBlockingRequestor(port=port, origin=origin)
        else:
            raise Exception('Only blocking requestors supported.')
            pass
        
    def _queryValue(self, target):
        request = ZmqRequest(target=target, command='query')
        reply = self.requestor.sendRequest(request)
        if reply is not None:
            if reply.ok():
                return reply.data
            else:
                self.error.emit(reply.errorMessage)
        logger.warn('No luck processing "query" request.')
        return None

    def _isEnabled(self, target):
        request = ZmqRequest(target=target, command='enabled')
        reply = self.requestor.sendRequest(request)
        if reply is not None:
            if reply.ok():
                return reply.data
            else:
                self.error.emit(reply.errorMessage)
        logger.warn('No luck processing "enabled" request.')
        return None

    def _setValue(self, target, value):
        request = ZmqRequest(target=target, command='set', parameters=value)
        reply = self.requestor.sendRequest(request)
        if reply is not None:
            if reply.ok():
                return reply.data
            else:
                self.error.emit(reply.errorMessage)
        logger.warn('No luck processing "set" request.')
        return None
        
    def _clickButton(self, target):
        request = ZmqRequest(target=target, command='click', parameters=None)
        reply = self.requestor.sendRequest(request)
        if reply is not None:
            if reply.ok():
                return reply.data
            else:
                self.error.emit(reply.errorMessage)
        logger.warn('No luck processing "click" request.')
        return None
    
    def _execute(self, target, parameters=None):
        request = ZmqRequest(target=target, command='execute', parameters=parameters)
        reply = self.requestor.sendRequest(request)
        if reply is not None:
            if reply.ok():
                return reply.data
            else:
                self.error.emit(reply.errorMessage)
        logger.warn('No luck processing "execute" request.')
        return None
        

from PyQt4.QtGui import QWidget, QDoubleSpinBox, QAbstractSpinBox, QAbstractButton, QLineEdit, QComboBox
from LabWidgets.Indicators import LedIndicator
class RequestReplyThreadWithBindings(ZmqRequestReplyThread):
    '''A ZmqRequestReplyThread that provides convenient functions to bind directly
    to QWidgets or variables, or functions with a standardized command set.'''
    SupportedWidgets = [QAbstractSpinBox, QAbstractButton, QLineEdit, QComboBox, LedIndicator]
    
    def __init__(self, port, name = '', parent = None):
        super(RequestReplyThreadWithBindings, self).__init__(port, parent)
        self._widgetsDict = {}
        self._propertiesDict = {}
        self._propertyLimits = {}
        self._functionsDict = {}
        self.name = name
        
    def checkDuplicateName(self, name):
        duplicate = self._widgetsDict.has_key(name) or self._propertiesDict.has_key(name) or self._functionsDict.has_key(name)
        if duplicate:
            raise Exception('Property with identical name is already bound')

    def bindToProperty(self, name, prop, minimum=None, maximum=None):
        self.checkDuplicateName(name)
        self._propertiesDict[name] = prop
        if type(prop) in [int, float]:
            self._propertyLimits[name] = (minimum, maximum)
            
    def bindToFunction(self, name, function):
        if not callable(function):
            raise Exception('Unable to bind "%s": not a function.' % name)
        self.checkDuplicateName(name)
        self._functionsDict[name] = function
        
    def bindToWidget(self, name, widget):
        self.checkDuplicateName(name)
        for supportedWidget in self.SupportedWidgets:
            if isinstance(widget, supportedWidget):
                self._widgetsDict[name] = widget
                return
        raise Exception('Unable to bind %s: unsupported widget type %s' % (name, widget))
    
    def processRequest(self, origin, timeStamp, request):
        #print "Processing request in RequestReplyThreadWithBindings:", request
        target = request.target
        cmd = request.command
        parameters = request.parameters
        if len(target) == 0:
            if cmd == 'list widgets':
                return ZmqReply(data=self._widgetsDict.keys())
            elif cmd == 'list properties':
                return ZmqReply(data=self._propertiesDict.keys())
            elif cmd == 'list functions':
                return ZmqReply(data=self._functionsDict.keys())
            elif cmd == 'name':
                return ZmqReply(self.name)
            else:
                return ZmqReply.Error('Unsupported command')
        elif self._widgetsDict.has_key(target):
            return self._processWidgetCommand(self._widgetsDict[target], cmd, parameters)
        elif self._propertiesDict.has_key(target):
            return self._processPropertiesCommand(self._propertiesDict[target], cmd, parameters)
        elif self._functionsDict.has_key(target):
            return self._processFunctionsCommand(self._functionsDict[target], cmd, parameters)
        else:
            return ZmqReply.Deny('Unrecognized target: %s' % target)
            
    def _processPropertiesCommand(self, prop, cmd, parameters):
        if cmd in ['read', 'query', 'get']:
            return ZmqReply(data=prop)
        elif cmd in ['write', 'set']:
            try:
                prop = parameters
                return ZmqReply()
            except:
                return ZmqReply.Error('Illegal parameter')
        elif cmd in ['type']:
            return ZmqReply(data=type(prop))
        else:
            return ZmqReply.Error('Unsupported command for property')
            
    def _processFunctionsCommand(self, function, cmd, parameters):
        print "Received functions command:", cmd, function, parameters
        if cmd in ['execute']:
            print "Executing"
            try:
                if parameters is not None:
                    result = function(parameters)
                else:
                    result = function()
                print "Result is:", result
                return ZmqReply(data=result)
            except Exception,e:
                return ZmqReply.Error('Function call generated exception:%s' % e)
        elif cmd in ['doc']:
            return ZmqReply(data=function.__doc__)

    def _processWidgetCommand(self, widget, cmd, parameters):
        read = cmd in ['?', 'query', 'get', 'read']
        write = cmd in ['set', 'write']

        if cmd in ['enabled']:
            return ZmqReply(data = widget.isEnabled())
            
        if isinstance(widget, QAbstractSpinBox):
            if read:
                return ZmqReply(data=widget.value())
            elif write:
                try:
                    if isinstance(widget, QDoubleSpinBox):
                        value = float(parameters)
                    else:
                        value = int(parameters)
                except:
                    return ZmqReply.Error('Illegal value for parameter')
                widget.setValue(value)
                return ZmqReply(data = widget.value())
            elif cmd in ['min']:
                return ZmqReply(data=widget.minimum())
            elif cmd in ['max']:
                return ZmqReply(data=widget.maximum())
            elif cmd in ['range']:
                return ZmqReply(data=(widget.minimum(), widget.maximum()))
        elif isinstance(widget, QAbstractButton):
            if read:
                return ZmqReply(data = widget.isChecked())
            if write:
                try:
                    checked = bool(parameters)
                except:
                    return ZmqReply('Illegal value for parameter')
                widget.setChecked(checked)
                return ZmqReply(data = checked)
            if cmd in ['click']:
                widget.click()
                return ZmqReply(data = widget.isChecked())
        elif isinstance(widget, QComboBox):
            if read:
                return ZmqReply(data=str(widget.currentText()))
            elif write:
                print('Write combo with parameters=', parameters)
                i = widget.findText(parameters)
                print('Find text:', i)
                if i < 0:
                    return ZmqReply.Error('Invalid selection')
                print('Set index:', i)
                widget.setCurrentIndex(i)
                print('Done set index:', i)
                return ZmqReply(data=str(widget.currentText()))
#            elif cmd in ['list']:
#                return widget.
        elif isinstance(widget, QLineEdit):
            if read:
                return ZmqReply(data = str(widget.text()))
            elif write:
                try:
                    widget.setText(parameters)
                    return ZmqReply(data = None)
                except:
                    return ZmqReply('Illegal value for parameter')
        elif isinstance(widget, LedIndicator):
            if read:
                return ZmqReply(data = widget.isOn())
        return ZmqReply.Deny('Illegal command')

class ZmqPublisher(QObject):
    '''Publish information via ZeroMQ publisher-subscriber architecture. A timestamp is automatically included.
    Data are also cached so they can be conveniently accessed later using the query() function, e.g. to also support request/reply access.'''
    def __init__(self, origin, port, parent = None):
        QObject.__init__(self, parent)
        self.origin = origin
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.address = 'tcp://*:%d' % int(port)
        self.socket.bind(self.address)
        logger.info('ZmqPublisher %s at %s', self.origin, self.address)
        self.cache = {}
        
    def __del__(self):
        logger.info('ZmqPublisher %s at %s signing off.', self.origin, self.address)
        self.socket.close()
        
    def query(self, item):
        try:
            return self.cache[item]
        except:
            return None

    def publish(self, item, data, arrays = {}):
        '''Publish a piece of data through the ZeroMQ socket, together with origin and timestamp information.'''
        self.cache[item] = data
        arrayInfo = []
        for arrayName in arrays.keys():
            a = arrays[arrayName]
            arrayInfo.append({'name': arrayName, 'dtype': str(a.dtype), 'shape': a.shape})
            
        message = { 'origin': self.origin,'timeStamp':time.time(), 'item': item, 'data': data, 'arrayInfo': arrayInfo}
        logger.debug('ZmqPublisher sending message: %s', message)
        flags = 0
        if len(arrayInfo):
            flags |= zmq.SNDMORE
        self.socket.send_json(message, flags)
        for arrayName in arrays.keys():
            self.socket.send(np.ascontiguousarray(arrays[arrayName]))
            
    def publishDict(self, item, data):
        '''Publish a dictionary through the ZeroMQ socket.'''
        self.cache[item] = data
        message = { 'origin': self.origin,'timeStamp':time.time(), 'item': item, 'data': data}
        logger.debug('ZmqPublisher sending message: %s', message)
        flags = 0
        self.socket.send_json(message, flags)

import numpy as np

class ZmqSubscriber(QThread):
    '''A QThread that subscribes to a single ZMQ publisher.
    Call start() to run the thread.'''
    floatReceived = pyqtSignal(str, str, float, float) # origin, item, value, timestamp
    intReceived = pyqtSignal(str, str, int, float)
    boolReceived = pyqtSignal(str, str, bool, float)
    stringReceived = pyqtSignal(str, str, str, float)
    arrayReceived = pyqtSignal(str, np.ndarray)
    dictReceived = pyqtSignal(str, str, object)

    def __init__(self, port, host='tcp://127.0.0.1', filterString = '', parent=None):
        QThread.__init__(self, parent)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect('%s:%d' % (host,port))
        self.socket.setsockopt(zmq.SUBSCRIBE,filterString)
        self.maxAge = 2.

    @property
    def maxAge(self):
        '''Maximum age of received messages in seconds. Set to zero if age checking is not desired'''
        return self._maxAge

    @maxAge.setter
    def maxAge(self, seconds):
        self._maxAge = max(0, float(seconds))

    def stop(self):
        '''Ask the thread to stop.'''
        self.stopRequested = True

    def _isExpired(self, tReceived, timeStamp):
        if timeStamp > LabviewThreshold: # Labview time-stamp
            timeStamp -= LabviewEpoch
        age = tReceived-timeStamp
        if self.maxAge > 0 and age > self._maxAge:
            logger.debug('Message too old (%f s)',age)
            return True
        else:
            return False

    def _processMessage(self, message, tReceived):
        '''Process the received message for simple data types.
        Emits the corresponding signals float, int, bool or stringReceived().
        Override as needed to handle more complex data.'''
        timeStamp = message['timeStamp']
        if self._isExpired(tReceived, timeStamp):
            return
        origin = message['origin']
        item = message['item']
        value = message['data']
        t = type(value)
        if t in [float, int]:
            self.floatReceived.emit(origin, item, value, timeStamp)
        elif t == int:
            self.intReceived.emit(origin, item, value, timeStamp)
        elif t == bool:
            self.boolReceived.emit(origin, item, value, timeStamp)
        elif t == str:
            self.stringReceived.emit(origin, item, value, timeStamp)
        elif t == dict:
            self.dictReceived.emit(origin, item, value)
        else:
            logger.warn('Unrecognized data type:%s', t)
        if message.has_key('arrayInfo'):
            arrayInfos = message['arrayInfo']
            for arrayInfo in arrayInfos:
                name = arrayInfo['name']
                dtype = arrayInfo['dtype']
                shape = arrayInfo['shape']
                arrayBuffer = self.socket.recv()
                A = np.frombuffer(arrayBuffer, dtype=dtype)
                A.reshape(shape)
                self.arrayReceived.emit(name, A)

    def run(self):
        '''Don't call this directly, instead call start().'''
        logger.debug('Zmq subscriber thread starting')
        self.stopRequested = False
        flags = zmq.NOBLOCK
        while not self.stopRequested:
            try:
                message = self.socket.recv_json(flags)
                tReceived = time.time()
            except:
                self.msleep(100)
                continue

            #logger.debug('Message received at %s:%s', tReceived, message)
            self._processMessage(message, tReceived)
        logger.debug('Zmq subscriber thread ending')
        self.socket.close()

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

#    def received(origin, timeStamp, request):
#        age = time.time()-timeStamp
#        print "Received from", origin, "time stamp=", timeStamp, "age=", age, "s", "Request=", request

#    server.requestReceived.connect(received)

    timer = QTimer()
    timer.singleShot(1000, server.start)
    timer.singleShot(20000, server.stop)
    app.exec_()


if __name__ == '__main__':
    from PyQt4.QtCore import QCoreApplication, QTimer
    logging.basicConfig(level=logging.DEBUG)
    #testZmqRequestReply()
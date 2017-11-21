# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 13:55:39 2015

@author: wisp10
"""

from PyQt4.QtGui import QWidget

from LabWidgets.Utilities import compileUi
compileUi('ZmqRequestReplyServerUi')
import ZmqRequestReplyServerUi

from Zmq import ZmqRequestReplyThread, ZmqReply
import logging
logging.basicConfig(level=logging.DEBUG)

class ServerThread(ZmqRequestReplyThread):
    def linkToControls(self, spinBox):
        self._spinBox = spinBox
    
    def processRequest(self, origin, timeStamp, request):
        print "Processing request..."
        if request.target == 'value':
            if request.command == 'set':
                print "request.parameters", request.parameters
                self._spinBox.setValue(request.parameters)
                return ZmqReply()
            elif request.command == 'query':
                return ZmqReply(data=self._spinBox.value())
        return ZmqReply.Deny('Command not understood')
    
class ServerWidget(ZmqRequestReplyServerUi.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(ServerWidget, self).__init__(parent)
        self.setupUi(self)
        self.startPb.clicked.connect(self.startServerThread)
        
    def startServerThread(self):
        self.serverThread = ServerThread(self.portSb.value())
        self.serverThread.linkToControls(self.valueSb)
        self.serverThread.allowRequests(self.allowRequestsCb.isChecked())
        self.allowRequestsCb.toggled.connect(self.serverThread.allowRequests)
        self.stopPb.clicked.connect(self.serverThread.stop)
        self.serverThread.finished.connect(self.serverFinished)
        self.serverThread.start()
        self.stopPb.setEnabled(True)
        self.startPb.setEnabled(False)
        
    def serverFinished(self):
        self.serverThread.deleteLater()
        self.serverThread = None
        self.startPb.setEnabled(True)
        self.stopPb.setEnabled(False)
        
        
import ZmqRequestReplyClientUi
from Zmq import ZmqBlockingRequestor, ZmqRequest
    
class ClientWidget(ZmqRequestReplyClientUi.Ui_Form, QWidget):
    def __init__(self, parent = None):
        super(ClientWidget, self).__init__(parent)
        self.setupUi(self)
        self.valueSb.valueChanged.connect(self.changeValue)
        self.askPb.clicked.connect(self.askValue)

    def askValue(self):
        requestor = ZmqBlockingRequestor(port=self.portSb.value(), origin='ClientWidget')
        request = ZmqRequest(target='value', command='query')
        reply = requestor.sendRequest(request)
        print "Reply:", reply
        if reply.ok():
            self.valueSb.setValue(reply.data)
            self.valueSb.setStyleSheet('')
        else:
            self.valueSb.setStyleSheet('background-color:yellow;')
            self.messagesTextEdit.append(reply.errorMessage)
        
    def changeValue(self, value):
        requestor = ZmqBlockingRequestor(port=self.portSb.value(), origin='ClientWidget')
        request = ZmqRequest(target='value', command='set', parameters=value)
        reply = requestor.sendRequest(request)
        print "Reply:", reply
        if reply.ok():
            self.valueSb.setStyleSheet('')
        else:
            self.valueSb.setStyleSheet('background-color:yellow;')
            self.messagesTextEdit.append(reply.errorMessage)
 
if __name__ == '__main__':
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    sw = ServerWidget()
    sw.show()
    
    cw = ClientWidget()
    cw.show()
    app.exec_()

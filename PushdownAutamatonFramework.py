'''
Created on Jan 10, 2018

@author: cvamb
'''

from PyQt4.QtCore import pyqtSignal,QThread,QObject
import logging
logging.basicConfig(level=logging.DEBUG)




class State(QObject):
    measurementReadyState = pyqtSignal(float,float,float)
    errorState = pyqtSignal(str)
    def __init__(self,stateInput=None,lia=None):
        QObject.__init__(self)
        self._logger = logging.getLogger(str(self))
        self.currInput=stateInput
        self.lia=lia
        self.FS=0
        
    def run(self,stateInput=None,stack=None,lockinParams=None):
        self.currInput=stateInput
        return self.currInput
        
'''

This is the core of the PDA.
To configure the PDA, it needs the following
    stateMap : statename to state Object map
    transitionMap : (currStateName,CurrInput,TopOfStack) -> (nextStateName,nextStackTop)    use 'e' if you want the top of the stack to be popped
    startingStateName
    startingInput
    startingStackInput
    
    sharedMemoryMap : A map that is passed around to all states, can be used for interstate communication

'''
class PushdownAutamaton(QThread):
    
    measurementReady = pyqtSignal(float, float, float)
    error = pyqtSignal(str)
    
    
    def __init__(self,stateMap,transitionMap,startingState,startingInput,startingStackInput,sharedMemoryMap):
        QThread.__init__(self)
        self.currState=startingState
        self.stack=[]
        self.stack.append(startingStackInput)
        self.stateMap = stateMap
        self.transitionMap = transitionMap
        self.stateInput=startingInput
        self.sharedMemoryMap=sharedMemoryMap
        self.finished = False

    def run(self):
        
        while self.finished == False:
            currState = self.stateMap[self.currState]
            nextStateInput = currState.run(self.stateInput,self.stack,self.sharedMemoryMap)
            (nextState,nextStackInput) = self.transitionMap[(self.currState,self.stateInput,self.stack.pop())]
            self.currState=nextState
            if nextStackInput != 'e':
                self.stack.append(nextStackInput)
            self.stateInput=nextStateInput
            if self.currState == 'finished':
                self.finished=True
    
    def stop(self):
        self.finished=True

    def sendMeasurement(self,f,X,Y):
        print("Measurement Ready" , f, X,Y)
        self.measurementReady.emit(f,X,Y)

    def sendErrorReport(self,errorStr):
        self.error.emit(errorStr)

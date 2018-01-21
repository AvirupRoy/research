'''
Created on Jan 10, 2018

@author: cvamb
'''
from PushdownAutamatonFramework import PushdownAutamaton,State
import time
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG)
from Visa.SR830_New import SR830


EXPAND_ON = 'Expand On'
EXPAND_OFF = 'Expand Off'

stack_Data = 'Data'
stack_Overload='Overload'
stack_Sensitivity='Sens'
stack_Offset = 'Offset'
stack_Expand='Expand'
stack_RNE='RNE'
stack_RWE='RWE'

transitionMap = {}
transitionMap[('RWE_INIT',EXPAND_ON,'Data')] = ('RWE_DATA','Data')
transitionMap[('RWE_INIT',EXPAND_OFF,'Data')] = ('RWE_DATA','Data')
transitionMap[('RWE_INIT',EXPAND_ON,'RNE')] = ('RWE_DATA','RNE')
transitionMap[('RWE_DATA',EXPAND_ON,'Data')] = ('RWE_DATA','Data')
transitionMap[('RWE_DATA',EXPAND_ON,'Overload')] = ('OVERLOAD','e')

transitionMap[('RWE_DATA',EXPAND_ON,'Sens')] = ('SENSITIVITY','e')
transitionMap[('OVERLOAD',EXPAND_ON,'Data')] = ('RWE_DATA','Data')
transitionMap[('OVERLOAD',EXPAND_ON,'RNE')] = ('RWE_DATA','RNE')
transitionMap[('SENSITIVITY',EXPAND_ON,'Data')] = ('RWE_DATA','Data')
transitionMap[('SENSITIVITY',EXPAND_ON,'RNE')] = ('RWE_DATA','RNE')
transitionMap[('RWE_DATA',EXPAND_ON,'Offset')] = ('OFFSET','e')
transitionMap[('OFFSET',EXPAND_ON,'Data')] = ('RWE_DATA','Data')
transitionMap[('OFFSET',EXPAND_ON,'RNE')] = ('RWE_DATA','RNE')
transitionMap[('RWE_DATA',EXPAND_ON,'Expand')] = ('EXPAND','e')
transitionMap[('EXPAND',EXPAND_ON,'Data')] = ('RWE_DATA','Data')
transitionMap[('EXPAND',EXPAND_ON,'RNE')] = ('RWE_DATA','RNE')


# Transition to RNE
transitionMap[('RWE_DATA',EXPAND_ON,'RNE')] = ('RNE_INIT','e')

transitionMap[('RNE_INIT',EXPAND_OFF,'Data')] = ('RNE_DATA','Data')
transitionMap[('RNE_INIT',EXPAND_ON,'Data')] = ('RNE_DATA','Data')
transitionMap[('RNE_INIT',EXPAND_OFF,'RWE')] = ('RNE_DATA','RWE')
transitionMap[('RNE_DATA',EXPAND_OFF,'Data')] = ('RNE_DATA','Data')
transitionMap[('RNE_DATA',EXPAND_OFF,'Overload')] = ('OVERLOAD','e')
transitionMap[('RNE_DATA',EXPAND_OFF,'Sens')] = ('SENSITIVITY','e')
transitionMap[('OVERLOAD',EXPAND_OFF,'Data')] = ('RNE_DATA','Data')
transitionMap[('OVERLOAD',EXPAND_OFF,'RWE')] = ('RNE_DATA','RWE')
transitionMap[('SENSITIVITY',EXPAND_OFF,'Data')] = ('RNE_DATA','Data')
transitionMap[('SENSITIVITY',EXPAND_OFF,'RWE')] = ('RNE_DATA','RWE')
# Transition to RWE
transitionMap[('RNE_DATA',EXPAND_OFF,'RWE')] = ('RWE_INIT','e')




lockinParamsFullScaleKey='FS'
lockinParamsStatusKey='Status'

lockinParamsOffsetXKey='OffsetX'
lockinParamsOffsetYKey='OffsetY'

lockinParamsExpandXKey='ExpandX'
lockinParamsExpandYKey='ExpandY'

lockinParamsFilterTimeConstantKey='filterTc'
lockinParamsLastChangeTimeKey='lastChangeTime'


lockInParams={}
lockInParams[lockinParamsFullScaleKey]=None
lockInParams[lockinParamsStatusKey] = None

lockInParams[lockinParamsOffsetXKey]=None
lockInParams[lockinParamsOffsetYKey] = None
lockInParams[lockinParamsExpandXKey]=None
lockInParams[lockinParamsExpandYKey] = None

lockInParams[lockinParamsFilterTimeConstantKey]=None
lockInParams[lockinParamsLastChangeTimeKey] = None

numberOfTimeConstantsToSleep =20
timeInSecsToSleepAfterData=1


class RWEInit(State):
    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering state RWEInit')
        #Initialize all lockin Params if they are not available
        if lockinParams[lockinParamsFullScaleKey] is None:
            lockinParams[lockinParamsFullScaleKey]=self.lia.sensitivity.value
        if lockinParams[lockinParamsStatusKey] is None:
            lockinParams[lockinParamsStatusKey]=self.lia.checkStatus()
            
        offsetPercentX, expandX = self.lia.offsetExpand('X')
        offsetPercentY, expandY = self.lia.offsetExpand('Y')
        
        if lockinParams[lockinParamsOffsetXKey] is None:
            lockinParams[lockinParamsOffsetXKey]=offsetPercentX
        if lockinParams[lockinParamsOffsetYKey] is None:
            lockinParams[lockinParamsOffsetYKey]=offsetPercentY            
        if lockinParams[lockinParamsExpandXKey] is None:
            lockinParams[lockinParamsExpandXKey]=expandX
        if lockinParams[lockinParamsExpandYKey] is None:
            lockinParams[lockinParamsExpandYKey]=expandY            
        
        
        if lockinParams[lockinParamsFilterTimeConstantKey] is None:
            lockinParams[lockinParamsFilterTimeConstantKey]=self.lia.filterTc.value
        
        
        self._logger.debug('Current Filter Time constant is %f',lockinParams[lockinParamsFilterTimeConstantKey])
        if lockinParams[lockinParamsLastChangeTimeKey] is None:
            lockinParams[lockinParamsLastChangeTimeKey]=0                    
        
        self._logger.debug('Exiting state RWEInit')
        return EXPAND_ON

class RWEData(State):
    
    def __init__(self,stateInput=None,lia=None):
        State.__init__(self, stateInput, lia)
        self.transitionToRNE=False

    
    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering state RWEData')
        
        if self.transitionToRNE:
            return EXPAND_OFF
        
        
        
        self.FS = lockinParams[lockinParamsFullScaleKey]
        status = self.lia.checkStatus()
        if status.anyOverload:
            stack.append(stack_Overload)
            return stateInput

        # No Overload, check if sensitivity is fine

        offsetPercentX, expandX = lockinParams[lockinParamsOffsetXKey],lockinParams[lockinParamsExpandXKey]
        offsetPercentY, expandY = lockinParams[lockinParamsOffsetYKey],lockinParams[lockinParamsExpandYKey]

        X,Y,f = self.lia.snapSignal()     
        
        signalX = offsetPercentX*self.FS*1E-2 + X
        signalY = offsetPercentY*self.FS*1E-2 + Y        
        
        
        #adjSensX = signalX > 0.8*self.FS or signalX < 0.2*self.FS        
        #adjSensY = signalY > 0.8*self.FS or signalY < 0.2*self.FS        


        adjSensUp = signalX > 0.8*self.FS or signalY > 0.8*self.FS        
        adjSensDown =  signalX < 0.2*self.FS and signalY < 0.2*self.FS


        if adjSensUp or adjSensDown:
            print("Sens Up : ",adjSensUp)
            print("Sens Down : ",adjSensDown)            
            stack.append(stack_Sensitivity)
            return stateInput


        
        # Sensitivity is good, check if offset is good, Delta value greater than 10 % of Full scale => can change offset
        
        adjOffX = np.abs(X) > 0.05*self.FS         
        adjOffY = np.abs(Y) > 0.05*self.FS        

        if adjOffX or adjOffY:
            print ("Adj Off X",adjOffX," X ",np.abs(X)," FS ",self.FS) 
            print ("Adj Off Y",adjOffY," Y ",np.abs(Y)," FS ",self.FS)            
            stack.append(stack_Offset)
            return stateInput
        
        # Offset is fine too, need to check if we are at optimum expand
        # Effective fullscale for expand = 10 is 0.1 * FS, so if X < 0.08 * FS and expand is 1, then case to change expand
        # or if 
        
        adjExpX = expandX <10 and expandX*X < 0.1*self.FS
        adjExpY = expandY <10 and expandY*Y < 0.1*self.FS        
        
        if adjExpX or adjExpY:
            print("Adj Exp X",adjExpX," X ",np.abs(expandX*X)," FS ",self.FS) 
            print("Adj Exp Y",adjExpY," Y ",np.abs(expandY*Y)," FS ",self.FS)                         
            stack.append(stack_Expand)
            return stateInput
        
        self._logger.info('X,Y=%f,%f', signalX,signalY)
        
        self.measurementReadyState.emit(f,signalX,signalY)
        
        time.sleep(timeInSecsToSleepAfterData)
        self._logger.debug('Exiting state RWEData')
        return stateInput
        
class HandleOverload(State):
    def __init__(self,stateInput=None,lia=None):
        State.__init__(self,stateInput,lia)        
        self.rangeChangedTime=0
    
    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering state HandleOverload')
        status = self.lia.checkStatus()
        
        currFilterTc = lockinParams[lockinParamsFilterTimeConstantKey]
        waitTime = numberOfTimeConstantsToSleep*currFilterTc
        t = time.time()
        rangeChangeAge = t - lockinParams[lockinParamsLastChangeTimeKey]   
        if status.anyOverload:
            # All code for this method is inside this block
            if status.outputOverload:
                if stateInput == EXPAND_ON:                
                    # Need to check if expand is ON
                    offsetPercentX, expandX = lockinParams[lockinParamsOffsetXKey],lockinParams[lockinParamsExpandXKey]
        
                    offsetPercentY, expandY = lockinParams[lockinParamsOffsetYKey],lockinParams[lockinParamsExpandYKey]
                    
                    if expandX != 1 and rangeChangeAge > waitTime:
                        expandX /= 10
                        self.lia.setOffsetExpand('X', offsetPercentX, expandX)
                        lockinParams[lockinParamsExpandXKey]=expandX
                        lockinParams[lockinParamsLastChangeTimeKey]=time.time()
                        time.sleep(waitTime)
                    if expandY != 1 and rangeChangeAge > waitTime:
                        expandY /= 10
                        self.lia.setOffsetExpand('X', offsetPercentY, expandY)
                        lockinParams[lockinParamsExpandYKey]=expandY
                        lockinParams[lockinParamsLastChangeTimeKey]=time.time()
                        time.sleep(waitTime)
                        
                        
                    rangeChangeAge = time.time() - lockinParams[lockinParamsLastChangeTimeKey]   
                    status = self.lia.checkStatus()
                    # Tried changing the expands, if the output is still overloaded, change the sensitivity
                    if status.outputOverload and rangeChangeAge > waitTime:
                        self.minSensCode=0;
                        currentCode = self.lia.sensitivity.code
                        self.lia.sensitivity.code=currentCode + 1
                        lockinParams[lockinParamsFullScaleKey] = self.lia.sensitivity.value
                        lockinParams[lockinParamsLastChangeTimeKey] = time.time()
                        time.sleep(waitTime)
                elif stateInput == EXPAND_OFF:
                    if rangeChangeAge > waitTime:
                        self.minSensCode=0;
                        currentCode = self.lia.sensitivity.code
                        self.lia.sensitivity.code=currentCode + 1
                        lockinParams[lockinParamsFullScaleKey] = self.lia.sensitivity.value
                        lockinParams[lockinParamsLastChangeTimeKey] = time.time()
                        time.sleep(waitTime)
            # Now, if it is not an output overload, it could be a filter Overload
        if status.filterOverload:
            # For filter overload, there is no difference between EXPAND on and off
            if rangeChangeAge > waitTime:
                currentFilterCode = self.lia.filterTc.code
                # Increase the filter time constant                
                self.lia.filterTc.code=currentFilterCode + 1
                lockinParams[lockinParamsLastChangeTimeKey] = time.time()
                lockinParams[lockinParamsFilterTimeConstantKey] = self.lia.filterTc.value
                waitTime = numberOfTimeConstantsToSleep*lockinParams[lockinParamsFilterTimeConstantKey]
                self._logger.debug('Filter Overload Corrected : Sleeping for %f seconds' %waitTime)
                time.sleep(waitTime)
        if status.inputOverload:
            # If it is an input overload or dynamic reserve overload, Fix is to decrease sensitivity or increase reserve
            if rangeChangeAge > waitTime:
                self.minSensCode=0;
                currentCode = self.lia.sensitivity.code
                if currentCode > self.minSensCode:
                    self.lia.sensitivity.code=currentCode - 1
                else:
                    self.lia.sensitivity.code=self.minSensCode
                    
                lockinParams[lockinParamsFullScaleKey] = self.lia.sensitivity.value
                lockinParams[lockinParamsLastChangeTimeKey] = time.time()
                time.sleep(waitTime)

        self._logger.debug('Exiting state HandleOverload')
        return stateInput

class AdjustSensitivity(State):
    def __init__(self,stateInput=None,lia=None):
        State.__init__(self,stateInput,lia)        
        self.rangeChangedTime=0
        
    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering state AdjustSensitivity')
        self.FS = lockinParams[lockinParamsFullScaleKey]
        currFilterTc = lockinParams[lockinParamsFilterTimeConstantKey]
        waitTime = numberOfTimeConstantsToSleep*currFilterTc
        t = time.time()
        
        rangeChangeAge = t - lockinParams[lockinParamsLastChangeTimeKey]

#        if rangeChangeAge > waitTime:
        ''' Need to change this to get the value of minimum sensitivity code from the UI'''
        
        self.minSensCode=0;
        currentCode = self.lia.sensitivity.code
        offsetPercentX = lockinParams[lockinParamsOffsetXKey]
    
        offsetPercentY = lockinParams[lockinParamsOffsetYKey]

        X,Y,f = self.lia.snapSignal()     
        
        signalX = offsetPercentX*self.FS*1E-2 + X
        signalY = offsetPercentY*self.FS*1E-2 + Y        

        adjSensUp = signalX > 0.8*self.FS or signalY > 0.8*self.FS        
        adjSensDown =  signalX < 0.2*self.FS and signalY < 0.2*self.FS        

        # Both of the if statements below can be true at the same time, but priority is to increase sensitivity when needed 
        if adjSensUp:
            self.lia.sensitivity.code=currentCode + 1
            lockinParams[lockinParamsLastChangeTimeKey] = time.time()
            time.sleep(waitTime)                
        elif adjSensDown and currentCode > self.minSensCode:
            self.lia.sensitivity.code=currentCode - 1
            lockinParams[lockinParamsLastChangeTimeKey] = time.time()
            time.sleep(waitTime)
                
        lockinParams[lockinParamsFullScaleKey] = self.lia.sensitivity.value


        self._logger.debug('Exiting state AdjustSensitivity')
        return stateInput

class AdjustOffset(State):
    def __init__(self,stateInput=None,lia=None):
        State.__init__(self,stateInput,lia)        
        self.rangeChangedTime=0

    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering state AdjustOffset')
        self.FS = lockinParams[lockinParamsFullScaleKey]
        currFilterTc = lockinParams[lockinParamsFilterTimeConstantKey]
        waitTime = numberOfTimeConstantsToSleep*currFilterTc
        t = time.time()
        rangeChangeAge = t - lockinParams[lockinParamsLastChangeTimeKey]
        X,Y,f = self.lia.snapSignal()     
        offsetPercentX, expandX = lockinParams[lockinParamsOffsetXKey],lockinParams[lockinParamsExpandXKey]
        
        offsetPercentY, expandY = lockinParams[lockinParamsOffsetYKey],lockinParams[lockinParamsExpandYKey]

        print("Off X ",offsetPercentX,"Off Y ",offsetPercentY)
        adjOffX = np.abs(X) > 0.05*self.FS         
        adjOffY = np.abs(Y) > 0.05*self.FS         
        if adjOffX and rangeChangeAge > waitTime:
            signalX = offsetPercentX*self.FS/100 + X
            offsetPercentX = float(int(1E4*signalX/self.FS))/100
            self.lia.setOffsetExpand('X', offsetPercentX, expandX)
            lockinParams[lockinParamsOffsetXKey] = offsetPercentX
            lockinParams[lockinParamsLastChangeTimeKey] = time.time()
            time.sleep(waitTime)
        if adjOffY and rangeChangeAge > waitTime:                
            signalY = offsetPercentY*self.FS/100 + Y        
            offsetPercentY= float(int(1E4*signalY/self.FS))/100
            self.lia.setOffsetExpand('Y', offsetPercentY, expandY)
            lockinParams[lockinParamsLastChangeTimeKey] = time.time()
            time.sleep(waitTime)
        self._logger.debug('Exiting state AdjustOffset')
        return stateInput  
            
class AdjustExpand(State):
    def __init__(self,stateInput=None,lia=None):
        State.__init__(self,stateInput,lia)        
        self.rangeChangedTime=0

    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering state AdjustExpand')

        self.FS = lockinParams[lockinParamsFullScaleKey]

        currFilterTc = lockinParams[lockinParamsFilterTimeConstantKey]
        
        waitTime = numberOfTimeConstantsToSleep*currFilterTc

        t = time.time()

        rangeChangeAge = t - lockinParams[lockinParamsLastChangeTimeKey]
        
        X,Y,f = self.lia.snapSignal()     
        
        offsetPercentX, expandX = lockinParams[lockinParamsOffsetXKey],lockinParams[lockinParamsExpandXKey]
        
        if expandX*X < 0.1*self.FS and rangeChangeAge > waitTime and expandX < 100:
            self.lia.setOffsetExpand('X', offsetPercentX, expandX*10)
            lockinParams[lockinParamsExpandXKey] = expandX*10
            lockinParams[lockinParamsLastChangeTimeKey] = time.time()
            time.sleep(waitTime)    
        offsetPercentY, expandY = lockinParams[lockinParamsOffsetYKey],lockinParams[lockinParamsExpandYKey]
        
        if expandY*Y < 0.1*self.FS and rangeChangeAge > waitTime and expandY < 100:
            self.lia.setOffsetExpand('Y', offsetPercentY, expandY*10)
            lockinParams[lockinParamsExpandYKey] = expandY*10            
            lockinParams[lockinParamsLastChangeTimeKey] = time.time()
            time.sleep(waitTime)
        self._logger.debug('Exiting state AdjustExpand')
        return stateInput  
        

class RNEInit(State):
    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering state RNEInit')
        self.lia.disableOffsetExpand()
        
        if lockinParams[lockinParamsFullScaleKey] is None:
            lockinParams[lockinParamsFullScaleKey]=self.lia.sensitivity.value
        
        lockinParams[lockinParamsStatusKey]=self.lia.checkStatus()
            
        offsetPercentX, expandX = self.lia.offsetExpand('X')
        offsetPercentY, expandY = self.lia.offsetExpand('Y')
        
        
        lockinParams[lockinParamsOffsetXKey]=0
        lockinParams[lockinParamsOffsetYKey]=0            
        lockinParams[lockinParamsExpandXKey]=1
        lockinParams[lockinParamsExpandYKey]=1            
        
        
        if lockinParams[lockinParamsFilterTimeConstantKey] is None:
            lockinParams[lockinParamsFilterTimeConstantKey]=self.lia.filterTc.value
        
        if lockinParams[lockinParamsLastChangeTimeKey] is None:
            lockinParams[lockinParamsLastChangeTimeKey]=0                    
        
        self._logger.debug('Exiting state RNEInit')
        return EXPAND_OFF


class RNEData(State):
    
    def __init__(self,stateInput=None,lia=None):
        State.__init__(self, stateInput, lia)
        self.transitionToRWE=False
    
    def run(self,stateInput,stack,lockinParams):
        self._logger.debug('Entering RNEData')

        if self.transitionToRWE:
            return EXPAND_ON
              
        self.FS = lockinParams[lockinParamsFullScaleKey]
        
        status = self.lia.checkStatus()
        if status.anyOverload:
            stack.append(stack_Overload)
            return stateInput

        X,Y,f = self.lia.snapSignal()

        #adjSensX = X > 0.8*self.FS or X < 0.2*self.FS        
        #adjSensY = Y > 0.8*self.FS or Y < 0.2*self.FS        

        adjSensUp = X > 0.8*self.FS or Y > 0.8*self.FS        
        adjSensDown =  X < 0.2*self.FS and Y < 0.2*self.FS


        if adjSensUp or adjSensDown:
            stack.append(stack_Sensitivity)
            return stateInput
        
        self._logger.info('X,Y=%f,%f', X,Y)
        
        self.measurementReadyState.emit(f,X,Y)
        time.sleep(timeInSecsToSleepAfterData)
        self._logger.debug('Exiting RNEData')

        
        return stateInput
    
class LockinThermometerAutomaton(PushdownAutamaton):
    def __init__(self,lia,initState,updateMethod=None):
        self.lia=lia
        rweInit = RWEInit('RWE_INIT',self.lia);
        self.rweData = RWEData('RWE_DATA',self.lia);
        rneInit = RNEInit('RNE_INIT',self.lia);
        self.rneData = RNEData('RNE_DATA',self.lia);
    
        adjSens = AdjustSensitivity('SENSITIVITY',self.lia);
        adjOff = AdjustOffset('OFFSET',self.lia);
        adjExp = AdjustExpand('EXPAND',self.lia);
        handleOverload = HandleOverload('OVERLOAD',self.lia);
                
        stateMap={}
        stateMap['RWE_INIT']=rweInit
        stateMap['RWE_DATA']=self.rweData
        stateMap['RNE_INIT']=rneInit
        stateMap['RNE_DATA']=self.rneData
        stateMap['SENSITIVITY']=adjSens
        stateMap['OFFSET']=adjOff
        stateMap['EXPAND']=adjExp
        stateMap['OVERLOAD']=handleOverload
        
        if initState=='RWE':
            initStateName='RWE_INIT'
            initInput=EXPAND_ON
        else:
            initStateName='RNE_INIT'
            initInput=EXPAND_OFF
        
        PushdownAutamaton.__init__(self,stateMap,transitionMap,initStateName,initInput,stack_Data,sharedMemoryMap=lockInParams)
        self.rweData.measurementReadyState.connect(self.sendMeasurement);
        self.rweData.errorState.connect(self.sendErrorReport)
        self.rneData.measurementReadyState.connect(self.sendMeasurement);
        self.rneData.errorState.connect(self.sendErrorReport)

        
#        self.PDA = PushdownAutamaton(stateMap,transitionMap,'RWE_INIT',EXPAND_ON,stack_Data,sharedMemoryMap=lockInParams)
        self.measurementReady.connect(updateMethod)
    
    def transitionToRWE(self):
        if self.stateInput == EXPAND_OFF:
            ''' Currently in RNE loop'''
            self.stack.append('RWE')
            #self.rweData.transitionToRNE=True
        
    def transitionToRNE(self):
        if self.stateInput == EXPAND_ON:
            ''' Currently in RWE Loop'''
            #self.rneData.transitionToRWE=True
            self.stack.append('RNE')


def updateMethod():
    print("Connect")

    
if __name__ == '__main__':
    stateMap = {}
    
    lia = SR830('GPIB0::8::INSTR')
    #lia = SR830('ASRL10')
    lia.checkStatus()
    print(lia.overload)    
    
    rweInit = RWEInit('RWE_INIT',lia);
    rweData = RWEData('RWE_DATA',lia);
    rneInit = RNEInit('RNE_INIT',lia);
    rneData = RNEData('RNE_DATA',lia);
    
    adjSens = AdjustSensitivity('SENSITIVITY',lia);
    adjOff = AdjustOffset('OFFSET',lia);
    adjExp = AdjustExpand('EXPAND',lia);
    handleOverload = HandleOverload('OVERLOAD',lia);
    
    
    stateMap={}
    stateMap['RWE_INIT']=rweInit
    stateMap['RWE_DATA']=rweData
    stateMap['RNE_INIT']=rneInit
    stateMap['RNE_DATA']=rneData
    stateMap['SENSITIVITY']=adjSens
    stateMap['OFFSET']=adjOff
    stateMap['EXPAND']=adjExp
    stateMap['OVERLOAD']=handleOverload
    #updateMethod=lambda : print("Connect")
    PDA = LockinThermometerAutomaton(lia,updateMethod) 
    PDA.run()
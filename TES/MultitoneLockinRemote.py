# -*- coding: utf-8 -*-
"""
Remote control interface for MultitoneLockin
2017-11-29
@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""
from __future__ import print_function
from Zmq.Zmq import RequestReplyRemote
from Zmq.Ports import RequestReply

class MultitoneLockinRemote(RequestReplyRemote, object):
	'''Remote control of ADR temperature PID via ZMQ request-reply socket.
	Use this class to interface with the ADR temperature PID control from other programs.'''
    
	def __init__(self, origin, parent=None):
		super(MultitoneLockinRemote, self).__init__(origin=origin, port=RequestReply.MultitoneLockin, parent=parent)

	def fileName(self):
		return self._execute('fileName')

	def setComment(self, comment):
		'''Set comment (string).
		
		Tooltip for comment:
		Put any arbitrary comments here.'''
		self._setValue('comment', comment)

	def comment(self):
		'''Return the string for comment.'''
		return self._queryValue('comment')

	def setDecimation(self, decimation):
		'''Select decimation with choices of [].
		
		Tooltip for decimation:
		<html><head/><body><p>Decimation to be applied before the lock-in mixer
		stage.</p><p>This allows reducing the computational load, but limits the
		highest frequency available for the lock-ins.</p><p>The resulting phase
		shift will be automatically accounted for.</p><p>Filtering is
		accomplished by a cascade of halfband FIR filters.</p></body></html>'''
		self._setValue('decimation', decimation)

	def decimation(self):
		'''Return the choice for decimation.'''
		return self._queryValue('decimation')

	def setAiTerminalConfig(self, aiTerminalConfig):
		'''Select aiTerminalConfig with choices of [].'''
		self._setValue('aiTerminalConfig', aiTerminalConfig)

	def aiTerminalConfig(self):
		'''Return the choice for aiTerminalConfig.'''
		return self._queryValue('aiTerminalConfig')

	def setAiChannel(self, aiChannel):
		'''Select aiChannel with choices of [].
		
		Tooltip for aiChannel:
		Input channel for the lock-in.'''
		self._setValue('aiChannel', aiChannel)

	def aiChannel(self):
		'''Return the choice for aiChannel.'''
		return self._queryValue('aiChannel')

	def stop(self):
		''''''
		self._clickButton('stop')

	def isRunning(self):
		'''See if the measurement is running (i.e. can be stopped)'''
		self._isEnabled('stop')

	def setSample(self, sample):
		'''Set sample (string).
		
		Tooltip for sample:
		Specify the ID of the sample here. Also used as the first part of the
		filename.'''
		self._setValue('sample', sample)

	def sample(self):
		'''Return the string for sample.'''
		return self._queryValue('sample')

	def setSamplingRate(self, samplingRate):
		'''Set the value of samplingRate (int from 1 to 99).
		
		Tooltip for samplingRate:
		Specify the sample rate. Note that this should be higher than 2x the
		bandwidth of the SQUID signal, unless you have provided appropriate
		analog filtering.'''
		self._setValue('samplingRate', samplingRate)

	def samplingRate(self):
		'''Get the value of samplingRate (int).'''
		return self._queryValue('samplingRate')

	def setRampRate(self, rampRate):
		'''Set the value of rampRate in units of V/s (from 0.000 to 100.000 V/s).
		
		Tooltip for rampRate:
		Ramp rate for DC offset. Set to 0 for instantaneous changes.'''
		self._setValue('rampRate', rampRate)

	def rampRate(self):
		'''Get the value of rampRate (float).'''
		return self._queryValue('rampRate')

	def setOffset(self, offset):
		'''Set the value of offset in units of V (from -10.0000 to 10.0000 V).
		
		Tooltip for offset:
		DC offset added to AC excitation signal.'''
		self._setValue('offset', offset)

	def offset(self):
		'''Get the value of offset (float).'''
		return self._queryValue('offset')

	def setDcFilterOrder(self, dcFilterOrder):
		'''Set the value of dcFilterOrder (int from 1 to 10).
		
		Tooltip for dcFilterOrder:
		Order of the DC filter. The roll of is 6dB*order.'''
		self._setValue('dcFilterOrder', dcFilterOrder)

	def dcFilterOrder(self):
		'''Get the value of dcFilterOrder (int).'''
		return self._queryValue('dcFilterOrder')

	def enableSaveRawData(self, enable=True):
		'''Enable (or disable) saveRawData.
		
		Tooltip for saveRawData:
		Check to save raw (but decimated) data to the file. This could consume a
		lot of disk space.'''
		self._setValue('saveRawData', enable)

	def disableSaveRawData(self):
		'''Disable saveRawData'''
		self.enableSaveRawData(False)

	def isSaveRawData(self):
		'''Return True if saveRawData is enabled.'''

	def setAiRange(self, aiRange):
		'''Select aiRange with choices of [].
		
		Tooltip for aiRange:
		Input range for the input channel.'''
		self._setValue('aiRange', aiRange)

	def aiRange(self):
		'''Return the choice for aiRange.'''
		return self._queryValue('aiRange')

	def start(self):
		''''''
		self._clickButton('start')

	def isFinished(self):
		''''''
		self._isEnabled('start')

	def enableSaveRawDemod(self, enable=True):
		'''Enable (or disable) saveRawDemod.
		
		Tooltip for saveRawDemod:
		Check here if you'd like to save the decimated demodulated data before
		it runs through the final low-pass filters. This is useful if you'd like
		to do the final filtering yourself e.g. with a non-causal filter to
		avoid phase shifts.'''
		self._setValue('saveRawDemod', enable)

	def disableSaveRawDemod(self):
		'''Disable saveRawDemod'''
		self.enableSaveRawDemod(False)

	def isSaveRawDemod(self):
		'''Return True if saveRawDemod is enabled.'''

	def setDcBw(self, dcBw):
		'''Set the value of dcBw in units of Hz (from 0.10 to 10.00 Hz).
		
		Tooltip for dcBw:
		Bandwidth of the filter used to calculate the DC signal. Note that the
		DC signal is also subtracted from the raw analog input siganl to
		effectively high-pass filter the input.'''
		self._setValue('dcBw', dcBw)

	def dcBw(self):
		'''Get the value of dcBw (float).'''
		return self._queryValue('dcBw')

if __name__ == '__main__':
	import time
	mtl = MultitoneLockinRemote('Testing')
	print('DC BW:', mtl.dcBw())
	print('DC filter order:', mtl.dcFilterOrder())
	mtl.start()
	
	for i in range(20):
		time.sleep(1)
		print('Running:', mtl.isRunning())
	print('Filename:', mtl.fileName())
	print('Stop requested')
	mtl.stop()
	for i in range(5):
		time.sleep(1)
		print('Running:', mtl.isRunning())
	
    #print('File name:', mtl.fileName())
    #print('Finished:', mtl.isFinished())
    #print(mtl.samplingRate())
    
    

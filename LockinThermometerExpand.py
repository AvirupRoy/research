# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 22:41:08 2017

@author: wisp10
"""

from Visa.SR830_New import SR830
from PyQt4.QtGui import QWidget,QErrorMessage, QIcon,QApplication
from PyQt4.Qt import Qt
from PyQt4.QtCore import QSettings
from Calibration.RuOx import RuOx600, RuOxBus, RuOx2005, RuOxBox
from LockinThermometerPDA import LockinThermometerAutomaton
from Zmq.Zmq import ZmqPublisher
from Zmq.Ports import PubSub #,RequestReply
import os
try:
	from PyQt4.QtCore import QString
except ImportError:
	# we are using Python3 so QString is not defined
	QString = str

import time
import logging
logging.basicConfig(level=logging.DEBUG)
from LabWidgets.Utilities import compileUi
compileUi('LockinThermometerExpandUi')
import LockinThermometerExpandUi as Ui
import pyqtgraph as pg

class LockinThermometerWithExpandWidget(Ui.Ui_Form, QWidget):
	def __init__(self,parent=None):
		super(LockinThermometerWithExpandWidget, self).__init__(parent)
		self.setupUi(self)
		self.setWindowTitle('Lockin Thermometer')
		self.Rthermometer = float('nan')
		
		axis = pg.DateAxisItem(orientation='bottom')
		self.plot = pg.PlotWidget(axisItems={'bottom': axis})
		self.plot.setBackground('w')
		self.plot.plotItem.showGrid(x=True, y=True)
		self.plot.addLegend()
		self.verticalLayout.addWidget(self.plot)
		self.curve = pg.PlotCurveItem(name='X', symbol='o', pen='b')
		self.plot.addItem(self.curve)
		self.clearPb.clicked.connect(self.clearData)
		self.clearData()
		self.plotYAxisCombo.currentIndexChanged.connect(self.updatePlot)
		
		self.publisher=None
		
		self.adjOffsetCb.stateChanged.connect(self.transitionState)
		self.adjustExcitationCb.stateChanged.connect(self.adjustExcitation)		
		self.lia=None
		self.runPb.clicked.connect(self.run)
		self.parameterItems = [self.attenuatorGainSb, self.sourceImpedanceSb, self.driveResistanceSb, self.leadResistanceSb, self.preampGainSb, self.sensorVoltageSb]
		self.savePb.clicked.connect(self.saveParameterSet)
		self.loadPb.clicked.connect(self.loadParameterSet)
		self.deletePb.clicked.connect(self.deleteParameterSet)
		self.attenuatorAttenuationSb.valueChanged.connect(self.updateAttenuatorGain)
		self.attenuatorGainSb.valueChanged.connect(self.updateAttenuatorAttenuation)
		self.sensorVoltageIndicator.setUnit('V')
		self.sensorCurrentIndicator.setUnit('A')
		self.sensorPowerIndicator.setUnit('W')
		self.adjustLiaExcitation=self.adjustExcitationCb.isChecked()
		lia=SR830(None)
		lia.sensitivity.populateEnumComboBox(self.minSensitivityCombo)
		
		self.loadParameterSets()
		self.restoreSettings()
# 		self.adrResistanceIndicator.setUnit(u'Ω')
# 		self.adrResistanceIndicator.setPrecision(5)
		
		combo = self.calibrationCombo
		combo.addItem('RuOx 600')
		combo.addItem('RuOx 2005')
		combo.addItem('RuOx Bus (Shuo)')
		combo.addItem('RuOx Chip (InsideBox)')
		combo.setItemData(0, 'Nominal sensor calibration for RuOx 600 series', Qt.ToolTipRole)
		combo.setItemData(1, 'Calibration for RuOx sensor #2005 series', Qt.ToolTipRole)
		combo.setItemData(2, 'Cross-calibration against RuOx #2005 by Shuo (not so good above ~300mK)', Qt.ToolTipRole)
		combo.setItemData(3, 'Cross-calibration against RuOx #2005 by Yu', Qt.ToolTipRole)
		
		self.selectCalibration()
		combo.currentIndexChanged.connect(self.selectCalibration)

	def updateSensitivity(self,sens):
		sensStr= "%f" %sens
		#print(sensStr)
		self.sensLineEdit.setText(sensStr)

	def updateFilterTc(self,filterTc):
		filterTcStr = "%f" %filterTc
		self.filterTcLineEdit.setText(filterTcStr)

	def updateOffsetX(self,offsetX):
		offsetXStr="%f" %offsetX
		self.offsetXLineEdit.setText(offsetXStr)

	def updateExpandX(self,expandX):
		expandXStr = "%d" %expandX
		self.expandXLineEdit.setText(expandXStr)
		


	def adjustExcitation(self):
		if self.adjustExcitationCb.isChecked():
			self.adjustLiaExcitation=True


	def updateValues(self,f,X,Y):
		#print("In update values : ",X,Y)
		
		t = time.time()
		VsineOut = self.lia.sineOut.value
		G1 = self.attenuatorGainSb.value()
		G2 = self.preampGainSb.value()
		Rsource = self.sourceImpedanceSb.value()
		Rd = self.driveResistanceSb.value()
		Rl = self.leadResistanceSb.value()
		Rs = Rsource+Rd+Rl
		Vx = X / G2		
		Vex = VsineOut * G1 # Real excitation
		self.sensorVoltageIndicator.setValue(Vx)
		Rx = Rs / (Vex/Vx-1.)
		I = Vx / Rx
		self.sensorCurrentIndicator.setValue(I)
		P = Vx*I
		Temp = self.calibration.calculateTemperature([Rx])[0] # @todo This is really a crutch
		Tbase = self.calibration.correctForReadoutPower(Temp, P)
# 		with open(self.fileName, 'a+') as of:
# 			of.write('%.3f\t%.3f\t%.5E\t%.5E\t%.3f\t%.1E\t%.5E\t%.5E\n' % (t, VsineOut, X, Y, f, sensitivity, Rx, self.Rthermometer))

		if self.publisher is not None:
			if Temp > 0 and Temp < 10:
				self.publisher.publishDict(self.sensorName(), {'t': t, 'R': Rx, 'T': Temp, 'P': P, 'Tbase':Tbase})

		
		sensitivityStr = self.sensLineEdit.text()
		
		if sensitivityStr is not None:
                  #print(sensitivityStr)
                  sensitivity=float(sensitivityStr)
		
		'''When to close the file'''
		
		with open(self.fileName, 'a+') as of:
			of.write('%.3f\t%.3f\t%.5E\t%.5E\t%.3f\t%.1E\t%.5E\t%.5E\n' % (t, VsineOut, X, Y, f, sensitivity, Rx, self.Rthermometer))

		self.ts.append(t)
		self.xs.append(X)
		self.ys.append(Y)
		self.fs.append(f)
		self.VsineOuts.append(VsineOut)
		self.Rs.append(Rx)
		self.Vxs.append(Vx)
		self.Ps.append(P)
		self.Ts.append(Temp)
		self.Tbases.append(Tbase)
		self.sensorIndicator.setValue(Rx)
		self.temperatureIndicator.setKelvin(Temp)
		self.baseTempIndicator.setKelvin(Tbase)
		self.sensorPowerIndicator.setValue(P)
		self.updateLed.flashOnce()
		self.updatePlot()

		if not self.adjustExcitationCb.isChecked():
			return

		VxDesired = self.sensorVoltageSb.value()
		IDesired = VxDesired / Rx
		VexDesired = IDesired*(Rx+Rs)
		change = (VexDesired-Vex)/Vex
		tolerance = 1E-2*self.toleranceSb.value()
		if abs(change) < tolerance:
			return
		
		VsineOutDesired = VexDesired / G1 # This is what we would like to see
		# What we actually get may be something different
		Vnew = min(5,max(VsineOutDesired,0.004))
		if tolerance == 0 and abs(Vnew - VsineOut) > 0.009:   # If a large step is required, do it slowly
			Vnew = (3.*VsineOut+1.*Vnew)/4.
		
		if abs(Vnew - VsineOut) < 0.002:
			return
		self.exChangedTime = t
		
# 		if self.adjustLiaExcitation:
# 			self.adjOffsetState = self.adjOffsetCb.isChecked()
# 			if self.adjOffsetState:
# 				self.PDA.transitionToRNE()
# 				self.adjOffsetCb.setEnabled(False)
# 				print("Disabled Offset")
# 				time.sleep(5)
#			self.adjustLiaExcitation=False
		self.lia.sineOut.value = Vnew
		
# 		if self.adjOffsetState:
# 			self.PDA.transitionToRWE()
# 			self.adjOffsetCb.setEnabled(True)
# 			self.adjOffsetState=False
	

	def transitionState(self):
		if self.PDA is None:
			return
		
		if self.adjOffsetCb.isChecked():
			''' Transition to RWEData'''
			self.PDA.transitionToRWE()
			#print("Transition Needed")
		else:
			'''Transition to RNEData'''
			self.PDA.transitionToRNE()


	def restoreSettings(self):
		s = QSettings()
		self.configCombo.setCurrentIndex(self.configCombo.findText(s.value('parameterSet', '', type=QString)))
		if len(self.configCombo.currentText()):
			self.loadParameterSet()

	def sensorName(self):
		return str(self.sensorNameLe.text())

	def run(self):
		if self.lia is not None:
			self.stop()
		else:
			self.start()

	def start(self):
		sensorName = self.sensorName()
		self.setWindowTitle('Lock-In Thermometer %s' % sensorName )
		
		if sensorName == 'BusThermometer':
			icon = QIcon('Icons/LockinThermometer_Bus.ico')
		elif sensorName == 'RuOx2005Thermometer':
			icon = QIcon('Icons/LockinThermometer_BoxOutside.ico')
		elif sensorName == 'BoxThermometer':
			icon = QIcon('Icons/LockinThermometer_BoxInside2.ico')
		else:
			icon = QIcon('Icons/LockinThermometer.ico')

		self.setWindowIcon(icon)

		
		visa = str(self.visaCombo.currentText())
		self.lia = SR830(visa)
		self.setupAutomaton()
		
		Sockets = {'BusThermometer':PubSub.LockinThermometerAdr, 'RuOx2005Thermometer':PubSub.LockinThermometerRuOx2005,'BoxThermometer':PubSub.LockinThermometerBox}
		socket = Sockets[sensorName]
		self.publisher = ZmqPublisher('LockinThermometer', socket)
		
		
		self.runPb.setText('Stop')
		self.enableWidgets(False)
		
		t = time.time()
		timeString = time.strftime('%Y%m%d-%H%M%S', time.localtime(t))
		dateString = time.strftime('%Y%m%d')
		sensorName = str(self.sensorNameLe.text())

		s = QSettings('WiscXrayAstro', application='ADR3RunInfo')
		path = str(s.value('runPath', '', type=str))
		fileName = os.path.join(path, '%s_%s.dat' % (sensorName, dateString))
		if not os.path.isfile(fileName): # Maybe create new file
			with open(fileName, 'a+') as f:
				f.write('#LockinThermometer.py\n')
				f.write('#Date=%s\n' % timeString)
				f.write('#SensorName=%s\n' % sensorName)
				f.write('#SR830=%s\n' % self.lia.visaId())
				f.write('#AttenuatorGain=%f\n' % self.attenuatorGainSb.value())
				f.write('#AttenuatorSourceImpedance=%f\n' % self.sourceImpedanceSb.value())
				f.write('#DriveResistance=%f\n' % self.driveResistanceSb.value())
				f.write('#LeadResistance=%f\n' % self.leadResistanceSb.value())
				f.write('#PreampGain=%f\n' % self.preampGainSb.value())
				f.write('#DesiredExcitation=%f\n' % self.sensorVoltageSb.value())
				k = self.lia.allSettingValues()
				for key,value in k.iteritems():
					f.write('#SR830/%s=%s\n' % (key,value))
				f.write('#'+'\t'.join(['time', 'VsineOut', 'X', 'Y', 'f', 'Sensitivity', 'RxCalc', 'Rtherm'])+'\n')
		self.fileName = fileName
		self.PDA.start()
		
	def stop(self):
		self.lia = None
		self.PDA.stop();	 
		while(self.PDA.isRunning()):
			pass
		
		self.PDA=None
		self.runPb.setText('Start')
		self.enableWidgets(True)
		del self.publisher
		self.publisher=None
		
	def enableWidgets(self, enable):
		self.visaCombo.setEnabled(enable)
		self.attenuatorGroupBox.setEnabled(enable)
		self.seriesResistanceGroupBox.setEnabled(enable)
		self.preampGroupBox.setEnabled(enable)
		self.sensorNameLe.setEnabled(enable)
		self.loadPb.setEnabled(enable)
		self.savePb.setEnabled(enable)
		self.deletePb.setEnabled(enable)
		self.configCombo.setEnabled(enable)

# 	def collectAdrResistance(self, R):
# 		self.Rthermometer = R
# 		self.adrResistanceIndicator.setValue(R)

	def updateAttenuatorGain(self, v):
		sb = self.attenuatorGainSb
		block = sb.blockSignals(True)
		sb.setValue(1./v)
		sb.blockSignals(block)
		
	def updateAttenuatorAttenuation(self, v):
		sb = self.attenuatorAttenuationSb
		block = sb.blockSignals(True)
		sb.setValue(1./v)
		sb.blockSignals(block)
		
	def saveParameterSet(self):
		s = QSettings()
		s.beginGroup('ParameterSets')
		name = self.configCombo.currentText()
		s.beginGroup(name)
		s.setValue('adjustExcitation', self.adjustExcitationCb.isChecked())
		s.setValue('sensorName', self.sensorNameLe.text())
		s.setValue('sr830Visa', self.visaCombo.currentText())
		s.setValue('autoRanging', self.autoRangingCb.isChecked())
		s.setValue('minSensitivity', self.minSensitivityCombo.currentCode())
		for item in self.parameterItems:
			s.setValue(item.objectName(), item.value())
		s.endGroup()
		s.endGroup()
		
	def loadParameterSet(self):
		s = QSettings()
		name = self.configCombo.currentText()
		s.beginGroup('ParameterSets')
		if not name in s.childGroups():
			dlg = QErrorMessage(self)
			dlg.setWindowTitle('Error')
			dlg.showMessage('No saved parameters available for %s' % name)
			return
		s.beginGroup(name)
		for item in self.parameterItems:
			item.setValue(s.value(item.objectName(), item.value(), type=float))
		self.adjustExcitationCb.setChecked(s.value('adjustExcitation', False, type=bool))
		self.sensorNameLe.setText(s.value('sensorName', '', type=QString))
		self.visaCombo.setCurrentIndex(self.visaCombo.findText(s.value('sr830Visa', 'GPIB0::12', type=QString)))
		self.autoRangingCb.setChecked(s.value('autoRanging', True, type=bool))
		self.minSensitivityCombo.setCurrentCodeSilently(s.value('minSensitivity', 0, type=int))
		s.endGroup()
		s.endGroup()
		
	def loadParameterSets(self):
		s = QSettings()
		s.beginGroup('ParameterSets')
		names = s.childGroups()
		self.configCombo.addItems(names)
		
	def deleteParameterSet(self):
		i = self.configCombo.currentIndex()
		name = self.configCombo.itemText(i)		
		
		s = QSettings()
		s.beginGroup('ParameterSets')
		s.beginGroup(name)
		s.remove('')
		s.endGroup()
		s.endGroup()
		
		self.configCombo.removeItem(i)


	def selectCalibration(self):
		cal = self.calibrationCombo.currentText()
		if cal == 'RuOx 600':
			self.calibration = RuOx600()
		elif cal == 'RuOx 2005':
			self.calibration = RuOx2005()
		elif cal == 'RuOx Bus (Shuo)':
			self.calibration = RuOxBus()
		elif cal == 'RuOx Chip (InsideBox)':
			self.calibration = RuOxBox()



	def clearData(self):
		self.ts = []
		self.xs = []
		self.ys = []
		self.fs = []
		self.Rs = []
		self.Ps = []
		self.VsineOuts = []
		self.Vxs = []
		self.Ts = []
		self.Tbases = []
		self.updatePlot()
		
	def updatePlot(self):
		yAxis = self.plotYAxisCombo.currentText()
		pl = self.plot
		if yAxis == 'X':
			y = self.xs
			pl.setLabel('left', 'Lock-in X', 'V')
		elif yAxis == 'Y':
			y = self.ys
			pl.setLabel('left', 'Lock-in Y', 'V')
		elif yAxis == 'R':
			y = self.Rs
			pl.setLabel('left', 'R sensor', u'Ω')
		elif yAxis == 'V sine out':
			y = self.VsineOuts
			pl.setLabel('left', 'V sine out', 'V')
		elif yAxis == 'V sensor':
			y = self.Vxs
			pl.setLabel('left', 'V sensor', 'V')
		elif yAxis == 'P sensor':
			y = self.Ps
			pl.setLabel('left', 'P sensor', 'W')
		elif yAxis == 'Sensor temperature':
			y = self.Ts
			pl.setLabel('left', 'T sensor', 'K')
		elif yAxis == 'Base temperature':
			y = self.Tbases
			pl.setLabel('left', 'T base', 'K')
		elif yAxis == '':
			return
		x = self.ts
		self.curve.setData(x, y)

	def setupAutomaton(self):
		if self.adjOffsetCb.isChecked():
			initState='RWE'
		else:
			initState='RNE'
		self.PDA=LockinThermometerAutomaton(self.lia,initState,self.updateValues,self.updateSensitivity,self.updateFilterTc,self.updateOffsetX,self.updateExpandX)
		
		
		
def setAppId(name):
	import ctypes
	myappid = u'WISCXRAYASTRO.ADR3.%s.1' % name # arbitrary string
	ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)  

if __name__ == '__main__':
	app = QApplication([])
	app.setApplicationName('Lockin Thermometer')
	app.setApplicationVersion('0.1')
	app.setOrganizationDomain('wisp.physics.wisc.edu')
	app.setOrganizationName('McCammon X-ray Astrophysics')
	
	setAppId('LockInThermometer')
	
	mainWindow = LockinThermometerWithExpandWidget()	
	icon = QIcon('Icons/LockinThermometer.ico')
	mainWindow.setWindowIcon(icon)
	mainWindow.show()
	app.exec_()


	
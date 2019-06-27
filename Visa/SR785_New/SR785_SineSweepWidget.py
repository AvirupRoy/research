# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 19:03:30 2015

@author: jaeckel
"""
#from PyQt4.QtGui import QGroupBox

#include <Qtimer>

import SR785_SineSweepUi

from PyQt4.QtGui import QWidget

from PyQt4 import Qt, Qwt5, QtGui, QtCore

#rom PyQt4.Qwt5.anynumpy import *
import numpy as np

#from matplotllib.figure import Figure
#
#from matplotlib.backends.backen_qt4agg import FigureCanvasQTAgg

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

#import matplotlib.pyplot as plt

import random


class ColePlot(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.layout = QVboxLayout()
        self.plot = QMatplotlibWidget()
        self.toolbar = NavigationToolbar(self.plot, self)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.plot)
        

        

class SR785_SineSweepWidget(QWidget, SR785_SineSweepUi.Ui_Form):
    def __init__(self, sr785, parent=None):
        QWidget.__init__(self, parent)
        SR785_SineSweepUi.Ui_Form.__init__(self)       
        self.sr785 = sr785
#        super(SR785_SineSweepWidget, self).__init__(self)
        self.setupUi(self)
        self.startPb.clicked.connect(self.startMeasurement)
        self.pausePb.setDisabled(True)        
        self.pausePb.clicked.connect(self.sr785.pauseMeasurement)
        
        # Frequency Menu
        self.sr785.sweptSine.startFrequency.bindToSpinBox(self.startFrequencySb)
        self.sr785.sweptSine.stopFrequency.bindToSpinBox(self.stopFrequencySb)
        self.sr785.sweptSine.repeat.bindToEnumComboBox(self.repeatCombo)        
        self.sr785.sweptSine.sweepType.bindToEnumComboBox(self.typeCombo)
        self.sr785.sweptSine.autoResolution.bindToEnumComboBox(self.autoResolutionCombo)        
        self.sr785.sweptSine.numberOfPoints.bindToSpinBox(self.numberOfPointsSb)
        self.sr785.sweptSine.maximumStepSize.bindToSpinBox(self.maximumStepSizeSb)
        self.sr785.sweptSine.fasterThreshold.bindToSpinBox(self.fasterThresholdSb)
        self.sr785.sweptSine.slowerThreshold.bindToSpinBox(self.slowerThresholdSb)
        
        # Source Menu
        self.sr785.sweptSine.autoLevelReference.bindToEnumComboBox(self.autoLvlReferCombo)
        self.sr785.sweptSine.idealReference.bindToSpinBox(self.idealReferSb)
        self.sr785.sweptSine.sourceRamping.bindToEnumComboBox(self.sourceRampCombo)
        self.sr785.sweptSine.sourceRampRate.bindToSpinBox(self.sourceRampRateSb)
        self.sr785.sweptSine.referenceUpperLimit.bindToSpinBox(self.referUpperLimitSb)
        self.sr785.sweptSine.referenceLowerLimit.bindToSpinBox(self.referLowerLimitSb)
        self.sr785.sweptSine.maximumSourceLevel.bindToSpinBox(self.maxSourceLvlSp)
        self.sr785.sweptSine.offset.bindToSpinBox(self.offsetSb)        
        
        # Average Menu        
        self.sr785.sweptSine.settleTime.bindToSpinBox(self.settleTimeSb)
        self.sr785.sweptSine.settleCycles.bindToSpinBox(self.settleCycleSb)
        self.sr785.sweptSine.integrationTime.bindToSpinBox(self.integrationTimeSb)
        self.sr785.sweptSine.integrationCycles.bindToSpinBox(self.integrationCyclesSb)
                
        
        
        #self.qwtPlot.setCanvasBackground(Qt.Qt.white)
#        x=np.arange(-2*np.pi, 2*np.pi, 0.01)
#        y = np.pi*np.sin(x)
        #curve = Qwt5.QwtPlotCurve('y = pi*sin(x)')
        #curve.attach(self.qwtPlot)
        #curve.setPen(Qt.QPen(Qt.Qt.green, 2))
        #curve.setData(x,y)
        #self.qwtPlot.replot()

## Creates the matplotlib typical output...
## See www.training.prace-ri.eu/uploads/tx_pracetmo/QtGuiIntro.pdf
##
#        self.figure = plt.figure()
#        self.mplwidget.
        self.mplwidget
#        self.mplwidget.draw()
        self.toolbar = NavigationToolbar(self.mplwidget, self)
        self.verticalLayout_2.addWidget(self.toolbar)
#        self.canvas = FigureCanvas(self.figure)
#        self.toolbar = NavigationToolbar(self.canvas, self)
#        self.button = QtGui.QPushButton('Plot')
#        self.button.clicked.connect(self.plot)
#        layout = QtGui.QVBoxLayout()
#        layout.addWidget(self.toolbar)
#        layout.addWidget(self.canvas)
#        layout.addWidget(self.button)
#        self.setLayout(layout)
#        
        
#class matPlot(FigureCanvas):
#    def __init__(self):
#        self.toolbar = NavigationToolbar(self, self)
        
    def startMeasurement(self):
        ## Maybe enable a stop button and disable the start button
        self.sr785.startMeasurement()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.checkIfDone)
        self.timer.start(1000)
        self.startPb.setDisabled(True)
        self.pausePb.setEnabled(True)



    def plot(self):
        #data = [random.number() for i in range(25)]
        #ax = self.figure.add_subplot(1,1,1)
        #ax.hold(False)
        #ax.plt(data, '*-')
        #self.canvas.draw()
        pass

# Not liking something about this, unsupported operand type(s) for -: 'builtin_function_or_method' and 'int'     
    def checkIfDone(self):
        progress = sr785.measurementProgress()
        numPts = self.numberOfPointsSb.value()   #Doesn't like this and now doesn't like the retrieveData function...
        if numPts-1 == progress:
            self.timer.stop()
            d = sr785.Display.retrieveData(0) # TypeError: unbound method retrieveData() must be called with Display instance as first argument (got int instance instead)
            self.mplwidget.update(d)
#    print "Display status:", sr.displayStatus
#    finishedA = False
#    finishedB = False
#    while True:
#        status = sr.displayStatus
#        if status & 32:
#            finishedA = True
#        if status & 4096:
#            finishedB = True
#        if finishedA and finishedB:
#            break
#        else:
#            print "Still measuring:", finishedA, finishedB, status

#        if self.sr785.displayStatus() :
#            self.timer.stop()
#            d = sr785.getData()
#            self.plot.update(d)
            
        
#    def pushButtonClicked(self):
#        print "Clicked!"


#class TestPlot(FigureCanvasQTAgg):
#    def __init__(self):
#        self.fig = Figure()
#        self.axes = self.fig.add_subplot(111)


## implemented above
#class TestPlot(SR785_SineSweepUi.Qwt5.QwtPlot):
#    
#    def __init__(self, *args):
#        Qwt5.QwtPlot.__init__(self, *args)
#        self.setCanvasBackground(Qt.QWidget.white)
#        grid = Qwt5.QwtPlotGrid()
#        grid.attach(self)
#        grid.setPen(Qt.QPen(Qt.Qt.black, 0, Qt.Qt.DotLine))
#        x=arange(-2*pi, 2*pi, 0.01)
#        y = pi*sin(x)
#        curve = Qwt5.QwtPlotCurve('y = pi*sin(x)')
#        curve.attach(self)
#        curve.setPen(Qt.QPen(Qt.Qt.green, 2))
#        curve.setData(x,y)
#        self.replot()

#def make():
#    demo = TestPlot()
#    demo.show()
#    return demo


if __name__ == '__main__':
    import sys
    from SR785 import SR785
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    visaAddress = 'GPIB0::10'
    sr785 = SR785(visaAddress)
    sr785.debug = True
        
    mainWindow = SR785_SineSweepWidget(sr785)
    mainWindow.show()
    sr785.display.selectMeasurement(2,'frequency response')
    display0 = sr785.display.retrieveData(0)
    display1 = sr785.display.retrieveData(1)
    mainWindow.mplwidget.axes.plot(display0, '-')
    #app.exec_()
    sys.exit(app.exec_())

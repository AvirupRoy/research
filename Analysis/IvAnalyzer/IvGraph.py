# -*- coding: utf-8 -*-
"""
Created on Tue Jan 16 19:08:00 2018

@author: wisp10
"""
from __future__ import division
import pyqtgraph as pg
from qtpy.QtWidgets import QWidget, QVBoxLayout
from Analysis.TesIvSweepReader import IvSweepCollection

from matplotlib import cm
import numpy as np
import warnings

class IvGraphWidget(QWidget):
    def __init__(self, sweepCollection, parent = None):
        QWidget.__init__(self, parent)
        plotWidget = pg.PlotWidget(parent=None)
        plotWidget.addLegend()
        layout = QVBoxLayout()
        layout.addWidget(plotWidget)
        self.setLayout(layout)
        self.plotWidget = plotWidget
        self.sweepCollection = sweepCollection
        self._sweepMap = {}
        self.colorMap = cm.coolwarm
        self.setAxes('Raw')
        self.setSelection()
        
    def setAxes(self, axesChoice):
        if axesChoice == 'Raw':
            xLabel = 'Vbias'; xUnit = 'V'; ylabel = 'Vsquid'; yUnit = 'V'
        elif axesChoice == 'TES IV':
            xLabel = 'Vtes'; xUnit = 'V'; ylabel = 'Ites'; yUnit = 'A'
        elif axesChoice == 'TES RT':
            xLabel = 'Ttes'; xLabel = 'T'; ylabel = 'Rtes'; yUnit = u'Ω'
        else:
            raise Exception('Unsupported axes choice')
            
        self.axesChoice = axesChoice
        self.updateAllCurveData()
        self.plotWidget.setLabel('bottom', xLabel, xUnit)
        self.plotWidget.setLabel('left', ylabel, yUnit)
        
    def setSelection(self, selection = 'down+/down-'):
        sc = self.sweepCollection
        s = np.zeros_like(sc.iRampUp1, dtype=bool)
        if 'zeros' in selection:
            for zero in sc.iZeros:
                s |= zero
        if 'up+' in selection:
            s |= sc.iRampUp1
        if 'up-' in selection:
            s |= sc.iRampUp2
        if 'down+' in selection:
            s |= sc.iRampDo1
        if 'down-' in selection:
            s |= sc.iRampDo2
            
        self.iSelect = s
        self.updateAllCurveData()

    def updateAllCurveData(self):
        for index in self._sweepMap.keys():
            self.updateCurveData(index)
    
    def updateCurveData(self, index):
        curve = self._sweepMap[index]
        sweep = self.sweepCollection[index]
        curve.setData(sweep.Vbias[self.iSelect], sweep.Vsquid[self.iSelect])

    def showSweep(self, sweepIndex, enable=True):
        if not enable:
            self.hideSweep(sweepIndex)
            return
            
        if sweepIndex in self._sweepMap.keys():
            return
            
        #sweep = self.sweepCollection[sweepIndex]
        curve = pg.PlotDataItem(name='%d' % sweepIndex)
        self._sweepMap[sweepIndex] = curve
        self.updateCurveData(sweepIndex)
        k = self.colorMap(sweepIndex/len(self.sweepCollection))
        color = pg.mkColor(255*k[0], 255*k[1], 255*k[2], 255*k[3])
        pen = pg.mkPen(width=1.0, color=color)
        curve.setPen(pen)
        self.plotWidget.addItem(curve)
        print('Added curve:', curve)

    def hideSweep(self, sweepIndex):
        print('Removing sweep:', sweepIndex)
        try:
            curve = self._sweepMap[sweepIndex]
        except KeyError:
            warnings.warn('Sweep %d not found!', sweepIndex)
            return
        legend = self.plotWidget.plotItem.legend
        print('Legend:', legend)
        legend.removeItem('%d' % sweepIndex)
        print('Removing item:', curve)
        self.plotWidget.removeItem(curve)
        print('items in plotWidget.plotItem:', self.plotWidget.plotItem.items)
        del self._sweepMap[sweepIndex]
        print('Removed sweep')


if __name__ == '__main__':
    from qtpy.QtGui import QApplication
    from qtpy.QtCore import QTimer

    path = 'ExampleData/'
    fileName = path+'TES2_IV_20180117_090049.h5'

    app = QApplication([])
    print('Loading data')
    sweepCollection = IvSweepCollection(fileName)
    print('making widget')
    mw = IvGraphWidget(sweepCollection)
    for i in range(0, len(sweepCollection), 4):
        mw.showSweep(i)
        
    mw.show()
    QTimer.singleShot(3000, lambda: mw.setSelection('up+/up-'))
    
    app.exec_()

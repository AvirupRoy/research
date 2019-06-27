#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 00:03:08 2018

@author: jaeckel
"""

from qtpy.QtWidgets import QSplitter, QDockWidget
from qtpy.QtCore import Qt

import pyqtgraph as pg

class HkDockWidget(QDockWidget):
    def __init__(self, hkData, parent = None):
        QDockWidget.__init__(self, parent)
        self.hkData = hkData

        faaTimeAxis = pg.DateAxisItem(orientation='bottom')
        faaTempPlot = pg.PlotWidget(axisItems={'bottom': faaTimeAxis})

        gggTimeAxis = pg.DateAxisItem(orientation='bottom')
        gggTempPlot = pg.PlotWidget(axisItems={'bottom': gggTimeAxis})
        
        for plot in [gggTempPlot, faaTempPlot]:
            plot.setBackground('w')
            plot.showGrid(x=True, y=True)
            plot.setLabel('left', 'T', 'K')
            #plot.setLabel('bottom', 'time')
            plot.addLegend()
        faaTempPlot.setXLink(gggTempPlot)
        
        pens = {'BusThermometer': 'r', 'RuOx2005Thermometer': 'b', 'BoxThermometer': 'g', 'GGG': 'k'}
        for thermometerId in self.hkData.thermometers.keys():
            thermo = self.hkData.thermometers[thermometerId]
            try:
                pen = pens[thermometerId]
            except KeyError:
                pen = 'k'
            curve = pg.PlotDataItem(name=thermometerId, pen = pen)
            curve.setData(thermo.t, thermo.T)
            #curve.setPen(pen)
            if thermometerId in ['BoxThermometer', 'BusThermometer', 'RuOx2005Thermometer']:
                faaTempPlot.addItem(curve)
            elif thermometerId in ['GGG']:
                gggTempPlot.addItem(curve)
            else:
                print('Ignoring thermometer:', thermometerId)

        magnetTimeAxis = pg.DateAxisItem(orientation='bottom')
        magnetPlot = pg.PlotWidget(axisItems={'bottom': magnetTimeAxis})
        magnetPlot.setBackground('w')
        magnetPlot.showGrid(x=True, y=True)
        magnetPlot.setLabel('left', 'Magnet I', 'A')
        #magnetPlot.setLabel('bottom', 'time')
        magnetPlot.addLegend()
        magnet = hkData.magnet
        magnet.Ifine
        curve = pg.PlotDataItem(name='I (fine)', pen = 'b')
        curve.setData(magnet.t, magnet.Ifine)
        magnetPlot.addItem(curve)
        curve = pg.PlotDataItem(name='I (coarse)', pen = 'r')
        curve.setData(magnet.t, magnet.Icoarse)
        magnetPlot.addItem(curve)
        magnetPlot.setXLink(faaTempPlot)
        
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(faaTempPlot)
        splitter.addWidget(gggTempPlot)
        splitter.addWidget(magnetPlot)
        self.setWidget(splitter)
        self.faaTempPlot = faaTempPlot
        self.gggTempPlot = gggTempPlot
        self.magnetPlot = magnetPlot
        self.lri = None
        
    def highlightTimeSpan(self, tStart, tEnd):
        if self.lri is None:
            self.lri = pg.LinearRegionItem(values=[tStart, tEnd],
                                           orientation=pg.LinearRegionItem.Vertical,
                                           movable=False)
            self.lri.setZValue(10)
            self.faaTempPlot.addItem(self.lri, ignoreBounds=True)
        else:
            self.lri.setRegion([tStart, tEnd])
        rect = self.faaTempPlot.plotItem.viewRect()
        dt = tEnd-tStart
        xl = rect.left(); span = rect.width(); xr = rect.right()
        if span < 1.5*dt:
            span = 2*dt
            self.faaTempPlot.setXRange(tStart-0.25*span, tEnd+0.25*span)
        elif tStart < xl:
            self.faaTempPlot.setXRange(tStart-0.1*span, tStart+0.9*span)
        elif tEnd > xr:
            self.faaTempPlot.setXRange(tEnd-0.9*span, tEnd+0.1*span)
            
    def removeTimeSpanHighlight(self):
        if self.lri is not None:
            self.faaTempPlot.removeItem(self.lri)
            self.lri = None


if __name__ == '__main__':
    from qtpy.QtGui import QApplication
    #from qtpy.QtCore import QTimer
    import h5py as hdf
    path = 'ExampleData/'
    fileName = path+'TES2_IV_20180117_090049.h5'

    app = QApplication([])
    from Analysis.HkImport import HkImporter
    
    f = hdf.File(fileName, 'r')
    hkGroup = f['HK']
    hk = HkImporter(hkGroup)
    mw = HkDockWidget(hk)
    mw.show()
    #QTimer.singleShot(3000, lambda: mw.setSelection('up+/up-'))
    
    app.exec_()
    
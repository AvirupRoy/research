# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 14:40:47 2018

@author: wisp10
"""

from qtpy.QtWidgets import QWidget, QTableWidget, QDoubleSpinBox, QTableWidgetItem, QSizePolicy, QVBoxLayout, QComboBox, QFormLayout, QHBoxLayout,QGridLayout
from qtpy.QtCore import QSettings, Signal

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from FitParameterTable import FitParameterTable
import numpy as np

class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=7, height=6, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig = fig
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
class TransferFunctionPlot(MplCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        MplCanvas.__init__(self, parent, width, height, dpi)
        self.ax1 = self.fig.add_subplot(1,1,1)
        self.ax1.set_xlabel('$f$ (Hz)')
        self.ax1.set_ylabel('$Z$ ($\\Omega$)')
        self.realLine = None
        self.imagLine = None
        self.quantity = 'Impedance'
        #self.ax2 = self.fig.add_subplot(1,2,2)
        #self.ax2.set_aspect('equal')
        #self.ax2.set_xlabel('Re')
        #self.ax2.set_ylabel('Im')


    def changeQuantity(self, quantity):
        if quantity == 'Impedance':
            self.ax1.set_ylabel('$Z$ ($\\Omega$)')
        elif quantity == 'Admittance':
            self.ax1.set_ylabel('$Y$ (Mohs)')
        self.quantity = quantity
        self.replot()
            
    def updateModel(self, f, Z):
        self.f = f
        self.Z = Z
        self.replot()
        
    def replot(self):
        x = self.f
        if self.quantity == 'Impedance':
            y1 = np.real(self.Z)
            y2 = np.imag(self.Z)
        elif self.quantity == 'Admittance':
            Y = 1./self.Z
            y1 = np.real(Y)
            y2 = np.imag(Y)
            
        if self.realLine is None:
            print('Plotting')
            self.realLine, = self.ax1.semilogx(x, y1, 'r-', label='real')
            self.imagLine, = self.ax1.semilogx(x, y2, 'b-', label='imag')
            #self.reimLine = self.ax2.plot(y1, y2, 'k-')
            self.axes.legend()
            self.updateGeometry()
        else:
            print('Updating plot')
            self.realLine.set_xdata(x)
            self.imagLine.set_xdata(x)
            self.realLine.set_ydata(y1)
            self.imagLine.set_ydata(y2)
            #self.reimLine.set_xdata(y1)
            #self.reimLine.set_ydata(y2)
            self.fig.canvas.draw()
            self.ax1.relim()
            self.ax1.autoscale_view(True,True,True)
            #self.ax2.relim()
            #self.ax2.autoscale_view(False, True, True)
            #self.fig.canvas_flush_events()
            
    def replotData(self, f, Z):
        pass

AvailableModels = ['Hanging', 'Intermediate', 'Parallel']

class ControlsWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)
        self.tfPlot = TransferFunctionPlot() 
        
        self.modelCombo = QComboBox()
        self.modelCombo.addItems(AvailableModels)
        self.quantityCombo = QComboBox()
        self.quantityCombo.addItems(['Impedance', 'Admittance'])
        
        
        self.fMinSb = QDoubleSpinBox()
        self.fMinSb.setRange(0.1, 1E6)
        self.fMaxSb = QDoubleSpinBox()
        self.fMaxSb.setRange(10, 1E6)
        self.fMinSb.setKeyboardTracking(False)
        self.fMaxSb.setKeyboardTracking(False)
        self.fMinSb.valueChanged.connect(self.fMinSb.setMinimum)
        self.fMaxSb.valueChanged.connect(self.fMaxSb.setMaximum)
        self.fMinSb.setValue(1)
        self.fMaxSb.setValue(250E3)
        
        self.shuntSb = QDoubleSpinBox()
        self.shuntSb.setDecimals(4)
        self.shuntSb.setKeyboardTracking(False)
        self.shuntSb.setRange(0.010, 10)
        self.shuntSb.setSuffix(u' m\u03A9')
        self.shuntSb.setValue(0.257)

        l = QFormLayout()
        l.addRow('Model', self.modelCombo)
        l.addRow('Quantity', self.quantityCombo)
        l.addRow('f (min)', self.fMinSb)
        l.addRow('f (max)', self.fMaxSb)
        l.addRow('Shunt resistance', self.shuntSb)
        self.setLayout(l)

class ThermalModelWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        l = QVBoxLayout(self)
        self.tfPlot = TransferFunctionPlot()
        self.cwidget = ControlsWidget()
        self.noiseCanvas = MplCanvas()
        

        #l.addWidget(self.noiseCanvas)
        l.addWidget(self.tfPlot)
        l.addWidget(self.cwidget)
        self.parameterTable = FitParameterTable()
        self.parameterTable.guessChanged.connect(self.recalculate)
        l.addWidget(self.parameterTable)
        self.setLayout(l)
        self.cwidget.modelCombo.activated.connect(self.modelChanged)
        #self.modelChanged()
        self.restoreSettings()
        
    def closeEvent(self, e):
        #print('Close event')
        self.saveSettings()
        
    def saveSettings(self, s = None):
        if s is None:
            s = QSettings()
    
        ps = self.parameterTable.guess()

        s.beginGroup('HangingModel')
        for key in ps:
            #print('Saving value:', key)
            s.setValue(key, ps[key])
        s.endGroup()
        #print('Saved settings:', ps)
            
    def restoreSettings(self, s = None):
        if s is None:
            s = QSettings()
        guess = self.parameterTable.guess()
        s.beginGroup('HangingModel')
        for key in guess:
            guess[key] = s.value(key, type=float)
        s.endGroup()
        #print('Restoring settings:', guess)
        self.parameterTable.setGuess(guess)
        
    def modelChanged(self):
        modelName = str(self.cwidget.modelCombo.currentText())
        #modelName = 'Hanging'
        if modelName == 'Hanging':
            model = HangingModel(Rshunt=self.cwidget.shuntSb)
        elif modelName == 'Intermediate':
            model = IntermediateModel(Rshunt=self.cwidget.shuntSb)
        elif modelName == 'Parallel':
            model = ParallelModel(Rshunt=self.cwidget.shuntSb)
        else:
            print('Unsupported model')
        self.model = model
        self.parameterTable.setupParameters(model)
        
    def recalculate(self):
        parameters = self.parameterTable.guess()
        
        print(parameters)
        omega = np.logspace(np.log10(1), np.log10(1E5))
        Z = self.model.impedance(**parameters, omega=omega)
        self.tfPlot.f = 0.5*omega/np.pi
        self.tfPlot.Z = Z
        self.tfPlot.updateModel(self.tfPlot.f, self.tfPlot.Z)
        #self.cwidget.quantityCombo.activated.connect(self.tfPlot.changeQuantity(str(self.cwidget.quantityCombo.currentText())))


if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    
    app.setOrganizationDomain('wisp.physics.wisc.edu')
    app.setApplicationName('ThermalModelWidgetDemo')
    
    from Analysis.TesModel_Maasilta import HangingModel, IntermediateModel, ParallelModel
    
    #model = HangingModel(Rshunt=0.257)
    
    mw = ThermalModelWidget()
    #ControlsWidget().show()
    #mw.setupParameters(model)
    mw.show()
    
    app.exec_()
        
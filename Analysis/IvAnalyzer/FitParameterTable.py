# -*- coding: utf-8 -*-
"""
Created on Mon Jul 16 13:10:57 2018

@author: wisp10
"""

from qtpy.QtWidgets import QTableWidget, QDoubleSpinBox, QTableWidgetItem
from qtpy.QtCore import Qt, Signal
class FitParameterTable(QTableWidget):
    guessChanged = Signal()
    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)
        columnLabels = ['Parameter', 'Guess', 'Minimum', 'Maximum', 'Fit', 'Error']
        self.setColumnCount(len(columnLabels))
        self.setHorizontalHeaderLabels(columnLabels)

    def setupParameters(self, model):
        pBias = model.biasParameters()
        pSpecific = model.modelSpecificParameters()
        parameters = pBias+pSpecific
        self.setRowCount(len(parameters))
        self.siScale = {}
        self.rowMap = {}
        for row,parameter in enumerate(parameters):
            name, latex, unit, siScale, minimum, maximum, text = parameter
            guessSb = QDoubleSpinBox()
            if len(unit):
                guessSb.setSuffix(' %s' % unit)
            guessSb.setMinimum(minimum)
            guessSb.setMaximum(maximum)
            guessSb.setKeyboardTracking(False)
            item = QTableWidgetItem(name)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked)
            item.setToolTip(text)
            self.setItem(row, 0, item)
            self.setCellWidget(row, 1, guessSb)
            minSb = QDoubleSpinBox()
            maxSb = QDoubleSpinBox()
            minSb.setMinimum(minimum)
            minSb.setMaximum(maximum)
            minSb.setValue(minimum)
            maxSb.setMinimum(minimum)
            maxSb.setMaximum(maximum)
            maxSb.setValue(maximum)
            minSb.setKeyboardTracking(False)
            maxSb.setKeyboardTracking(False)
            
            maxSb.valueChanged.connect(minSb.setMaximum)
            maxSb.valueChanged.connect(guessSb.setMaximum)
            minSb.valueChanged.connect(maxSb.setMinimum)
            minSb.valueChanged.connect(guessSb.setMinimum)
            self.setCellWidget(row, 2, minSb)
            self.setCellWidget(row, 3, maxSb)
            guessSb.valueChanged.connect(self.parameterGuessChanged)
            self.siScale[name] = siScale
            self.rowMap[name] = row
            
    def parameterGuessChanged(self):
        self.guessChanged.emit()
        
    def guess(self):
        '''Return a dictionary of all the parameter guesses'''
        d = {}
        for key in self.rowMap:
            row = self.rowMap[key]
            w = self.cellWidget(row, 1)
            v = w.value() * self.siScale[key]
            d[key] = v
        return d
    
    def setGuess(self, parameterDict):
        for parameter in parameterDict:
            row = self.rowMap[parameter]
            w = self.cellWidget(row, 1)
            v = parameterDict[parameter]
            w.setValue(v / self.siScale[parameter])
        

if __name__ == '__main__':
    from qtpy.QtWidgets import QApplication
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    
    from Analysis.TesModel_Maasilta import HangingModel
    
    model = HangingModel(Rshunt=0.257)
    
    mw = FitParameterTable()
    mw.setupParameters(model)
    print('Guess:', mw.guess())
    mw.show()
    
    app.exec_()

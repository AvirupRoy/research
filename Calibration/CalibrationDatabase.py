# -*- coding: utf-8 -*-
"""
Wrapper to access Thermometer calibrations
Created on Tue Nov 20 18:10:03 2018

@author: wisp10
"""

from __future__ import print_function
import RuOx
import ThermometerCalibration

#        combo.addItem('RuOx 600')
#        combo.addItem('RuOx 2005')
#        combo.addItem('RuOx Bus (Shuo)')
#        combo.addItem('RuOx Chip (InsideBox)')
#        combo.setItemData(0, 'Nominal sensor calibration for RuOx 600 series', Qt.ToolTipRole)
#        combo.setItemData(1, 'Calibration for RuOx sensor #2005 series', Qt.ToolTipRole)
#        combo.setItemData(2, 'Cross-calibration against RuOx #2005 by Shuo (not so good above ~300mK)', Qt.ToolTipRole)
#        combo.setItemData(3, 'Cross-calibration against RuOx #2005 by Yu', Qt.ToolTipRole)

ThermometerCalIds = ['RuOx 600', 'RuOx 2005', 'RuOx Bus (Shuo)', 'RuOx chip (Yu)' , 'UW Ge#5 21692']

def getThermometerCalibration(calId):
    if calId in 'RuOx 600':
        return RuOx.RuOx600()
    elif calId in 'RuOx 2005':
        return RuOx.RuOx2005()
    elif calId in 'RuOx Bus (Shuo)':
        return RuOx.RuOxBus()
    elif calId in 'RuOx chip (Yu)':
        return RuOx.RuOxBox()
    elif calId in 'UW Ge#5 21692':
        cal = ThermometerCalibration.CalibrationSet(sensorSerial='21692')
        cal.loadCalibrationFile('D:\\Users\\FJ\\ADR3\\Calibration\\21692.cof')
        return cal
    else:
        raise KeyError('Unsupported thermometer ID:%s' % calId)


if __name__ == '__main__':
    R = 3500.
    for calId in ThermometerCalIds:
        cal = getThermometerCalibration(calId)
        Th = cal.calculateTemperature(R)
        Tl = cal.correctForReadoutPower(Th, P=1E-12)
        print('Cal ID:', calId, 'Th=',Th, 'Tl=',Tl)

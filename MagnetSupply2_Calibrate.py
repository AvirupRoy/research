# -*- coding: utf-8 -*-
"""
Created on Tue Mar 01 10:01:24 2016

@author: wisp10
"""

from MagnetSupply2 import MagnetControlThread

from Visa.Agilent6641A import Agilent6641A
from Visa.Agilent34401A import Agilent34401A

def promptUser(prompt):
    print prompt
    while True:
        response = raw_input('Type enter to proceed, N to abort!')
        if len(response) == 0:
            return True
        elif response.lower() == 'n':
            return False

dmmVisa = 'GPIB0::23'

dmm = Agilent34401A(dmmVisa)

ps = Agilent6641A('GPIB0::5')
if not '6641A' in ps.visaId():
    raise Exception('Agilent 6641A not found!')
    
print "Starting MagnetSupply"

magnetSupply = MagnetControlThread(ps)
magnetSupply.setupDaqChannels()
magnetSupply.samplesPerChannel = 10000
magnetSupply.setupDaqTasks()
#ps.setVoltage(3.5)
magnetSupply.enableMagnetVoltageControl(True)
magnetSupply.programMagnetVoltage(-0.1)
print "Vps:", ps.measureVoltage()
print "Ips:", ps.measureCurrent()

import pandas as pd
import time
import matplotlib.pyplot as mpl
import numpy as np

def calibrateMagnetVoltageGain(ps, magnetSupply, dmm):
    import DAQ.PyDaqMx as daq
    task = daq.AoTask('Simulate Magnet Voltage')
    task.addChannel(daq.AoChannel('USB6002_B/ao0', -10,+10))
    VReadOutMax = 3.4
    approxGain = 34
    Vmax = VReadOutMax / approxGain
    df = pd.DataFrame(columns=['VmagSim', 'Vdmm', 'Vmag', 'VmagStd'], dtype=float)
    print "VmagSim, Vdmm, Vmag"
    for Vsim in np.linspace(-Vmax, +Vmax, 41):
        task.writeData([Vsim], autoStart=True)
        time.sleep(0.2)
        Vdmm = dmm.voltageDc()
        Vmag, VmagStd = magnetSupply.readDaqTask(magnetSupply.aiTaskMagnetVoltage)
        print Vsim, Vdmm, Vmag
        df.loc[len(df)] = [Vsim, Vdmm, Vmag, VmagStd]
    task.writeData([0], autoStart=True)    
    
    mpl.figure()
    mpl.subplot(2,1,1)
    x = df.Vdmm
    y = df.Vmag
    mpl.plot(x,y, '.')
    fit = np.polyfit(x,y,1)
    mpl.plot(x, np.polyval(fit,x), '-', label='fit')
    mpl.ylabel('Vmag (uncal.) [V]')
    gain = fit[0]
    offset = -fit[1]/fit[0]
    mpl.subplot(2,1,2)
    mpl.plot(x, y/gain+offset - x, 'o')
    mpl.ylabel('Residuals')
    mpl.xlabel('Vmag [V]')
    print "Magnet voltage readout fit:"
    fitString = "Offset=%.5g V, Gain=%.5g A/V" % (offset, gain) 
    print fitString
    mpl.suptitle('Magnet voltage readout:\n%s' % fitString)
    mpl.savefig('MagnetSupplyCalibration_MagnetVoltage.png')
    mpl.show(

def calibrateDiode(ps, magnetSupply, dmm):
    print "---- Calibrating diode ----"
    print "Prerequisites:"
    print "* Coarse and fine current read-outs calibrated."
    print "* Magnet supply output shorted."
    print "* DMM connected to measure voltage drop across diode."
    promptUser("")
    dmm.setFunctionVoltageDc()
    ps.setCurrent(9)
    ps.setVoltage(4.5)
    magnetSupply.setOutputVoltage(0)
    magnetSupply.enableMagnetVoltageControl(False)
    df = pd.DataFrame(columns=['Vcommand', 'Vfet', 'Icoarse', 'Ifine', 'Ips', 'Vdiode'], dtype=float)
    print "Vcom, Vfet, Icoarse, Ifine, Ips, Vdiode"
    
    Vcommand = 0.0
    while True:
        magnetSupply.setOutputVoltage(Vcommand)
        time.sleep(2)
        magnetSupply.readDaqData()
        Vdiode  = dmm.voltageDc()
        Vfet = magnetSupply.fetOutputVoltage
        Icoarse = magnetSupply.currentCoarse
        Ifine   = magnetSupply.currentFine
        Ips = ps.measureCurrent()
        df.loc[len(df)] = [Vcommand, Vfet, Icoarse, Ifine, Ips, Vdiode]
        print Vcommand, Vfet, Icoarse, Ifine, Ips, Vdiode
        if Ips < 0.1:
            step = 0.05
        Vcommand += step
        if Vcommand > 2.2 or Icoarse > 8 or Ips > 8:
            break
    magnetSupply.setOutputVoltage(0)
    df.to_hdf('MagnetSupplyCalibration.h5', 'Diode')
    df.to_csv('MagnetSupplyCalibration_Diode.csv')
       
    
    def diodeVoltage(current, I0, A):
        Vdiode = np.log(current/I0+1.)/A
        return Vdiode
    
    from scipy.optimize import curve_fit
        
    mpl.figure()
    mpl.subplot(2,1,1)
    x=df.Icoarse
    y=df.Vdiode
    good = x > 0.01
    guess = [4.2575E-11, 37.699]
    fit, pcov = curve_fit(diodeVoltage, x[good], y[good], guess)
    mpl.semilogx(x, y, 'o-')
    xfit = np.linspace(0, 8.5, 100)
    mpl.semilogx(xfit, diodeVoltage(xfit, *fit), '-')
    mpl.xlabel('Current [A]')
    mpl.ylabel('Diode voltage[V]')
    mpl.subplot(2,1,2)
    mpl.plot(df.Vfet, df.Vdiode/df.Vfet, 'o-')
    mpl.xlabel('FET voltage [V]')
    mpl.ylabel('Vdiode/Vfet')
    mpl.show()

def calibrateIntegratorOffset(ps, magnetSupply, dmm):
    promptUser("Calibrating integrator offset.\nLeave magnet supply output open circuit. Short magnet voltage input terminals.")
    ps.setCurrent(0.2) # Don't need any current for this
    ps.setVoltage(4.5)
    
    df = pd.DataFrame(columns=['Vcommand', 'Vfet', 'VfetStd'], dtype=float)
    Vs = np.arange(-0.01, 0.01, 0.0003)
    Vs = np.hstack([Vs, Vs[::-1]])
    magnetSupply.magnetVControlTask.writeData([Vs[0]], autoStart = True)
    magnetSupply.enableMagnetVoltageControl(True)
    time.sleep(1)
    print "Vcommand, Vfet"
    for Vcommand in Vs:
        magnetSupply.magnetVControlTask.writeData([Vcommand], autoStart = True)
        time.sleep(0.1)
        Vfet, VfetStd = magnetSupply.readDaqTask(magnetSupply.aiTaskFetOutput)
        print Vcommand, Vfet
        df.loc[len(df)] = [Vcommand, Vfet, VfetStd]
    up = np.diff(df.Vcommand) > 0
    up = np.hstack([up, False])
    mpl.plot(df.Vcommand[up], df.Vfet[up], 'ro-', label='up')
    mpl.plot(df.Vcommand[~up], df.Vfet[~up], 'bo-', label='down')
    mpl.xlabel('Raw command voltage [V]')    
    mpl.ylabel('Raw FET output voltage [V]')
    mpl.suptitle('Magnet voltage integrator test')
    mpl.legend(loc='best')
    mpl.savefig('MagnetSupplyCalibration_Integrator.png')
    mpl.show()

def calibrateCurrentReadouts(ps, magnetSupply, dmm):
    maxCurrent = 2.8 # More than 3A will burn fuse on HP34401A
    promptUser("Calibrating current readout.\nConnect magnet supply output to Agilent DMM (%s) to measure current!" % dmmVisa)
    dmm.setFunctionCurrentDc()
    ps.setCurrent(maxCurrent)
    ps.setVoltage(4.5)
    magnetSupply.enableMagnetVoltageControl(False)
    
    df = pd.DataFrame(columns=['Vcommand', 'Vfet', 'VfetStd', 'Idmm', 'Icoarse', 'IcoarseStd', 'Ifine', 'IfineStd'], dtype=float)
    
    print "Vcom, Vfet, Idmm, Icoarse, Ifine"
    
    Vcommand = 0.0
    while True:
        magnetSupply.setOutputVoltage(Vcommand)
        time.sleep(2)
        Vfet, VfetStd       = magnetSupply.readDaqTask(magnetSupply.aiTaskFetOutput)
        Icoarse, IcoarseStd = magnetSupply.readDaqTask(magnetSupply.aiTaskCurrentCoarse)
        Idmm = dmm.currentDc()
        Ifine, IfineStd     = magnetSupply.readDaqTask(magnetSupply.aiTaskCurrentFine)
        df.loc[len(df)] = [Vcommand, Vfet, VfetStd, Idmm, Icoarse, IcoarseStd, Ifine, IfineStd]
        print Vcommand, Vfet, Idmm, Icoarse, Ifine
        if Ifine < 0.02:
            step = 0.05
        elif Ifine > 10:
            step = 0.05
        else:
            step = 0.005
        Vcommand += step
        if Vcommand > 2.2 or Idmm > 2.5:
            break
    magnetSupply.setOutputVoltage(0)
    df.to_hdf('MagnetSupplyCalibration.h5', 'Current')
    df.to_csv('MagnetSupplyCalibration_Current.csv')
    
    import numpy as np
    
    mpl.figure() 
    x=df.Idmm
    y=df.Icoarse
    good = abs(y) < 10.
    x = x[good]
    y = y[good]
    fit = np.polyfit(x,y,1)
    res = y - np.polyval(fit, x)
    stdDev = np.std(res)
    good = abs(res) < 2*stdDev
    fit = np.polyfit(x[good],y[good],1)
    mpl.subplot(2,1,1)
    mpl.plot(x[good], y[good], 'bo', label='good')
    mpl.plot(x[~good], y[~good], 'ro', label='bad')
    mpl.plot(x[good], np.polyval(fit, x[good]), '-', label='fit')
    mpl.ylabel('I coarse [V]')
    gain = fit[0]
    offset = -fit[1]/fit[0]
    mpl.subplot(2,1,2)
    mpl.plot(x[good], y[good]/gain+offset - x[good], 'o')
    mpl.ylabel('Residual [A]')
    mpl.xlabel('DMM current [A]')
    print "Coarse current readout fit:"
    fitString = "Offset=%.5g V, Gain=%.5g A/V" % (offset, gain) 
    print fitString
    mpl.suptitle('Coarse current readout:\n%s' % fitString)
    mpl.savefig('MagnetSupplyCalibration_CoarseCurrent.png')
    
    mpl.figure()
    x=df.Idmm
    y=df.Ifine
    good = abs(y) < 10.
    fit = np.polyfit(x[good],y[good],1)
    mpl.subplot(2,1,1)
    mpl.plot(x[good], y[good], 'o')
    mpl.plot(x[good], np.polyval(fit, x[good]), '-', label='fit')
    mpl.ylabel('I fine [V]')
    gain = fit[0]
    offset = -fit[1]/fit[0]
    mpl.subplot(2,1,2)
    mpl.plot(x[good],  y[good]/gain+offset - x[good], 'o')
    mpl.ylabel('Residual [A]')
    mpl.xlabel('DMM current [A]')
    print "Fine current readout fit:"
    fitString = "input offset=%.5g V, Gain=%.5g A/V" % (offset, gain) 
    mpl.suptitle('Fine current readout:\n%s' % fitString)
    mpl.savefig('MagnetSupplyCalibration_FineCurrent.png')
    mpl.show()
    
    mpl.figure()
    x = df.Vcommand
    y = df.Vfet
    good = abs(x) <= 2.
    mpl.subplot(2,1,1)
    mpl.plot(x[good],y[good], 'bo', label='good')
    mpl.plot(x[~good],y[~good], 'ro', label='bad')
    fit = np.polyfit(x[good], y[good], 1)
    yfit = np.polyval(fit, x[good])
    mpl.plot(x[good], yfit, '-', label='fit')
    mpl.ylabel('FET voltage [V]')
    mpl.subplot(2,1,2)
    mpl.plot(x[good], y[good]-yfit, 'o')
    mpl.xlabel('Command voltage [V]')
    mpl.ylabel('Residual')
    gain = fit[0]
    offset = -fit[1]/fit[0]
    fitString = "input offset=%.5g V, Gain=%.5g A/V" % (offset, gain) 
    print "FET voltage read-out fit:", fitString
    print "This includes the input divider, therefore it's not the true gain of the read-out!"
    mpl.savefig('MagnetSupplyCalibration_FetOutput.png')
    mpl.show()
    

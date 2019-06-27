#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  9 18:22:01 2019

@author: calorim
"""
import h5py as hdf 

path = '/Users/calorim/Documents/ADR3/G8C/IV/'
fileName = 'TES2_IV_20190409_144959.h5'

f =hdf.File(path+fileName,'r')

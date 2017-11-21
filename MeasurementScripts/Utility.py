# -*- coding: utf-8 -*-
"""
Created on Thu Oct 05 12:48:41 2017

@author: wisp10
"""

import time
from PyQt4.QtGui import QApplication

def wait(seconds):
    t0 = time.time()
    while time.time()-t0 < seconds-2:
        QApplication.processEvents()
        time.sleep(1)
        
    while time.time()-t0 < seconds:
        time.sleep(0.1)

if __name__ == '__main__':
    t1 = time.time()
    wait(2)
    t2 = time.time()
    print(t2-t1)
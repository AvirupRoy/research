# -*- coding: utf-8 -*-
"""
Created on Wed Jan 06 16:25:08 2016

@author: wisp10
"""

import PyQt4.QtGui as gui
import numpy as np
from PyQt4.QtCore import QRect, QByteArray
from hashlib import sha1

#hashTable = {'ButtonUnchecked':'e0367e47f110d95ff7f598f0be878d31ca541dba', 'ButtonChecked': 'd65898a9a3b6bc1943ad9f3824b5ff628e6a7661', 'Return':'803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'SubMenu':'2b0ea8100dd89bf19751ae169f601a9bc3c19cc4','Black':'4d8c0270cad6cd45dbe3afacaabb0ba830015f88'}
#valueTable = {}
valueHashTable = { 'd65898a9a3b6bc1943ad9f3824b5ff628e6a7661': 'ButtonChecked',
                   '2b0ea8100dd89bf19751ae169f601a9bc3c19cc4': 'SubMenu',
                   'e0367e47f110d95ff7f598f0be878d31ca541dba': 'ButtonUnchecked' }
headingHashTable = {'803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1': 'Return',
                    '4d8c0270cad6cd45dbe3afacaabb0ba830015f88': 'Black'}

def hashQImage(image):
    ptr = image.bits()
    ptr.setsize(image.byteCount())
    d = np.array(ptr)
    return sha1(d).hexdigest()
    
class MenuImageAnalyzer():
    def __init__(self, image):
        w = image.width()
        h = image.height()
        if w==800 and h == 600:
            self.menuImage = image.copy(QRect(640,0,160,600))
        elif w==160 and h == 600:
            self.menuImage = image
            
        self.headingHashes = []
        self.valueHashes = []
        for i in range(10):
            self.headingHashes.append(hashQImage(self.menuHeadingImage(i)))
            self.valueHashes.append(hashQImage(self.menuValueImage(i)))
            
    def headerImage(self):
        header = self.menuImage.copy(QRect(5,5,150,22))
        return header
        
    def menuHeadingImage(self, i):
        heading = self.menuImage.copy(QRect(5,i*57+35, 150, 22))
        return heading
        
    def menuValueImage(self, i):
        value = self.menuImage.copy(QRect(5,i*57+35+23, 150, 22))
        return value
        
    def menuType(self, i):
        try:
            return valueHashTable[self.valueHashes[i]]
        except:
            return None
            
    def heading(self, i):
        try:
            return headingHashTable[self.headingHashes[i]]
        except:
            return None
        
    def isButton(self, i):
        return self.menuType(i) in ['ButtonChecked', 'ButtonUnchecked']
        
    def isSubMenu(self, i):
        return self.menuType(i) in ['SubMenu']
        
    def isEditable(self, i):
        return self.menuType(i)
        
    def isReturn(self, i):
        return self.heading(i) == 'Return'
        

if __name__ == '__main__':
    
    #fileName = 'Menu_System_Diagnostics_Memory.png'
    #fileName = 'Menu_Analysis_LimitTesting_EditLimits_Active.png'
    #fileName = 'Menu_Analysis_CurveFit.png'
    fileName = 'Menu_Disk_GetSettings.png'
    #fileName = 'Menu_Window.png'
    #fileName = 'Menu_Window_WindowForceExp.png'
    
    #app = gui.QApplication([])
    #pixmap = gui.QPixmap(fileName)
    image = gui.QImage(fileName)
    
    
    analyzer = MenuImageAnalyzer(image)
    for i in range(10):
        print i,
        print analyzer.menuType(i),
        print 
        
    


    assert(image.height() == 600)
    assert(image.width() == 800)
    menu = image.copy(QRect(640,0,160,600))
    
    header = menu.copy(QRect(5,5,150,22))
    header.save('header.png')
    
    print "Header hash:", hashQImage(header)
    
    for i in range(10):
        print "Item:",i
        title = menu.copy(QRect(5,i*57+35, 150, 22))
        title.save('item%.2d_title2.png' % i)
        print "Title hash:", hashQImage(title)
        value = menu.copy(QRect(5,i*57+35+23, 150, 22))
        value.save('item%.2d_value2.png' % i)
        print "Value hash:", hashQImage(value)
    

    #menu.save('test.png')


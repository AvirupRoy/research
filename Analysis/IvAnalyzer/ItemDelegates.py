# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 00:25:27 2018

@author: wisp10
"""
from __future__ import print_function
from PyQt4 import QtGui, QtCore

class CheckBoxDelegate(QtGui.QStyledItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)
 
    def createEditor(self, parent, option, index):
        '''
        Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model
        '''
        return None
 
    def paint(self, painter, option, index):
        '''
        Paint a checkbox without the label.
        '''
        checked = index.model().data(index, QtCore.Qt.DisplayRole)
        print('Checked:', checked)
        check_box_style_option = QtGui.QStyleOptionButton()
 
        if (index.flags() & QtCore.Qt.ItemIsEditable) > 0:
            check_box_style_option.state |= QtGui.QStyle.State_Enabled
        else:
            check_box_style_option.state |= QtGui.QStyle.State_ReadOnly
 
        if checked:
            check_box_style_option.state |= QtGui.QStyle.State_On
        else:
            check_box_style_option.state |= QtGui.QStyle.State_Off
 
        check_box_style_option.rect = self.getCheckBoxRect(option)
            
        # this will not run - hasFlag does not exist
        #if not index.model().hasFlag(index, QtCore.Qt.ItemIsEditable):
            #check_box_style_option.state |= QtGui.QStyle.State_ReadOnly
            
        check_box_style_option.state |= QtGui.QStyle.State_Enabled
 
        QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox, check_box_style_option, painter)
 
    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton or presses
        Key_Space or Key_Select and this cell is editable. Otherwise do nothing.
        '''
        # This is essentially copied from QStyledItemEditor, except that we
        # have to determine our own "hot zone" for the mouse click.
        # See StackOverflow https://stackoverflow.com/questions/3363190/qt-qtableview-how-to-have-a-checkbox-only-column/3388876#3388876
        #print('Check Box editor Event detected : ')
        #print('Item is editable:', bool(index.flags() & QtCore.Qt.ItemIsEditable))
        if not bool(index.flags() & QtCore.Qt.ItemIsEditable):
            return False

        if event.type() in [QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseMove]:
              return False            
        print('Check Box edior Event detected : passed first check')
        # Do not change the checkbox-state
        if event.type() in [QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseButtonDblClick]:
            if event.button() != QtCore.Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
                return False
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                return True
        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() != QtCore.Qt.Key_Space and event.key() != QtCore.Qt.Key_Select:
                return False
        else:
            return False
        
        self.setModelData(None, model, index)
        return True

    def setModelData(self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        print('SetModelData')
        oldValue = index.model().data(index, QtCore.Qt.DisplayRole)
        print('Old Value : {0}'.format(oldValue))
        
        newValue = not oldValue
        print('New Value : {0}'.format(newValue))
        model.setData(index, newValue, QtCore.Qt.EditRole)
 
    def getCheckBoxRect(self, option):
        check_box_style_option = QtGui.QStyleOptionButton()
        check_box_rect = QtGui.QApplication.style().subElementRect(QtGui.QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QtCore.QPoint (option.rect.x() +
                             option.rect.width() / 2 -
                             check_box_rect.width() / 2,
                             option.rect.y() +
                             option.rect.height() / 2 -
                             check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())

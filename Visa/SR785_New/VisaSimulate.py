# -*- coding: utf-8 -*-
"""
Just a stand-in if pyvisa is not installed
Created on Tue Mar 31 17:38:05 2015

@author: jaeckel
"""

CR = 0x10
LF = 0x13

class instrument(object):
    def __init__(self, resource):
        self.resource = resource
        print "VISA resource:", self.resource

    def write(self, string):
        print "VISA write to %s:" % self.resource, string

    def ask(self, string):
        print "VISA query to %s:" % self.resource, string
        response = input("Type response:")
        return response

    def read(self):
        response = input("VISA read from %s. Type response:" % self.resource)
        return response

    term_chars = LF

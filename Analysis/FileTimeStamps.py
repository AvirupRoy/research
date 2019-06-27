# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 18:24:43 2017

@author: wisp10
"""

def generateHdfImportCode(hdfRoot):
    for key in hdfRoot.attrs.keys():
        print("self.%s = attrs['%s']" % (key,key))

def timeStampFromPath(filePath):
    '''Return the Unix epoch time from a filename (with full path) of the form x_YYYYMMDD_HHMMSS.y'''
    import os
    baseName = os.path.basename(filePath).split('.')[0]
    pieces = baseName.split('_')
    dateStr = '_'.join(pieces[-2:])
    return timeStampFromString(dateStr)
    
def timeStampFromString(dateStr):
    '''Return the Unix epoch time from a string of the form YYYYMMDD_HHMMSS'''
    import time
    t = time.mktime(time.strptime(dateStr, '%Y%m%d_%H%M%S'))
    return t


def filesInDateRange(filePathPattern, startTime, endTime):
    '''Find all files matching the name pattern with a timestamp inside the interval specified by start and endTime.
    filePathPattern: Search pattern used by glob.glob
    startTime: Unix epoch time or string of the form YYYYMMDD_HHMMSS (interpreted as local time)
    endTime: Unix epoch time or string of the form YYYYMMDD_HHMMSS (interpreted as local time)
    '''
    if type(startTime) is str:
        startTime = timeStampFromString(startTime)
    if type(endTime) is str:
        endTime = timeStampFromString(endTime)
    import glob
    candidates = glob.glob(filePathPattern)
    good = []
    for candidate in candidates:
        t = timeStampFromPath(candidate)
        if startTime <= t and t <= endTime:
            good.append(candidate)
    return good

if __name__ == '__main__':
    result = filesInDateRange('D:\\Users\\Runs\\G4C\\IV\\TES2_SIV_RampT_*.h5', '20180110_180826', '20180111_143046')
    print(result)

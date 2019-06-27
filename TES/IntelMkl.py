# -*- coding: utf-8 -*-
"""
Interface to Intel Math Kernel Library for fast sin, cos, and sincos functions (and more to be added later)

Some conclusions:
On WISP3, single thread MKL sincos for float64 is about 5x faster than numpy.
For float32 it is faster yet by a factor of ~2.5. Numpy shows no improvement with float32
For numpy it makes no difference whether we do x=sin(a) or sin(a,x)
For MKL sincos is about 20% faster than sin,cos
Had to copy all DLL files from C:\Program Files (x86)\IntelSWTools\compilers_and_libraries_2017\windows\redist\ia32_win\mkl\
to the working directory to make the import work.
On Win32 MKL expects int32 for array size.
With doing the product, MKL gives a speedup of about 4x for double and 8x for single precision.
Created on Tue Dec 20 20:38:50 2016

@author: Felix Jaeckel <fxjaeckel@gmail.com>
"""

from numpy import sin,cos
import numpy as np
import ctypes

if ctypes.sizeof(ctypes.c_voidp) == 8: # 64-bit Python
    MKL_INT = ctypes.c_int64
    BITNESS = 64
else:
    MKL_INT = ctypes.c_int32
    BITNESS = 32
    
import sys
if sys.platform == 'win32':
    if BITNESS == 32:
        libPath = libFile = 'C:\\Program Files (x86)\\IntelSWTools\\compilers_and_libraries_2017\\windows\\redist\\ia32_win\\mkl\\'
    elif BITNESS == 64:
        libPath = libFile = 'C:\\Program Files (x86)\\IntelSWTools\\compilers_and_libraries_2017\\windows\\redist\\intel64_win\\mkl\\'
    libFile = 'mkl_rt.dll'
    mkl_rt = ctypes.CDLL(libFile)
else:
    import warning
    warning.warn('Unsupported platform:', sys.platform)


class ThreadingLayer:
    INTEL        = 0
    SEQUENTIAL   = 1
    PGI          = 2
    GNU          = 3
    TBB          = 4

mklSetThreadingLayer = mkl_rt.mkl_set_threading_layer; mklSetThreadingLayer.argtypes = [ctypes.c_int32]; mklSetThreadingLayer.restype=ctypes.c_int32

mklSetNumThreads = mkl_rt.MKL_Set_Num_Threads; mklSetNumThreads.argtypes = [MKL_INT]
mklGetMaxThreads = mkl_rt.MKL_Get_Max_Threads

_mklGetVersionString = mkl_rt.MKL_Get_Version_String; _mklGetVersionString.argtypes = [ctypes.c_char_p, ctypes.c_int]
_mklGetCpuClocks = mkl_rt.MKL_Get_Cpu_Clocks; _mklGetCpuClocks.argtypes = [ctypes.POINTER(ctypes.c_int64)];
mklGetCpuFrequency = mkl_rt.MKL_Get_Cpu_Frequency; mklGetCpuFrequency.restype = ctypes.c_double;
mklGetMaxCpuFrequency = mkl_rt.MKL_Get_Max_Cpu_Frequency; mklGetMaxCpuFrequency.restype = ctypes.c_double;
mklGetClocksFrequency = mkl_rt.MKL_Get_Clocks_Frequency; mklGetClocksFrequency.restype = ctypes.c_double;

#class Flag:
#    def __init__(self, value):
        

class VmlAccuracy:
    '''Defines accuracy settings for the Vector Math Library (VML)
    Use vmlSetMode() to set the accuracy globally.'''
    LA = 0x00000001
    '''Low accuracy'''
    HA = 0x00000002
    '''High accuracy'''
    EP = 0x00000003
    '''Enhanced performance (even lower accuracy)'''
    
class VmlErrorMode:
    '''Defines error mode settings for the Vector Math Library (VML)
    Use vmlSetMode() to set the error mode globally.'''
    IGNORE   = 0x00000100
    '''ignore errors'''
    ERRNO    = 0x00000200
    '''errno variable is set on error'''
    STDERR   = 0x00000400
    '''error description text is written to stderr on error'''
    EXCEPT   = 0x00000800
    '''exception is raised on error'''
    CALLBACK = 0x00001000
    '''user's error handler function is called on error'''
    DEFAULT  = ERRNO | CALLBACK | EXCEPT
    '''errno variable is set, exceptions are raised and user's error handler is called on error'''
    
class VmlFtzDaz:
    FTZDAZ_ON  = 0x00280000
    '''FTZ & DAZ MXCSR mode enabled for faster (sub)denormal values processing'''
    FTZDAZ_OFF = 0x00140000
    '''FTZ & DAZ MXCSR mode disabled for accurate (sub)denormal values processing'''

class VmlErrorStatus:
    OK              =    0
    BADSIZE         =   -1
    '''array dimension is not positive'''
    BADMEM          =   -2
    '''invalid pointer passed'''
    ERRDOM          =    1
    '''at least one of arguments is out of function domain'''
    SING            =    2
    '''at least one of arguments caused singularity'''
    OVERFLOW        =    3
    '''at least one of arguments caused overflow'''
    UNDERFLOW       =    4
    '''at least one of arguments caused underflow'''
    ACCURACYWARNING = 1000
    '''function doesn't support set accuracy mode, lower accuracy mode was used instead'''

vmlSetMode = mkl_rt.vmlSetMode; vmlSetMode.argtypes=[ctypes.c_uint]; vmlSetMode.restype=ctypes.c_uint

mklSecondsFloat =  mkl_rt.second; mklSecondsFloat.restype=ctypes.c_float; mklSecondsFloat.__doc__ = "Return the number of seconds that have elapsed at a float32 value"

mklSecondsDouble = mkl_rt.dsecnd; mklSecondsFloat.restype=ctypes.c_double; mklSecondsDouble.__doc__ = "Return the number of seconds that have elapsed at a float64 value"

def mklGetVersionString():
    buf = ctypes.create_string_buffer('', size=255)
    _mklGetVersionString(buf, len(buf))
    return buf.value
    
def mklGetCpuClocks():
    '''The mkl_get_cpu_clocks function returns the elapsed CPU clocks.
    This may be useful when timing short intervals with high resolution.
    The mkl_get_cpu_clocks function is also applied in pairs like second/dsecnd.
    Note that out-of-order code execution on IA-32 or Intel® 64 architecture
    processors may disturb the exact elapsed CPU clocks value a little bit,
    which may be important while measuring extremely short time intervals. '''
    clocks = ctypes.c_int64(0)
    _mklGetCpuClocks(ctypes.byref(clocks))
    return clocks.value

#def mklGetCpuFrequency():
#    f = ctypes.c_double(0)
#    ret=_mklGetCpuFrequency(ctypes.byref(f))
#    print "Returns", ret
#    return f.value

FloatArrayIn = np.ctypeslib.ndpointer(dtype=np.float32)
FloatArrayOut = np.ctypeslib.ndpointer(dtype=np.float32, flags='WRITEABLE')
DoubleArrayIn = np.ctypeslib.ndpointer(dtype=np.float64)
DoubleArrayOut = np.ctypeslib.ndpointer(dtype=np.float64, flags='WRITEABLE')

mulDouble = mkl_rt.vdMul
mulDouble.argtypes = [MKL_INT, DoubleArrayIn, DoubleArrayIn, DoubleArrayOut]
mulDouble.restype = None

mulFloat = mkl_rt.vsMul
mulFloat.argtypes = [MKL_INT, FloatArrayIn, FloatArrayIn, FloatArrayOut]
mulFloat.restype = None

sinCosDouble = mkl_rt.vdSinCos
sinCosDouble.argtypes = [MKL_INT, DoubleArrayIn, DoubleArrayOut, DoubleArrayOut]
sinCosDouble.restype = None

sinCosFloat = mkl_rt.vsSinCos
sinCosFloat.argtypes = [MKL_INT, FloatArrayIn, FloatArrayOut, FloatArrayOut]
sinCosFloat.restype = None

sinDouble = mkl_rt.vdSin
sinDouble.argtypes = [MKL_INT, DoubleArrayIn, DoubleArrayOut]
sinDouble.restype = None

sinFloat = mkl_rt.vsSin
sinFloat.argtypes = [MKL_INT, FloatArrayIn, FloatArrayOut]
sinFloat.restype = None

cosDouble = mkl_rt.vdCos
cosDouble.argtypes = [MKL_INT, DoubleArrayIn, DoubleArrayOut]
cosDouble.restype = None

cosFloat = mkl_rt.vsCos
cosFloat.argtypes = [MKL_INT, FloatArrayIn, FloatArrayOut]
cosFloat.restype = None

scalFloat = mkl_rt.cblas_sscal
scalFloat.argtypes = [MKL_INT, ctypes.c_float, FloatArrayOut, MKL_INT]
scalFloat.restype = None

scalDouble = mkl_rt.cblas_dscal
scalDouble.argtypes = [MKL_INT, ctypes.c_double, DoubleArrayOut, MKL_INT]
scalDouble.restype = None

# y += a*x "ax+y"
axpyFloat = mkl_rt.cblas_saxpy
#saxpy (const MKL_INT n, const float a, const float *x, const MKL_INT incx, float *y, const MKL_INT incy)
axpyFloat.argtypes=[MKL_INT, ctypes.c_float, FloatArrayIn, MKL_INT, FloatArrayOut, MKL_INT]
axpyFloat.restype = None

axpyDouble = mkl_rt.cblas_daxpy
#saxpy (const MKL_INT n, const float a, const float *x, const MKL_INT incx, float *y, const MKL_INT incy)
axpyDouble.argtypes=[MKL_INT, ctypes.c_double, DoubleArrayIn, MKL_INT, DoubleArrayOut, MKL_INT]
axpyDouble.restype = None

if __name__ == '__main__':
    repeats = 10
    cycles = 100
    length = 100000

    import time
    #mklSetThreadingLayer(ThreadingLayer.INTEL) # This causes access violation
    print "MKL version:", mklGetVersionString()
    print "MKL default max threads:", mklGetMaxThreads()
    print "CPU frequency:", mklGetCpuFrequency(), 'GHz'
    print "Max CPU frequency:", mklGetMaxCpuFrequency(), 'GHz'
    print "TSC Clocks frequency:", mklGetClocksFrequency(), 'GHz'
    
    mklSetNumThreads(1)
    print "MKL new max threads:", mklGetMaxThreads()

    oldMode = vmlSetMode(VmlAccuracy.LA | VmlErrorMode.IGNORE)
    print "Old mode:",
    if oldMode & VmlAccuracy.HA:
        print "high accuracy"
    elif oldMode & VmlAccuracy.LA:
        print "low accuracy"
    elif oldMode & VmlAccuracy.EP:
        print "enhanced performance"
    
    a = np.random.normal(size=length); out_sin = np.empty_like(a); out_cos = np.empty_like(a)
    x = np.empty_like(a); y = np.empty_like(a);

    
    for i in range(repeats):
        tmkl1 = mklSecondsFloat()
        for j in range(cycles):
            scalDouble(a.size, 1.05, a, 1)
        tmkl2 = mklSecondsFloat()
        print "MKL scal", tmkl2-tmkl1
    
    for i in range(repeats):
        tmkl1 = mklSecondsFloat()
        for j in range(cycles):
            a = 1.05 * a
        tmkl2 = mklSecondsFloat()
        print "np *=", tmkl2-tmkl1

    for i in range(repeats):
        tmkl1 = mklSecondsFloat()
        for j in range(cycles):
            axpyDouble(a.size, 0.2, x, 1, y, 1)
        tmkl2 = mklSecondsFloat()
        print "MKL axpy", tmkl2-tmkl1

    for i in range(repeats):
        tmkl1 = mklSecondsFloat()
        for j in range(cycles):
            y += 0.2*x
        tmkl2 = mklSecondsFloat()
        print "np axpy", tmkl2-tmkl1
    
    for i in range(repeats):
        t1=time.time()
        tmkl1 = mklSecondsFloat()
        clks1 = mklGetCpuClocks()
        for j in range(cycles):
            sinDouble(a.size, a, out_sin)
            mulDouble(a.size, a, out_sin, x)
            cosDouble(a.size, a, out_cos)
            mulDouble(a.size, a, out_cos, y)
        clks2 = mklGetCpuClocks()
        tmkl2 = mklSecondsFloat()
        t2=time.time()
        print "MKL sin,cos", t2-t1, 'CLKs:', clks2-clks1, 'MKL seconds:', tmkl2-tmkl1
    
    for i in range(repeats):
        t1=time.time()
        for j in range(cycles):
            sinCosDouble(a.size, a, out_sin, out_cos)
            mulDouble(a.size, a, out_sin, x)
            mulDouble(a.size, a, out_cos, y)
        t2=time.time()
        print "MKL sincos", t2-t1
    
    for i in range(repeats):
        t1=time.time()
        for j in range(cycles):
            sinCosDouble(a.size, a, out_sin, out_cos)
            x,y = out_sin*a, out_cos*a
        t2=time.time()
        print "MKL sincos, numpy product", t2-t1
        
    for i in range(repeats):
        t1=time.time()
        for j in range(cycles):
            #x,y = sin(a), cos(a)
            x,y = a*sin(a),a*cos(a)
        t2=time.time()
        print "numpy sin,cos", t2-t1
    
    #for i in range(10):
    #    t1=time.time()
    #    sin(a, out_sin); cos(a, out_cos)
    #    t2=time.time()
    #    print "numpy ops sin,cos", t2-t1
    
    print "Now float32"
    a = np.asarray(np.random.normal(size=length),dtype=np.float32); out_sin = np.empty_like(a); out_cos = np.empty_like(a)
    x = np.empty_like(a); y = np.empty_like(a);

    for i in range(repeats):
        tmkl1 = mklSecondsFloat()
        for j in range(cycles):
            axpyFloat(a.size, 0.2, x, 1, y, 1)
        tmkl2 = mklSecondsFloat()
        print "MKL axpy float32", tmkl2-tmkl1

    for i in range(repeats):
        tmkl1 = mklSecondsFloat()
        for j in range(cycles):
            y += 0.2*x
        tmkl2 = mklSecondsFloat()
        print "np axpy float32", tmkl2-tmkl1

    for i in range(repeats):
        t1=time.time()
        for j in range(cycles):
            sinCosFloat(a.size, a, out_sin, out_cos)
            mulFloat(a.size, a, out_sin, x)
            mulFloat(a.size, a, out_cos, y)
        t2=time.time()
        print "MKL sincos float32", t2-t1
        
    for i in range(repeats):
        t1=time.time()
        for j in range(cycles):
            #x,y = sin(a), cos(a)
            x,y = a*sin(a),a*cos(a)
        t2=time.time()
        print "numpy sin,cos", t2-t1

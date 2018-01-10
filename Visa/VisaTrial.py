'''
Created on Jan 8, 2018

@author: cvamb
'''

import visa

if __name__ == '__main__':
    rm = visa.ResourceManager()
    print(rm.list_resources())
    my_instrument = rm.open_resource('GPIB0::8::INSTR')
    print(my_instrument)
#    my_instrument.timeout=8000
    my_instrument.read_termination='\n'
    my_instrument.write_termination='\n'
    print(my_instrument.timeout)
    print(my_instrument.query('*IDN?'))
#    print(my_instrument.write('*IDN?'))
    print(my_instrument.read_raw())
    
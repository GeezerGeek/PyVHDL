#------------------------------------------------------------------------------
#
#   builtin_op.py - 1/28/16
#
#   Support for VHDL builtin operations
#
#------------------------------------------------------------------------------

import logging, dis
# from design_parser import Parsing_Exception

#------------------------------------------------------------------------------
#
# A function called from bytecode to process VHDL builtin binary Operations

def binary_op(L, R, op):
    
    if op == 'EQUAL':
        return L.getVal() == R.getVal()
    
    if op == 'OR':
        return L or R
    
    else:
        logging.warning('*** BINARY op  %s not implemented yet' % op)
        return False


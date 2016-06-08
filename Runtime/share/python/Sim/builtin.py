#------------------------------------------------------------------------------
#
#   builtin_op.py - 1/2/16
#
#   Support for VHDL builtin operations
#
#------------------------------------------------------------------------------

import logging, dis

#------------------------------------------------------------------------------
#
# A function called from bytecode to process VHDL builtin binary Operations

def binary_op(L, R, op):
    
    if op == 'EQUAL':
        return str(L) == str(R)

#------------------------------------------------------------------------------
#
# std.py - 1/23/16
#
# Python implementation of VHDL standard logic types
#
#------------------------------------------------------------------------------

import logging

from array import *
from types import StringType

#------------------------------------------------------------------------------

# Character to enumeration id
encode = {'U':0, 'X':1, '0':2, '1':3, 'Z':4, 'W':5, 'L':6, 'H':7, '-':8,
          'u':0, 'x':1, 'z':4, 'w':5, 'l':6, 'h':7
}

encode_table = encode

def encoder(c):
    return encode[c]

# Enumeration id to character
decode = 'UX01ZWLH-'

def decoder(c):
    return decode[c]
    

decode_table = decode

# Logical function look-up tables

and_table = (
    (0, 0, 2, 0, 0, 0, 2, 0, 0),
    (0, 1, 2, 1, 1, 1, 2, 1, 1),
    (2, 2, 2, 2, 2, 2, 2, 2, 2),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 2, 1, 1, 1, 2, 1, 1),
    (0, 1, 2, 1, 1, 1, 2, 1, 1),
    (2, 2, 2, 2, 2, 2, 2, 2, 2),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 2, 1, 1, 1, 2, 1, 1) 
)

or_table = (
    (0, 0, 0, 3, 0, 0, 0, 3, 0),
    (0, 1, 1, 3, 1, 1, 1, 3, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (3, 3, 3, 3, 3, 3, 3, 3, 3),
    (0, 1, 1, 3, 1, 1, 1, 3, 1),
    (0, 1, 1, 3, 1, 1, 1, 3, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (3, 3, 3, 3, 3, 3, 3, 3, 3),
    (0, 1, 1, 3, 1, 1, 1, 3, 1) 
)

xor_table = (
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 3, 2, 1, 1, 3, 2, 1),
    (0, 1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 2, 3, 1, 1, 2, 3, 1),
    (0, 1, 3, 2, 1, 1, 3, 2, 1),
    (0, 1, 1, 1, 1, 1, 1, 1, 1) 
)


# Convert encoded StdLogic value to add_table index
add_table_index = (2,2,0,1,2,2,0,1,2)

# Table for addition: add_table[a][b][c] returns [sum, carry] 
add_table = (
    (               # A = 0
        (               # B = 0
            ([2,2]),        # C = 0
            ([3,2]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([3,2]),        # C = 0
            ([2,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
    (               # A = 1
        (               # B = 0
            ([3,2]),        # C = 0
            ([2,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([2,3]),        # C = 0
            ([3,3]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
    (               # A = X
        (               # B = 0
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = 1
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        ),
        (               # B = X
            ([1,1]),        # C = 0
            ([1,1]),        # C = 1
            ([1,1])         # C = X
        )
    ),
)


def sl_sum(a, b, c):
    return add_table[add_table_index[a]][add_table_index[b]][add_table_index[c]]

sum_table = sl_sum

not_table = (0, 1, 3, 2, 1, 1, 3, 2, 1)

# Convert 9-level logic to 4-level logic for VCD dump

to_x01z = 'xx01zx01x'

X01Z_table = to_x01z 
    
#------------------------------------------------------------------------------
#
# Functions for the unified interface for StdLogic, StdLogicVector, SLVRange 

def unary_op(table, a):
    # encode, decode, to_X01Z, not        
    return [table[x] for x in a]

#----

def binary_op(table, a, b):       
    return [table[x][y] for x,y in zip(a,b)]

#----

def arith_op(table, a, b):
    
    carry = encode['0']
    result = []
    for i in range(len(a)):
        q,carry = table(a[i], b[i], carry)
        result.append(q)
    
    return result

#------------------------------------------------------------------------------
#
# Superclass to implement common operations of unified interface objects 
# Inherited by StdLogic, StdLogicVector, SLVRange
#
# Note that for VHDL simulation, these are now functions in std_logic_1164.py
# These methods are still used by PyModule processes!

class Operations(object):
    
    __slots__ = ('And', 'Or', 'Nor', 'Xor', 'Not', 'Add', 'Concat', 'Equal',
                 'sim', 'current', 'last', 'waiting', 'vcd_mgr', 'vcd_nodes',
                 )
    
    def And(self, other):        
        return self.new().setVal([and_table[x][y] for x,y in zip(self.getVal(), other.getVal())])       
    
    #----
    
    def Or(self, other):
        return self.new().setVal([or_table[x][y] for x,y in zip(self.getVal(), other.getVal())])       
    
    #----
    
    def Xor(self, other):
        return self.new().setVal([xor_table[x][y] for x,y in zip(self.getVal(), other.getVal())])       
    
    #----
    
    def Not(self):
        return self.new().setVal([not_table[x] for x in self.getVal()])       
    
    #----
    
    def Nor(self):
        temp = self.new().setVal([or_table[x][y] for x,y in zip(self.getVal(), other.getVal())])       
        return self.new().setVal([not_table[x] for x in temp.getVal()])       
    
    #----
    
    def Add(self, other):
        result = self.new()
        result.setVal(arith_op(sum_table, self.getVal(), other.getVal()))
        return result
    
    #----
    
    def NotImplemented(self, other):
        print '!!! Sub & Concat operation not implemented'
        raise Exception
    
    #----
    
    def Concat(self, other):
        return StdLogicVector([str(len(self)+len(other)-1), 'DOWNTO', '0']).setVal(other.getVal() + self.getVal())

    #----
    
    def Equal(self, other):            
        return Bool(other.getVal() == self.getVal())

    #----
    
    def NEqual(self, other):            
        return Bool(other.getVal() != self.getVal())

#------------------------------------------------------------------------------

class StdLogic(Operations):

    __slots__ = ('name', 'spec', '_val', 'sid', 'inst', 'current', 'sim', '_min',
                 '_literal_to_Std', '__len__', 'first', 'getVal', 'setVal', '__getstate__',
                 'new', 'rising_op', '__le__', 'setValue', 'is_equal', 'last', '__repr__',
                 'waiting', 'vcd_mgr', 'vcd_nodes', 'initialize', 'updateValue',
                 '__setstate__', 'is_variable', 'evt_cycle', 'not_rising_op'
                )

    def __init__(self, initializer='U'):
    
        Operations.__init__(self)
        
        self._val  = self._literal_to_Std(initializer)
        self._min  = 0
                
        self.name  = '??'     # set by DesignParser
        self.spec  = []     # set by DesignParser
        self.inst  = None   # set by DesignParser
        
        self.sid         = -1
        
        self.is_variable = False
        
        self.evt_cycle   = -1

    #----
        
    def initialize(self, sim):
               
        self.sim        = sim
         
        self.current    = [self._val, 0.0]
        self.last       = [self._val, 0.0]        
        self.waiting    = set()
        self.evt_cycle  = -1
        
#         # VCD attributes
        self.vcd_mgr  = None 
        self.vcd_nodes    = []
        
    #----
    
    def updateValue(self, other, cycle, time):
                                
        if str(other) != str(self):
            # Value has changed
            try:
                self._val = other.getVal()[0]                
            except AttributeError:
                self._val = encode[str(other)]
                
                
            # Process transitions for VDC file
                
            if not self.is_variable:
                try:
                    if self.vcd_mgr:
                        # This would probably be faster with a single call to vcd_mgr
                        for node in self.vcd_nodes:
                            self.vcd_mgr.VCD_transition(self, node, time)
                except AttributeError:
                    
                    print '@@@ No vcd_mgr for >%s< @ %0.3f' % (self.name, time)
                    print '@@@   self.spec: %s' % self.spec                    
                    raise AttributeError

            
            self.last = self.current
            self.current = (decode[self._val], time)
            self.evt_cycle = cycle

            # Return set of waiting VMs & processes
            return self.waiting
            
        # Value hasn't changed, return empty waiting set
        return set()
        
    #----
           
    def _literal_to_Std(self, literal):

        if isinstance(literal, StringType):
            try:
                return encode[literal]
            except KeyError:
                logging.error('Non-standard value in  _literal_to_Std(); %s' % literal)
                raise ValueError, '%s is not a StdLogic value' % literal
    
        elif literal in [1, 0]:
            return encode[str(literal)]
    
        else:
            raise ValueError, '%s %s is not a StdLogic value' % (literal.__class__, literal)

    #----
    #
    # Methods to implement unified interface
   
    def __len__(self):
        return 1
    
    #----
    
    def first(self):
        return 0
    
    #----
    
    def getVal(self):         
        return [self._val]
    
    #----
    
    def setVal(self, val):
        self._val = val[0]        
        return self
        
    #----
    
    def new(self):
        result = StdLogic()
        return result    
   
    #----
    
    def event_op(self):
        raise Exception
        return Bool(self.current[1] == self.sim.time)
    
    #----
    
    def rising_op(self):
                
        if self.current[0] != '1':
            return False        
        if self.last[0] == '1':
            return False
        
        return self.current[1] == self.sim.time
    
    #----
    
    def not_rising_op(self):
                
        if self.current[0] != '1':
            return True 
               
        if self.evt_cycle != self.sim.current_cycle:
            return True
         
        return self.current[1] != self.sim.time
               
    #--------------------------------------------------------------------------
    #
    # Used by zcode & bytecode for concurrent assignments
    
    def setValue(self, operand):
        
        try:
            self.setVal(operand.getVal())
        except AttributeError:
            self._val = self._literal_to_Std(str(operand))
                               
    #--------------------------------------------------------------------------
    #
    # Used by Python bytecode assembler for LOAD_CONST

    def is_equal(self, other):
        
        if not isinstance(other, StdLogic):
            return False
        
        if other.spec != self.spec:
            return False
        
        return self._val == other._val
                        
    #----
    #            
    # representation 
    
    def __str__(self):
        return decode[self._val]
    
    def VCD_str(self):
        return to_x01z[self._val]
    
    def __repr__(self):
        return "%s: StdLogic('%s')" % (self.name, decode[self._val])
    
    #----
    #
    # Persistence
        
    def __getstate__(self):
        result = {}
        result['_val']        = self._val                
        result['name']        = self.name
        result['spec']        = self.spec

        result['sid']         = self.sid
        result['is_variable'] = self.is_variable
        
        if self.name == '':
            print '@@@ getstate: %s' % result
            print '@@@ getstate class: %s' % self.__class__
        
        return result
    
    #----
    
    def __setstate__(self, dict):
         
        self._val        = dict['_val']                
        self.name        = dict['name']
        self.spec        = dict['spec']
        self.sid         = dict['sid']
        self.is_variable = dict['is_variable']
        
        self.current    = [self._val, 0.0]
        self.last       = [self._val, 0.0]        
        self.waiting    = set()

#------------------------------------------------------------------------------

class StdLogicVector(Operations):
       
    # internal representation (self._val) is a list of ecoded indices with 
    # the LSB in _val[0]
    
    __slots__ = ('_min', '_max', '_dir', '_val', 'name', 'inst', 'vcd_nodes', 'spec',
                 'const', 'enc_val', 'sid', 'current', 'last', '__le__', 'first',
                 'getVal', 'setVal', 'new', 'int2SLV', 'add_int_op', 'setValue',
                 'is_equal', '__str__', '__repr__', 'VCD_str', 'updateValue',
                 'waiting', 'vcd_mgr', 'initialize', '__getstate__', '__setstate__',
                 'is_variable', 'evt_cycle'
                )
    
    #----

    def __init__(self, spec):
                
        # For processing events of VCD enabled nodes
        self.vcd_nodes = []

        # Process rng specification
        l,d,r = spec
        if d == 'TO':
            self._dir = 1
            self._min = int(l)
            self._max = int(r)
        else:
            self._dir = -1
            self._min = int(r)
            self._max = int(l)
        
        self.name  = ''     # set by DesignParser
        self.spec  = []     # set by DesignParser
        self.inst  = None     # set by DesignParser
             
        # Initialize _val as undefined
        self._val = [encode['u']] * (self._max - self._min + 1)
        
        self.sid        = -1
        
        self.is_variable = False
                
    #----
        
    def initialize(self, sim):
                
        self.sim        = sim                
        self.current    = [self._val, 0.0]
        self.last       = [self._val, 0.0]        
        self.waiting    = set()
        
        # VCD attributes
        self.vcd_mgr  = None 
        self.vcd_nodes    = []
        

    #--------------------------------------------------------------------------
    #
    # Methods to implement unified interface
   
    def __len__(self):
        return self._max - self._min + 1
    
    #----
    
    def first(self):
        return self._min
    
    #----
    
    def getVal(self):
        return self._val
    
    #----
    
    def setVal(self, val):
                
        # * * * VERY IMPORTANT * * *
        # The code below insures that assignment COPIES the value
        # rather than creating a reference to the value
        
        self._val = val[:]
        return self
        
    #----
        
    def new(self):
        # Return a StdLogicVector object with the same length
        slv = StdLogicVector(['%d' % (len(self)-1), 'DOWNTO', '0'])
        slv.name = 'new'
        return slv 
                
    #--------------------------------------------------------------------------
    
    def int2SLV(self, i):

        # Convert integer value i to std_logic_vector string
        s = bin(i)[2:]
        s = '0' * (len(self) - len(s)) + s

        if self._dir < 0:
            # Reverse order of bits
            s = s[::-1]
            
        return [encode[c] for c in s]

    #----
    #
    # <= used to assign a value
    
    def __le__(self, value):
        
        if isinstance(value, StringType):
            
            value = value.replace('"', '')
            
            if value.startswith(('0x', '0X')):
                # Process hexadecimal value
                self._val = self.int2SLV(int(value, 16))
                return
            
            else:
                # Process std_logic_vector string value                
                if self._dir < 0:
                    v = reversed(value)
                else:
                    v = valu
                    
                exp_len = self._max - self._min + 1
                if len(value) == exp_len:
                    
                    try:
                        self.enc_val = [encode[c] for c in v]
                        
                    except KeyError:
                        raise ValueError, '%s contains a bogus StdLogic value' % v
                else:
                    args = (value, exp_len, len(value))
                    raise ValueError, '%s, Expect std_logic_vector literal of length %d not %d' % args 
                
            self._val = self.enc_val
        
        elif type(value) == type(1):
            self._val = self.int2SLV(value)
            
        else:
            logging.error('StdLogicVector.__le__ processing ????')

    #----
        
    def updateValue(self, other, cycle, time):
                
        try:
            o = other.getVal()
            if o != self.getVal():                
                self.setVal(other.getVal()[:])
            else:
                # Value has not changed
                return set()
                
        except AttributeError:
            
            if str(other) != str(self):
                 self.__le__(other)
            else:
                # Value has not changed
                return set()

        # Process transitions for VDC file
            
        if not self.is_variable:
            if self.vcd_mgr:
                # This would probably be faster with a single call to vcd_mgr
                for node in self.vcd_nodes:
                    self.vcd_mgr.VCD_transition(self, node, time)
            
        self.last = self.current
        self.current = (str(self), time)
                                         
        # Return set of waiting VMs & processes
        return self.waiting
        
    #----
     
    def add_int_op(self, other):

        result = self.new()
        result.setVal(arith_op(sum_table, self.getVal(), self.int2SLV(other)))
        return result 
                    
    #--------------------------------------------------------------------------
    #
    # Used by Python bytecode assembler for LOAD_CONST

    def is_equal(self, other):
        
        if not isinstance(other, StdLogicVector):
            return False
        
        if other.spec != self.spec:
            return False
        
        return self._val == other._val

    #---- representation 
    
    def __str__(self):
         
        if self._dir < 0:
            return ''.join(map(decoder, self._val))[::-1]
            
        return ''.join(map(decoder, self._val))
    
    #---------------------------
    #
    # return a string with LSB at index 0
    
    def VCD_str(self):
        s = '' 
        for c in self._val:
            s += to_x01z[c]            
        return s
    
    #----

    def __repr__(self):
        if self._dir < 0:
            spec = '%d DOWNTO %d' % (self._max, self._min)
        else:
            spec = '%d TO %d' % (self._min, self._max)
            
        return '%s: StdLogicVector(%s)=%s' % (self.name, spec, self)
    
    #----
    #
    # Persistence
        
    def __getstate__(self):
        result = {}
        result['_val']  = self._val                
        result['name']  = self.name
        result['spec']  = self.spec
        result['sid']   = self.sid
        
        result['_dir']  = self._dir
        result['_min']  = self._min
        result['_max']  = self._max

        result['is_variable']  = self.is_variable
        
        return result
    
    #----
    
    def __setstate__(self, dict):
         
        self._val  = dict['_val']                
        self.name  = dict['name']
        self.spec  = dict['spec']
        self.sid   = dict['sid']

        self._dir  = dict['_dir']
        self._min  = dict['_min']
        self._max  = dict['_max']
        
        self.is_variable = dict['is_variable']       
        
        self.current    = [self._val, 0.0]
        self.last       = [self._val, 0.0]        
        self.waiting    = set()

#------------------------------------------------------------------------------
#
# A function used by bytecode, returning an SLVRange instance

def SLVRange_bc(args):    
    slv, left, asc, right = args
    return SLVRange(slv, asc, left, right)

#------------------------------------------------------------------------------
#
# A function used only by IndexOp, returning an SLVRange
# object with a length of 1.

def SLVRange_bc2(slv, index):    
    return SLVRange(slv, False, index, index)    

#------------------------------------------------------------------------------
#
# A function used only by AggregateOp, returning a literal string
# of width appropriate for slv arg, initialized with the 1 char. string ini

def SLVRange_bc3(ini, slv):
    width = (slv._max - slv._min) + 1
    # Return a string with the correct width
         
    return ini * width

#------------------------------------------------------------------------------
#
# A wrapper of StdLogicVector objects that selects a sub-range

class SLVRange(Operations):
    
    __slots__ = ('__init__', '_min', '_max', '_dir', 'slv', 'first', 'getVal',
                 'setVal', 'new', 'updateValue', '__len__', 'name', 'inst',
                 'val_left', 'val_right', 'initialize', 'rng_node', 'rng_name',
                 'rng_id', 'tid', 'spec', 'vcd_nodes', 'VCD_str', 'vcd_mgr',
                 'is_variable', '__str__', 'evt_cycle'
                )
    
    def __init__(self, slv, asc, left, right, rng_node=None):

        if asc:
            # n TO m
            self._dir = 1
            self._min = left
            self._max = right
        else: 
            # n DOWNTO m
            self._dir = -1
            self._min = right
            self._max = left
            
        # The SLV that is wrapped
        self.slv = slv       
        
        self.val_left  = self._min - slv.first()
        self.val_right = self._max + 1 - slv.first()

        self.rng_node = rng_node        
        if self.rng_node != None:
            self.spec = rng_node.sig_spec
            self.rng_name = rng_node.Name
        else:
            self.rng_name = ''
                      
    #----
        
    # Noop for SLVRange
    def initialize(self, sim):
        self.waiting    = set()
                
    #----
    
    def  setValue(self, operand):            
        self.setVal(operand.getVal())

    #----
        
    def updateValue(self, other, cycle, time):
         
        try:
            if other.getVal() != self.getVal():
                self.setVal(other.getVal())
            else:
                # Value has not changed
                return set()
                
        except AttributeError:
            # self or other is a string, int, etc            
            if str(other) != str(self):
                if isinstance(other, str):
                    self.setVal([encode[c] for c in other])

            else:
                # Value has not changed
                return set()
                
        # Process transitions for VDC file
            
        if self.vcd_mgr:
            # This would probably be faster with a single call to vcd_mgr
            for node in self.vcd_nodes:
                self.vcd_mgr.VCD_transition(self, node, time)
        
        self.last = self.current
        self.current = (str(self), time)
                                         
        # Return set of waiting VMs & processes
        return self.waiting
                                  
    #----
    #
    # Methods to implement unified interface
   
    def __len__(self):
        return self._max - self._min + 1
    
    #----
    
    def first(self):
        return self._min
    
    #----
    
    def getVal(self):
        return self.slv.getVal()[ self.val_left : self.val_right]
    
    #----
    
    def setVal(self, val):
        slv = self.slv
        self.slv._val[self.val_left : self.val_right] = val
        return self
        
    #----
        
    def new(self):
        # Return a StdLogicVector object with the same length
        return StdLogicVector(['%d' % (len(self)-1), 'DOWNTO', '0'])

    #----
    
    @property
    def name(self):
        # getter property method for self.name
        return self.slv.name
        
    #----
    
    @property
    def vcd_trace(self):
        # getter property method for self.vcd_trace
        return self.slv.vcd_trace
    #----

    @vcd_trace.setter
    def vcd_trace(self, value):
        # Setter property method for self.vcd_trace
        self.slv.vcd_trace = value
        
    #----
    
    @property
    def vcd_nodes(self):
        # getter property method for self.vcd_nodes
        return self.slv.vcd_nodes
        
    #----
    
    @property    
    def current(self):
        # getter property method for self.current
        return self.slv.current

    #----

    @current.setter
    def current(self, value):
        # Setter property method for self.current
        self.slv.current = value        
                
    #----
    
    @property
    def last(self):
        # getter property method for self.last
        return self.slv.last

    #----

    @last.setter
    def last(self, value):
        # Setter property method for self.current
        self.slv.last = value
               
    #----
    
    @property
    def waiting(self):
        # getter property method for self.waiting
        return self.slv.waiting   

    #----

    @waiting.setter
    def waiting(self, value):
        # Setter property method for self.current
        self.slv.waiting = value
               
    #----
    
    @property
    def sim(self):
        # getter property method for self.sim
        return self.slv.sim   
               
    #----
    
    @property
    def sid(self):
        # getter property method for self.sid
        if self.rng_node != None:
            return self.rng_node.sid
        else:
            return self.slv.sid
       
    #----
    
    @property
    def vcd_mgr(self):
        # getter property method for self.svl_manager 
        return self.slv.vcd_mgr
       
    #----
    
    @property
    def VCD_str(self):
        # getter property method for self.VCD_str
        return self.slv.VCD_STR()

    #----
    
    @property
    def is_variable(self):
        # getter property method for self.is_variable
        return self.slv.is_variable
    #----
    
    def __str__(self):
        if self._dir < 0:
            return ''.join(map(decoder, self.getVal()))[::-1]            
        return ''.join(map(decoder, self.getVal()))
        
    #----
    #
    # Persistence
        
    def __getstate__(self):
        result = {}
        result['name']  = self.rng_node.name
        result['spec']  = [self._dir, self._min, self._max] 
        result['sid']   = self.sid
        result['slv']   = self.rng_node.target.signal
        result['tid']   = self.rng_node.target.signal.sid
        
        return result
    
    #----
    
    def __setstate__(self, dict):
                         
        self.rng_name = dict['name']
        self.rng_id   = dict['sid']
        self.tid      = dict['tid']
        self.slv      = dict['slv']
        
        self._dir, self._min, self._max = dict['spec']
        self.val_left  = self._min - self.slv.first()
        self.val_right = self._max + 1 - self.slv.first()
        
        self.is_variable = False
         
        self.current  = [self.getVal(), 0.0]
        self.last     = [self.getVal(), 0.0]        
        self.waiting  = set()
       
#------------------------------------------------------------------------------
#
# This class is only used to allow method_map look-ups to succeed. Integer
# operations become native Python operations

class Integer(object):
 
    def __init__(self, val=0):
        self.val = int(val)
 
    def __repr__(self):
        return 'Integer(%d)' % self.val
 
    __str__ = __repr__
 
    def add_op(self, other):
        raise Exception
 
    def sub_op(self, other):
        raise Exception
     
    def gt_op(self, other):
        raise Exception
       
#------------------------------------------------------------------------------
#
# A BOOL object 

class Bool(int):

    def __init__(self, val=0):
        if val:
            self.val = True
        else:
            self.val = False

    def __repr__(self):
        if self.val:
            return "True"
        else:
            return "False"

    __str__ = __repr__

    def and_op(self, other):
        return Bool(self.val and other.val)

    def or_op(self, other):
        return Bool(self.val or other.val)

    def not_op(self):
            return Bool( not self.val)
       
#------------------------------------------------------------------------------
#
# Map a CALL signature to (operand_count, method)
#
# *** Replace this with something that references library functions *** 

method_map = {
    '"AND"(CONSTANT L : STD_ULOGIC, CONSTANT R : STD_ULOGIC) RETURN UX01'  : (2, StdLogic.And),
    '"OR"(CONSTANT L : STD_ULOGIC, CONSTANT R : STD_ULOGIC) RETURN UX01'   : (2, StdLogic.Or),
    '"XOR"(CONSTANT L : STD_ULOGIC, CONSTANT R : STD_ULOGIC) RETURN UX01'  : (2, StdLogic.Xor),
    '"NOT"(CONSTANT L : STD_ULOGIC) RETURN UX01'                           : (1, StdLogic.Not),
    '"="(CONSTANT A : STD_ULOGIC, CONSTANT B : STD_ULOGIC) RETURN BOOLEAN' : (2, StdLogic.Equal),
    
    'RISING_EDGE(SIGNAL S : STD_ULOGIC) RETURN BOOLEAN'                    : (1, StdLogic.rising_op),    

    '"NOT"(CONSTANT L : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR'                              : (1, StdLogicVector.Not),
    '"&"(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR' : (2, StdLogicVector.Concat),

    '"&"(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC) RETURN STD_LOGIC_VECTOR'        : (2, StdLogicVector.Concat),
    '"&"(CONSTANT A : STD_LOGIC, CONSTANT B : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR'        : (2, StdLogicVector.Concat),
    '"&"(CONSTANT A : STD_LOGIC, CONSTANT B : STD_LOGIC) RETURN STD_LOGIC_VECTOR'               : (2, StdLogicVector.NotImplemented),

    '"AND"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR': (2, StdLogicVector.And),
    '"OR"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR': (2, StdLogicVector.Or),
    '"NOR"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR' : (2, StdLogicVector.NotImplemented),
    '"+"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR' : (2, StdLogicVector.Add),
    '"="(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC_VECTOR) RETURN BOOLEAN'          : (2, StdLogicVector.Equal),
    '"="(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN BOOLEAN'          : (2, StdLogicVector.Equal),
    '"/="(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN BOOLEAN'         : (2, StdLogicVector.NEqual),
    '"/="(CONSTANT A : STD_LOGIC_VECTOR, CONSTANT B : STD_LOGIC_VECTOR) RETURN BOOLEAN'         : (2, StdLogicVector.NEqual),
    '"XOR"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR' : (2, StdLogicVector.Xor),

    '"-"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : STD_LOGIC_VECTOR) RETURN STD_LOGIC_VECTOR' : (2, StdLogicVector.NotImplemented),
    '"+"(CONSTANT L : STD_LOGIC_VECTOR, CONSTANT R : INTEGER) RETURN STD_LOGIC_VECTOR'          : (2, StdLogicVector.add_int_op),

    '"+"(CONSTANT A : INTEGER, CONSTANT B : INTEGER) RETURN INTEGER'        : (2, Integer.add_op),
    '"-"(CONSTANT A : INTEGER, CONSTANT B : INTEGER) RETURN INTEGER'        : (2, Integer.sub_op),
    '">"(CONSTANT A : INTEGER, CONSTANT B : INTEGER) RETURN BOOLEAN'        : (2, Integer.gt_op),
        
    '"AND"(CONSTANT A : BOOLEAN, CONSTANT B : BOOLEAN) RETURN BOOLEAN'      : (2, Bool.and_op),
    '"OR"(CONSTANT A : BOOLEAN, CONSTANT B : BOOLEAN) RETURN BOOLEAN'       : (2, Bool.or_op)
}

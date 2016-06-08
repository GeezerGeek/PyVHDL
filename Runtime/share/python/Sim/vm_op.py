#------------------------------------------------------------------------------
#
#   vm_op.py - 12/21/15
#
# Classes representing Code objects
#
#------------------------------------------------------------------------------

from std import StdLogic, StdLogicVector, SLVRange, Integer, Bool, encode 
from builtin_op import binary_op

from byteplay import Label

import operator
import logging

import sys
python_version = '.'.join(str(x) for x in sys.version_info[:2])

print 'python_version: %s' % '.'.join(str(x) for x in sys.version_info[:3])

#------------------------------------------------------------------------------
#
# Exception class for vm errors

class VM_Exception(Exception):
    pass


#------------------------------------------------------------------------------
    
class AliasOp(object):
    pass

#------------------------------------------------------------------------------

class AllocateOp(object):
    pass

#------------------------------------------------------------------------------

class AggregateOp(object):
    
    def __init__(self, line):
        
        self.label = line[0]
        self.args = {}
        
        s = ' '.join(line[2:])[1:-1]
        self.args  = dict([x.split('=') for x in s.replace('#', '').split(', ')])       
        spec  = self.args['RESTYPE'].split()
        self.width = abs(int(spec[1]) - int(spec[3])) + 1
                   
    #----
    
    def genBytecode(self, vm):
        
        bc = []       
        # convert tos to a string
        bc.append(('LOAD_GLOBAL', 'str'))
        bc.append(('ROT_TWO', None))           
        bc.append(('CALL_FUNCTION', 1))
        
        # TOS = '1'/'0'
        # NOS = SLVRange instance
        
        bc.append(('ROT_TWO', None))
        bc.append(('DUP_TOP', None))
        bc.append(('ROT_THREE', None))
        
        # TOS = SLVRange instance
        # NOS = initialization char.
        
        # width is now controlled by SLVRange instance
        bc.append(('LOAD_GLOBAL', 'SLVRange_bc3'))
        bc.append(('ROT_THREE', None))
        bc.append(('CALL_FUNCTION', 2))

        # TOS = initialization string
        # NOS = SLVRange instance

        return (int(self.label), bc)
    
    #----         
    
    def execute(self, vm):
        
        if self.args['HAVEOTHERS'] == 'TRUE':
            
            # Pop initializer
            ini = vm.stack.pop()
            value = str(ini) * self.width
            vm.stack.append(value)
                        
            vm.pc += 1
            return False
            
        else:
            logging.info('In AggregateOp: *** NOT IMPLEMENTED YET')
        
    #----
    
    def __str__(self):
        return '%s AGGREGATE %s' % (self.label, self.args)   

#------------------------------------------------------------------------------

class AssertOp(object):
    pass

#------------------------------------------------------------------------------

class AttributeOp(object):
    
    def __init__(self, line):
        self.attr_name = line[-1]
        self.line = line
        self.label = line[0]
        
        # More processing needed
        
    def execute(self, vm):
        
        if self.attr_name == 'EVENT':
            
            # pop the operand
            operand = vm.stack.pop()
            # Put result on stack 
            vm.stack.append(Bool(operand.current[1] == operand.sim.time))
            
            vm.pc += 1
            return False
        
        else:    
            logging.info('AttributeOp.attr: %s, not implemented yet' % self.attr_name)
            raise Exception
        
    #----

    def genBytecode(self, vm):
        
        bc = []       
        if self.attr_name == 'EVENT':
            logging.info('AttributeOp.attr: %s' % self.attr_name)
                                    
            # Signal is at TOS            
            bc.append(('LOAD_ATTR', 'event_op'))
            bc.append(('CALL_FUNCTION', 0))
            # Result of event_op (True/False) is at TOS
            return (int(self.label), bc)

    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class BinaryOp(object):
    
    def __init__(self, line):
        self.line  = line
        self.label = line[0]
        self.op    = line[3]

    #----
    
    def genBytecode(self, vm):
        
        bc = []        
        # TOS = right operand
        # NOS = left operand
        
        bc.append(('LOAD_CONST', self.op))
        # TOS = operation name
        # NOS = right operand
        # ... = left operand
        
        bc.append(('LOAD_GLOBAL', 'binary_op'))
        bc.append(('ROT_FOUR', None))
        # TOS = operation name
        # NOS = right operand
        # ... = left operand
        # ... = Function object
        
        bc.append(('CALL_FUNCTION', 3))       
        # TOS = result of Binary operation
        
        return (int(self.label), bc)
    
    #----
    
    def execute(self, vm):
        
        # Get operands
        operand1 = vm.stack.pop()
        operand2 = vm.stack.pop()
        # Put result on stack        
        vm.stack.append(str(operand1) == str(operand2))
        vm.pc += 1
        return False
 
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)
        
        
#------------------------------------------------------------------------------

class BinaryEqualOp(object):
    
    def __init__(self, line):
        self.line  = line
        self.label = line[0]

    #----
    
    def genBytecode(self, vm):
        
        bc = []
        
        # TOS = operand 1
        # NOS = operand 2        
        bc.append(('LOAD_GLOBAL', 'str'))
        bc.append(('ROT_TWO', None))
        bc.append(('CALL_FUNCTION', 1))
        
        # TOS = str(operand 1)
        # NOS = operand 2    
        bc.append(('ROT_TWO', None))
        bc.append(('LOAD_GLOBAL', 'str'))
        bc.append(('ROT_TWO', None))
        bc.append(('CALL_FUNCTION', 1))
        
        # TOS = str(operand 2)
        # NOS = str(operand 1)    
        bc.append(('COMPARE_OP', '=='))

        # TOS = result of COMPARE_OP (True/False)
        return (int(self.label), bc)
    
    #----
    
    def execute(self, vm):
        
        # Get operands
        operand1 = vm.stack.pop()
        operand2 = vm.stack.pop()
        # Put result on stack        
        vm.stack.append(str(operand1) == str(operand2))
        vm.pc += 1
        return False
 
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)
        
        
#------------------------------------------------------------------------------

class CallOp(object):
    
    native_map = {
        'add_op' : ('BINARY_ADD', None),
        'sub_op' : ('BINARY_SUBTRACT', None),
        'gt_op'  : ('COMPARE_OP', '>')
    }
    
    def __init__(self, line, argc, method, type_str):
        
        self.line      = line
        self.label     = line[0]
        self.type      = line[2]
        self.op        = ''
        self.klass     = method.im_class
        
        self.argc      = argc
        self.op_method = method
        self.op_name   = method.__name__
        
        self.signature = ' '.join(self.line[3:]) 
               
        self.converted = None
    
    #----
    # For new-style calls
    def newGenBytecode(self, vm):
        
        if self.signature not in lib_dict:
            return self.genBytecode(vm)
        
        else:
            # Here generate new-style bytecode
            
            # Get the arg count
            f = lib_dict[self.signature]
            argc  = f.func_code.co_argcount
            
            bc = []
            bc.append(('CALL_FUNCTION', argc))
            return (int(self.label), bc)
    #----
    
    def genBytecode(self, vm):
         
        bc = []
                     
        if self.argc == 2:
             
            if self.klass.__name__ == 'Integer':
                # Use native python operation                
                bc.append(CallOp.native_map[self.op_name])
                 
            else:
                # TOS = other, NOS = self           
                bc.append(('ROT_TWO', None))
                # TOS is now self
                bc.append(('LOAD_ATTR', self.op_name))
                # TOS is now bound method
                # NOS is other
                # Move method object to proper place on stack
                bc.append(('ROT_TWO', None))
                bc.append(('CALL_FUNCTION', 1))
                         
        else:
            #argc = 1, TOS = self
            bc.append(('LOAD_ATTR', self.op_name))
            # TOS is now bound method
            bc.append(('CALL_FUNCTION', 0)) 
           
        return (int(self.label), bc)
                               
    #----
   
    def execute(self, vm):
                                
        if self.argc == 2:
            op1 = vm.stack.pop()        
            op2 = vm.stack.pop()
            try:
                result =self.op_method(op2, op1)
                    
            except TypeError:
                
                # Type of op2 does not match type of op_method
                new_op2 = coerce(op2, self.klass)                     
                result = self.op_method(new_op2, op1)
                        
            vm.stack.append(result)

        else:
            vm.stack.append(self.op_method(vm.stack.pop()))
                        
        vm.pc += 1
        return False
 
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)
        
    
#------------------------------------------------------------------------------

class DerefOp(object):
    pass

#------------------------------------------------------------------------------

class EnterOp(object):
    
    def __init__(self, line):        
        self.label  = line[0]
        self.line = line

        self.signature = ' '.join(self.line[3:]).upper()

     #----
    
    def genBytecode(self, vm):
                            
        text_bc = []              
        return (int(self.label), text_bc)
    
     #----
    
    def newGenBytecode(self, vm):
        
        if self.signature not in lib_dict:
            return self.genBytecode(vm)
        
        else:       
            f = lib_dict[self.signature]
            name = '%s_lcl' % f.__name__    
                                        
            return (int(self.label), [('LOAD_FAST', name)])

    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class ExitOp(object):
    # This Op ignored
    pass

#------------------------------------------------------------------------------

class IndexOp(object):
    
    def __init__(self, line):        
        self.label  = line[0]
        self.line = line
                   
    #----
    
    def genBytecode(self, vm):
        
        text_bc = []        
        text_bc.append(('LOAD_GLOBAL', 'SLVRange_bc2'))
        text_bc.append(('ROT_THREE', None))
        text_bc.append(('CALL_FUNCTION', 2))                       
        return (int(self.label), text_bc)
                     
    #----
    
    def execute(self, vm):
        
        index   = int(vm.stack.pop())
        operand = vm.stack.pop()
        
        if isinstance(operand, (StdLogicVector, SLVRange)):
            bit = str(operand)[-(index+1)]
            vm.stack.append(StdLogic(bit))
            
        else:
            logging.info('IndexOP not implemented for %s' % operand.__class__)
        vm.pc += 1               
        return False

    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------
#
# Jump if condition(TOS) is False

class JumpNCOp(object):
    
    def __init__(self, line):
        
        self.line   = line
        self.label  = line[0]
        self.new_pc = int(line[-1])
                   
        self.conditional = True
        
    #----
    
    def genBytecode(self, vm):
        
        label2 = vm.bc_labels[self.new_pc][1]
        if python_version == '2.7':
            bc = [('POP_JUMP_IF_FALSE', label2)]          
        
        else:       
            bc = [('JUMP_IF_FALSE', label2), ('POP_TOP', None)]          
        
            
        return (int(self.label), bc)
             
    #----
    
    def execute(self, vm):
        
        if vm.stack.pop() == False:
            # Jump
            vm.pc = self.new_pc

        else:
            # Continue
            vm.pc += 1               
        return False

    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------
#
# Jump if condition(TOS) is True

class JumpCOp(object):
    
    def __init__(self, line):
        
        self.line   = line
        self.label  = line[0]
        self.new_pc = int(line[-1])
        
        self.conditional = True
             
    #----
    
    def execute(self, vm):
              
        if vm.stack.pop() == True:
            # Jump
            vm.pc = self.new_pc
            
        else:
            # Continue
            vm.pc += 1               
        return False
        
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------
#
# Jump Unconditionally

class JumpUOp(object):
    
    def __init__(self, line):
        
        self.line   = line
        self.label  = line[0]
        self.new_pc = int(line[-1])
        
        self.conditional = False
                   
    #----
    
    def genBytecode(self, vm):
        
        label1 = vm.bc_labels[self.new_pc][0]
        bc = [('JUMP_ABSOLUTE', label1)]          
                    
        return (int(self.label), bc)
        
    #----
    
    def execute(self, vm):       
        vm.pc = self.new_pc

    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------
#
# Jump if timeout (Actually an unconditional jump)

class JumpTOp(object):
    
    def __init__(self, line):
        
        self.line   = line
        self.label  = line[0]
        self.new_pc = int(line[-1])
        
        self.conditional = False
                   
    #----
    
    def genBytecode(self, vm):
        
        bc_label = vm.bc_labels[self.new_pc][0]
        bc = [('JUMP_ABSOLUTE', bc_label)]          
        
        return (int(self.label), bc)
             
    #----
    
    def execute(self, vm):
        
        # For now this is the same as 'ALWAYS'           
        vm.pc = self.new_pc
        return False
        
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class JumpEOp(object):
    
    def __init__(self, line):
        
        self.line   = line
        self.label  = line[0]
        self.new_pc = int(line[-1])
                 
        self.conditional = False
            
    #----
    
    def genBytecode(self, vm):
        
        #-------------------------------
        # This is an unconditional JUMP
        #-------------------------------
        
        bc_label = vm.bc_labels[self.new_pc][0]
        bc = []
                                
        # POP signal object
        bc.append(('POP_TOP', None))
        # the unconditional JUMP
        bc.append(('JUMP_ABSOLUTE', bc_label))          
           
        return (int(self.label), bc)
             
    #----
    
    def execute(self, vm):
        
        if vm.stack.pop().event():
            # Jump
            vm.pc = self.new_pc
        else:
            # Continue
            vm.pc += 1               
        return False

    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class JumpNotRisingOp(object):
    
    def __init__(self, line):
        
        self.line   = line
        self.label  = line[0]
        self.key    = line[3]
        self.new_pc = int(line[4])
        self.object = None          # Set this up when signal is determined
        
        # For Python bytecode
        self.conditional = True
            
    #----
    
    def genBytecode(self, vm):
        
        # This is a conditional JUMP
        
        label2  = vm.bc_labels[self.new_pc][1]
        text_bc = []
        
        text_bc.append( ('LOAD_FAST', 'sig__%d' % self.object.sid) )
        # Signal is at TOS
        
        text_bc.append(('LOAD_ATTR', 'not_rising_op'))
        text_bc.append(('CALL_FUNCTION', 0))
        # Result of not_rising_op (True/False) is at TOS
        
        if python_version == '2.7':
            text_bc.append(('POP_JUMP_IF_TRUE', label2))                  
        else:               
            text_bc.append(('JUMP_IF_TRUE', label2))
            text_bc.append(('POP_TOP', None))          
                                           
        return (int(self.label), text_bc)
         
    #----
    
    def execute(self, vm):
        if self.signal.rising_op():
            vm.pc += 1
        else:
            vm.pc = self.new_pc
            
        return False
        
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class MapOp(object):
    # This Op not used
    pass

#------------------------------------------------------------------------------

class NewOp(object):
    # This Op not used
    pass

#------------------------------------------------------------------------------
#
# This is for pushing signals onto the stack

class PushSigOp(object):
    
    def __init__(self, line):
        
        self.line     = line
        self.label    = line[0]
        self.type     = line[2]
        self.value    = None        
        self.object   = "object uninitialized"        
        self.key      = line[4]                
     
    #----
    
    def genBytecode(self, vm):
        
        # Generate python bytecode in a text format
        text_bc = []
        
        text_bc.append( ('LOAD_FAST', 'sig__%d' % self.object.sid) )

        if isinstance(self.object, StdLogicVector) and len(self.object) == 1:
            
            # **** SLV(0 DOWNTO 0) IS A SPECIAL CASE ****
            # IndexOP is used to push element 0 of SLV

            text_bc.append( ('LOAD_CONST', 0) )
            text_bc.append( ('LOAD_GLOBAL', 'SLVRange_bc2') )
            text_bc.append( ('ROT_THREE', None) )
            text_bc.append( ('CALL_FUNCTION', 2) )
            
        return (int(self.label), text_bc)
     

#------------------------------------------------------------------------------
#
# This is for pushing variables onto the stack

class PushVarOp(object):
     
    def __init__(self, line):
         
        self.line     = line
        self.label    = line[0]
        self.type     = line[2]
        self.value    = None        
        self.object   = "object uninitialized"        
        self.key      = line[4]                
      
    #----
     
    def genBytecode(self, vm):
         
        # Generate python bytecode in a text format
        text_bc = []
         
        text_bc.append( ('LOAD_FAST', 'var__%d' % self.object.sid) )
 
        if isinstance(self.object, StdLogicVector) and len(self.object) == 1:
             
            # **** SLV(0 DOWNTO 0) IS A SPECIAL CASE ****
            # IndexOP is used to push element 0 of SLV
            
            text_bc.append( ('LOAD_CONST', 0) )
            text_bc.append( ('LOAD_GLOBAL', 'SLVRange_bc2') )
            text_bc.append( ('ROT_THREE', None) )
            text_bc.append( ('CALL_FUNCTION', 2) )
             
        return (int(self.label), text_bc)
      
    #----
     
    def execute(self, vm):
 
        vm.stack.append(self.object)
        vm.pc += 1
        return False
     
    #----
     
    def __str__(self):
        return ' '.join(self.line)
     
    #----
         
    def __repr__(self):
        return str(self)
     
#------------------------------------------------------------------------------

class PushConstOp(object):
    
    def __init__(self, line, value):
        self.line  = line
        self.label = line[0]
        self.klass = line[6]
        
        if self.klass in ['STD_ULOGIC', 'STD_LOGIC']:
            self.value = StdLogic(value)
            self.value.spec = self.klass
        
        elif self.klass == 'ARRAY':
            spec = line[7:10]
            self.value = StdLogicVector(spec)
            self.value <= value
        
        elif self.klass == 'INTEGER':
             self.value = int(value)
        
        elif self.klass == 'NATURAL':
             self.value = int(value)
        
        elif self.klass == 'BOOLEAN':
            self.value = Bool(value)
        
        else:
            logging.info('PushConstant %s not implemented yet' % self.klass)
            raise Exception

        self.run_count = 0
                   
    #----
    
    def genBytecode(self, vm):
        return (int(self.label), [('LOAD_CONST', self.value)])
             
    #----
    
    def execute(self, vm):

        vm.stack.append(self.value)
        vm.pc += 1
        return False
        
    #----
    
    def __str__(self):
        return '%s PUSH CONSTANT %s:%s' % (self.label, self.klass, self.value)
        
#------------------------------------------------------------------------------
#
# Push LITERAL:
#
#  "01.." = a StdLogicVector literal
#
#  123..  = an integer
#
# Push STATIC:
#
#  TRUE/FALSE = Corresponding Python Bool value
#
#  1/0/...    = StdLogic literal

class PushLitOp(object):
    
    def __init__(self, line):
        
        self.line  = line
        self.label = line[0]
        self.type  = line[2]
        self.value = None
        self.key   = ''
        
        if self.type == 'LITERAL':
            arg = line[3]
            if arg[0] == '"':
                # Create an SLV object
                left = str(len(arg) - 3)
                
                spec = [left, 'DOWNTO', '0']                                
                self.value = StdLogicVector(spec)
                self.value <= arg[1:-1]
                
            else:
                # Literal is a number
                 self.value = int(arg)            
        
        elif self.type == 'STATIC':
            arg = line[4]
            if arg == 'TRUE':
                self.value = True
                
            elif arg == 'FALSE':
                self.value = False
                                
            else:
                # Create a StdLogic object
                self.value = StdLogic(arg)
                self.value.spec = 'STD_ULOGIC'
                self.value.name = 'STATIC LITERAL'
                   
    #----
    
    def genBytecode(self, vm):
        return (int(self.label), [('LOAD_CONST', self.value)])
                                               
    #----
    
    def execute(self, vm):

        vm.stack.append(self.value)
        vm.pc += 1
        return False
    
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------
#
# Pop is really a concurrent assignment

class PopOp(object):
    
    def __init__(self, line):
        
        self.line  = line
        self.label = line[0]
        self.memo  = False
        
        self.i_flag, self.d_flag, self.r_flag = [f == 'T' for f in line[2:]]
        
        if self.r_flag:
            raise Exception, 'Concurrent signal assignment with REJECT not implemented'
                   
    #----
    
    def genBytecode(self, vm):

        bc = []
               
        if not self.d_flag:
            # Put a delay value of 0.0 on stack
            bc.append(('LOAD_CONST', 0))
            
        # Put vm.ScheduleAssignment func object on stack
        bc.append(('LOAD_FAST', 'vm'))
        bc.append(('LOAD_ATTR', 'scheduleAssignment'))
                        
        # func, target, value & delay are on stack
        # Move func object to proper place on stack            
        bc.append(('ROT_FOUR', None))
            
        bc.append(('CALL_FUNCTION', 3))
        bc.append(('POP_TOP', None))
          
        return (int(self.label), bc)
             
    #----
    
    def execute(self, vm):
                
        # Process delay
        if self.d_flag:
            delay = vm.stack.pop()
        else:
            delay = 0.0

        # Process Inertial (i_flag) not implemented yet
        # Default of True is assumed
                                  
        operand = vm.stack.pop()
        target = vm.stack.pop()
        
        vm.scheduleAssignment(target, operand, delay, 0, True)
        
        vm.pc += 1
        return False
    
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class RangeApplyOp(object):
    
    # This is now a NoOp
    
    def __init__(self, line):
        self.line  = line
        self.label = line[0]
                   
    #----
    
    def genBytecode(self, vm):                       
        return (int(self.label), [])
                   
    #----
    
    def execute(self, vm):
        
        x = vm.stack.pop()
        right     = int(x)
        ascending = vm.stack.pop()
        left      = int(vm.stack.pop())
                    
        # Push a SLVRange object with the target and a sub-range onto the stack            
        target = vm.stack.pop()
        vm.stack.append(SLVRange(target, ascending, left, right))
        vm.pc += 1
        return False
    
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------
#
# 
class RangeCreateOp(object):
 
    def __init__(self, line):
        
        logging.info('RangeCreateOp: %s', line)
        
        self.line      = line
        self.label     = line[0]
        self.adrs      = line[0]
        self.klass     = line[3]        
        self.target    = line[4]
        self.sid       = -1
        self.left      = int(line[5])
        self.ascending = line[6] == 'TRUE'
        self.right     = int(line[7])
        
        try:
            self.initial = line[8]
        except IndexError:
            self.initial = None
            
        self.loc_name  = ''                   
    #----
    
    def genBytecode(self, vm):                
        return (int(self.label), [('LOAD_FAST', self.loc_name)])
                                         
    #----
    #
    # Stack contains: right, ascending, left
    
    def execute(self, vm):
        # This is a NOOP
        vm.pc += 1
        return False
    
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class RangeAscendingOp(object):
    
    def __init__(self, line):
        self.label = line[0]
             
    #----
    #
    # Stack contains: right, ascending, left
    
    def execute(self, vm):
        pass
            
    #----
    
    def __str__(self):       
        return '%4s RANGE ASCENDING' % self.label


#------------------------------------------------------------------------------

class RangeLeftOp(object):
    
    def __init__(self, line):
        self.label = line[0]
        
    #----
    
    def execute(self, vm):
        pass
          
    #----
    
    def __str__(self):       
        return '%4s RANGE LEFT' % self.label


#------------------------------------------------------------------------------

class RangeRightOp(object):
    
    def __init__(self, line):
        self.label = line[0]
             
    #----
    
    def execute(self, vm):
        pass
            
    #----
    
    def __str__(self):       
        return '%4s RANGE RIGHT' % self.label

#------------------------------------------------------------------------------

class RecordOp(object):
    pass

#------------------------------------------------------------------------------

class ReportOp(object):
    pass

#------------------------------------------------------------------------------

class ReturnOp(object):
    pass

#------------------------------------------------------------------------------

class ScheduleDelayOp(object):
    
    def __init__(self, line):
        self.label = line[0]
                   
    #----
    
    def genBytecode(self, vm):
#         print 'ScheduleDelayOp.genBytecode'
        bc = []
        
        #TOS = delay value in picoseconds
        bc.append(('LOAD_GLOBAL', 'float'))
        # Move func object to proper place on stack            
        bc.append(('ROT_TWO', None))                           
        # Convert int to float
        bc.append(('CALL_FUNCTION', 1))

        # Convert TOS from picoseconds to nanoseconds
        bc.append(('LOAD_CONST', 1000000.0))
        bc.append(('BINARY_DIVIDE', None))
                        
        # Setup vm.ScheduleDelay()            
        bc.append(('LOAD_FAST', 'vm'))
        bc.append(('LOAD_ATTR', 'scheduleDelay'))
        # Move func object to proper place on stack            
        bc.append(('ROT_TWO', None))

        # Call vm.ScheduleAssignment    
        bc.append(('CALL_FUNCTION', 1))
        bc.append(('POP_TOP', None))
          
        return (int(self.label), bc)
             
    #----
    
    def execute(self, vm):

        # Get delay and scale from fs to ns
        t = float(vm.stack.pop()) / 1000000.0
        
        vm.scheduleDelay(t)
        vm.pc += 1
        # False indicates a wait
        return False
    
    #----
    
    def __str__(self):        
        return '%s SCHEDULE DELAY' % self.label

#------------------------------------------------------------------------------

class ScheduleEventOp(object):
    
    def __init__(self, line):

        self.line = line
        self.label = line[0]
                   
    #----
    
    def genBytecode(self, vm):

        bc = []
        
        # TOS = signal object        
        # signal.waiting.add(vm)
        bc.append(('LOAD_ATTR', 'waiting'))
        bc.append(('LOAD_ATTR', 'add'))
        bc.append(('LOAD_FAST', 'vm'))

        # Call method    
        bc.append(('CALL_FUNCTION', 1))
        bc.append(('POP_TOP', None))
          
        return (int(self.label), bc)
                         
    #----
    
    def execute(self, vm):

        # Get signal
        sig = vm.stack.pop()            
        vm.addWakeup(sig)
        
        vm.pc += 1
        return False
    
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)


#------------------------------------------------------------------------------
#
# Generated by WAIT forever

class StopOp(object):
    
    def __init__(self, line):

        self.line = line
        self.label = line[0]
                   
    #----
    
    def genBytecode(self, vm):
        
        bc = [('LOAD_CONST', None), ('RETURN_VALUE', None)]
        return (int(self.label), bc)
                     
    #----
    
    def execute(self, vm):
        # No need to increment pc since this vm is done
        # Return True so the vm returns to the scheduler 
        return True
    
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)

#------------------------------------------------------------------------------

class TypeOp(object):
    pass

#------------------------------------------------------------------------------

class UnaryOp(object):
    pass

#------------------------------------------------------------------------------
#
# This is a noop for zcode - See ScheduleDelayOp & ScheduleEventOp
# For Python bytecode this is a yield

class WaitOp(object):
    
    def __init__(self, line):
        
        self.line = line
        self.label = line[0]
                   
    #----
    
    def genBytecode(self, vm):
        
        bc = [('LOAD_FAST', 'vm'),('YIELD_VALUE', None),('POP_TOP', None)]          
        return (int(self.label), bc)
             
    #----
    
    def execute(self, vm):
        vm.pc += 1
        return True
    
    #----
    
    def __str__(self):
        return ' '.join(self.line)
    
    #----
        
    def __repr__(self):
        return str(self)
    
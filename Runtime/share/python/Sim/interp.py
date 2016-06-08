#------------------------------------------------------------------------------
#
#   interp.py - 2/19/16
#
#   A Python VHDL simulator
#
#------------------------------------------------------------------------------

# Project file imports
from design_parser import Design, Parsing_Exception
from sim_events import ComparableEvent, SignalEvent, DelayEvent
from PyModule import PyModule
from vcd_dump import IDchar, VCD_File

# Needed by bytecode virtual machines
from std import StdLogic, StdLogicVector, SLVRange, SLVRange_bc, SLVRange_bc2, SLVRange_bc3 ,binary_op

# Python library imports
import stackless as ss
import sys, os, logging

from heapq       import heappush, heappop
from collections import deque
from time        import clock
from dis         import dis, disassemble
from pprint      import pprint
from sys         import version_info, path

# Get a reference to the vm_op module
import vm_op
# Get all the vm_op classes
from vm_op import *

# Imports for Python bytecode processing
import byteplay as bp
import types

python_version = '.'.join(str(x) for x in version_info[:2])

# For serialization
import pickle as g_pickle

#------------------------------------------------------------------------------
#
# Exception class for SimBuilder errors

class Simulation_Exception(Exception):
    pass

#------------------------------------------------------------------------------
#
# Exception class for sim.queue markers

class MarkerException(Exception):
    pass

#------------------------------------------------------------------------------
#
# Exception class for sim.queue StopEvent

class StopException(Exception):
    pass

#------------------------------------------------------------------------------
#
# Class for simulation serialization / de-serialization

class Serializer(object):
  
    def __init__(self):
                
        self.signals   = []
        self.processes = []
        self.modules   = []
        self.functions = []
        self.hierarchy = None
                  
    #----
    
    def save(self):
                
        jpk_file  = open('design.ser', 'wb')
               
        container = {}         
        container['signals']   = self.signals
        container['modules']   = self.modules 
        container['processes'] = self.processes
        
        container['functions'] = self.functions
        container['hierarchy'] = self.hierarchy
         
        # Serialize the container object
        g_pickle.dump(container, jpk_file)                              
        jpk_file.close() 

    #----
 
    def load(self):

        jpk_file = open('design.ser', 'rb')
        container = g_pickle.load(jpk_file)                                        
        jpk_file.close()
        
        self.signals   = container['signals']
        self.modules   = container['modules']       
        self.processes = container['processes']
        
        self.functions = container['functions']
        self.hierarchy = container['hierarchy']
        
        print "serializer.load done"
        print

#------------------------------------------------------------------------------
#
# This class is for executing simulations from the design.ser file

class SimExe(object):
    
    
    def __init__(self):
        
        self.vm_list    = []
        self.current_vm = None         
        self.queue      = []
        
        self.time       = 0.0 
        self.runtime    = 0.0
        
        self.stepping   = False        # If True, single-step VMs
        
        self.vcd        = None         # instance of VCD_File if dumping    
        
        self.log_file   = None
        
        self.serial     = Serializer()
        
        self.hierarchy  = None
        
        self.current_cycle = 0
                                                  
    #-------------------------------------------------------
    #
    # Load function objects from deserialized func_info data structure
    
    def loadFunctions(self, func_info):
        
        for lib_name, func_names in func_info:
                
            # Import the required functions
            module = __import__(lib_name, globals(), locals(), ['registerAll'], -1)
            reg = getattr(module, 'registerAll')
            lib_dict = reg(module)
            names = set()
            
            # Add functions to interp module namespace           
            globals_dict = globals()           
            for signature in func_names:                
                f = lib_dict[signature.upper()]
                globals_dict[f.__name__] = f
                
                names.add(f.__name__)
                                            
    #---------------------------------------------------------------------------
    #
    # Deserialize the simulation object
    
    def deserialize(self):
        
        self.serial.load()
        
        # Deserialize signals 
        self.signals = self.serial.signals
        
        for sig in self.signals:
            sig.initialize(self)
        
        # Deserialize processes        
        self.testProcesses = self.serial.processes
        
        # Deserialize instance hierarchy info.
        self.hierarchy = self.serial.hierarchy
        
#         print
#         print 'Deserialized hierarchy:'
#         self.hierarchy.listAll()
#         print

        # Deserialize Python testbench        
        for fn, key, port_list in self.serial.modules: 
            py_mod = PyModule(self, key)
            py_mod.load(fn, key, port_list)

        # Deserialize library function info.
        self.loadFunctions(self.serial.functions)
  
    #----
    
    def initialize(self, time=None):
                    
        self.deserialize()
                    
        # Generate VCD header
        if self.vcd != None:
            self.vcd.GenerateHeader()

        # Setup stop time event
        if time != None:
            heappush(self.queue, StopEvent(self, time + self.time))
        else:
            heappush(self.queue, StopEvent(self, self.runtime + self.time))
                    
        # Setup vm_list with bytecodeProcesses
                         
        bytecodeProcesses = [None for i in range(len(self.testProcesses))]
        for k, p in self.testProcesses.items():
            bytecodeProcesses[p.pid] = p
            
        self.vm_list = bytecodeProcesses + self.vm_list

        #===============================================
        
        # Initialize virtual machines          
        for vm in self.vm_list:
            vm.run_start(self)
                  
        # Setup a start events for all VMs
        heappush(self.queue, StartEvent(self.vm_list))                  

    #----
    
    def run(self):
        
        # Run simulation
        self.processEvents()
        
        # Simulation done        
        if self.vcd:
            # Finish up VCD file and close
            self.vcd.close()
            self.vcd = None
                      
        while len(self.queue):
            evt = heappop(self.queue)
#             logging.info('   event %s, time: %.3f' % (evt, evt.time))                                   
     
     #----       
        
    def processEvents(self):
        
        # Do special VCD processing for first event
        
        try:
            
            evt = heappop(self.queue)
            self.time = evt.time

            if (self.vcd != None):
                self.vcd.genInitial(self.signals)
            
            vm_list = evt.operate(0)
            if vm_list == None:
                # Got a stop event
                return
            
            for vm in vm_list:
                vm.channel.send(None)
                self.current_vm = vm                

        except IndexError:
            logging.error('Event queue empty')                                   
            raise Exception
        
        except RuntimeError:
            logging.info('RuntimeError in process %s at %.3f' % (vm.name, evt.time))
            raise Exception
                    
        except UnboundLocalError, msg:
            print '*** UnboundLocalError : %s' % msg
            print '*** in process %s' % vm.name
            raise Exception
        
        #---------------------------------------------
        # Processing for all events after first event
        #---------------------------------------------
                      
        heappush(self.queue, MarkerEvent(self.time))        
        resume_set = set()
        self.current_cycle = 0
        
        try:
                       
            while True:
                
                #---------------------------------------------                                                
                # accumulate events until a marker is reached
                #---------------------------------------------

                while True:
                    
                    try:
                        evt = heappop(self.queue)
                        resume_set = resume_set.union(set(evt.operate(self.current_cycle)))
                        
                    except MarkerException:                                                
                        break    
                    
                #-------------
                # Now run VMs
                #-------------
                
                # Reset value used to keep signal events in FIFO order in event queue  
                SignalEvent.evt_id  = 1
                                           
                for vm in resume_set:
                    vm.channel.send(None)                                            
                    vm.wakeups = []
                                      
                resume_set = set()                        
                
                evt = self.queue[0]                
                if not isinstance(evt, StopEvent):                
                    heappush(self.queue, MarkerEvent(evt.time))
                    
                if evt.time > self.time:
                    self.time = evt.time
                    # Reset cycle counter 
                    self.current_cycle = 0
                else:
                    # Increment cycle count
                    self.current_cycle += 1
                
        except StopException:
            print
            print 'Simulation done (StopEvent)'
            print
            return
        
        except RuntimeError:
            # Occurs at end of simulation when there is nothing to run
            # print 'RuntimeError'
            pass
                    
        # Here simulation is done
        print 'Simulation done'
        print
        
    #----
       
    def run_time(self, t):
        self.runtime = float(t)
                              
    #----
        
    def VCD_open(self, file_name = ''):
                 
        if file_name == '':
            f = sys.stdout
        else:
            f = open(file_name, 'w')
                      
        self.vcd_file_name = file_name            
        self.vcd = VCD_File(self.hierarchy, self.signals, f)
        
        return self.vcd
                                                                
    #---------------------------------------------------------------------------
    #
    # Utility methods
    #
    #---------------------------------------------------------------------------
        
    def listVMs(self):
        print 'ProcessBuilders:'
        
        for i, vm in enumerate(self.vm_list):

            print'  %2d %s' % (i, vm.vm_name())
            logging.info('  %2d %s' % (i, vm.vm_name()))
                                            
    #----
    # 
    # List all VCD signals
        
    def VCD_Signals(self):
        
        vcd = VCD_File(self.design, sys.stdout)
        vcd.GenerateHeader()
        
    #----
        
    def listCode(self, vm_id, force_zcode=False):           
        self.vm_list[vm_id].listCode(force_zcode)
                        
    #----
            
    def dump_queue(self):
        
        print 'QUEUE DUMP (in pop order)'
        
        dq = self.queue[:]
        while True:
            try:
                evt = heappop(dq)
                print '  %s' % evt
            except:
                break
        print
                                       
    #----
        
    def listQueue(self):           
        logging.info('SIM %.2f queue: %s' % (self.time, self.queue))

# For import by python testbench
Simulation = SimExe

#------------------------------------------------------------------------------

class SimBuilder(object):
    
    def __init__(self, design, project_path):
        
        self.design      = design                
        self.signals     = design.signals        
        self.vm_list     = []        
        self.pyModules   = []           # List of PyModule objects       
        self.proj_path   = project_path         
        self.lib_dict    = {}        
        self.hierarchy   = None
        
        self.log_file    = None
        
        #-----------------------------------------------------
        
        # Set current instance to top (for finding signals)
        self.current_inst = self.design.instances[0]
        
        # Setup serializer object
        self.serial = Serializer()
            
        # Setup sim attribute of each signal
        for sig in self.signals:
            sig.initialize(self)
                
        #------------------------------------------------------------------
        #
        # Setup FUNCTION objects from the design object
        #
        # Later this list will come from processing VHDL "USE" statements
         
        libraries = ['ieee.std_logic_1164']
        self.function_info = []
        
        # Import the required functions
        
        for lib_name in ['library.' + fn for fn in libraries]:

            module = __import__(lib_name, globals(), locals(), ['registerAll'], -1)
            reg = getattr(module, 'registerAll')
            lib_dict = reg(module)
            self.lib_dict = lib_dict
            
            # Add functions to interp module namespace           
            globals_dict = globals()
            
            names = [str(f) for f in self.design.functions]
            self.function_info.append([lib_name, names])
         
            for signature in names:                
                f = lib_dict[signature.upper()]
                globals_dict[f.__name__] = f
                
        self.func_names = set(names)
                    
        # Add lib_dict to vm_op namespace for op.newGenBytecode()
        setattr(vm_op, 'lib_dict', lib_dict)
                                
        #----------------------------------------------------------------------
                    
        # Setup a ProcessBuilder for each process in each instance 
                           
        for inst in self.design.instances:
            logging.info('INSTANCE: %s, has_generic=%s' % (inst.key, inst.has_generic))
                        
            if inst.foreign == True:                                
                #-------------------------------------------
                # Process python files
                # Keep track of Python module info
                # until signals are deserialized
                
                logging.info('FOREIGN INSTANCE: %s' % inst.key)
                logging.info('FOREIGN FILE    : %s' % inst.file_name)
                 
                port_list = [(name, node.sid) for name, node in  inst.local_nodes.items()]
                
                # file path = project_path + inst.file_name
                file_path = r'%s\%s' % (self.proj_path, inst.file_name)
                
                self.pyModules.append([file_path, inst.key, port_list])                    
                #self.pyModules.append([inst.file_name, inst.key, port_list])
                
            else:
                # Create bytecode processes
                processes = inst.processes
                for i, proc in enumerate(processes):
                    vm = ProcessBuilder(self, inst, proc)
                    self.vm_list.append(vm)
                    
        # Setup the DesignHierarchy object for vcd_dump
        
        self.hierarchy = DesignHierarchy(self.design.instances[0], None)

        #  self.hierarchy.listAll()      
                                        
    #---- Serialize simulation objects
        
    def serialize(self):

        # Serialize simulation object   
        self.serial.signals = self.signals        
        self.serial.modules = self.pyModules
        
        testProcesses = {}
        vm_processes = [v for v in self.vm_list if isinstance(v, ProcessBuilder)]
        for vm in vm_processes:
            # Fill testProcesses with BytecodeProcess objects
            testProcesses[vm.name] = vm.getProcess()
        self.serial.processes = testProcesses
        
        # Save library function info
        self.serial.functions = self.function_info
        
        # Save the design instance hierarchy
        self.serial.hierarchy = self.hierarchy 

        # Save the serializer object        
        self.serial.save() 
                         
#------------------------------------------------------------------------------
# 
# A StartEvent is put on the queue to startup each:
#  . Python bytecode vm
#  . Python testbench process

class StartEvent(ComparableEvent):
        
    def __init__(self, vms):
        
        self.vms      = vms
        self.time     = 0.0
        self.priority = 0         
        
    #----
    
    def operate(self, cycle):
        return self.vms
       
#------------------------------------------------------------------------------

class MarkerEvent(ComparableEvent):

    __slots__ = ('time', 'priority', 'operate', '__cmp__', '__str__')
        
    def __init__(self, time):
               
        self.time     = time
        self.priority = 10003 # After signal and delay events
        
    #----
    
    def operate(self, cycle):
        raise MarkerException
     
    #----
    
    def __str__(self):
        return 'MarkerEvent: %.2f ns' % self.time
       
#------------------------------------------------------------------------------

class StopEvent(ComparableEvent):
        
    def __init__(self, sim, when):       
        self.time     = float(when) + sim.time
        self.eid      = -1
        self.name     = 'StopEvent'
        self.sim      = sim
        self.priority = 10004 # after all other events

    #----
    
    def operate(self, cycle):
        raise StopException

    #----
    
    def __str__(self):
        return 'StopEvent: %.2f ns' % self.time

#------------------------------------------------------------------------------
#
# Emulates stackless.channel.send

class VMchannel(object):
    
    def __init__(self, vm):
        self.vm = vm
                
    # ----
    
    def send(self, message):
        self.vm.bc_iterator.next()
        
#------------------------------------------------------------------------------
#
# Prototype function containing vm bytecode

def bytecode_vm(vm, signals, variables):    
    pass

#------------------------------------------------------------------------------
#
# equality function for including StdLogic & SLV in Python code.co_consts

def const_equality(existing, new):
    
    try:
        return existing.is_equal(new)
    except AttributeError:
        return existing is new
    
# Patch this into BytePlay
bp.extended_eq = const_equality
                           
#------------------------------------------------------------------------------
#
# Container for static range objects that are created once at process startup
# rather than every time the code of a process loop is run. 

class RangeObjects():

    def __init__(self, proc):
        # The process containing these SLVRange refrences
        self.proc = proc
        self.names = {} # maps target name / signature to loc_name
        self.op_list = [] # The RANGE objects 
        
    #----
        
    def add(self, op):
        
        # Get target name / signature
        tag = ' '.join(op.line[3:])
        
        if self.names.has_key(tag):
            # target/signature already encountered
            name = self.names[tag]
        else:
            # This is a new target/signature
            name = 'rng%d_lcl' % len(self.names)       
            self.names[tag] = name

        op.loc_name = name
        self.op_list.append(op)
            
    #----
    
    def list(self):
        print '>>> SLVRange refrences in process %s' % self.proc.name
        for tag in self.names.keys():
            print '  > %s : %s' % (tag, self.names[tag])
                           
#------------------------------------------------------------------------------
#
# Classes for serializing/deserializing the design hierarchy 

class DesignHierarchy(object):
    
    def __init__(self, instance, parent):
        
        self.label       = instance.label
        self.sig_nodes   = {}
        self.children    = {}
        self.vcd_count   = 0
        self.on_vcd_path = False
        self.parent      = parent
        
        sig_nodes = [(name, node) for name, node in  instance.local_nodes.items() if node.type == 'SIGNAL']
         
        for name, node in sig_nodes:
            self.sig_nodes[name] = SignalNode(node)
        
        for name, inst in instance.children.items():
            self.children[name] = DesignHierarchy(inst, self)
        
    #----
        
    def getChild(self, name):
        return self.children[name]
    
    #----
        
    def listAll(self):
        self.list1(1)
    
    #----
        
    def list1(self, indent):
        print '%s%s' % (' '*indent, self.label)
        for child in self.children.values():
            child.list1(indent+2)  
    
#------------------------------------------------------------------------------

class SignalNode(object):
    
    def __init__(self, lcl_node):
        
        self.name       = lcl_node.name
        self.sid        = lcl_node.sid
        self.node_type  = lcl_node.sig_spec[1] 
        self.vcd_enable = False
        self.var_obj    = None
        self.vcd_mgr    = None
    #----
    
    def __repr__(self):        
        return 'SignalNode: %s(%d), %s' % (self.name, self.sid, self.node_type)
                               
#------------------------------------------------------------------------------
#
# Create & serialize a process

class ProcessBuilder(object):
    
    __slots__ = ('sim', 'inst', 'id', 'name', 'code', 'var_list', 'var_map',
                 'signals', 'bytecode', 'bc_labels', 'bc_iterator',
                 'bytecode_vm', 'text_bc', 'f_names', 'called', 'ranges'
                 )
                
    def __init__(self, sim, inst, proc):
        
        # Setup stuff
        self.sim     = sim
        self.inst    = inst
        self.id      = len(self.sim.vm_list)        
        self.name    = proc.name
        self.f_names = sim.func_names

        self.code      = proc.code.code
        self.bytecode_vm = None
        self.bc_iterator = None
        
        # For bytecode assembler       
        self.signals     = sim.signals
        self.var_list    = proc.var_list
        self.var_map     = proc.var_map
        self.bytecode    = None
        self.bc_labels   = {}
        self.called      = []
        self.ranges      = RangeObjects(proc)
                
        #----------------------------------------------------------------------
        #                       
        # Link signal refrences to instances of Signal/LiteralConstant
        # Keep track of refrences for generating local signal objects

        args = (self.inst.key, self.name, self.id)       
        logging.error('LINKING: %s for vm %s(%d)' % args)
                     
        links           = {}
        local_nodes     = self.inst.local_nodes
        signal_ids      = set()
        variable_ids    = set()
        call_signatures = set() 
        
        # self.code is a list of vm_op classes
        for op in self.code:
            
            # op is an instance of one of the classes in vm_op.py
            if op.__class__.__name__ in ['PushSigOp', 'JumpNotRisingOp']:
                                                                    
                node = local_nodes[op.key]    
                sid  = node.sid
                signal_ids.add(sid)
                    
                # This is a Signal or LiteralConst object
                op.object = self.sim.signals[sid]
                if op.__class__.__name__ == 'JumpNotRisingOp':
                    op.sid = sid
                    
                links[op.key] = '%s - %d' % (repr(op.object), sid)
                                
            # op is a PushVar
            elif op.__class__.__name__ == 'PushVarOp':
                
                var       = self.var_map[op.key]
                sid       = var.sid
                op.object = var
                
                variable_ids.add(sid)                
                
            # op is a CALL, keep track of signatures
            elif op.__class__.__name__ == 'CallOp':
                call_signatures.add(op.signature)
                
            # op is a RangeCreate, keep track of ranges
            elif op.__class__.__name__ == 'RangeCreateOp':
                
                if op.klass == 'SIGNAL':
                    op.sid = local_nodes[op.target].sid
                    
                elif op.klass == 'VARIABLE':
                    op.sid = self.var_map[op.target].sid
                
                self.ranges.add(op)
               
        if len(call_signatures):
            self.called = [self.sim.lib_dict[fs].__name__ for fs in call_signatures]
            
        #----------------------------------------------------------------------
        # Generate Python bytecode for this VM
        #----------------------------------------------------------------------
                               
        self.text_bc = None
        self.buildBytecode(signal_ids, variable_ids)
                         
    #----
    
    def buildBytecode(self, sig_ids, var_ids):
        
        #---- Local function to return a prototype bytecode_vm function
        
        def proto_func():
            
            f = bytecode_vm
            vm = types.FunctionType(f.func_code, f.func_globals, name = f.func_name,
                  argdefs = f.func_defaults,
                  closure = f.func_closure
            )
            
            vm.__dict__.update(f.__dict__)
            
            return vm
        
        #---- End local function
                 
        # Create a dict mapping jump targets to bytecode Label objects
        # Also, track ENTER and EXIT CONTEXT for python call optimization        
        for zc in self.code:
            try:
                # Only jump zcodes have a new_pc attribute
                adrs = zc.new_pc
                if zc.conditional:
                    # Setup labels 1 & 2 if this is a target of a conditional branch
                    self.bc_labels[adrs] = (bp.Label(adrs, 1), bp.Label(adrs, 2))
                else:
                    # Setup only label 1 for unconditional if not already setup
                    if not adrs in self.bc_labels.keys():
                        self.bc_labels[adrs] = (bp.Label(adrs, 1), None)
                                   
            except:
                # For all other zcodes
                continue
                    
        # Create a prototype bytecode_vm function        
        self.bytecode_vm = proto_func()        
        bytecode = bp.Code.from_code(self.bytecode_vm.func_code)
                        
        # Generate python bytecode process loop preamble

        text_bc = []
        
        # Generate code for fast signal access
        for sid in sig_ids:
            text_bc.append(('LOAD_FAST', 'signals'))
            text_bc.append(('LOAD_CONST', sid))
            text_bc.append(('BINARY_SUBSCR', None))
            # Signal is at TOS
            text_bc.append(('STORE_FAST', 'sig__%d' % sid))
        
        # Generate code for fast variable access
        for sid in var_ids:
            text_bc.append(('LOAD_FAST', 'variables'))
            text_bc.append(('LOAD_CONST', sid))
            text_bc.append(('BINARY_SUBSCR', None))
            # Signal is at TOS
            text_bc.append(('STORE_FAST', 'var__%d' % sid))

        # Generate code for fast function access
        for func_name in self.called:
            text_bc.append(('LOAD_GLOBAL', func_name))
            # Function is at TOS
            text_bc.append(('STORE_FAST', '%s_lcl' % func_name))

        # Generate code for fast SLVRange access
                          
        completed = []
        for op in self.ranges.op_list:
                        
            # Filter out duplicate ranges
            name = op.loc_name
            if name in completed:
                continue
            else:
                completed.append(name) 
            
            text_bc.append(('LOAD_GLOBAL', 'SLVRange'))            
            # TOS = SLVRange class
                
            if op.klass == 'VARIABLE': 
                text_bc.append(('LOAD_FAST', 'variables'))                
            else:
                text_bc.append(('LOAD_FAST', 'signals'))
            
            text_bc.append(('LOAD_CONST', op.sid))
            text_bc.append(('BINARY_SUBSCR', None))
            # TOS = SLVRange target signal
            
            text_bc.append(('LOAD_CONST', op.ascending))
            text_bc.append(('LOAD_CONST', op.left))
            text_bc.append(('LOAD_CONST', op.right))
            
            text_bc.append(('CALL_FUNCTION', 4))
            # TOS = SLVRange instance
            
            text_bc.append(('STORE_FAST', op.loc_name))
        
        # Generate code for process loop             
        opc = 0
        for ad, op in enumerate(self.code):
            # Translate a single zcode op
            
            if str(op.__class__.__name__) == 'CallOp':
                adrs, text = op.newGenBytecode(self)
                
            elif op.__class__.__name__ == 'EnterOp':
                adrs, text = op.newGenBytecode(self)
                                                
            else:
                adrs, text = op.genBytecode(self)
            
            opc += 1
            
            # Process Jump labels
            if adrs in self.bc_labels.keys():
                
                label1, label2 = self.bc_labels[adrs]
                if label2 != None:                    
                    
                    # this is a conditional jump
                    if python_version != '2.7':
                        # Add jump over POP
                        text_bc.append(('JUMP_FORWARD', label1))
                    
                    # Add label for conditional jump
                    text_bc.append((label2, None))
                
                    if python_version != '2.7':
                        # Add POP_TOP to clean up stack for conditional jump
                        text_bc.append(('POP_TOP', None))
                    
                # Add label for unconditional jump & Jump over POP 
                text_bc.append((label1, None))               

            # Append generated text bytecode to the text bytecode for this VM
            text_bc += text
                    
        # save a copy of the text_bc for persistance
        self.text_bc = text_bc[:]
        
        # Encode text_bc to a byteplay bytecode list
        bytecode.code = bp.encode(text_bc)        
        self.bytecode = bytecode.code
        
        self.bytecode_vm.func_code = bytecode.to_code()
               
    #----                    
                   
    def listCode(self, force_zcode = False):
        print 'bytecode for vm %s %d:' % (self.name, self.id)
        for i, code in enumerate(self.bytecode):
            print '  %d %s' % (i, code)                
                
    #----
                
    def getProcess(self):
                    
        attributes = [self.id, self.name, self.bytecode_vm, self.var_list, self.inst.key]       
        return BytecodeProcess(attributes)

    #---------------------------------------------------------------------------
    #
    # Utility methods
    #
    #---------------------------------------------------------------------------
      
    def vm_name(self):       
        return 'ProcessBuilder - %s/%s' % (self.inst.key, self.name)
  
    #----
       
    def __str__(self):       
        return 'ProcessBuilder %d - %s' % (self.id, self.name)
      
    #----
      
    def __repr__(self):
        return str(self)
                                         
#-------------------------------------------------------------------------------        
#
# The runtime bytecode process object that is created
# and serialized by SimBuilder, and de-serialized by SimExe

class BytecodeProcess(object):
    
    __slots__ = ('sim', 'pid', 'name', 'queue', 'code', 'variables',
                 'channel', 'signals',  'bc_iterator', 'key',
                 'has_bc', 'bytecode_vm', 'wakeups',
                 '__getstate__', '__setstate__' )
    
    def __init__(self, attributes):       
         
        self.pid, self.name, self.bytecode_vm, self.variables, self.key = attributes
        
     #----
        
    def run_start(self, sim):

        self.sim         = sim
        self.signals     = sim.signals
        self.queue       = sim.queue
        
        self.channel     = VMchannel(self)        
        self.wakeups     = []
        
        # Can't trace variables using VCD
        for v in self.variables:
            v.vcd_mgr = None
        
        self.bc_iterator = self.bytecode_vm(self, self.signals, self.variables)

    #---------------------------------------------------------------------------
    #
    # Methods called by bytecode
    
    def scheduleAssignment(self, target, operand, delay, reject=False, inertial=False):
        
        # reject & inertial are ignored for now
        
        if target.is_variable:
            target.setVal(operand.getVal())           
        else:
            heappush(self.queue, SignalEvent(self, target, operand, delay/1000000.0))

    #----
    
    def scheduleDelay(self, delay):
        heappush(self.queue, DelayEvent(self, delay))

    #---------------------------------------------------------------------------
    #
    # Utility methods
    #
    #---------------------------------------------------------------------------
     
    def vm_name(self):       
        return 'BytecodeProcess - %s/%s' % (self.key, self.name)

    #----
     
    def __str__(self):       
        return 'BytecodeProcess %d - %s/%s' % (self.pid, self.key, self.name)
    
    #----
    
    def __repr__(self):
        return str(self)
                                                     
    #---------------------------------------------------------------------------
    #
    # Serialization methods
    #
    #---------------------------------------------------------------------------
        
    def __getstate__(self):            
        return [self.pid, self.name, self.bytecode_vm, self.variables, self.key]
    
    #----
    
    def __setstate__(self, saved):            
        self.pid, self.name, self.bytecode_vm, self.variables, self.key = saved
        
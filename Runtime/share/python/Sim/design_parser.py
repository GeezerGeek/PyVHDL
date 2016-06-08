#------------------------------------------------------------------------------
#
#   design_parser.py - 2/19/16
#
#   Convert design.txt into a class structure for Python Simulator
#
#------------------------------------------------------------------------------

from vm_op import *

import std, logging
from StringIO import StringIO

#------------------------------------------------------------------------------
#
# Exception class for design parsing errors

class Parsing_Exception(Exception):    
    pass
 
#------------------------------------------------------------------------------
#
# A generator of split lines from a file

class LineGenerator(object):
    
    def __init__(self, file_obj):    
        self.f = file_obj
        self.line_no = 0
        self.line = ''
        
        self.current = []
        
    #----
        
    def next(self):
        
        while True:
    
            self.line = self.f.readline()
            self.line_no += 1
    
            # At EOF    
            if not self.line:
                break
    
            # Strip /n
            self.line = self.line[:-1]
            logging.warning('design.txt: %s' % self.line)

            # Skip empty lines
            if len(self.line.replace(' ', '')) == 0:
                continue
                
            break
        
        if not self.line:
            # EOF
            self.f.close()    
            raise StopIteration
        
        self.current = self.line.split()
        return self.current
        
    #----
        
    def expect(self, name, i=0, require=False):
                
        if self.current[i] == name:
            return True 
            
        if require:
            args = (name, self.line_no, self.current[i]) 
            msg = "Design Parsing Error: expected '%s' at line %d, got '%s'" % args 
            raise Parsing_Exception, msg

#------------------------------------------------------------------------------
#
# Classes representing design.txt objects
#
#------------------------------------------------------------------------------

class Design():

    def __init__(self, design_file_name):
        
        self.file_name = design_file_name        
        self.lines     = LineGenerator(file(design_file_name, 'r'))
        
        self.name      = ''
        
        self.instances = [] # Instance objects in top-down order
        self.inst_map  = {} # from Instance name to Instance
        
        self.modules   = [] # Module objects in top-down order
        self.mod_map   = {} # from Module name to Module
        
        self.signals   = []
        
        self.functions = [] # List of called subprogram function objects 
      
    def build(self):
        
        global op_set
        
        # Parse design.txt
        
        self.lines.next()
        self.lines.expect('DESIGN')
        self.name = self.lines.current[1]
        
        self.lines.next()        
        while True:
        
            if self.lines.expect('MODULE'):
                # Process a MODULE description
                mod = Module(self, self.lines)
                mod.build()
                
                self.mod_map[mod.search_name] = mod                
                self.modules.append(mod)
                self.lines.next()
                
            elif self.lines.expect('INSTANCE'):
                inst = Instance(self, None, self.lines)
                inst.build()                
                self.inst_map[inst.key] = inst                
                self.instances.append(inst)
                
                self.lines.next()
                
            elif self.lines.expect('SUBPROGRAM'):
                
                line = self.lines.current
                if line[1] == 'FUNCTION':
                    f = Function(' '.join(line[2:])) 
                    self.functions.append(f)
                    
                else:
                    msg = "Unable to parse %s" % line 
                    raise Parsing_Exception, msg
                    
                self.lines.next()
                
            else:
                break
            
        self.lines.expect('END_DESIGN', require=True)
        
        # Parsing done. Next, create signals
        
        self.setupSignals()
               
        self.setupProcesses()
        
    #----
    
    def setupProcesses(self):
        # For each instance, copy processes from its module
        for inst in self.instances:
            mod_name = '%s:%s' % (inst.label, inst.module_name)
            mod = self.mod_map[mod_name]          
            
            inst.processes = mod.processes
            for p in inst.new_processes:
                p.build(mod)
    #----
    
    def setupSignals(self):

        # Local function to process sid attribute of linked nodes        
        def linkNodes(node):
            for out in node.outputs:
                out.sid = node.sid
                linkNodes(out)
                        
        # End local function
        
        # Local function to create a signal        
        def createSignal(sid, node):
            
            spec  = node.sig_spec
            inst  = node.label
            name  = node.name
            const = spec[0] == 'CONSTANT'
            klass = spec[1]
                        
            # Default return value
            signal = None
                            
            if klass == 'STD_LOGIC':
                if spec[-2] == '=':
                    # Create StdLogic object with initializer
                    signal = std.StdLogic(spec[-1])
                else:
                    signal = std.StdLogic()
                    
                node.signal  = signal
                signal.name  = name
                signal.spec  = spec
                signal.sid   = sid
                stat         = True 
            
            elif klass == 'STD_LOGIC_ARRAY':
                signal = std.StdLogicVector(spec[2:5])
                if spec[-2] == '=':
                    # Initialize StdLogicVector object
                    signal <= spec[-1]
                    
                node.signal  = signal
                signal.name  = name
                signal.spec  = spec
                signal.sid   = sid
                stat         = True
            
            elif klass == 'INTEGER':
                if const:
                    
                    # Create INTEGER constant
                    ini = spec[-1]
                    logging.warning('Create INTEGER Constant: name=%s, value=%s' % (name, ini))
                    
                else:
                    logging.warning('Constant of type %s not implemented yet' % klass)
                    raise Parsing_Exception                    
            
            else:
                logging.warning('Signal of type %s not implemented yet' % klass)
                raise Parsing_Exception                    
                
            return signal 
             
        # End local function
            
        # First process mappings for each instance top-down setting up
        #  1. has_inputs flag
        #  2. outputs list 
        for inst in self.instances: 
            for link in inst.mappings:

                if link.direction == 'IN':
                    # linking from parent signal to child port
                    port = link.port_node
                    port.has_inputs = True
                    link.signal_node.outputs.append(port)
                
                elif link.direction == 'OUT':
                    # linking from child port to parent signal
                    signal = link.signal_node 
                    signal.has_inputs = True
                    link.port_node.outputs.append(signal)
                
                else:
                    raise Exception, 'Unimplemented mapping direction: %s' % link.direction 
        
        # Second process local_nodes for each instance
        #  1. creating signals for nodes where has_inputs = False. 
        #  2. Copy the signal id to all linked output nodes recursively
        for inst in self.instances:
            
            for name,node in inst.local_nodes.items():
                                                   
                if (node.has_inputs == False) or (len(node.ranges) > 0):
                
                    
                    sid = len(self.signals)
                    node.sid = sid                  
                    # Assig this SID to possible output destinations
                    linkNodes(node)
                    
                    
                    # Create a Signal or LiteralConstant object
                    sig = createSignal(sid, node)
                    sig.inst = inst                    
                    self.signals.append(sig)
                    node.signal = sig

    #----
        
    def listSignals(self):

        print 'Signals:'
        names = []
        for sig in self.signals:
            
            if  sig.__class__.__name__ == 'SLVRange':
                names.append('%s/%s' % (sig.inst.label, sig.rng_name))
                
            else:
                names.append('%s/%s' % (sig.inst.label, sig.name))
            
        w = max([len(n) for n in names])
        for i, sig in enumerate(self.signals):
            s_name = names[i].ljust(w + 1)
            args = (i, s_name, ' '.join(sig.spec[1:]), str(sig), sig.sid)
            print '  %2d %s %s:%s, sid=%d' % (args)

    #----
        
    def topModule(self):
        return self.instances[0]

    #----
        
    def findModule(self, m_id):
        try:
            return self.modules[m_id]
        except KeyError: 
            msg = "Design Parsing Error: module %s undefined" % m_id 
            raise Parsing_Exception, msg

#------------------------------------------------------------------------------
#
# An Instance object containing constant, signal & mapping definitions,
# links to its Module and parent instance, and a list of child instances

class Instance():
    
    def __init__(self, design, parent, lines):
        
        self.design = design
        self.lines  = lines
        self.parent = parent  # parent instance object
        
        self.has_generic = False
        self.new_processes = [] 
        
        
    #----
    
    def build(self):

        self.label       = self.lines.current[1]
        self.module_name = self.lines.current[2]
        self.key         = '%s:%s' % (self.label, self.module_name)

        self.constants   = {}
        self.local_nodes = {}        
        self.mappings    = []
                
        self.children    = {}               
        self.processes   = []
        
        # For foreign Instances
        self.foreign     = False
        self.FileName    = ''       # For foreign instance
        
        # for VCD support
        self.vcd_enable  = False
        self.vcd_count   = 0
        self.on_vcd_path = False
                
        while True:              
            self.lines.next()
              
            if self.lines.expect('END_INSTANCE'):
                break
              
            elif self.lines.expect('MAPPING'): 

                # Process 'MAPPING' line in INSTANCE definition
                # A mapping connects a localNode in this instance to a
                # localNode in a parent instance
                 
                self.mappings.append(MappingEdge(self))
                    
            elif self.lines.expect('LOCAL'):               
                self.addLocal()
                
    #----
    
    def addLocal(self):
        
        # Process 'LOCAL' line in INSTANCE definition 
        l_type = self.lines.current[1]
                            
        if l_type in ['CONSTANT', 'GENERIC']:
            name  = self.lines.current[2]
            value = self.lines.current[-1] 
            self.constants[name] = value
            
            # Flag this for code generation
            if l_type == 'GENERIC':
                self.has_generic = True
             
        elif l_type == 'SIGNAL':
            node = LocalNode(self.label, self.lines.current)
            self.local_nodes[node.name] = node
             
        else:
            raise Exception, 'LOCAL %s not implemented yet' % self.lines.current
        
    #----
    
    def addMapping(self, local_nodes, inst_key, lines): 
               
        # Process 'MAPPING' line in INSTANCE definition
        # A mapping connects a localNode in this instance to a
        # localNode in a parent instance         
        
        edge = MappingEdge(self, lines.current)
        self.mappings.append(edge)
                        
    #----
    # Method to support vcd_dump
    
    def getChild(self, name):
        return self.children[name]
    
    #----
    
    def list(self):
                
        print 'Instance %s:%s' % (self.label, self.module_name)
        print 'Constants:'
        pprint(self.constants)
        print 'Locals:'
        pprint(self.local_nodes)
        print 'Mappings:'
        pprint(self.mappings)
        

#------------------------------------------------------------------------------
#
# An MODULE object
#
# A Module object contains processes and child instances

class Module():

    def __init__(self, design, lines):
        
        self.lines  = lines        
        self.design = design
        
        self.label       = ''
        self.entity      = ''
        self.search_name = ''
        self.name        = ''       
        self.parent      = None
        
        # STUFF BELOW HERE IS REDUNDANT WITH INSTANCE ATTRIBUTES !!
        
        # !!! These refer to instances 
        # a list of (label, Context)
        self.child_list  = []
        # a dict of name:Context
        self.children    = {}
        
        # Used for VCD signal mapping
        self.vcd_count   = 0
        self.on_vcd_path = False
 
        # Each local_node maps a name in the namespace of this instance
        # Ports have a direction of 'IN', 'OUT'or 'INOUT'
        # local signals have a direction of 'NONE'            
        self.local_nodes = {}
        
        # mappings connect a local node in this module
        # to a local node of an instance within this module
        self.mappings = []
                    
        self.processes = []                
        self.foreign   = False
        self.FileName  = '' # Attribute for Foreign (python) instance
                              
    #----        
        
    def build(self):
        
        global pid
                    
        self.label       = self.lines.current[1]
        self.entity      = self.lines.current[2]
        self.name        = self.entity.split('.')[1]
        self.search_name = '%s:%s' % (self.label, self.entity)
        self.instance    = self.design.inst_map[self.search_name]
        
        logging.warning('Building Module %s' % self.search_name)
                  
        while True:
            self.lines.next()
            
            if self.lines.expect('END_MODULE'):
                return
                                
            # Process 'FOREIGN_MODULE' line in design.txt           
            if self.lines.expect('FOREIGN_MODEL'):
                
                self.instance.foreign   = True
                
#                 py_file_name = self.lines.current[1]
#                 # Full file path = Zamiacad project path + py_file_name                
#                 self.instance.file_name = r'%s\%s' % (self.design.file_name, py_file_name)
                
                # File name without path
                self.instance.file_name = self.lines.current[1]
            
                inst_label  = self.label
                inst_entity = self.entity
                inst_key    = '%s:%s' % (inst_label, inst_entity)                
                self.child_list.append((inst_label, inst_key))
                
            if  self.lines.expect('INSTANCE'):
                
                inst = Instance(self.design, self.instance, self.lines)
                inst.build()
                self.design.inst_map[inst.key] = inst                
                self.design.instances.append(inst)
                self.instance.children[inst.label] = inst
                                                                                            
            if self.lines.expect('PROCESS'):
                 
                pid = len(self.processes)
                p = Process(self, self.lines, pid)
                p.build()
                self.processes.append(p)
                continue
            
        # TODO: MAKE THIS UNNECESSARY !!
        
        self.instance.processes = self.processes
                        
    #----
    # Probably un-needed
        
    def isTop(self):
        return self == self.design.instances[0]
                 
#------------------------------------------------------------------------------
#
# A node object created from a 'LOCAL' line in design.txt
# May be a signal (direction = None) or port (direction = IN/OUT)
        
class LocalNode(object):
    
    def __init__(self, label, line):
        
        self.label      = label     # Label of containing entity
        self.type       = line[1]   # SIGNAL/CONSTANT/GENERIC
        self.direction  = line[3]   # IN/OUT/NONE
        self.name       = line[2]   # local_nodes key
        
        self.sig_spec   = [self.type]+line[4:]  # Signal specification
        self.sid        = -1        # Signal id
        
        self.has_inputs = False     # True if any inputs
        self.outputs    = []        # list of instance local nodes
        self.ranges     = []        # list of LocalRangeNodes of this signal
        
        self.signal     = None      # The signal this node references
        
        self.vcd_enable = False
        
        # This is a list of integers for STD_LOGIC_ARRAY signals
        # and an interger for STD_LOGIC signals 
        self.vcd_id     = None
        
    def __repr__(self):
        return 'LocalNode %s, %s, %s' % (self.name, self.type, self.direction)
                 
                 
#------------------------------------------------------------------------------
#
# A node object created from a 'VARIABLE' line in design.txt
        
class VariableNode(object):
    
    def __init__(self, label, line):
        
        self.label      = label      # Label of containing entity
        self.type       = 'VARIABLE' # SIGNAL/CONSTANT/GENERIC
        self.direction  = None       # IN/OUT/NONE
        self.name       = line[2]    # local_nodes key
        
        self.sig_spec   = [self.type]+line[4:]  # Signal specification
        self.sid        = -1        # Signal id
        
        self.has_inputs = False     # True if any inputs
        self.outputs    = []        # list of instance local nodes
        self.ranges     = []        # list of LocalRangeNodes of this signal
        
        self.signal     = None      # The signal this node references
        
        self.vcd_enable = False
        
        # This is a list of integers for STD_LOGIC_ARRAY signals
        # and an interger for STD_LOGIC signals 
        self.vcd_id     = None
        
    #----
        
    def __repr__(self):
        return 'VariableNode %s, %s, %s' % (self.name, self.type, self.direction)
                 
#------------------------------------------------------------------------------
#
# A mapping object created from a  'MAPPING' line in design.txt
#   Represents a connection between a signal of a parent instance and
#   a port of a child instance
            
class MappingEdge(object):
    
    def __init__(self, instance):
        
        line            = instance.lines.current
        self.direction  = line[1]       # direction wrt instance        
        self.port_name  = line[2]       # instance port name
        source_node     = instance.parent.local_nodes[line[3]]            
        self.port_node  = instance.local_nodes[self.port_name]
        
        # LOCAL FUNCTION
        
        def range_test(src, dest):
             
            if dest[0] != 'SLV_RANGE':
                # Not an SLV_RANGE mapping
                return False
            
            # Don't process as SLV_RANGE if not a sub-range
            return not(dest[1]==src[0] and dest[2]==src[1] and dest[3]==src[2])
        
        # END LOCAL FUNCTION
              
        if range_test(source_node.sig_spec[2:], line[4:]):
            
            # Process SLVRange input mapping to switch the destination to a newly
            # created port node and change the original port node to a local signal
                                    
            # Create a new port local node with a munged name and direction = IN
            self.actual = '%s_I_N_T' % self.port_name
            s = 'LOCAL SIGNAL %s IN ' % self.actual
            new_line = s.split() + source_node.sig_spec[1:]            
            self.port_node = LocalNode(instance.label, new_line)
            instance.local_nodes[self.actual] = self.port_node
             
            # Map the source node to the new port local node
            self.signal_node = source_node
            
            # Setup info needed to create a new Process for a concurrent signal
            # assignment like: value <= NEW_SIGNAL_NAME(x DOWNTO y)
            
            args = {}
            args['inst_name']   = instance.key
            args['proc_name']   = '_int_proc_%03d' % len(instance.new_processes)
            args['sig_name']    = self.port_name
            args['sig_spec']    = ' '.join(['ARRAY', line[5], line[6], line[7], 'OF STD_LOGIC'])
            args['sig_left']    = line[5]
            args['sig_right']   = line[7]
            if line[6] == 'TO':
                args['sig_asc'] = 'TRUE'
            else:
                args['sig_asc'] = 'FALSE'
            args['port_name'] = self.actual
            args['port_spec'] = ' '.join(['ARRAY'] + source_node.sig_spec[2:] + ['OF STD_LOGIC'])

            ip = InternalProcess(args)
            ip.var_list = []
            instance.new_processes.append(ip)           
                                   
        else:
            # One-to-one mapping without sub-range in actual arg
            self.signal_node = instance.parent.local_nodes[line[3]]           
                                 
#------------------------------------------------------------------------------

class Literal():

    def __init__(self, value, spec):
        
        self.value = value
        self.spec  = spec 
        self.id    = -1
        
        self.klass = spec.split()[0]
        
    def __repr__(self):
        return 'Literal(%s)' % self.value

#------------------------------------------------------------------------------
#
# An internally created Process to assign the range of a signal to a port
# redefined as a local signal

class InternalProcess():

    def __init__(self, args):
        
        self.inst_name = args['inst_name']
        self.name      = args['proc_name']
        self.var_list  = []
        self.var_map   = {}

                
        template = '''0 PUSH OBJECT SIGNAL {sig_name} : {sig_spec}
        1 PUSH OBJECT SIGNAL {port_name} : {port_spec}
        2 PUSH LITERAL {sig_left}
        3 PUSH STATIC VALUE {sig_asc}
        4 PUSH LITERAL {sig_right}
        5 RANGE CREATE
        6 RANGE APPLY
        7 POP T F F
        8 PUSH OBJECT SIGNAL {port_name} : {port_spec}
        9 SCHEDULE EVENT WAKEUP
        10 WAIT
        11 PUSH OBJECT SIGNAL {port_name} : {port_spec}
        12 JUMP EVENT 13
        13 CANCEL ALL WAKEUPS
        14 JUMP 0
        END_CODE
        '''
                
        ip_code = template.format(**args)        
        self.lines = LineGenerator(StringIO(ip_code))
            
    #----
    
    def build(self, mod):
        self.module = mod
        self.pid = len(mod.processes)
        mod.processes.append(self)
        
        code = Code(self, self.lines)
        code.build()
        self.code = code
    
    #----
    
    def __repr__(self):       
        return 'InternalProcess %s in inatance %s' % (self.name, self.inst_name)

#------------------------------------------------------------------------------

class Process():

    def __init__(self, module, lines, pid):
        
            self.lines    = lines        
            self.module   = module
            self.design   = module.design
            self.inst     = module.instance
            self.name     = ''
            self.code     = None
            self.pid      = pid
            self.signals  = {}
            
            self.var_list = []  # Variable objects in vid order
            self.var_map  = {}  # Variable name to variable object
            
#             print '*** Process %s .init()' % self.lines.current[1]           
#             print '***   module %s' % module.search_name           
#             print '***   pid %s' % pid           
        
    def build(self):
        
        #----- Local Function -----
        
        vid = 0
        
        def createVariable(line):
            
            name = line[1]
            spec  = line[2:]
            klass = spec[0]
                                 
            # Default return value
            variable = None
                            
            if klass == 'STD_LOGIC':
                try:
                    if spec[-2] == '=':
                        # Create StdLogic object with initializer
                        variable = std.StdLogic(spec[-1])
                    else:
                        variable = std.StdLogic()
                        
                except IndexError:
                        # spec is just ['STD_LOGIC'] 
                        variable = std.StdLogic()
                    
                variable.is_variable = True
                variable.name = name
            
            elif klass == 'STD_LOGIC_ARRAY':
                variable = std.StdLogicVector(spec[1:5])
                if spec[-2] == '=':
                    # Initialize StdLogicVector object
                    variable <= spec[-1]
                    
                variable.is_variable = True
                variable.name = name
            
            elif klass == 'INTEGER':
                if const:
                    
                    # Create INTEGER constant
                    ini = spec[-1]
                    logging.warning('Create INTEGER Constant: name=%s, value=%s' % (name, ini))
                    
                else:
                    logging.warning('Constant of type %s not implemented yet' % klass)
                    raise Parsing_Exception                    
            
            else:
                logging.warning('Signal of type %s not implemented yet' % klass)
                raise Parsing_Exception                    
                
            return variable 

        #----- End Local Function -----
        
        self.name = self.lines.current[1]       
        
        while True:
            self.lines.next()
            if self.lines.expect('END_PROCESS'):
                # End of PROCESS definition
                return
            
            if self.lines.expect('VARIABLE'):
                v_name = self.lines.current[1]
                
                var             = createVariable(self.lines.current)
                var.is_variable = True
                var.name        = v_name
                var.sid         = vid
                vid += 1 
                               
                self.var_map[v_name] = var
                self.var_list.append(var)

            if self.lines.expect('BEGIN_CODE'):               
                # Process 'CODE' line in design.txt
                code = Code(self, self.lines)
                code.build()
                self.code = code
                           
#------------------------------------------------------------------------------

class Function():

    def __init__(self, signature):
        
        self.signature = signature  # Used to lookup function
        
        # These will be populated later
        self.func      = None       # A python function object
        self.argc      = 0          # Function arg count for CALL
        
    #----
    
    def __str__(self):
        return self.signature        
                
#------------------------------------------------------------------------------

class Code():

    def __init__(self, proc, lines):
        self.process = proc
        self.inst    = proc.module.instance
        self.lines   = lines
        
        self.code     = []        
        self.jumps    = []
        self.labels   = {}
        
    def build(self):
        logging.warning('Processing code for pid: %s' % self.process.pid)
            
        self.code_buf = []
        while True:
             # Create a list of the code           
            self.lines.next()
            self.code_buf.append(self.lines.current)
            if self.lines.expect('END_CODE'):                    
                break            
            
            
        # New code processing
        cc = CodeOptimizer(self.code_buf, self.inst.constants, self.process)
        cc.analyze()                
        self.code = cc.to_VM_Op()
            
    # Process ENTER CONTEXT ... EXIT CONTEXT            
    def doContext(self):
            
        ignore = ['CALL', 'EXIT', 'MAP']
        
        while True:
            self.lines.next()
            label, tag = self.lines.current[0:2]
            
            if tag == 'EXIT':
                self.labels[label] = len(self.code)
                break
            
            if tag == 'NEW':
                ignore.append(self.lines.current[4])
                self.labels[label] = len(self.code)
                
            elif tag == 'PUSH':
                self.doPush(ignore)
                                
            elif tag == 'MAP':
                self.labels[label] = len(self.code)
            
            elif tag == 'CALL':
                self.doCall()
            
            else:
                raise Exception, 'Code op %s not implemented yet, pos=%s' % (tag, label)
                           
    # Process IGRANGEOP            
    def doRange(self):
        
        op = self.lines.current[2]
        
        if op == 'CREATE':
            self.addToCode(RangeCreateOp(self.lines.current))
         
        elif op == 'APPLY':
            self.addToCode(RangeApplyOp(self.lines.current))
         
        elif op == 'ASCENDING':
            self.addToCode(RangeAscendingOp(self.lines.current))
         
        elif op == 'LEFT':
            self.addToCode(RangeLeftOp(self.lines.current))
         
        elif op == 'RIGHT':
            self.addToCode(RangeRightOp(self.lines.current))
        
        else:
            raise Exception, 'RANGE %s not implemented yet' % op
            
    # Process PUSH
    def doPush(self, ignore=[]):
                
        # Check for PUSH LITERAL
        if self.lines.current[2] in ['LITERAL', 'STATIC']:
            self.addToCode(PushLitOp(self.lines.current))
    
        elif self.lines.current[4] not in ignore:                   
            self.addToCode(PushSigOp(self.lines.current))
            
    # Process SCHEDULE
    def doSchedule(self):
        if self.lines.current[2] == 'TIMED':
            self.addToCode(ScheduleDelayOp(self.lines.current))
            
        elif self.lines.current[2] == 'EVENT':
            self.addToCode(ScheduleEventOp(self.lines.current))
            
        else: 
            msg = 'SCHEDULE %s not implemented' % self.lines.current[2] 
            raise Parsing_Exception, msg        

    # Process CALL
    def doCall(self):
        signature = ' '.join(self.lines.current[3:])
        argc, method = std.method_map[signature]
        
        self.addToCode(CallOp(self.lines.current, argc, method))
                                      
    # Add op to code list            
    def addToCode(self, op):
        
        self.labels[op.label] = len(self.code)
        self.code.append(op)
                                  
    # Update JUMP targets            
    def update(self):
        
        for j in self.jumps:
            op = self.code[j]
            op.new_pc = self.labels[str(op.new_pc)]
            
        # Also, remove possible extra "JUMP ALWAYS 0" at end of code
        s = str(self.code[-2])[5:]
        if (s == 'JUMP ALWAYS 0') and (s == str(self.code[-1])[5:]):
            self.code = self.code[:-1]
                                       
    # Print code list           
    def dump(self):
        
        for adrs, c in enumerate(self.code):
            print '%4d %s' % (adrs, str(c)[5:])
            
#------------------------------------------------------------------------------

class CodeOptimizer():

    def __init__(self, code_buf, constants, proc):
        self.code_buf  = code_buf   # code as a list of tokenized z-code strings
        self.constants = constants  # constants dict
        self.proc      = proc
        
        self.pc        = 0          # code_buf index
        self.stack     = []         # For nested contexts
        self.evt_list  = []         # For ATTRIBUTE OP EVENT instructions
        self.wait_list = []
        
        # A dict of with key = jump target and values = list of jump references
        self.jmp_data = {}
        
        # A list of data for code_buf items: [keep, new_pc]
        self.buf_data = []
        
        # The compiled and assembled code - A list of vm_op classes
        self.code = []
        
        # True if processing a new-style CALL
        self.new_style = False
        
        #-----------------------------------------------------------------------
          
        if ' '.join(self.code_buf[-3][1:]) == 'JUMP 0':
            
            # Remove duplicate JUMP 0 instruction at end of code            
            adrs = len(self.code_buf) - 3
            del self.code_buf[adrs]            
            # Fix label on remaining JUMP
            self.code_buf[adrs][0] = str(adrs)
         
        for code in self.code_buf[:-1]:
            # code is an individual z-code inst. as a list of string tokens            
            # Populate jmp_data & buf_data
            if code[1] == 'JUMP':
                # Populate jmp_data
                target = int(code[-1])
                adrs   = int(code[0])
                try:
                    self.jmp_data[target].append(adrs)
                except KeyError:
                    self.jmp_data[target] = [adrs]
                    
            # Also change $$UNIVERSAL_INTEGER$$ to INTEGER
            for j, token in enumerate(code):
                if token.startswith('$$UNIVERSAL_INTEGER$$'):
                    code[j] = token.replace('$$UNIVERSAL_INTEGER$$', 'INTEGER')
                    
            # Populate default buf_data
            self.buf_data.append([False, -1])
               
    #----
    #
    #  Methods for accessing z-code tokenized instructions
        
    def get_inst(self, offset=0):        
        if offset != 0:
            # Get inst relative to pc
            inst = self.code_buf[self.pc + offset]
        else:
            # Get next instruction
            inst = self.code_buf[self.pc]
            self.pc += 1
            
        return inst
               
    #----
        
    def get_abs_inst(self, adrs):                    
        return self.code_buf[adrs]     
               
    #----
        
    def replace_inst(self, adrs, inst):                    
        self.code_buf[adrs] = inst
         
    #----
       
    def analyze(self):
        
        logging.warning('  CodeOptimizer.analyze()')
        # Pass 1  -  Optimize calls to built-in functions
        wait_flag = False
        while True:
            inst = self.get_inst()
            if inst[0] == 'END_CODE':
                break
            
            if wait_flag:
                if inst[1] == 'CANCEL':
                    wait_flag = False
                continue
                
            if inst[1] == 'WAIT':
                wait_flag = True
                logging.error('%s WAIT at %s' % ( self.proc.name, inst[0]))
                                           
            if inst[1] == 'ENTER':
                self.stack    = []
                self.context()
                                           
            if inst[1] == 'RANGE' and inst[2] == 'APPLY':
                ok = self.doApply(int(inst[0]))
                if not ok:
                    print '!!! doApply in analyze() returned False'
                    self.show_code(int(inst[0]))
                
                # Mark instruction KEEP
                pc = int(inst[0])
                self.buf_data[pc][0] = True
                
            else:
                # Mark instruction KEEP
                pc = int(inst[0])
                self.buf_data[pc][0] = True
                
        # Pass 2 -  Condense IF(clk'EVENT and clk='1') to JumpNotRisingOp      
        for pc in self.evt_list:
            self.do_rising(pc)
                
    #----
    # 
    # Process z-code CALLs marked by by ENTER CONTEXT & EXIT CONTEXT instructions
                
    def context(self):
        
        logging.warning('  ENTERING CONTEXT %d @ %s' % (len(self.stack), self.get_inst(-1)[0]))
        self.stack.append(self.pc)
        
        # List of function call arg names
        arg_name = set()
        
        while True:
            inst = self.get_inst()
            pc = int(inst[0])
            
            if inst[1] == 'ENTER':
                # Recursion
                self.context()

            elif inst[1] == 'NEW':
                # Keep track of arg. DBIDs
                arg_name.add(inst[4])
                
            elif inst[1] == 'MAP':
                # Ignore MAP instructions
                continue
                
            elif inst[1:4] == ['PUSH', 'OBJECT', 'CONSTANT'] and inst[4] in arg_name:
                # Ignore instructions that reference formal parameters
                continue
                
            elif inst[1] == 'EXIT':
                # Get the instruction just above this EXIT CONTEXT
                call_inst = self.get_inst(-2)
                
                signature = ' '.join(call_inst[3:])
                fix_pc   = self.stack[-1] - 1
                fix      = [str(fix_pc), 'ENTER', 'CONTEXT'] + call_inst[3:]

                
                # Append signature to ENTER CONTEXT instruction
                self.replace_inst(fix_pc, fix )
                
                # Set keep flag for this instruction
                self.buf_data[fix_pc][0] = True
                
                if signature in std.method_map.keys():
                    logging.warning('  Built_in')                    

                elif signature == '"-"(CONSTANT A : $$UNIVERSAL_INTEGER$$, CONSTANT B : $$UNIVERSAL_INTEGER$$) RETURN $$UNIVERSAL_INTEGER$$':
                    pass 
                                           
                else: 
                    logging.warning('VHDL FUNCTION CALL NOT IMPLEMENTED %s' % signature)
#                    msg = 'VHDL function call not implemented %s' % signature 
#                    raise Parsing_Exception, msg

                    # Here instructions that were not kept must be restored
                    # so a VHDL function or procedure call can be processed 
                    
                logging.warning('  EXITING CONTEXT %d @ %d\n' % (len(self.stack)-1, self.pc-1))
                self.stack.pop()
                return
            
            elif inst[1] in ['AGGREGATE', 'ATTRIBUTE', 'ENTER', 'CALL', 'JUMP', 'PUSH', 'POP', 'WAIT', 'CANCEL', 'SCHEDULE', 'INDEX']:
                # Set keep flag for this instruction
                self.buf_data[pc][0] = True

                if ' '.join(inst[1:]) == 'ATTRIBUTE OP EVENT':
                    # Keep track of ATTRIBUTE OP EVENT instructions 
                    self.evt_list.append(int(inst[0]))

                if inst[1] == 'WAIT':
                    # Keep track of WAIT instructions 
                    self.wait_list.append(int(inst[0]))
                    
            elif inst[1] =='RANGE':
                
                # Set keep flag for this instruction
                self.buf_data[pc][0] = True
                
                if inst[2] == 'APPLY':
                    ok = self.doApply(pc)
                    if not ok:
                        print '!!! doApply in context() returned False'
                        self.show_code(pc)
                                         
            else:
                logging.warning('Code %s not implemented yet' % inst)
                raise Parsing_Exception
                 
    #----
    #
    # Try to match clk'event and clk=1
        
    def do_rising(self, pc):        
          
        self.pc = pc

        inst = self.get_inst(-5)
        if inst[1] != 'ENTER':
            # Not what we are looking for
            return
        
        inst = self.get_inst(-1)
        if inst[3] != 'SIGNAL':
            # Not what we are looking for
            return
        
        sig_name = inst[4]
        inst = self.get_inst(10)
        if ' '.join(inst[1:]) != 'PUSH STATIC VALUE 1':
            return
                
        inst = self.get_inst(12)
        if ' '.join(inst[1:4]) != 'CALL FUNCTION "="(CONSTANT':
            return
                
        inst = self.get_inst(15)
        if ' '.join(inst[1:4]) != 'CALL FUNCTION "AND"(CONSTANT':
            return
                
        inst = self.get_inst(17)
        if ' '.join(inst[1:3]) != 'JUMP NC':
            return
        
        # Pattern matched
        address = inst[3]
        
        # Update code_buf
        p = pc-1
        self.buf_data[p-4][0] = False

        while True:
            # Set keep to false
            self.buf_data[p][0] = False
            p += 1
            if p == pc+17:
                # Substitute JUMP NR instruction
                self.code_buf[p] = ('%d JUMP NR %s %s' % (p, sig_name, address)).split()
                break
                          
    #----
    #
    # Try to match expected RANGE APPLY attributes and consolidate them
    #
    # This results in the RANGE APPLY being overwritten with a RANGE CREATE
    # with target, left, ascending & right appended

    def doApply(self, pc):        
        
        # Validate expected sequence leading to RANGE APPLY
        # Gather attributes along the way
        
        inst = ' '.join(self.get_inst(-2)[1:])
        if inst != 'RANGE CREATE':
            return False
        create_pc = pc - 1
        
        inst = ' '.join(self.get_inst(-3)[1:3])
        if inst != 'PUSH LITERAL':
            return False
        right = self.get_inst(-3)[3]
        
        inst = ' '.join(self.get_inst(-4)[1:4])
        if inst != 'PUSH STATIC VALUE':
            return False
        ascending = self.get_inst(-4)[4]
        
        inst = ' '.join(self.get_inst(-5)[1:3])
        if inst != 'PUSH LITERAL':
            return False
        left = self.get_inst(-5)[3]
        
        inst = ' '.join(self.get_inst(-6)[1:4])
        if inst not in ['PUSH OBJECT SIGNAL', 'PUSH OBJECT CONSTANT', 'PUSH OBJECT VARIABLE']:
            return False
        target = self.get_inst(-6)[4]
        klass  = self.get_inst(-6)[3]
        
        # Clear keep flag for loop invariant attribute setup instructions
        # that are moved to process bytecode preamble
        
        self.buf_data[pc-5][0] = False # PUSH target
        self.buf_data[pc-4][0] = False # PUSH left
        self.buf_data[pc-3][0] = False # PUSH ascending
        self.buf_data[pc-2][0] = False # PUSH right       
        
        
        if inst == 'PUSH OBJECT CONSTANT':
            
            # Apply the range to the constant value and replace all the range creation
            # operations with a PUSH LITERAL
            literal  = self.get_inst(-6)[-1]

            if ascending == 'FALSE':
                # Reverse so LSB is at [0]
                literal = literal[::-1]
                _min = int(right)
                _max = int(left)
            else:
                _min = int(left)
                _max = int(right)

            rng = literal[_min:_max+1]
            # Reverse bits of rng
            rng = rng[::-1]
                            
            replacement = [create_pc, 'PUSH', 'LITERAL', '"%s"' % rng]
        else:
            replacement = [create_pc, 'RANGE', 'CREATE', '%s' % klass, target, left, ascending, right]
               
        # Here RANGE APPLY is replaced with new PUSH CONST RANGE instruction
        # or PUSH LITERAL sub-range string ie. "101"
        self.replace_inst(int(create_pc), replacement)
        
        return True # Success
        
    #----
    #
    # Process z-code into a list of vm_op classes with adjusted jump targets 
        
    def to_VM_Op(self):

        # Populate self.buf_data[1] and list code 
        i = 0
        for code in self.code_buf[:-1]:
            pc = int(code[0])
            keep = self.buf_data[pc][0]
            if keep:
                self.buf_data[pc][1] = str(i)
                self.code_buf[pc][0] = str(i)                                     
                i += 1
                 
        # Update jump targets
        kl = self.jmp_data.keys()
        for target in self.jmp_data.keys():
            i = target
            while True:
                keep = self.buf_data[i][0]
                if keep:
                    # Found the updated target
                    update = self.buf_data[i][1]
                    # Update jumps referencing this target
                    for ref in self.jmp_data[target]:
                        self.code_buf[ref][-1] = update
                        
                    # Process next jump_data item
                    break
                
                else:
                    # see if next instruction is being kept
                    i += 1
                       
        # Assemble instructions to corresponding vm_op classes            
    
        logging.warning('Assemble instructions to method calls started')
        tag = 'NOP'    
        for i, inst in enumerate(self.code_buf[:-1]):
            
            if not self.buf_data[i][0]:
                # keep = False
                continue
            
            last = tag
            label, tag = inst[0:2]
                
            if tag == 'AGGREGATE':
                self.code.append(AggregateOp(inst))
                
            elif tag == 'ATTRIBUTE':
                self.code.append(AttributeOp(inst))
                 
            elif tag == 'BINARY':
                self.doBinary(inst)
                 
            elif tag == 'JUMP':
                self.doJump(inst)
                                
            elif tag == 'PUSH':

                try:
                    self.doPush(inst, i)
                except KeyError:
                    print 'Key error at line %d %s' % (i, inst)
                    raise KeyError
                
            elif tag == 'POP':                   
                self.code.append(PopOp(inst))
                
            elif tag == 'WAIT':
                if last == 'SCHEDULE':                   
                    self.code.append(WaitOp(inst))
                else:
                    # This is a WAIT forever
                    self.code.append(StopOp(inst))
                                
            elif tag == 'CALL':
                self.doCallOp(inst)
                
            elif tag == 'SCHEDULE':
                self.doSchedule(inst)

            elif tag == 'RANGE':
                self.doRange(inst)                   

            elif tag == 'INDEX':
                self.code.append(IndexOp(inst))                   

            elif tag == 'ENTER':
                self.doEnter(inst)
                
            else:
                logging.warning('Assembler:  %s not implemented yet' % inst)
                raise Exception
        
        logging.warning('Assembler done')    
        return self.code

    #-------------------
    #
    # Assembler helpers
                
    def doJump(self, inst):
        
        if len(inst) > 3:
            
            # This is a conditional Jump        
            cond = inst[2]
            
            if cond == 'NC':
                self.code.append(JumpNCOp(inst))
             
            elif cond == 'NR':
                self.code.append(JumpNotRisingOp(inst))
             
            elif cond == 'C':
                self.code.append(JumpCOp(inst))
             
            elif cond == 'EVENT':
                self.code.append(JumpEOp(inst))
             
            elif cond == 'TIMEOUT':
                self.code.append(JumpTOp(inst))
                
        else:            
            # This is an unconditional Jump
            self.code.append(JumpUOp(inst))
            

    #----
                    
    def doRange(self, inst):
        
        op = inst[2]
        
        if op == 'CREATE':
            logging.warning('>>> RangeCreateOp(%s)' % inst)
            self.code.append(RangeCreateOp(inst))
         
        elif op == 'APPLY':
            self.code.append(RangeApplyOp(inst))
         
        elif op == 'ASCENDING':
            self.code.append(RangeAscendingOp(inst))
         
        elif op == 'LEFT':
            self.code.append(RangeLeftOp(inst))
         
        elif op == 'RIGHT':
            self.code.append(RangeRightOp(inst))
        
        else:
            logging.warning('Code %s not implemented yet' % inst)
            raise Parsing_Exception, 'Code %s not implemented yet' % inst
            
    # ----
    
    def doPush(self, inst, i):        
        
        # Check for PUSH LITERAL
        if inst[2] in ['LITERAL', 'STATIC']:
            self.code.append(PushLitOp(inst))
            
        # Check for PUSH CONSTANT
        elif inst[3] == 'CONSTANT':
            name  = inst[4]
            try:
                value = self.constants[name]
            except KeyError:
                # Resolved value is at end of inst
                value = inst[-1] 
            
            self.code.append(PushConstOp(inst, value))
            
        # Check for PUSH VARIABLE
        elif inst[3] == 'VARIABLE':
            self.code.append(PushVarOp(inst))
    
        else:
            # Push a signal                   
            self.code.append(PushSigOp(inst))
              
    # ----
    
    def doSchedule(self, inst):
        if inst[2] == 'TIMED':
            self.code.append(ScheduleDelayOp(inst))
            
        elif inst[2] == 'EVENT':
            self.code.append(ScheduleEventOp(inst))
            
        else: 
            msg = 'SCHEDULE %s not implemented' % inst[2] 
            raise Parsing_Exception, msg        

    #----
    #
    # This is for old-style CALLs which call methods of the operand class
    #  *** std.method_map will become obsolete **
    
    def doCallOp(self, inst):
        
        signature = ' '.join(inst[3:])        
        argc, method = std.method_map[signature]
        
        # Type of first operand must match type_str when Call is executed
        t = inst[-1]
        if t == 'STD_LOGIC_VECTOR':
            type_str = "<class 'std.StdLogicVector'>"
 
        elif t in ['STD_LOGIC', 'STD_ULOGIC', 'UX01']:
            type_str = "<class 'std.StdLogic'>"
 
        elif t == 'INTEGER':
            type_str = "<class 'std.Integer'>"
 
        elif t == 'BOOLEAN':
            type_str = "<class 'std.Bool'>"
 
        else:
            logging.warning('### Call of type %s not implemented yet' % t)
            raise Exception, 'Call of type %s not implemented yet' % t
         
        call = CallOp(inst, argc, method, type_str)
        self.code.append(call)

    #----
    #
    # This is for new-style CALL scheme, where the function is placed on the
    # Python stack before the args. by the ENTER vm_op
    
    def doEnter(self, inst):
        self.code.append(EnterOp(inst))
 
    # ----
    
    def doBinary(self, inst):
        
        # Process built-in operators
        
        op = inst[-1]
              
        if op in ['EQUAL','AND','NAND','OR','NOR','XOR','XNOR']:
            self.code.append(BinaryOp(inst))
                    
        elif op in ['LESSEQ','LESS','GREATER','GREATEREQ','NEQUAL']:
            logging.warning('BINARY op  %s not implemented yet, %s' % (op, inst))
            raise Parsing_Exception(op)
            
        elif op in ['SCALAR_EQUALS','SCALAR_GREATER','SCALAR_GREATEREQ','SCALAR_LESS','SCALAR_LESSEQ','SCALAR_NEQUALS']:                   
            logging.warning('BINARY built-in op  %s not implemented yet' % op)
            raise Parsing_Exception(op)
            
        elif op in ['BOOL_AND','BOOL_NAND','BOOL_NOR','BOOL_OR','BOOL_XNOR','BOOL_XOR','BOOL_NOT']:                   
            logging.warning('BINARY built-in op  %s not implemented yet' % op)
            raise Parsing_Exception(op)
            
        elif op in ['BIT_NOT','BIT_AND','BIT_NAND','BIT_NOR','BIT_OR','BIT_XNOR','BIT_XOR']:                   
            logging.warning('BINARY built-in op  %s not implemented yet' % op)
            raise Parsing_Exception(op)
            
        elif op in ['ARRAY_NOT','ARRAY_EQUALS','ARRAY_NEQUALS','ARRAY_GREATER','ARRAY_GREATEREQ','ARRAY_LESS','ARRAY_LESSEQ']:                   
            logging.warning('BINARY built-in op  %s not implemented yet' % op)
            raise Parsing_Exception(op)
                   
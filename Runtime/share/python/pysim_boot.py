#------------------------------------------------------------------------------
#
# pysim_boot.py - 1/28/16
#
# Location = ...\Runtime\share\python\pysim_boot.py
#
#   *************************************************************************
#   * This is a Jython file that runs in the ZamiaCAD environment.          *
#   *                                                                       *
#   * It creates the design.txt file                                        *                                                                      *
#   *                                                                       *
#   *************************************************************************
#
#  If necessary create/update design.txt, then run the simulator. The project   
#  to simulate is setup with the ZamiaCAD run configuration dialog.
#  Select the "Python Simulator".
#

from org.zamia import ZamiaLogger
from org.zamia.instgraph.interpreter import IGPopStmt
from org.zamia.instgraph.interpreter import IGInterpreterCode

import java.lang.reflect.Method
import java.io.File
import java.net.URL
import java.net.URLClassLoader
import jarray

import os, sys, re 
from subprocess import Popen, PIPE
from org.zamia.instgraph import IGOperationObject

process_id  = 1
#------------------------------------------------------------------------------
#
# Select Python or PyPy interpreter for running Py+VHDL

py_interpreter = 'python'
# py_interpreter = 'pypy'

#------------------------------------------------------------------------------
#
# For printing to Zamia Console

logger = ZamiaLogger.getInstance()

def printf(format, *args):
    logger.info(format, args)
    
def printi(indent, format, *args):
    fmt = ' ' * indent + format
    logger.info(fmt, args)
    

#------------------------------------------------------------------------------
#
# Base class of all IG nodes

class Node(object):
    
    def __init__(self, parent, zdb=None, name=''):
        
        INDENT_STEP = 2        
        self.parent = parent
        self.indent_num = 0
        self.dmuid = name

        if zdb == None:
            # This is a child node
            self.zdb = self.parent.zdb
            self.indent_num = self.parent.indent_num + INDENT_STEP 
            self.is_top = False
        else:
            # This is the top node
            self.zdb = zdb
            
        self.is_top = not(zdb == None)
            
    #----
        
    def build(self, obj):
        
        self.ig_obj = obj        
        self.cls = self.ig_obj.getClass()
        self.name = self.cls.getName().split('.')[-1]    
        
        self.processFields()
                    
        return self
    
    #----
    
    def processFields(self):
        printi(self.indent_num, '*** Class %s needs a processFields method', self.name)
        return None
    
    #----
    
    def igToNode(self, a_obj):        
        cls = a_obj.getClass()
        name = cls.getName().split('.')[-1]
        klass = name_to_class[name](self)
        return klass
    
    # Process a sequence of statements
    
    def getSOS(self, sos=None):            

        if sos == None:
            try:                    
                sos = self.ig_obj.getSequenceOfStatements()
                self.ig_sos = sos
            except AttributeError:
                return []    
            
        ns = sos.getNumStatements()        
        statements = []
        for n in range(ns):
            stmt = sos.getStatement(n)
            klass = self.igToNode(stmt)            
                        
            statements.append(klass)
            klass.build(stmt)
                        
        return statements

#------------------------------------------------------------------------------
#
# Manager for subprograms referenced by CALL zcode instructions 

class SubManager(object):

    def __init__(self):

        # Maps signature to subList index
        self.signatureMap = {}
        # List of IGSubProgram objects
        self.subList      = []

    #----

    def addSub(self, sub):

        signature = sub.getSignature()

        if signature in self.signatureMap:
            # Return the subList index
            return self.signatureMap[signature]

        else:
            spid = len(self.subList)
            self.signatureMap[signature] = spid
            self.subList.append(sub)

            # Recursively process calls within this subprogram
            
#             stmts = sub.getCode()
#             if stmts != None:
#                 
#                 code = sub.getInterpreterCode()
#                 code.dump()
#             
#                 n = code.getNumStmts()
#                 for i in range(n):
#                     stmt = code.getStmt(i)
#                     if str(stmt).upper().startswith('CALL'):
#                         i = subMgr.addSub(stmt.getSub())             

            # Return the subList index
            return spid

    #----
    #
    # List information about all subprograms

    def list_all(self, list_code=False):
    
        printf('>>> subPrograms:')
        printf("")
        for i, sub in enumerate(self.subList):
            
            printf("  subprogram %d", i)
            printf("    %s", sub.toString())
            
            stmts = sub.getCode()
            if stmts != None:
                
                code = sub.getInterpreterCode()
            
                # Process locals
                
                container = sub.getContainer()
                for i in range(container.getNumLocalItems()):
                
                    item = container.getLocalItem(i) 
                    cls_name = item.getClass().getName().split('.')[-1]
                    
                    if cls_name == 'IGObject':
                        
                        i_cat = str(item.getCat())
                        i_dir = item.getDirection()
                        i_def = str(item).upper().split()
                        t_def = i_def[i_def.index(':'):]
                        
                        if (i_cat == 'VARIABLE'):
                      
                            if t_def[1] == 'STD_LOGIC':
                                t_string = t_def[1]
                                
                            elif (t_def[1] == 'ARRAY') and (t_def[-1] == 'STD_LOGIC'):
                                t_string = 'STD_LOGIC_ARRAY %s %s %s' % tuple(t_def[2:5])
                                
                            elif t_def[-1] == 'INTEGER':
                                t_string = 'INTEGER'
                                
                            elif t_def[-1] == 'POSITIVE':
                                t_string = 'POSITIVE'
                                    
                            else:
                                break
                                                        
                            ini = item.getInitialValue()
                            if ini:
                                t_string += ' = %s' % str(ini).replace('"', '')
                                
                            printf('    LOCAL %s %s %s %s' % (i_def[0], i_def[1], i_dir, t_string))                                          
                
                if list_code:    
                    n = code.getNumStmts()
                    printf("   code size: %d", n)
                    for i in range(n):
                        stmt = code.getStmt(i)
                        printf("    %3d %s", i, stmt)

            bi = sub.getBuiltin()
            if bi != None:
                printf("   builtin: %s",bi)
        
            printf('')
    
        printf('>>> End subPrograms')
        printf('')

    #----
    #
    # Add SUBPROGRAM lines to design.txt

    def dump(self):
            
        for sub in self.subList:
            print >> design_file, 'SUBPROGRAM %s' % sub.toString()
            
#------------------------------------------------------------------------------
#
# An IGSequenceOfStatements object 

class CodeList(object):
    
    def __init__(self, ig_obj):        
        self.ig_obj = ig_obj
        self.code = IGInterpreterCode('', self.ig_obj.computeSourceLocation()) 

    def generate(self):
        self.ig_obj.generateCode(self.code)
                
    def add(self, stmt):
        self.code.add(stmt)
        
    def dump(self, indent):
        for i in range(self.code.getNumStmts()):
            printi(indent, '  %3d:   %s', i, self.code.getStmt(i))
                    
    def output(self, mod, proc):
        global status
        print >> design_file, 'BEGIN_CODE'
        
        for i in range(self.code.getNumStmts()):
            
            stmt = self.code.getStmt(i)
            if str(stmt).upper() == 'POP':
                op = self.gen_pop(stmt)

            elif str(stmt).startswith('IGRangeOp'):
                op = self.gen_range(stmt, i)

            #-------------------------------------------------------------------
            
            elif str(stmt).upper().startswith('CALL'):
                spid = subMgr.addSub(stmt.getSub())
                op = str(stmt).upper()

            #-------------------------------------------------------------------

            elif str(stmt).upper().startswith('PUSH OBJECT CONSTANT'):
                s = str(self.code.getStmt(i)).upper()
                tokens = s.split()
                name = tokens[3]
                
                # Not a function formal parameters
                if not name in ['L','R','A','B','ARG']:
                    
                    # Get the constant value
                    rr = mod.cont.resolve(str(name))
                    if rr.getNumResults():
                        value = rr.getResult(0).getInitialValue()
                        op = '%s = %s' % (s, str(value).replace('"', ''))
                    else:
                        args = (name,) + proc.args + (i,)
                        printf("RESOLVE '%s' FAILED IN PROCESS %s %s:%s AT CODE LINE %d" % args)
                        status = 'error'
                        op = s
                else:
                    op = str(stmt).upper()
                                           
            #-------------------------------------------------------------------
         
            else:
                op = str(stmt).upper()
                
            print >> design_file, i, op
                
        print >> design_file, 'END_CODE'
        
    def export(self):
        pass

    def gen_range(self, stmt, i):
        fields = stmt.getClass().getDeclaredFields()
        f = fields[0]
        f.setAccessible(True)
        return 'RANGE %s' % f.get(stmt)
    
            
    def gen_pop(self, stmt):
        
        fields = stmt.getClass().getDeclaredFields()
        items = ['POP']
        names = ['INST']
        
        for f in fields:
            f.setAccessible(True)
            items.append(str(f.get(stmt))[0])
            names.append(f.getName())
        
        return ' '.join(items)
                
#------------------------------------------------------------------------------

class Module_node(Node):
    
    m_counter = 0
        
    # Custom build function with label arg
    def build(self, obj, label):
        
        self.ig_obj = obj        
        self.cls = self.ig_obj.getClass()
        
        # We are removing 'work.' from name. This ignores fact
        # that the module may be in a library other than 'work'
        
        self.name  = self.cls.getName().split('.')[-1]
        self.label = label
        
        self.is_foreign = 1 == 0    # Klugy replacement for False
        
        self.cont = self.ig_obj.getContainer()
             
        self.processFields()
        Module_node.m_counter += 1            
        return self
    
   #----
    
    def processFields(self):
        
        if Module_node.m_counter == 0:
            # Only for top module
            self.ProcessInstance()

        print >> design_file, 'MODULE %s %s' % (self.label, self.dmuid.upper())

        # Not needed for now
#         self.ProcessPackages()

        self.ProcessForeign()
        self.addStructure()
        print >> design_file, 'END_MODULE'
                
    #----
    
    def addStructure(self):
        struct = self.ig_obj.getStructure()
        klass = self.igToNode(struct)
        self.structure = klass
        klass.build(struct)
        
    #----

#  MAY BE USEFUL LATER  <-----<<<
#    
#     def ProcessPackages(self):
#     
#         cont = self.ig_obj.getContainer()         
#         n    = cont.getNumPackageImports()       
#         packages = [cont.getPackageImport(i) for i in range(n)]
#         
#         for p in packages:
#             name = str(p)[4:]
#             print >> design_file, '# PACKAGE: %s' % name 
#             if name == 'WORK.MLITE_PACK.ALL':
#                 print >> design_file, '# PROCESSING MLITE_PACK, %s' % p.getId()
#                 lib = cont.resolve('FROM_LBRANCH')
#                 item = lib.getResult(0)
#                 print >> design_file, '# ITEM: %s, %s' % (item, item.getInitialValue())
                                                                              
    #----
    
    def ProcessInstance(self):

        cont = self.ig_obj.getContainer()         
        n    = cont.getNumLocalItems();

        if n == 0:
            return
            
        print >> design_file, 'INSTANCE %s %s' % (self.label, self.dmuid.upper())
        for i in range(n):
            
            item = cont.getLocalItem(i)
        
            cls = item.getClass()
            cls_name = cls.getName().split('.')[-1]
                        
            if cls_name == 'IGOperationLiteral':                            
                print >> design_file, 'FOREIGN_MODEL %s' % item.getId()[1:-1]
    
            elif Module_node.m_counter == 0:
                
                # Generate instance for top module
                
                i_dir = item.getDirection()
                i_def = str(item).upper().split()
                t_def = i_def[i_def.index(':'):]
                
                if t_def[1] == 'STD_LOGIC':
                    t_string = t_def[1]
                    
                elif (t_def[1] == 'ARRAY') and (t_def[-1] == 'STD_LOGIC'):
                    t_string = 'STD_LOGIC_ARRAY %s %s %s' % tuple(t_def[2:5])
                    
                elif t_def[-1] == 'INTEGER':
                    t_string = 'INTEGER'
                    
                elif t_def[-1] == 'POSITIVE':
                    t_string = 'POSITIVE'
                        
                else:
                    t_string = ' '.join(t_def)
                    printf('<DBG> UNABLE to create %s', t_string)
                    x = cont.resolve(t_string)
                    printf('<DBG> %s resolved to %s', t_string, str(x))
                    exit() 
                    
                ini = item.getInitialValue()
                if ini:
                    t_string += ' = %s' % str(ini).replace('"', '')
                    
                print >> design_file, 'LOCAL %s %s %s %s' % (i_def[0], i_def[1], i_dir, t_string)
  
        print >> design_file, 'END_INSTANCE'

    #----
    
    def ProcessForeign(self):
        
        cont = self.ig_obj.getContainer()
        n = cont.getNumLocalItems();
        for i in range(n):
            item = cont.getLocalItem(i)        
            cls = item.getClass()
            cls_name = cls.getName().split('.')[-1]

            if cls_name == 'IGOperationLiteral$STR':                                            
                print >> design_file, 'FOREIGN_MODEL %s' % item.getId()[1:-1]
                                                                                           
#------------------------------------------------------------------------------

class Structure_node(Node):
    
    def processFields(self):
        
        self.processContainer()
        self.addStatements()
        self.mappings = []
                                    
    #----
    
    def addStatements(self):
        
        self.statements = []
        ns = self.ig_obj.getNumStatements()
        for i in range(ns):
            
            stmt = self.ig_obj.getStatement(i)
            klass = self.igToNode(stmt)
            self.statements.append(klass)
            klass.build(stmt)
                                                                    
    #----
    
    def processContainer(self):
        
        cont = self.ig_obj.getContainer()        
        n = cont.getNumInterfaces()
        for i in range(n): 
            intf = cont.getInterface(i)
                                                   
#------------------------------------------------------------------------------

class Instantiation_node(Node):
    
    def processFields(self):
        
        global IGManager
        
        self.ig_instance = self.ig_obj.getChildDUUID()
        self.label = str(self.ig_obj.getLabel())
        self.instance = str(self.ig_instance)
        
        self.constants = {}
                
        print >> design_file, 'INSTANCE %s %s' % (self.label, self.instance)
        
        self.addGenerics() 
        self.newAddLocals()
        self.addMappings()
        
        print >> design_file, 'END_INSTANCE'
        
    #----
        
    def addMappings(self):
    
        self.mappings = []
        n = self.ig_obj.getNumMappings()
        for i in range(n):
            mapping = self.ig_obj.getMapping(i)
            # klass is always a Mapping_node instance
            klass = self.igToNode(mapping)
            klass.build(mapping)
            klass.emit()
            
            self.mappings.append(klass)
        
    #----
        
    def addGenerics(self):
        
        self.generics = {}
        ag = self.ig_obj.getActualGenerics()
        for pair in ag:
            self.generics[pair.getFirst()] = pair.getSecond()            
        
    #----
        
    def newAddLocals(self):
        
        self.locals = []
        
        signature = self.ig_obj.getSignature()
        module = IGManager.findModule(signature)
        structure = module.getStructure()
        container = structure.getContainer()
        
        for i in range(container.getNumLocalItems()):
            
            item = container.getLocalItem(i) 
            cls_name = item.getClass().getName().split('.')[-1]
            
            if cls_name == 'IGObject':
                
                
                i_cat = str(item.getCat())
                i_dir = item.getDirection()
                i_def = str(item).upper().split()
                t_def = i_def[i_def.index(':'):]
                
                if i_cat in ['CONSTANT', 'SIGNAL']:
              
                    if t_def[1] == 'STD_LOGIC':
                        t_string = t_def[1]
                        
                    elif (t_def[1] == 'ARRAY') and (t_def[-1] == 'STD_LOGIC'):
                        t_string = 'STD_LOGIC_ARRAY %s %s %s' % tuple(t_def[2:5])
                        
                    elif t_def[-1] == 'INTEGER':
                        t_string = 'INTEGER'
                        
                    elif t_def[-1] == 'POSITIVE':
                        t_string = 'POSITIVE'
                        
                    elif t_def[-1] == 'NATURAL':
                        t_string = 'NATURAL'
                            
                    else:
                        t_string = ' '.join(t_def)
                        printf('<DEBUG> In newAddLocals, UNABLE to create %s', t_string)
                        
                        cont = module.getContainer()
                        x = cont.resolve(t_string)
                        printf('<DBG> In newAddLocals, %s resolved to %s', t_string, str(x))
                        
                    if i_def[1] in self.generics:  
                        ini = self.generics[i_def[1]]
                        t_string += ' = %s' % str(ini)
                                          
                        print >> design_file, 'LOCAL GENERIC %s NONE %s' % (i_def[1], t_string)
               
                    else:
                        ini = item.getInitialValue()
                        if ini:
                            
                            if i_cat == 'CONSTANT':
                                self.constants[i_def[1]] = ini
                                t_string += ' = %s' % str(ini).replace('"', '')
                            else:
                                # i_cat == 'SIGNAL'
                                if ini.getClass().getName().split('.')[-1] == 'IGOperationObject':
                                    cont = module.getContainer()
                                    s = str(cont.resolve(i_def[1]).getResult(0).getInitialValue())
                                    value = self.constants[s.split('(')[1][:-1]] 
                                    t_string += ' = %s' % value
                            
                        print >> design_file, 'LOCAL %s %s %s %s' % (i_def[0], i_def[1], i_dir, t_string)
                                           
#------------------------------------------------------------------------------

class Process_node(Node):
    
    def processFields(self):
        
        self.addLabel()
        
        module = self.parent.parent
        self.args = (self.label, module.label, module.dmuid.upper())
        print >> design_file, 'PROCESS %s %s:%s' % self.args
        
        # Include possible process-scope variables
        container = self.ig_obj.getContainer()
        
        for i in range(container.getNumLocalItems()):
            item = container.getLocalItem(i)

            cls_name = item.getClass().getName().split('.')[-1]
            if (cls_name == 'IGObject'):            
                if str(item.getCat() == 'VARIABLE'):
                    s = str(item).upper()
                    
                    name, td = s.split(' : ')
                    t_def = td.split()
                    if t_def[0] == 'STD_LOGIC':
                        t_string = t_def[0]
                    elif (t_def[0] == 'ARRAY') and (t_def[-1] == 'STD_LOGIC'):
                        t_string = 'STD_LOGIC_ARRAY %s %s %s' % tuple(t_def[1:4])
                    else:
                        t_string = '*%s*' % td
                    
                    # Process possible initializer
                    ini = item.getInitialValue()
                    if ini:
                        t_string += ' = %s' % str(ini).replace('"', '')
                        
                    print >> design_file, '%s %s' % (name, t_string)
                            
         
        self.statements = self.getSOS()

        code = CodeList(self.ig_sos)
        
        code.generate()

        code.output(module, self)
        print >> design_file, 'END_PROCESS'

    #----
                
    def addLabel(self):
        global process_id
        self.label = self.ig_obj.getLabel()    
        if self.label:
            pass
        else:
            self.label = 'ANON_%d' % (process_id,)
            process_id += 1
                                    
#------------------------------------------------------------------------------

class Mapping_node(Node):
    
    def processFields(self):
        
        self.ig_formal = self.ig_obj.getFormal().toHRString()
        self.ig_type   = self.ig_obj.getFormal().getType().toHRString()
        self.ig_dir    = self.ig_obj.getFormal().getDirection()
        t_def          = str(self.ig_type).upper().split()

        actual = self.ig_obj.getActual()               
        self.cls_name = str(actual.getClass().getName().split('.')[-1])
                
        if self.cls_name == 'IGOperationRange':
            # Process range in a port mapping
            self.ig_actual = actual.getOperand().toHRString()     
     
            if t_def[0] == 'STD_LOGIC':
                self.t_string = t_def[0]
                
            elif (t_def[0] == 'ARRAY') and (t_def[-1] == 'STD_LOGIC'):
                self.t_string = 'SLV_RANGE %s %s %s' % tuple(t_def[1:4])
                
            else:
                self.t_string = t_def[0]
            
        else:
            # Process one-to-one port mapping
            self.ig_actual = actual.toHRString()
            
            # Fix what seems to be a Zamia source typo
            if self.ig_actual.endswith(']'):
                self.ig_actual = self.ig_actual.replace(']', ')')
                self.ig_actual = self.ig_actual.replace('[', '(')
                
            if t_def[0] == 'STD_LOGIC':
                self.t_string = t_def[0]
                
            elif (t_def[0] == 'ARRAY') and (t_def[-1] == 'STD_LOGIC'):
                self.t_string = 'STD_LOGIC_ARRAY %s %s %s' % tuple(t_def[1:4])
                
            else:
                self.t_string = t_def[0]
                
    def emit(self):
        if self.cls_name == 'IGOperationRange':
            # with a range        
            args = (self.ig_dir, self.ig_formal, self.ig_actual, self.t_string)       
            print >> design_file, 'MAPPING %s %s %s %s' % args

        else:
            # Without range 
            args = (self.ig_dir, self.ig_formal, self.ig_actual, self.t_string)       
            print >> design_file, 'MAPPING %s %s %s %s' % args
                            
#------------------------------------------------------------------------------

class Operation_node(Node):
    
    def build(self, obj):
        printi(self.indent_num, 'Operation: %s', obj)
                            
#------------------------------------------------------------------------------

class SequentialWait_node(Node):
        
    def processFields(self):
        
        self.timeout = self.ig_obj.getTimeoutClause()
        self.condition = self.ig_obj.getConditionClause()
        self.sensitivity = []
        
        if self.timeout == None:
            self.timeout = 0.000000
        else:
            self.timeout = float(str(self.timeout)) / 1000000.0
    
        self.buildSensitivityList()
        ss = ', '.join(self.sensitivity)
        
    def buildSensitivityList(self):        
        ns = self.ig_obj.getNumSensitivityOps()
        for i in range(ns):
            s = self.ig_obj.getSensitivityListOp(i).toHRString() 
            self.sensitivity.append(s)
                                    
#------------------------------------------------------------------------------

class SequentialRestart_node(Node):
    
    def processFields(self):
        pass
                                
#------------------------------------------------------------------------------

class SequentialAssignment_node(Node):

    def processFields(self):
        
        self.target = self.ig_obj.getTarget().toHRString()
        self.value  = self.ig_obj.getValue().toHRString()        
        self.delay  = self.ig_obj.getDelay()
        self.reject = self.ig_obj.getReject()
        
        if self.delay == None:
            self.delay = 0.000000
        else:
            self.delay = float(str(self.delay)) / 1000000.0
                                                                                             
#------------------------------------------------------------------------------

class SequentialIf_node(Node):

    def processFields(self):
        
        self.cond = self.ig_obj.getCond()
        self.then = self.ig_obj.getThenSOS()
        self.els = self.ig_obj.getElseSOS()
                                        
#------------------------------------------------------------------------------

class StaticValue_node(Node):

    def processFields(self):
        self.value = self.ig_obj.toHRString()
                                
#------------------------------------------------------------------------------

class OperationArrayAggreate_node(Node):

    def processFields(self):
        self.value = self.ig_obj.toString()
                                
#------------------------------------------------------------------------------

class OperationInvokeSubprogram_node(Node):

    def processFields(self):
        printi(self.indent_num, 'OperationInvokeSubprogram_node')
                                    
#------------------------------------------------------------------------------

class LibraryImport_node(Node):
    pass
                                    
#------------------------------------------------------------------------------
#
# Map names to Node subclasses

name_to_class = {
    'IGStructure'                   : Structure_node,
    'IGInstantiation'               : Instantiation_node,
    'IGProcess'                     : Process_node,
    'IGMapping'                     : Mapping_node,
    'IGOperationObject'             : Operation_node,
    'IGSequentialAssignment'        : SequentialAssignment_node,
    'IGSequentialWait'              : SequentialWait_node,
    'IGSequentialRestart'           : SequentialRestart_node,
    'IGSequentialIf'                : SequentialIf_node,
    'IGStaticValue'                 : StaticValue_node,
    'IGOperationArrayAggregate'     : OperationArrayAggreate_node,
    'IGLibraryImport'               : LibraryImport_node,
    'IGOperationInvokeSubprogram'   : OperationInvokeSubprogram_node
}

#------------------------------------------------------------------------------
#
# Get design modules in depth first order

def moduleListDepthFirst():
    
    # Local function to recursively create a list
    # structure of nested design modules
    
    def scan(name):
            
        # Get the named design module
        dm = igm.findModule(Toplevel(DMUID.parse(name), None))
        
        # Find instances in the design module
        struct = dm.getStructure()
        ns = struct.getNumStatements()
        
        instances = []
        for i in range(ns):
            stmt = struct.getStatement(i)
            cls = stmt.getClass().getName().split('.')[-1]
            if cls == 'IGInstantiation':
                iname = str(stmt.getChildDUUID())    
                instances.append(iname)
                
        # Remove duplicates from instances
        instances = list(set(instances))                
        
        # Recursively process instances
        subs = []
        for inst in instances:
            subs = scan(inst)
            
        return subs + instances

    # End local function
                    
    # Get the name of the top level module
    igm = project.getIGM()
    bp = project.getBuildPath()
    tl = bp.getToplevel(0)
    tls = str(tl).split()
    print >> design_file, 'instance %s:%s' % (tls[0], tls[1])
    name = tls[1]
    
    # get the module structure
    return scan(name) + [name]


#------------------------------------------------------------------------------
#
# Get design modules in top-down order

def topDownModuleList(label):
    
    # Local function to recursively create a 
    # top-down list of nested design modules    
    def scan(name, instances):
            
        # Get the named design module
        dm = igm.findModule(Toplevel(DMUID.parse(name), None))
        if dm == None:
            # For some reason need to use the signature
            dm = igm.findModule(signatures[name])

        # Find instances in the design module        
        struct = dm.getStructure()
        ns = struct.getNumStatements()
        subs = []
        for i in range(ns):
            stmt = struct.getStatement(i)
            cls = stmt.getClass().getName().split('.')[-1]
            
            if cls == 'IGInstantiation':
                iname = str(stmt.getChildDUUID())    
                subs.append((str(stmt.getLabel()),iname))

                sig = stmt.getSignature()
                signatures[iname] = sig
                
        # Add found instances to the result
        result = instances + subs
        
        # recursively process found instances
        for m_label, m_name in subs:
            result = scan(m_name, result)
            
        return result
    
    # --------------- End local function ---------------
                                    
    # Get the name of the top level module
    igm = project.getIGM()
    bp = project.getBuildPath()
    tl = bp.getToplevel(0)
    name = str(tl).split()[1]
    signatures = {}
    
    # get the module list
    ml = scan(name, [(label, name)])
    return (ml, signatures)          

#------------------------------------------------------------------------------
#
# Check for errors in the project source files

def proj_error_chk():

    erm = project.getERM()
    error_count = erm.getNumErrors()
    if error_count > 0:
        
        # Project source file errors exist   
        printf('')
        printf('-------------------')
        printf('Found %d errors', error_count)
        printf('-------------------')
    
        for i in range(error_count):
            err = erm.getError(i).toString().split('\n')
            loc = erm.getError(i).getLocation()
            printf('  %s', err)
        
        # No further processing
    
        printf('')
        printf('----------------------')
        printf('design.txt NOT updated')
        printf('----------------------')

        return True
    
    else:
        return False

#------------------------------------------------------------------------------
#
# Return True if ig_export.py has changed since design.text was last created,
# or if design.txt does not exist 

def ig_exp_changed():
	
    # Get timestamp of design.txt
    try:
        design_timestamp = os.path.getmtime(dsnPath)
    except:
        # design.txt does not exist
        design_timestamp = 0
        printf('Rebuilding since design.txt does not exist\n')
        return False 
           
    try:
        exp_timestamp = os.path.getmtime(proj_path + r'\ig_export.py')
    except:
        exp_timestamp = 0    

    if exp_timestamp > design_timestamp:
        printf('Rebuilding since export.py has been changed')
        return True
    else:
        return False

#------------------------------------------------------------------------------
#
# Return True if any design .vhd file is more recent than design.txt

def design_file_obsolete():

    # Get timestamp of design.txt
    try:
        design_ts = os.path.getmtime(dsnPath)
    except:
        # design.txt does not exist
        design_ts = 0
 
    # Compare with time stamp of source files
    for f in project.fBasePath.getFiles():
        if str(f).endswith('.vhd'):
            source_ts = os.path.getmtime(str(f))
            if source_ts > design_ts:
                printf('Rebuilding since source file %s has changed', str(f)) 
                return True
                
    return False
    
#==============================================================================
#
# Main

# THIS IS FOR DEBUG
force_build = True
# force_build = False

printf ('-----------------------')
printf ('pysim_boot.py - 1/23/16')
printf ('-----------------------')
printf ('')

# Initialize globals
proj_path = project.fBasePath.toString()
dsnPath   = proj_path + r'\design.txt'
printf('Project path: %s', proj_path)

dir1, base = os.path.split(proj_path) 
dir2, base = os.path.split(dir1)
share_path = dir2 + r'\Runtime\share\python'

# Not used!!
plugin_path = dir2 + r'\Runtime\plugins\org.zamia.plugin_0.11.3.jar'

subMgr = SubManager()

#-------------------------------------------------------------
#
# First task is to update design.txt if necessary
#
# Update logic (Note that ZamiaCAD keeps IG up to date) :
#
# 1. If ZamiaCAD project has errors, then don't run ig_export.
#
# 2. If ig_export has been changed since design.txt was created then:
#     need to run ig_export.
#
# 3. If design.txt doesn't exist  
#     need to run ig_export.
#
# 4. If design files have been changed since design.txt was created then:
#     need to run ig_export.
#
# 5. If force_build is True then: need to run ig_export.

status = 'unchanged'

if proj_error_chk() == True:
    # Error(s) in source files. Nothing more to do
    status = 'src_err'

elif ig_exp_changed() or design_file_obsolete() or force_build:

    # Rebuild design.txt

    design_file = open(dsnPath, 'w')
    
    igm = project.getIGM()
    IGManager = igm
    top_label = project.getId().upper()
    modules, signatures = topDownModuleList(top_label)

    status = 'OK'
    
    print >> design_file, 'DESIGN %s' % top_label
    
    for label, dmuid in modules:
        
        uid = DMUID.parse(dmuid)
    
        design_module = igm.findModule(Toplevel(uid, None))
        if design_module == None:
            design_module = igm.findModule(signatures[str(uid)])
    
        zdb = design_module.getZDB()
        
        node = Module_node(None, zdb, dmuid).build(design_module, label)
        
    subMgr.dump()
    
    print >> design_file, 'END_DESIGN'
    
    design_file.close()

    printf('')
    printf('Export done')
    printf('')

if status != 'error':
    
    #-------------------------------------------------------------

    if status == 'unchanged':
        # design.txt is up to date
        printf('')
        printf('------------------------')
        printf('design.txt is up to date')
        printf('------------------------')
    
    #-------------------------------------------------------------
    #
    # Now simulation can be run
    #
    # py_interpreter can be 'python' or 'pypy'
    
    process = Popen([py_interpreter, share_path + r'\Sim\sim_exec.py', proj_path], stderr=PIPE, stdout=PIPE)
    
    out = process.stdout.read()
    err = process.stderr.read()
    
    for line in re.split("\n+", out):
      if line:
        printf("%s", line[:-1])
    
    for eline in re.split("\n+", err):
      if eline:
        printf("%s", eline[:-1])
        
else:
    printf("Errors during export, SIMULATION ABORTED")    

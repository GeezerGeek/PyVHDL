#------------------------------------------------------------------------------
#
#   PyModule.py - 2/19/16
#
#   Python simulation module & process classes
#
#------------------------------------------------------------------------------

import stackless as ss

import sys, os.path, os, imp, logging
from heapq import heappush

from sim_events import ComparableEvent, SignalEvent, DelayEvent
                
#------------------------------------------------------------------------------
#
# Global wait functions

def waitFor(t=sys.maxint):
    
    # If called as 'waitFor()', then will essentially wait for ever (sys.maxint)
    
    # Put DelayEvent on queue
    task    = ss.getcurrent()
    process = task.proc
    heappush(process.sim.queue, DelayEvent(process, t))
            
    # Here process that called wait.. suspends
    task.proc.channel.receive()
    
#----

def waitOn(sig):
        
    vm = ss.getcurrent() 
    proc = vm.proc    
    # equivalent to vm.addWakeup(self, sig)  
    proc.wakeups.append(sig)
    sig.waiting.add(proc)
            
    # Suspend process that called waitOn(sig)   
    discard_list = vm.proc.channel.receive()    
    discard_list.append((sig, proc))
 
#------------------------------------------------------------------------------
#
# A property class for SigContainer items

class ItemProperty(object):
    
    def __init__(self, name):
        # Note that VHDL parser converts names to upper case
        self.name = name        
        
    def __get__(self, obj, objtype=None):
        return obj.itemDict[self.name]
        
    def __set__(self, obj, val):
        sig = obj.itemDict[self.name]
        if isinstance(val, Delayed):
            v = val.value
            delay = val.delay
        else:
            v = val
            delay = 0
        
        # Schedule the assignment
        process = ss.getcurrent().proc
        process.scheduleAssignment(sig, v, delay, 0, True)
         
#------------------------------------------------------------------------------
#
# PYModule.ports is an instance of this class

class SigContainer(object):
    
    def __init__(self, py_mod):
        
        self.module    = py_mod    # The PyModule object                
        self.itemDict  = {}
        self.itemList  = []
    
    def addSignal(self, name, signal):
        
        self.itemDict[name] = signal
        self.itemList.append(signal)        
        setattr(self.__class__, name, ItemProperty(name))

#------------------------------------------------------------------------------

class PyModule:
    
    def __init__(self, simulator, key):       

        self.sim        = simulator
        self.testBench  = None      # The python tesbench module object
        self.instance   = None 
        self.key        = key
        self.ports      = SigContainer(self)
        
        self.port_data  = []        # For __getstate__
        
        self.file_name  = ''
                       
    #----
    #
    # Load a python testbench file
    #
    # This can't be called until sim.signals are deserialized
    
    def load(self, file_name, key, port_list):
        
        logging.error('PyModule.load started')       
                
        self.instance  = None
        
        self.file_name = file_name
        self.key       = key
        self.port_list = port_list

        self.testbenchImport()
                
        # Setup ports
        self.testBench.module = self

        for name, sid in self.port_list:
            sig = self.sim.signals[sid]
            self.ports.addSignal(name, sig)
            
            # For self.__getstate__
            self.port_data.append((name, sid))
                    
        # Run setup function in self.testBench
        self.testBench.setup(self, self.ports)
                       
    #----
    #
    # import a python simulation module
    
    def testbenchImport(self):
                
        name = os.path.splitext(os.path.basename(self.file_name))[0]
         
        print 'Python module import: %s:%s' % (self.file_name, name)
        
        p1 = sys.path
        sys.path.insert(0, os.path.dirname(self.file_name))        
        fp, pathname, description = imp.find_module(name)        
        logging.error('PyModule > fp %s' % fp)       
        
        try:
            self.testBench = imp.load_module(name, fp, pathname, description)
        finally:
            sys.path = p1
            if fp:
                fp.close()
        
    #----
    
    def addProcess(self, process):
        logging.info('PyModule > addProcess %s' % process)

        process.setup(self, self.sim, self.key)

        self.sim.vm_list.append(process)
        
    #----
    
    def addClock(self, signal, t_high, t_low):
        cp = ClockProcess(self.sim, signal, t_high, t_low)
        self.sim.vm_list.append(cp)
            
    #----

    def waitOn(self, sig):
                    
        self.wakeups.append(sig)
        sig.waiting.add(self)
                
        # Suspend process that called waitOn(sig)   
        self.channel.receive()        
             
    #----
    #
    # Persistence
        
    def __getstate__(self):
        
        result = [self.file_name, self.port_data, self.key]       
        return result
        
    #----
    
    def __setstate__(self, serialized):
        
        self.file_name, port_data, self.key = serialized
        
        # convert unicode to UTF-8
        self.port_data = [(name.encode('utf-8'), sid) for name, sid in port_data]
                               
        self.testbenchImport()
        self.testBench.module = self
        
    #----
        
    def rebuild(self, sim):
        self.sim      = sim
        self.ports    = SigContainer(self)
        
        # Setup ports
        signals = sim.signals
        for name, sid in self.port_data:
            
            self.ports.addSignal(name, signals[sid])
                    
        # Run setup function in self.testBench
        self.testBench.setup(self, self.ports)

#------------------------------------------------------------------------------
#
# A class to contain signal values with a delay

class Delayed(object):
    
    def __init__(self, value, delay):
        self.value = value
        self.delay = delay
         
#------------------------------------------------------------------------------
#
# This subclass allows tasklet attributes to be created & accessed

class TB_Tasklet(ss.tasklet):
    pass
            
#------------------------------------------------------------------------------
#
# A class for Python based processes. Equivalent to a VM

class Process:
    
    __slots__ = ('sim', 'key', 'name', 'id', 'module', 'initialize', 'setup',
                 'run_start', 'run_step', 'run_loop', 'scheduleAssignment',
                 'vm_name', 'task', 'channel', 'wakeups','__getstate__','__setstate__' 
                 )

    def __init__(self):       
        self.sim      = None
        self.key      = ''
        self.name     = ''
        self.id       = None
        self.module   = None
        
    # Method overridden if needed by Process instances
    def initialize(self):
        pass
            
    # Called from PyModule.addProcess        
    def setup(self, module, sim, key, ports=None):

        self.sim     = sim
        self.key     = key
        self.name    = str(self).split()[0][1:]
        self.id      = len(self.sim.vm_list)
        self.module  = module
        
        logging.info('PyModule > setup:  Process %s, %d' % (self.name, self.id))
        
        # call initialize method
        if ports == None:
            P = self.module.ports
        else:
            P= ports
            
        self.initialize()
        
        # Simulation stuff
        self.queue   = sim.queue 
                    
    #----
        
    def run_start(self, sim=None):
                
        # Setup tasklet and channel
        self.task      = TB_Tasklet(self.run_step)()
        self.task.proc = self        
        self.channel   = ss.channel()
        self.wakeups = []
            
    #----
        
    def run_step(self):
                
        msg = self.channel.receive()
        
        self.module.current_process = self 
        self.run(self.module.ports, [])
        self.module.current_process = None
                 
    #----
    
    def scheduleAssignment(self, target, operand, delay, reject, inertial):
        
        # target  = aSignal
        # operand = aValue
        # delay   = aTime in ns        
        # reject & inertial are ignored for now
        
        heappush(self.queue, SignalEvent(self, target, operand, float(delay)))
            
#----

    def waitOn(self, sig):
                    
        self.wakeups.append(sig)
        sig.waiting.add(self)
               
        # Suspend process that called waitOn(sig)   
        self.channel.receive()

    #----
    
    def waitRising(self, sig):
        
        while True:
            self.waitOn(sig)
            # Yes, this is correct
            if '%s' % sig == '0':
                break                             

    #----
    
    def waitFalling(self, sig):
        
        while True:
            self.waitOn(sig)
            # Yes, this is correct
            if '%s' % sig == '1':
                break                             
    #----
     
    def vm_name(self):       
        return 'PyProcess - %s/%s' % (self.key, self.name.split('.')[1])

#------------------------------------------------------------------------------

class CPchannel(object):
                
    # This is a no-op that is only called by startEvent
    def send(self, message):
        return
                                    
#------------------------------------------------------------------------------

class CPinstance(object):
                
    # This is for compatibility of ClockProcess with other process instances 
    def __init__(self, sig):
        self.sig = sig
        self.key = 'ClockProcess pseudo-instance for %s' % self.sig.name
                                    
#------------------------------------------------------------------------------
#
# This class behaves like a process and can also be put on the event queue like
# a signal event.
 
class ClockProcess(ComparableEvent):
    
    __slots__ = ('sim', 'queue', 'id', 'name', 'signal', 't_high', 't_low',
                 'time', 'channel', 'enc_val', 'str_val', '__init__', 'inst',
                 'run_start', '__cmp__', 'operate', 'vm_name', 'wakeups', '__str__',
                 'priority', 'evt_cycle'
                )
                
    def __init__(self, sim, signal, t_high, t_low):
        
        # Setup stuff
        self.sim     = sim
        self.queue   = sim.queue
        self.id      = len(self.sim.vm_list)
        self.name    = 'ClockProcess%d' % self.id
        self.inst    = CPinstance(signal)
        self.priority = 1

        # Simulation stuff
        self.signal  = signal
        self.t_high  = t_high
        self.t_low   = t_low
        self.time    = self.t_high
        
        self.channel = CPchannel()
        
        self.enc_val = 2
        self.str_val = '0'         
            
    #----
        
    def run_start(self, sim=None):
        
        # Start high
        self.signal._val = 3
        self.time        = self.t_high 
        self.wakeups     = []
        
        heappush(self.queue, self)
       
    #----
    # This method is called when an instance of this class is popped from the
    # queue, as if it was a SignalEvent.
     
    def operate(self, cycle):
        
        sig      = self.signal
        sig.last = sig.current
        sig.evt_cycle = cycle
            
        # Process transitions for VDC file
        if sig.vcd_mgr:
                            
            for node in sig.vcd_nodes:
                sig.vcd_mgr.VCD_transition(sig, node, self.time)
        
        # Schedule next event. This is now compatible with JumpNotRising
        old_time = self.time
        if sig._val == 3:            
            sig._val = 2
            sig.current = ('1', self.time)
            self.time += self.t_high
            
        else:
            sig._val = 3
            sig.current = ('0', self.time)
            self.time += self.t_low
            
        # Self is put on event queue like a SignalEvent
        heappush(self.queue, self)
        
        # Return a list of VMs
        return sig.waiting
    
    #----
    
    def __str__(self):
        return 'ClockProcess event: %s <= %s at %.2f' % (self.signal.name, self.signal.current, self.time)
        
    #----
            
    def vm_name(self):
        return self.name
                        
#------------------------------------------------------------------------------
#
#  event_compare.py - 2/5/16
#
#  Superclass of objects used with sim.queue. Facilitates priority sorting 
#   
#------------------------------------------------------------------------------

import logging

#------------------------------------------------------------------------------

class ComparableEvent(object):
            
    def __lt__(self, other):
        
        if self.time == other.time:
            return self.priority < other.priority
        
        if self.time < other.time:
            return True
        
        if self.time > other.time:
            return False
                
#------------------------------------------------------------------------------

class SignalEvent(ComparableEvent):
    
    evt_id = 1
    
    __slots__ = ('target', 'operand', 'time', 'priority', 'operate', '__str__', 'vm')
                         
    def __init__(self, vm, target, operand, delay):
        
        self.target  = target
        self.operand = operand
        self.time    = float(delay) + vm.sim.time
        
        self.priority = SignalEvent.evt_id # Before all but stop
        
        # Increment value used to keep SignalEvents in FIFO order in event queue
        SignalEvent.evt_id += 1
            
    #----
    
    def operate(self, cycle):
        # Return a list of processes to resume 
        return self.target.updateValue(self.operand, cycle, self.time)
    
    #----
    
    def __str__(self):
        return 'SignalEvent at %.2f, %s <= %s, priority = %d' % (self.time, self.target.name, self.operand, self.priority)

#------------------------------------------------------------------------------

class DelayEvent(ComparableEvent):

    __slots__ = ('vm_list', 'time', 'priority', 'operate', '__cmp__', '__str__')
        
    def __init__(self, vm, delay=0.0):
               
        self.vm_list  = [vm]
        self.time     = float(delay) + vm.sim.time
        self.priority = 10002 # After signal events
        
    #----
    
    def operate(self, cycle):
        return self.vm_list
     
    #----
    
    def __str__(self):
        return 'DelayEvent: %.2f ns' % self.time
       
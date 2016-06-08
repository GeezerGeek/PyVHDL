#------------------------------------------------------------------------------
#
#   simSignal.py - 12/29/13
#
#   Signal class for a VM based simulator
#
#------------------------------------------------------------------------------

import logging

class SimSignal(object):
    
#    __slots__ = ('sim', 'current', 'last', 'waiting', 'vcd_manager', 'vcd_nodes',
#                 'initialize', 'updateValue', 'enableVCD', 'event',
#                 'addWakeup', 'cancelWakeup', 'getMethod'
#                 )
        
    def __init__(self):
        pass
    
    #----
    
#    def initialize(self, sim):
#        
#        print 'SimSignal.initialize()'
#               
#        self.sim        = sim
#                
#        self.current    = [self._val, 0.0]
#        self.last       = [self._val, 0.0]
#        
#        self.waiting    = set()
#        
#        # VCD attributes
#        self.vcd_manager  = None 
#        self.vcd_nodes    = []

    #----
    
#    def updateValue(self, operand, time):
#        
#        if str(operand) != str(self):
#            # Value has changed. Dispatch to subclass method
#            self.setValue(operand)
#                
#            # Process transitions for VDC file
#                
#            if self.vcd_manager:
#                # This would probably be faster with a single call to vcd_manager
#                for node in self.vcd_nodes:
#                    self.vcd_manager.VCD_transition(self, node, time)
#            
#            self.last = self.current
#            self.current = (str(self), time)
#                                             
#            # Return set of waiting VMs & processes
#            return self.waiting
#            
#        # Value hasn't changed, return empty waiting set
#        #logging.error('Update value of unchanged signal %s' % self.name)
#        return set()
        
    #----
    
#    def enableVCD(self, var_id, vcd_method):
#        
#        self.var_id     = var_id
#        self.vcd_method = vcd_method
#        self.vcd_trace  = True            
              
   
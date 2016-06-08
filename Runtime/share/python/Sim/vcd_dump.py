#------------------------------------------------------------------------------
#
#   vcd_dump.py - 1/28/16
#
#   Classes to manage VCD dump files
#
#------------------------------------------------------------------------------

import time, sys, logging

#------------------------------------------------------------------------------

#
# Manage ASCII id characters

class IDchar(object):
    
    # Class variable for getNextID
    int_id = 0
    
    #----
        
    def getID(self):
        return IDchar.int_id 
             
    #----
        
    def getStringID(self):
        return self.int2str(IDchar.int_id) 
             
    #----
    
    def NextID(self):
        # Bump value of int_id         
        IDchar.int_id += 1
          
    #----
    
    def str2int(self, s):
        # Return integer value of string identifier         
        
        ls_char = ord(s[0]) - 33
        
        try:
            ms_char = ord(s[1]) - 33
        except IndexError:
            ms_char = 0
            
        modulo = ord('}') - ord('!') + 1
        return ms_char * modulo + ls_char
    
    #----
    
    def int2str(self, i):        
        # Return an identifier string                
        q,r = divmod(i, ord('}') - ord('!') + 1)
                
        if q > 92:
            raise ValueError, "VCD index overflow"        
        elif q > 0:
            return chr(r+ord('!')) + chr(q+ord('!'))       
        else:
            return str(chr(r+ord('!')))
     
#-------------------------------------------------------------------------------

class VCD_File(object):
        
    def __init__(self, hierarchy, signals, f):
        
        self.f           = f
        self.top         = hierarchy
        self.signals     = signals
        
        # a list of SL_var or SLArray_var objects
        self.vcd_nodes = []
        
        # Set True after genInitial done
        self.started   = False
        
        self.id_char = IDchar()
        
        # Initialize current time
        self.current_time = 0
                        
    #----
    #
    # Add instance nodes to VCD variable list
    
    def add(self, url):
                
        # Local function to add a local node(PORT/SIGNAL)
        # to list of VCD variables
        
        def add_node(name, node, inst):
           
            sig = self.signals[node.sid]
            
            # Mark node for self.GenerateHeader()
            node.vcd_enable = True
            # Update instance attribute for self.GenerateHeader() 
            inst.vcd_count += 1            
            # Create a var object
            node_type = node.node_type
            if node_type == 'STD_LOGIC':
                node.var_obj = SL_var(name, node, sig, self.id_char.getStringID())
                self.id_char.NextID()
                
            elif node_type == 'STD_LOGIC_ARRAY': 
                node.var_obj = SLArray_var(name, node, sig, self.id_char.getStringID())
                self.id_char.NextID()
                
            else:
                print 'Cannot create VCD variable for %s' % node_type
                return
            
            # Add var object to vcd_nodes of this class
            self.vcd_nodes.append(node.var_obj)
            
            # Add var object to vcd_nodes of associated signal
            sig.vcd_nodes.append(node.var_obj)
            # Setup vcd_manager attribute of signal
            sig.vcd_mgr = self
            
            # Mark node for self.GenerateHeader()
            node.vcd_enable = True
            # Update instance attribute for self.GenerateHeader() 
            inst.vcd_count += 1
            
            # Update on_vcd_path attributes for self.GenerateHeader()                               
            p = inst
            while True:
                p.on_vcd_path = True
                p = p.parent
                if p == None:
                    break
         
        #----
        #
        # Recursively build a list of all locals in design 
        # Currently these are signals, but not ports
        
        def getAllLocals(inst, all):
            names = inst.sig_nodes.keys()
            names.sort()
            for name in names:
                all.append((name.lower(), inst.sig_nodes[name], inst))
                
            for name, child in inst.children.items():
                getAllLocals(child, all)
                
        #---- End local functions
        
        elements = url.split('/')
        
        if url == '*':
            # Get all signals in design for ZamiaCAD VCD file
            all_locals = []
            getAllLocals(self.top, all_locals)

            for name, node, inst in all_locals:                
                # filter out internally created signals
                if name.endswith('_i_n_t'):
                    continue
                add_node(name, node, inst)
                
            return
                
        elif len(elements) == 1:
            # Just a signal in the top instance
            inst = self.top
            signal = elements[0]
            path = []
        
        else:
            try:
                signal = elements[-1]
                path   = elements[:-1]
            except IndexError:
                raise ValueError, 'Cannot find %s, %s' % (url, elements)
                    
            if path[0] == '':
                # first element is '/'. Start from top
                inst = self.top
                # replace '/' with top inst.label
                path[0] = inst.label
                
                relative = False
                
            elif path[0] == '.':
                # Relative to current
                inst = self.current_inst
                path = path[1:]
                relative = True
            
            else:
                raise ValueError, 'Cannot find %s, path[0] >%s< ' % (url, path[0])
        
            # Process instance hierarchy path elements
            for i in range(len(path)):
                if (i == 0) and not relative:
                    # At start
                    pn = inst.label
                    if pn != path[i].upper():
                        raise ValueError, 'Cannot find %s (%s)' % (url, pn)
                                        
                else:
                    # Below start
                    try: 
                        inst = inst.getChild(path[i].upper())               
                    except KeyError:
                        raise ValueError, 'Cannot find %s (%s)' % (url, path[i].upper())

        # Process signal name path element(s)
        try:
            if signal == '*':                       
                # Get all signals in instance
                for key,node in inst.local_nodes.items():
                    
                    if node.sig_spec[0] == 'SIGNAL':                    
                        # Add a var object to self.vcd_nodes
                        add_node(key, node, inst)
                                                                   
            else:
                # Get an individual signal
                node = inst.sig_nodes[signal.upper()]
                    
                # Add a var object to self.vcd_nodes
                add_node(signal, node, inst)
                
        except KeyError:
            raise ValueError, 'Cannot find %s (%s)' % (url, signal.upper())
                          
    #----
    #
    # Create VDC header lines
    #
    # 8/18/15 - Zamiacad VCD processing cannot handle an instance label and
    # a signal with the same name. This is a Zamiacad bug!
    # Work around the bug by checking for name clashes in this method 
    
    def GenerateHeader(self):
        
        # Local function to generate $scope and $var statements
        
        all_labels  = set()
        all_signals = set()
        
        def define_var(inst):
            if inst.on_vcd_path:
                if inst != self.top:
                    
                    label = inst.label
                    if label in all_signals:
                        # Raise an exception
                        raise NameError, 'VCD name reused: %s' % label
                    
                    all_labels.add(label)
                    print >> self.f, "$scope module %s $end" % label.lower()
                
                # Generate $var statements for selected signals
                if inst.vcd_count:
                    
                    names = inst.sig_nodes.keys()
                    names.sort()
                    for k in names:                        
                        if k in all_labels:
                            # Raise an exception
                            raise NameError, 'VCD name reused: %s' % k
                        
                        all_signals.add(k)                        
                        node = inst.sig_nodes[k]
                        if node.vcd_enable:
                            print >> self.f, node.var_obj.gen_var()                               
                
                # Process child instances
                for child in inst.children.values():
                    # Recursively call this method
                    define_var(child)
                
                if inst != self.top:
                    print >> self.f, "$upscope $end"
        
        # End local function
        
        # Basic header stuff
        print >> self.f, '$date'
        print >> self.f, '  %s' % time.asctime()
        print >> self.f, '$end'

        print >> self.f, '$version'
        print >> self.f, '  ZamiaCAD + PyVHDL 0.1.0'
        print >> self.f, '$end'
        
        print >> self.f, '$timescale'
        print >> self.f, '  1 ns'
        print >> self.f, '$end'
        
        # Generate $scope and $var statements starting at top instance
        define_var(self.top)
        
        print >> self.f, '$enddefinitions $end'
                                      
    #----
    #
    # Generate initial values
    
    def genInitial(self, signals):

        # Time = 0
        print >> self.f, "#0"
        for var in self.vcd_nodes:
            print >> self.f, var.gen_dump()            
        
        self.started = True
            
    #----
    #
    # Generate VCD signal transition statements     
                     
    def VCD_transition(self, signal, var_obj, time):
        if self.started:        
            if time != self.current_time:
                print >> self.f, '#%d' % time
                self.current_time = time

            print >> self.f, var_obj.gen_dump()
                                                    
    #----    
                     
    def close(self):
        
        if self.f != sys.stdout:
            self.f.close()

#------------------------------------------------------------------------------
#
# Std_logic VCD Variable

class SL_var(object):
        
    def __init__(self, name, node, sig, id_string):
        
        self.name   = name
        self.sig    = sig
        self.var_id = id_string
          
    #----
    
    def gen_var(self):
        args = (self.var_id, self.name.lower())
        return '$var reg 1 %s %s $end' % args       
          
    #----
    
    def gen_dump(self):
        # Return value + id        
        return '%s%s' % (self.sig.VCD_str().upper(), self.var_id)
          
    #----
    
    def gen_dumpx(self):
        return 'X%s' % self.var_id

#------------------------------------------------------------------------------
#
# Std_logic_array VCD Variable

class SLArray_var(object):
        
    def __init__(self, name, node, sig, id_string):
        
        self.name   = name
        self.sig    = sig
        self.var_id = id_string
          
    #----
    
    def gen_var(self):
    
        inc = self.sig._dir
        if inc == 1:
            # Process LSB to MSB
            first = self.sig._min
            last  = self.sig._max + 1
            # A string with LSB at index 0            
        else:
            # Process MSB downto LSB
            first = self.sig._max
            last  = self.sig._min - 1
                                    
        # Populate args
        args       = {}                    
        args['width'] = abs(first - last)
        args['id']    = self.var_id   
        args['name']  = '%s[%d:%d]' % (self.name.lower(), first, last+1)
                                     
        s = '$var reg {width} {id} {name} $end'
        return s.format(**args)
      
    #----
    
    def gen_dump(self):
        if self.sig._dir == -1:
            # Return to MSB to LSB value
            return 'b%s %s' % (self.sig.VCD_str()[::-1].upper(), self.var_id)
        else:   
            # Return to LSB to MSB value
            return 'b%s %s' % (self.sig.VCD_str().upper(), self.var_id)

    #----
    
    def gen_dumpx(self):
        s = 'X' * len(self.var_id)
        return '%s %s' % (s, self.var_id)
         
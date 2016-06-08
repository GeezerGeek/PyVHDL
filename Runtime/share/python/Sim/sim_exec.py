#------------------------------------------------------------------------------
#
#   C:\Projects\Zamiacad-0-11-3\Runtime\share\python\py_sim\sim_exec.py
#
#   1/28/16
#
#   Run a simulation of the design in the named project directory
#
# Command: python sim_exec.py <project_directory_name>
#
#------------------------------------------------------------------------------
#-                        This is a Python file                               -
#------------------------------------------------------------------------------

import sys, platform

#-------------------------------------------------------------------------------
# Imports for python 2.6
#-------------------------------------------------------------------------------
	
# pp = ['C:\windows\system32\python26.zip',
#    	  'C:\Software_Tools\Python26\DLLs',
#    	  'C:\Software_Tools\Python26\lib',
#    	  'C:\Software_Tools\Python26\lib\plat-win',
#    	  'C:\Software_Tools\Python26'
# ]
	
# 	print
# 	print '------------------------------------------'
# 	print 'Running sim_exec.py on CPython 2.6 1/4/16'
# 	print '------------------------------------------'
# 	print
	
#-------------------------------------------------------------------------------
# Imports for Stackless Python 2.7
#-------------------------------------------------------------------------------

ex_path = '\\'.join(sys.executable.split('\\')[:-1])
	
pp = ['C:\windows\system32\python27.zip',
	'%s\DLLs' % ex_path,
	'%s\lib' % ex_path,
	'%s\lib\plat-win' % ex_path,
	'%s' % ex_path
]

print
print '-----------------------------------------------------'
print 'Running sim_exec.py on Stackless Python 2.7  1/4/16'
print '-----------------------------------------------------'
print
	
#-------------------------------------------------------------------------------
# Imports for PyPy 2.7
#-------------------------------------------------------------------------------
	
# pp = ['C:/Software_Tools/pypy-2.5.1-win32/lib_pypy/__extensions__',
# 	'C:/Software_Tools/pypy-2.5.1-win32/lib_pypy',
# 	'C:/Software_Tools/pypy-2.5.1-win32/lib-python/2.7'
# ]
# 
# print
# print '-----------------------------------'
# print 'Running sim_exec.py on PyPy 1/4/16'
# print '-----------------------------------'
# print

sys.path = pp

import re, os, shutil, sys, logging
from time import clock, strftime, localtime
import cProfile, dis

#------------------------------------------------------------------------------

# Waste less time checking for another thread to run
sys.setcheckinterval(200000)

try:
    # argv[1] is the complete project path
    project_path = sys.argv[1]
    os.chdir(project_path)

except WindowsError:
    print 'Project directory %s does not exist' % sys.argv[1]
    exit(1)

print 'Running simulation at : %s' % project_path

#-------------------------------------------------------------------------------
# SETUP LOG FILE
#-------------------------------------------------------------------------------

# Debug level enables itself and all levels below. Choose one

dbg_level = logging.DEBUG
#dbg_level = logging.INFO
#dbg_level = logging.WARNING
#dbg_level = logging.ERROR
#dbg_level = logging.CRITICAL

log_file_name = project_path + '\\sim_log.txt'
logging.basicConfig(filename=log_file_name, filemode='w', level=dbg_level)
logger = logging.getLogger(__name__)

# Locate the simulator python source files

f_path = os.path.dirname(__file__)
location = os.path.realpath(os.path.join(os.getcwd(), f_path))

py_path = os.path.dirname(location)
sys.path.append(py_path)

# Simulator python source file imports
from Sim.design_parser import Design, Parsing_Exception
from Sim.interp import SimBuilder, SimExe
from Sim.vcd_dump import VCD_Filefrom Sim.PyModule import Process, waitFor, waitOn
 
#-------------------------------------------------------------------------------
#
# Run the simulation. This function allows profiling to be done

def runSim(sim, start_time):
	
	sim.run()
	
	end_time = clock()	
	print 'Elapsed time = %.4f' % (end_time - start_time)
	print 'Simulation time = %.2f ns' % sim.time
	print

#-------------------------------------------------------------------------------
#
# If design.ser is more recent than design.txt,
# 	then load design.ser
# Else,
#	run design parser & create design.ser 
#  

ser_path  = 'design.ser'
dsn_path  = 'design.txt'

   
dsn_ts    = os.path.getmtime(dsn_path)
print 'dsn_ts: %s' % strftime('%a %b. %d, %H:%M', localtime(dsn_ts))

try:
	ser_ts = os.path.getmtime(ser_path)
	print 'ser_ts: %s' % strftime('%a %b. %d, %H:%M', localtime(ser_ts))
	if ser_ts > dsn_ts:
        # design.ser is up to date
		serialize = False
	else:
        # design.txt is more recent than design.ser
		serialize = True
		 
except WindowsError:
    # design.ser does not exist
	print 'design.ser does not exist'
	serialize = True

###############################
# Force serialization if True #
###############################

serialize = True

print 'serialize = %s' % serialize


#-------------------------------------------------------------------------------

if serialize:
        
	print
	print 'Starting design_parser'
	des = Design('design.txt')
	print 'Design parsing done'
	
	try:
		des.build()
		print 'Design object built'
 		status = True
 	
	except Parsing_Exception, msg:
	    print msg
	    print des.lines.line
	    logging.info('Parsing Exception %s' % msg)
	    print 'Parsing Exception %s at %s' % (msg, des.lines.line)

	    status = False

else:
    # Skip design parser and SimBuilder
	status = True
	des    = None
	print 'Skipping design parser and SimBuilder'
	print

if status:
    # Design parsing successful
   	if serialize:   		    	       
	    build = SimBuilder(des, project_path)
	    build.serialize()
	    
	start_time = clock()
	sim = SimExe()
	sim.initialize()
	
	#---------------------------------------------------------------------------
	#
	# For listing referenced modules
	
# 	from modulefinder import ModuleFinder
# 
# 	finder = ModuleFinder()
# 	finder.run_script('runSim(sim, start_time)')
# 	
# 	print 'Loaded modules:'
# 	for name, mod in finder.modules.iteritems():
# 	    print '%s: ' % name,
# 	    print ','.join(mod.globalnames.keys()[:3])
# 	
# 	print '-'*50
# 	print 'Modules not imported:'
# 	print '\n'.join(finder.badmodules.iterkeys())

	#---------------------------------------------------------------------------	
	    
	# Run without profiling
	runSim(sim, start_time)
	
	# Run with profiling 
 	# cProfile.run('runSim(sim, start_time)')
	    
	
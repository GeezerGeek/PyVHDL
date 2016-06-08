#------------------------------------------------------------------------------
#
#   C:\Projects\Zamiacad-0-11-3\Runtime\share\python\Sim\pypy_sim.py
#
#   1/28/15
#
#   Run a simulation of the design in the named project directory.
#
# Command: pypy pypy_sim.py <project_directory_name ie. spi-3>
#
#------------------------------------------------------------------------------

import sys, os, logging
from time import clock

# Duplicated on line 55!
sys.path.append(r'C:\Projects\Zamiacad-0-11-3\Runtime\share\python')
from interp import SimExe

#------------------------------------------------------------------------------

# Set this as needed by installation
home = r'C:\Projects\Zamiacad-0-11-3\Workspace'

try:
    project = '\\' + sys.argv[1]
    os.chdir(home + project)

except WindowsError:
    printc
    print 'Project directory %s does not exist' % sys.argv[1]
    exit(1)

print
print 'Running project at : %s' % home + project

# Debug level enables itself and all levels below

dbg_level = logging.DEBUG
#dbg_level = logging.INFO
#dbg_level = logging.WARNING
#dbg_level = logging.ERROR
#dbg_level = logging.CRITICAL

log_file_name = home + project + '\\sim_log.txt'
logging.basicConfig(filename=log_file_name, filemode='w', level=dbg_level)
logger = logging.getLogger(__name__)


print
print '------------------'
print 'Starting simulator'
print '------------------'

sys.path.append(r'C:\Projects\Zamiacad-0-11-3\Runtime\share\python')
from interp import SimExe

start_time = clock()
sim = SimExe()
sim.initialize()    

sim.run()
    
end_time = clock()    
print 'Elapsed time = %.4f' % (end_time - start_time)
print 'Simulation time = %.2f ns' % sim.time
print
    
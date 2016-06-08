::------------------------------------------------------------------------------
::
:: Startup CLI version of PyVHDL with the default workspace
::
:: This file MUST be in the top Zamiacad+PyVHDL folder 
::
::------------------------------------------------------------------------------

set drive=%~dp0
set drivep=%drive%

SET PYTHONPATH=%drivep%Runtime\share\jython25\Lib
::python %drivep%\Runtime\share\python\Sim\sim_exec.py %drivep%Workspace\plasma-PyVHDL
python %drivep%\Runtime\share\python\Sim\sim_exec.py %drivep%Workspace\%1

::------------------------------------------------------------------------------
::
:: Startup Zamiacad+PyVHDL Eclipse Product with the default workspace
::
:: This file MUST be in the top Zamiacad+PyVHDL folder 
::
::------------------------------------------------------------------------------

set drive=%~dp0
set drivep=%drive%

SET PYTHONPATH=%drivep%Runtime\share\jython25\Lib

%drivep%Runtime\zamia.exe  -showlocation -Xmx1536M -data=%drivep%Workspace


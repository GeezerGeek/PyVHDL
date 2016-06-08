
SETLOCAL ENABLEDELAYEDEXPANSION

IF DEFINED ZAMIA_HOME (echo ZAMIA_HOME=%ZAMIA_HOME% is already defined) else (
	set ZAMIA_HOME=%~dp0
)


:echo "ZAMIA_HOME is %ZAMIA_HOME%"

set CLASSPATH=%ZAMIA_HOME%bin


for %%i in (%ZAMIA_HOME%share\jars\*.jar) do (
	set CLASSPATH=!CLASSPATH!;%%i
)


set CLASSPATH=%CLASSPATH%;%ZAMIA_HOME%share
:echo classpath is %CLASSPATH%


echo This will start python interpreter withing zamia project. You may run a script by zamia_source("your_script.py") or use %~nx0 --help for other options.
java -Xmx1424m -Xms768m -Xss4m -server org.zamia.cli.Zamia %*


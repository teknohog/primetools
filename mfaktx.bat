@echo off

REM expirimental/developing mfloop "automation" script on windows

REM ###
REM Arguments to mfakto
set mvar=

REM Executable name
set exec=
:run
%exec% %mvar%
goto run


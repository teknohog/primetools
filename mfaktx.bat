@echo off

REM expirimental/developing mfloop "automation" script on windows
REM mfloop settings
REM
REM Primenet username
set PrimenetUsername=

REM Primenet password
set PrimenetPassword=

REM Use gpu72 0/no 1/yes
set UseGpu72=1

REM ###
REM Arguments to mfakto
set mvar=

REM Executable name
set exec=
:run
%exec% %mvar%
goto run

:service
python.exe mfloop.py %mfloop_arg%
goto service


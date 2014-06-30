
REM expirimental/developing mfloop "automation" script on windows
REM Time to wait between reboots if needed. 
set waittime=60

REM mfloop settings
REM
REM Primenet username
set PrimenetUsername=test

REM Primenet password
set PrimenetPassword=test123

REM How much work to get: If using gpu72, use GHzdays. If not, number of assignments.
set cache=100

REM Use gpu72 0/no 1/yes
set UseGpu72=1

REM GPU72 settings
set gpu72user=test
set gpu72pass=test123

REM Arguments to mfakto
set mvar=-d 1

REM Executable name
set exec=mfakto.exe

:start
if %1:==-s: goto setservice
start mfaktx.bat -s
:crunch
%exec% %mvar%
timeout /T %waittime% > NUL
goto crunch

:setservice
title mfloop service
set mfloop_arg=--username %PrimenetUsername% --password=%PrimenetPassword% -w %cd%
IF %UseGpu72%==1 set mfloop_arg=%mfloop_arg% --gpu72user=%gpu72user% --gpu72pass=%gpu72pass% 
REM IF %UseGpu72%==1 set mfloop_arg=%mfloop_arg% --ghzd_cache=%cache%. ELSE set mfloop_arg=%mfloop_arg% --num_cache=%cache%.
:service
python.exe mfloop.py %mfloop_arg%
timeout /T %waittime% > NUL
goto service

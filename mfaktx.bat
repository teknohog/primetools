@echo off
REM Time to wait between reboots if needed. 
set waittime=120

REM ### mfloop settings
REM ###
REM Primenet username
set PrimenetUsername=test

REM Primenet password
set PrimenetPassword=test123

REM How much work to get: If using gpu72, use GHzdays. If not, number of assignments.
set cache=100

REM ### GPU72 settings
REM ###
REM Use gpu72 0/no 1/yes

set UseGpu72=1
set gpu72user=test
set gpu72pass=test123

REM Type of work from GPU72 to get, lltf or dctf
set gpu72_type=lltf

REM GPU72 fetch options:
REM GPU72 Option to fetch, default what_makes_sense. Other valid values are lowest_tf_level, highest_tf_level, lowest_exponent,
REM oldest_exponent, no_p1_done (dctf only), lhm_bit_first (lltf only), lhm_depth_first (lltf only), and let_gpu72_decide (let_gpu72_decide may override max_exp)
set gpu72_option=what_makes_sense

REM Arguments to mfakto
set mvar=-d 1

REM Executable name
set exec=mfakto.exe

:check
REM does not work; ?? IF NOT EXIST python.exe echo Error: python could not be found in path, press any key to exit&&pause >NUL &&goto exit
IF NOT EXIST mfloop.py echo Error: mfloop.py could not be found, press any key to exit&&pause >NUL &&goto exit

:start
if %1:==-s: goto setservice
start mfaktx.bat -s
:crunch
%exec% %mvar%
echo ERROR: %exec% unexpectedly quit, waiting %waittime% seconds to restart...
timeout /T %waittime% > NUL
cls
goto crunch

:setservice
title mfloop service
set mfloop_arg=--username %PrimenetUsername% --password=%PrimenetPassword% -w %cd% --timeout=%waittime%
IF %UseGpu72%==1 set mfloop_arg=%mfloop_arg% --gpu72user=%gpu72user% --gpu72pass=%gpu72pass% --gpu72type=%gpu72_type% --gpu72option=%gpu72_option%
IF %UseGpu72%==1 set mfloop_arg=%mfloop_arg% --ghzd_cache=%cache%

:service
cls
title Mfloop service
echo mfloop service
echo running at: %cd%
python.exe mfloop.py %mfloop_arg%
echo ERROR: mfloop.py unexpectedly quit, waiting %waittime% seconds to restart...
timeout /T %waittime% > NUL
goto service

:exit
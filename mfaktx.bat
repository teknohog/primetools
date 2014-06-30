
REM Time to wait between reboots if needed. 
set waittime=60

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

:start
if %1:==-s: goto setservice
start mfaktx.bat -s
:crunch
%exec% %mvar%
timeout /T %waittime% > NUL
goto crunch

:setservice
title mfloop service
set mfloop_arg=--username %PrimenetUsername% --password=%PrimenetPassword% -w %cd% --timeout=%waittime%
IF %UseGpu72%==1 set mfloop_arg=%mfloop_arg% --gpu72user=%gpu72user% --gpu72pass=%gpu72pass% --gpu72type=%gpu72_type% --gpu72option=%gpu72_option%
REM IF %UseGpu72%==1 set mfloop_arg=%mfloop_arg% --ghzd_cache=%cache%. ELSE set mfloop_arg=%mfloop_arg% --num_cache=%cache%.
:service
python.exe mfloop.py %mfloop_arg%
timeout /T %waittime% > NUL
goto service

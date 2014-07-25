@echo off
REM Time to wait between reboots if needed. 
set waittime=120

set PrimenetUsername=test
set PrimenetPassword=test123
REM How much work to get: If using gpu72, use GHzdays. If not, number of assignments.
set WorkCache=100
REM gpu72 0/no 1/yes
set UseGPU72=1
set gpu72user=test
set gpu72pass=test123
set gpu72_type=lltf

REM GPU72 fetch options:
REM GPU72 Option to fetch, default what_makes_sense. Other valid values are lowest_tf_level, highest_tf_level, lowest_exponent,
REM oldest_exponent, no_p1_done (dctf only), lhm_bit_first (lltf only), lhm_depth_first (lltf only), and let_gpu72_decide (let_gpu72_decide may override max_exp)
set gpu72_option=what_makes_sense
REM Maximum bit to fetch
set max_bit=73
REM Arguments to mfaktx
set mvar=-d 1

REM Executable name
set exec=mfakto.exe


REM Multi-clients
REM NOTICE: The first client does not count, use the second client's path in 2, and so on. Settings will be same for every client.
set MultipleClients=1
set Clients=3
set 2=C:\1
set 3=C:\2
REM ###END OF SETTINGS###

:check
IF %MultipleClients%==1 set dir=%~1 ELSE set dir=%cd% 
IF NOT EXIST mfloop.py echo Error: mfloop.py could not be found, press any key to exit&&pause >NUL &&goto exit
IF NOT EXIST %exec% echo Error: %exec% could not be found, press any key to exit&&pause >NUL &&goto exit
:check_multi
IF %MultipleClients%==1 goto multi else goto start
echo Warning: Unknown input for %MultipleClients%, disabling.  
goto start

:multi
REM Replace with "for" later
goto %clients%
:3
start mfloop.bat %3%
:2
start mfloop.bat %2%
:1
echo Warning: Only 1 client set.

:start
if %1:==-s: goto setservice
start mfaktx.bat -s
del *.lck /F/Q
title %dir%\%exec%
:check
cls
IF NOT EXIST worktodo.txt echo ERROR: worktodo.txt not found, waiting for work...&&timeout /T 3 >NUL&&goto check
:crunch
%exec% %mvar%
echo ERROR: %exec% unexpectedly quit or ranout of work, waiting %waittime% seconds to restart...
timeout /T %waittime% > NUL
cls
goto crunch

:setservice
title mfloop service
set mfloop_arg=--username %PrimenetUsername% --password=%PrimenetPassword% -w %cd% --timeout=%waittime% -e %max_bit% -d --ghzd_cache=%WorkCache%
REM IF %UseGPU72%==1 goto sGPU72 ELSE goto service
:sGPU72
IF %UseGpu72%==1 set mfloop_arg=%mfloop_arg% --gpu72user=%gpu72user% --gpu72pass=%gpu72pass% --gpu72type=%gpu72_type% --gpu72option=%gpu72_option%

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

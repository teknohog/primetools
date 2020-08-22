#!/bin/bash

# by teknohog

# Example script for automatic work assignment for clLucas and CUDALucas

# https://www.rieselprime.de/ziki/ClLucas
# https://www.mersenneforum.org/cllucas/

# https://www.rieselprime.de/ziki/CUDALucas
# https://sourceforge.net/projects/cudalucas/

BASEOPTS="-u teknohog -p 11235"
WORKOPTS="-n 1 -T 100"

#LLCMD="clLucas -d 0 -aggressive -threads 128" # 1.02
#LLCMD="clLucas -d 0 -polite 0 -threads 128 -sixstepfft" # 1.04
#BASEDIR=~/distr.projects/clLucas.1.04/bin/x86_64/Release
#export LD_LIBRARY_PATH=~/sources/clFFT/src/library/

LLCMD="CUDALucas"
BASEDIR=~/sources/cudalucas

# GPU workers sometimes hog the CPU needlessly. This is a simple
# solution, though it would be better to limit the worker process only
# within llloop.py.
NICE=5

while getopts f opt; do
    case $opt in
	f)
	    # Finish current work and exit
	    WORKOPTS="-n 0"
	;;
    esac
done

cd $BASEDIR

nice -n$NICE llloop.py $BASEOPTS $WORKOPTS -c "$LLCMD"

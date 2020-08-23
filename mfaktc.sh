#!/bin/bash

# by teknohog

# Automatic work assignment for mfaktc
# https://www.rieselprime.de/ziki/Mfaktc
# https://www.mersenneforum.org/mfaktc/

# mfloop.py was originally written for mfakto, and they can run in
# parallel with the use of lockfiles. However, mfaktc does not use
# lockfiles, so we need to run them one after the other, using the -t
# 0 option to avoid looping in mfloop.py.

LOOP="mfloop.py"

BASEDIR=~/sources/mfaktc-0.21
FACT="mfaktc.exe"

#BASEOPTS="-u teknohog -p 12345 -d"
#WORKOPTS="-n 1"

# Prefer gpu72.com work assignments; 72 is hardcoded minimum, but a
# lower -e still works for the Primenet fallback
BASEOPTS="-u teknohog -p 12345 -U teknohog -P hunter2 -d"
WORKOPTS="-n 1 -e 72"

# Defaults
DEVICE=0
FLUSH=false

while getopts d:f opt; do
    case $opt in
	d)
	    DEVICE=$OPTARG
	    ;;
	f)
	    FLUSH=true
	    ;;
    esac
done

cd $BASEDIR

# mfloop.py lockfiles may be left over after crashes
rm *.txt.lck

if $FLUSH; then
    # Complete current work and submit results only at the end
    ./$FACT -d $DEVICE
    $LOOP $BASEOPTS -n 0 -t 0
else
    while true; do
	$LOOP $BASEOPTS $WORKOPTS -t 0
	./$FACT -d $DEVICE
	
	# Some wait time is useful in case of errors
	sleep 5
    done
fi

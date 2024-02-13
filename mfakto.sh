#!/bin/bash

# by teknohog

# Trial Division with OpenCL
# http://mersenneforum.org/showthread.php?t=15646
# https://github.com/Bdot42/mfakto
# https://github.com/teknohog/primetools

# This script runs mfloop.py in the background and mfakto in the
# foreground, so that new work can be fetched while another number is
# being factorized. This needs -n 2 or higher in WORKOPTS, as the
# ongoing work unit is counted as one.

# To use -n 1, there is the alternative wrapper script mfaktc.sh which
# does not use background fetch. You can also use the -1 option here
# to fetch, factor and return a single batch of work, including -n 1
# for a single work unit.

LOOP="mfloop.py"

BASEOPTS="-u teknohog -p topsecret -d"
WORKOPTS="-n 2"

# Prefer gpu72.com work assignments; 72 is hardcoded minimum, but a
# lower -e still works for the Primenet fallback
#BASEOPTS="-u teknohog -p topsecret -U teknohog -P setecastronomy -d"

BASEDIR=~/sources/mfakto
FACT="mfakto"

# Defaults
DEVICE=1
FLUSH=false
ONESHOT=false

while getopts 1d:f opt; do
    case $opt in
	1)
	    ONESHOT=true
	    ;;
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

# 2024-02-08 From mfaktc.sh
if $ONESHOT; then
    # 2020-09-02 Fetch, process and send one batch of work
    $LOOP $BASEOPTS $WORKOPTS -t 0
    FLUSH=true
fi

if $FLUSH; then
    # Complete current work and submit results only at the end
    ./$FACT -d $DEVICE
    $LOOP $BASEOPTS -n 0 -t 0
    exit
fi

# Default: run indefinitely, getting new work in a loop
$LOOP $BASEOPTS $WORKOPTS &
LOOPID=$!

# Wait for initial work
while [ ! -e worktodo.txt ] || [ "$(wc -w < worktodo.txt)" == "0" ]; do
    sleep 2
done

./$FACT -d $DEVICE

kill $LOOPID

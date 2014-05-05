#!/bin/bash

# by teknohog

# Run clLucas and lliki.py in a continuous loop.

# Please check this script carefully before use, as the optimal
# settings (THREADS, aticonfig) depend on the GPU, and there are other
# custom settings like the working directory and LD_LIBRARY_PATH.

BASEOPTS="-u teknohog -p inhermajestyssecretcervix"
WORKOPTS="-n 1 -T 100"
FLUSH=false
ONESHOT=false
PROG=clLucas

# 2097152 and 4194304 fft work best.(-f)
# http://mersenneforum.org/showpost.php?p=350303&postcount=64
# Fewer threads seem to speed up large FFTs slightly
function set_fft () {
    if [ $MERSENNE -ge 38000000 ]; then
	FFT=4194304
	THREADS=128
    else
	FFT=2097152
	THREADS=64
    fi
}

while getopts fo opt; do
    case $opt in
        f)
            FLUSH=true
            ;;
	o)
	    ONESHOT=true
	    ;;
    esac
done

if $FLUSH; then
    WORKOPTS="-n 0"
fi

#cd ~/distr.projects/clLucas.1.01
cd ~/distr.projects/clLucas.1.02/bin/x86_64/Release

export LD_LIBRARY_PATH=~/sources/clFFT/src/library/

# Device numbering as in cgminer
# GB 7970
DEVICE=1
aticonfig --adapter=0 --odsc=1050,1500

# PCS+5870
#DEVICE=0
#aticonfig --adapter=0 --odsc=975,1200

# Speed test with known M#48
#MERSENNE=57885161

# Small tests of known M#
#MERSENNE=110503

# Avoid running twice on the same GPU
if [ -n "`ps aux | grep $PROG | grep \" -d $DEVICE\"`" ]; then
    echo $PROG already running on device $DEVICE.
    exit
fi

if $ONESHOT; then
    # Test an individual M# without looping, useful for testing and
    # benchmarking before production runs
    
    MERSENNE=58818269
    #MERSENNE=32163559
    set_fft
    ./$PROG -aggressive -d $DEVICE -f $FFT -threads $THREADS $MERSENNE
    #lliki.py $BASEOPTS -n 0
    exit
fi

while true; do
    # Basic, recommended operation
    eval $(lliki.py $BASEOPTS $WORKOPTS)

    # Advanced alternative: Quick file operations first, then handle
    # networking in the background.
    #eval $(lliki.py -N)
    #lliki.py $BASEOPTS $WORKOPTS -d &
    
    set_fft

    if [ -n "$MERSENNE" ]; then
	./$PROG -aggressive -d $DEVICE -f $FFT -threads $THREADS $MERSENNE
    else
	break
    fi
done

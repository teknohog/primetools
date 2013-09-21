#!/bin/bash

# by teknohog

# A more advanced example of running clLucas and lliki.py in a
# continuous loop.

# Please check this script carefully before use, as the optimal
# settings (THREADS, aticonfig) depend on the GPU, and there are other
# custom settings like the working directory and LD_LIBRARY_PATH.

BASEOPTS="-u user -p pass"
WORKOPTS="-n 2"
FLUSH=false

# 2097152 and 4194304 fft work best.(-f)
# http://mersenneforum.org/showpost.php?p=350303&postcount=64
# Fewer threads seem to speed up large FFTs slightly
function set_fft () {
    if [ $MERSENNE -ge 38000000 ]; then
	FFT=4194304
	THREADS=128
    else
	FFT=2097152
	THREADS=256
    fi
}

while getopts f opt; do
    case $opt in
        f)
            FLUSH=true
            ;;
    esac
done

# Finish current work without getting any new
if $FLUSH; then
    WORKOPTS="-n 0"
fi

cd distr.projects/clLucas.1.0/

export LD_LIBRARY_PATH=~/sources/clFFT/src/library/

# Device numbering as in cgminer
DEVICE=0
aticonfig --adapter=0 --odsc=1000,1500

while true; do
    # Quick file operations first...
    eval $(lliki.py -N)

    # ...then leave networking in the background.
    lliki.py $BASEOPTS $WORKOPTS -d &
    
    set_fft

    if [ -n "$MERSENNE" ]; then
	./clLucas -aggressive -d $DEVICE -f $FFT -threads $THREADS $MERSENNE
    else
	break
    fi
done

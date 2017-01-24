#!/bin/bash

BASEOPTS="-u prime -p example"
WORKOPTS="-n 1 -T 101"

#CLLOPTS="-d 0 -aggressive -threads 128" # 1.02
CLLOPTS="-d 0 -polite 0 -threads 128 -sixstepfft" # 1.04

cd ~/distr.projects/clLucas.1.04/bin/x86_64/Release

export LD_LIBRARY_PATH=~/sources/clFFT/src/library/

# Device numbering as in cgminer
# GB 7970
DEVICE=0
aticonfig --adapter=0 --odsc=1050,1500

llloop.py $BASEOPTS $WORKOPTS -o "$CLLOPTS" $@

#!/bin/bash

# by teknohog for mfakt[oc]
# https://github.com/teknohog/primetools

# Prints out the success percentage of trial factoring, based on your
# past results.

# Options:
# -v to show the succesful exponents explicitly
# -l 8e7 (example) to consider only exponents below 8*10^7.

# A space-separated list of results files -- edit this to your
# preferences. You can include multiple files separately and/or via
# shell expansion.
RESULTS="$HOME/distr.projects/mfakto-*/results*.txt"

function mersenne_find () {
    grep "M[0-9]\+" | sed -Ee 's/.*(M[0-9]+) .*/\1/'
}

function exp_limit () {
    # only accept exponents below given limit... like A*10^B with this
    # simple filter, where A is a single digit. Set this ridiculously
    # high for "no limit".
    A=$(echo $LIMIT | sed -Ee 's/([0-9])e([0-9]+)/\1/i')
    B=$(echo $LIMIT | sed -Ee 's/([0-9])e([0-9]+)/\2/i')
    grep "M[1-$((A-1))][0-9]\{$B\}$\|M[0-9]\{1,$B\}$"
}

#LIMIT=7e7
LIMIT=9e99
VERBOSE=false
while getopts l:v opt; do
    case $opt in
	l)
	    LIMIT=$OPTARG
	    ;;
	v)
	    VERBOSE=true
	    ;;
    esac
done

FACTORS=$(grep has.a.factor $RESULTS | mersenne_find | exp_limit | wc -l)

# There may be multiple results per number, if unsuccesful
TOTAL=$(cat $RESULTS | mersenne_find | exp_limit | sort -n | uniq | wc -l)

#echo $((FACTORS * 100 / TOTAL))
P=$(echo "scale=2; $FACTORS * 100 / $TOTAL" | bc -l)

if $VERBOSE; then
    echo Factors found in
    grep has.a.factor $RESULTS | mersenne_find | exp_limit
fi

echo $FACTORS factors in $TOTAL exponents tested = $P %

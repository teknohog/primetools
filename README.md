primetools
==========

Scripts for working with prime number search


motherfaktor.py
---------------

Automatic work assignment and submission script for mfakto and
possibly other similar applications.

mfakto does trial division of Mersenne numbers with OpenCL, so it can
speed up this stage greatly with GPUs. It relies on manual work
assignment and submission from/to
http://www.mersenne.org/. motherfaktor.py automates this, so mfakto
can keep working indefinitely.

It is written in Python without any external libraries.

At the moment, this script can be somewhat unsafe. It is probably best
to run this only when mfakto is not running, for example in a loop
like this:

     CMD="motherfaktor.py -u teknohog -p salakalasana -n 2 -e 71 -gs"
     while true; do
         if [ -n "`$CMD | grep -i fail`" ];
	    then exit
	 fi
         ./mfakto -d $DEVICE
     done

The script is self-documenting with motherfaktor.py -h and the design
should be rather simple to follow. Note that you can get and send work
with a single command, as in the above example.

Some of the ideas are adapted from http://www.gpu72.com/spider/.

More on mfakto:

http://mersenneforum.org/showthread.php?t=15646
http://mersenneforum.org/mfakto/


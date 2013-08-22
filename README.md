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

     while true; do
     	 motherfaktor.py -u teknohog -p salakalasana -n 1 -l 3 -e 71 -gs
         ./mfakto -d $DEVICE
	 sync
     done

The script is self-documenting with motherfaktor.py -h and the design
should be rather simple to follow. Note that you can get and send work
with a single command, as in the above example.

Some of the ideas are adapted from http://www.gpu72.com/spider/.

More on mfakto:

http://mersenneforum.org/showthread.php?t=15646

http://mersenneforum.org/mfakto/


L2 cache
--------

The -l option is intended to help with network problems in the above
loop. Mfakto exits when worktodo.txt is empty, thus timing a new
fetch+submit cycle, but motherfaktor.py can cache additional work in
l2cache.txt. So ideally you will never run out of work, even if the
network fails occasionally.


Plans/TODO/issues:
------------------

* When submitting soon after mfakto exits, the script sometimes only
  sends partial results. Maybe it just needs a sync first...

* We should take control of mfakto to enable file operations without a
  full restart. Perhaps something as simple as process stop and resume
  could work. It would be nicer to keep the work cache rather full all
  the time; the L2 cache construct should help a little.

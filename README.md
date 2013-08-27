primetools
==========

Scripts for working with prime number search


mfloop.py
---------

Automatic work assignment and submission script for mfakto and
possibly other similar applications.

Developed from motherfaktor.py, this version is intended to run in
parallel with mfakto. It uses lockfiles to avoid conflicts when
accessing files. Thus a few options are new or different:

* --getwork and --submit are removed as redundant. Use -n 0 in case
   you want to finish current work and quit, without getting any new
   work.

* --timeout for the wait loop. By default, attempt network update
  every hour.

Run mfloop.py -h for more details on options.


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

Since it operates on the same files as mfakto, it is probably best run
only when mfakto is not running, for example in a loop like this:

     while true; do
     	 motherfaktor.py -u teknohog -p salakalasana -n 2 -l 6 -e 71 -gs
         ./mfakto -d $DEVICE
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

By default, L2 cache is not used. If you use it for some time and then
disable it again, it will be flushed to worktodo.txt anyway, so there
is no work left unused. In fact, it is now flushed every time you run
motherfaktor.py.

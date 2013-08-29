primetools
==========

Scripts for working with prime number search

These are written in standard Python without any external libraries. I
have only tested these on Linux, but there should be no OS limitations.


mfloop.py
---------

Automatic work assignment and submission script for mfakto and
possibly other similar applications.

Mfakto does trial division of Mersenne numbers with OpenCL, so it can
speed up this stage greatly with GPUs. It relies on manual work
assignment and submission from/to http://www.mersenne.org/. mfloop.py
automates this, so mfakto can keep working indefinitely.

This script is intended to run in parallel with mfakto. It uses
lockfiles to avoid conflicts when accessing files. A typical command
line would be

mfloop.py -u teknohog -p salasana -n 10 -t 7200 -e 70

This would attempt updates every 2 hours, aiming to keep 10
assignments in worktodo.txt. The upper limit of exponent range is
increased to 70 (if lower than that). Also,

* Use -t 0 for a single update without looping.

* Use -n 0 to finish work and not get any new assignments.

Run mfloop.py -h for more details on options.

Some of the ideas are adapted from http://www.gpu72.com/spider/.

More on mfakto:

http://mersenneforum.org/showthread.php?t=15646

http://mersenneforum.org/mfakto/

https://github.com/Bdot42/mfakto

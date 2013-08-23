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
motherfakto.py.

There is a small caveat if you start with -l without any existing
assignments. Data from the network goes to L2 cache first, but the
flush from L2 to worktodo.txt happens at the start of motherfakto.py
(for a good reason). Rather than complicating this logic further, you
can just run the script again to fix it (which should happen with the
shell loop anyway).


Plans/TODO/issues:
------------------

* When submitting soon after mfakto exits, the script sometimes only
  sends a part of the complete set (as defined by the same M#). This
  is not a huge issue though, because the remaining results will be
  sent on the next round. Besides, I think it has been fixed now...

* We should take control of mfakto to enable file operations without a
  full restart. Perhaps something as simple as process stop and resume
  could work. It would be nicer to keep the work cache rather full all
  the time; the L2 cache + loop construct should suffice for this in
  practice.

* One idea for safe file operations would be pseudofiles that appear
  like the work files to mfakto, but are actually operated behind the
  scenes by Python. For example named pipes might work as gateways
  between the two programs. Or perhaps mfakto could be ported to
  PyOpenCL...

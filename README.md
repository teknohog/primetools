Warning
=======

As of 2025-01-01, mersenne.org no longer accepts results from these
scripts, due to updated data formats. I have no plans to fix this,
since a vastly improved and up-to-date fork already exists. So please
consider this repository for historical reference only, and switch to
AutoPrimeNet for production use: https://github.com/tdulcet/AutoPrimeNet


primetools
==========

Scripts for working with prime number search

These are written in standard Python without any external libraries. I
have only tested these on Linux, but there should be no OS limitations.

Currently, these tools comprise automatic work handlers so that
certain third-party software (that do the actual computation) can
access Primenet (mersenne.org):


mfloop.py
---------

For trial factoring with mfakto (should work with mfaktc too)


llloop.py
---------

For Lucas-Lehmer primality testing with clLucas (also CUDALucas)


Future plans
------------

* Serving multiple mfakto directories with one process. I already have
  a simple idea for this, but the benefits over running separate
  mfloops would be questionable: a slight reduction in network traffic
  vs. more complicated configuration and less control over individual
  GPUs.

* Merge the two scripts, as they share a lot of code - though there
  are lots of small differences all over, so the result may turn out
  quite ugly.
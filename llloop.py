#!/usr/bin/env python

# by teknohog

# Automatic assignment handler for Lucas-Lehmer primality testing on
# GPUs. Work is fetched from and submitted to Primenet (mersenne.org),
# and the LL test is done by programs such as clLucas and CUDALucas.

from primetools import *

def primenet_fetch(num_to_get):
    global primenet_logged_in
    
    if not primenet_logged_in:
        return []

    # <option value="102">World record tests
    # <option value="100">Smallest available first-time tests
    # <option value="101">Double-check tests
    assignment = {"cores": "1",
                  "num_to_get": str(num_to_get),
                  "pref": options.worktype,
                  "exp_lo": "",
                  "exp_hi": "",
    }
    
    try:
        r = primenet.open(primenet_baseurl + "manual_assignment/?" + ass_generate(assignment))
        return greplike(workpattern, r.readlines(), r.headers.get_content_charset())
    except urllib2.URLError:
        print_status("URL open error at primenet_fetch")
        return []

def get_assignment():
    w = read_list_file(workfile)
    if w == "locked":
        return "locked"

    tasks = greplike(workpattern, w)
    tasks_keep = []

    # If the work is finished, remove it from tasks
    tasks = list(filter(unfinished, tasks))

    num_to_get = num_topup(tasks, options.num_cache)

    if num_to_get < 1:
        print_status("Cache full, not getting new work")
    else:
        print_status("Fetching " + str(num_to_get) + " assignments")
        tasks += primenet_fetch(num_to_get)

    # Output work for cllucas
    if len(tasks) > 0:
        mersenne = mersenne_find_task(tasks[0])
    else:
        mersenne = ""

    write_list_file(workfile, tasks)

    return mersenne
    
def mersenne_find_task(line):
    s = re.search(r",([0-9]+),[0-9]+,[0-9]+", line)
    if s:
        return s.groups()[0]
    else:
        return ""

def unfinished(line):
    finished = readonly_file(resultsfile)
    mersenne = mersenne_find_task(line)
    if len(mersenne) > 0 and "( " + mersenne + " )" in finished:
        return False
    else:
        return True

def submit_work():
    # There is no concept of incomplete results, as in mfloop.py, so
    # we simply send every sensible line in resultsfile. But only
    # delete after a succesful send, and even those are backed up to
    # sentfile.

    files = [resultsfile, sentfile]
    rs = list(map(read_list_file, files))
  
    if "locked" in rs:
        # Remove the lock in case one of these was unlocked at start
        for i in range(len(files)):
            if rs[i] != "locked":
                write_list_file(files[i], [], "a")
                
        return "locked"

    results = rs[0]

    # Example: M( 110503 )P, n = 6144, clLucas v1.00
    results_send = greplike(r"M\( ([0-9]*) \).*", results)
    
    (sent, unsent) = primenet_submit(results_send)

    write_list_file(resultsfile, unsent)
    write_list_file(sentfile, sent, "a")

import argparse
parser = argparse.ArgumentParser()

parser.add_argument("-c", "--llcmd", help="LL command in a single string without the Mersenne exponent, e.g. 'clLucas -f 2048K -d 0 -polite 0 -threads 128 -sixstepfft'")

parser.add_argument("-u", "--username", dest="username", required=True, help="Primenet user name")
parser.add_argument("-p", "--password", dest="password", required=True, help="Primenet password")

parser.add_argument("-n", "--num_cache", type=int, default=1, help="Number of assignments to cache, default %(default)d")
# -t is reserved for timeout as in mfloop.py, although not currently used here
parser.add_argument("-T", "--worktype", dest="worktype", default="101", help="Worktype code, default %(default)s for DC, alternatively 100 or 102 for first-time LL")
parser.add_argument("-w", "--workdir", dest="workdir", default=".", help="Working directory with clLucas binary, default current")

options = parser.parse_args()

workdir = os.path.expanduser(options.workdir)

workfile = os.path.join(workdir, "worktodo.txt")

resultsfile = os.path.join(workdir, "results.txt")

# A cumulative backup
sentfile = os.path.join(workdir, "results_sent.txt")

workpattern = r"(DoubleCheck|Test)=.*(,[0-9]+){3}"

workcmd = options.llcmd.split()

# If no full path is given for the worker, assume it is relative to
# the workdir. Not sure how this would work outside Unix :-/
if workcmd[0][0] != "/":
    workcmd[0] = os.path.join(workdir, workcmd[0])

while True:
    primenet_logged_in = primenet_login(primenet, options)

    # The order of get_assignment, then submit_work is important,
    # because we check resultsfile for finished work when handling
    # workfile. clLucas does not use lockfiles, so in the present form
    # we can ignore them.
    
    # This doesn't require login as it also gets tasks from the file
    # cache.
    work = get_assignment()
    
    if primenet_logged_in:
        submit_work()
    
    if len(work) == 0:
        print_status("Out of work")
        break

    worklist = workcmd + [work]
        
    # Run worker in the foreground
    ecode = os.spawnvp(os.P_WAIT, worklist[0], worklist)
    
    if ecode != 0:
        print_status("Worker error")
        break

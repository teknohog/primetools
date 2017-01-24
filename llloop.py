#!/usr/bin/env python

# by teknohog

# Automatic assignment handler for clLucas and manual testing at
# mersenne.org. Should also work with CUDALucas and similar programs
# with minimal changes.

import sys
import os.path
import re
import os

import cookielib
import urllib2
import urllib
from time import sleep

primenet_baseurl = "http://www.mersenne.org/"
gpu72_baseurl = "http://www.gpu72.com/"

def ass_generate(assignment):
    output = ""
    for key in assignment:
        output += key + "=" + assignment[key] + "&"
    #return output.rstrip("&")
    return output

def cleanup(data):
    # as in submit_spider; urllib2.quote does not quite work here
    output = re.sub(" ", "+", data)
    output = re.sub(":", "%3A", output)
    output = re.sub(",", "%2C", output)
    output = re.sub("\n", "%0A", output)
    return output

def greplike(pattern, l):
    output = []
    for line in l:
        s = re.search(r".*(" + pattern +")$", line)
        if s:
            output.append(s.groups()[0])
    return output

def num_topup(l, targetsize):
    num_existing = len(l)
    num_needed = targetsize - num_existing
    return max(num_needed, 0)

def readonly_file(filename):
    # Used when there is no intention to write the file back, so don't
    # check or write lockfiles. Also returns a single string, no list.
    if os.path.exists(filename):
        File = open(filename, "r")
        contents = File.read()
        File.close()
    else:
        contents = ""

    return contents

def read_list_file(filename):
    # Used when we plan to write the new version, so use locking
    lockfile = filename + ".lck"

    try:
        fd = os.open(lockfile, os.O_CREAT | os.O_EXCL)
        os.close(fd)

        if os.path.exists(filename):
            File = open(filename, "r")
            contents = File.readlines()
            File.close()
            return map(lambda x: x.rstrip(), contents)
        else:
            return []

    except OSError, e:
        if e.errno == 17:
            return "locked"
        else:
            raise

def write_list_file(filename, l, mode="w"):
    # Assume we put the lock in upon reading the file, so we can
    # safely write the file and remove the lock
    lockfile = filename + ".lck"

    # A "null append" is meaningful, as we can call this to clear the
    # lockfile. In this case the main file need not be touched.
    if mode != "a" or len(l) > 0:
        content = "\n".join(l) + "\n"
        File = open(filename, mode)
        File.write(content)
        File.close()

    os.remove(lockfile)

def primenet_fetch(num_to_get):
    global primenet_login
    
    if not primenet_login:
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
        r = primenet.open(primenet_baseurl + "manual_assignment/?" + ass_generate(assignment) + "B1=Get+Assignments")
        return greplike(workpattern, r.readlines())
    except urllib2.URLError:
        print("URL open error at primenet_fetch")
        return []

def get_assignment():
    w = read_list_file(workfile)
    if w == "locked":
        return "locked"

    tasks = greplike(workpattern, w)
    tasks_keep = []

    # If the work is finished, remove it from tasks
    tasks = filter(unfinished, tasks)

    num_to_get = num_topup(tasks, options.num_cache)

    if num_to_get < 1:
        print("Cache full, not getting new work")
    else:
        print("Fetching " + str(num_to_get) + " assignments")
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
    rs = map(read_list_file, files)

    if "locked" in rs:
        # Remove the lock in case one of these was unlocked at start
        for i in range(len(files)):
            if rs[i] != "locked":
                write_list_file(files[i], [], "a")
                
        return "locked"

    results = rs[0]

    # Only for new results, to be appended to sentfile
    sent = []

    # Example: M( 110503 )P, n = 6144, clLucas v1.00
    results_send = greplike(r"M\( ([0-9]*) \).*", results)

    results_keep = []

    # Use the textarea form to submit several results at once.

    if len(results_send) == 0:
        print("No complete results found to send.")
        # Don't just return here, files are still locked...
    else:
        while len(results_send) > 0:
            sendbatch = []
            while sum(map(len, sendbatch)) < sendlimit and \
                  len(results_send) > 0:
                sendbatch.append(results_send.pop(0))

            data = "\n".join(sendbatch)
        
            print("Submitting\n" + data)

            try:
                r = primenet.open(primenet_baseurl + "manual_result/default.php?data=" + cleanup(data) + "&B1=Submit")
                if "processing:" in r.read():
                    sent += sendbatch
                else:
                    results_keep += sendbatch
                    print("Submission failed.")
            except urllib2.URLError:
                results_keep += sendbatch
                print("URL open error")

    write_list_file(resultsfile, results_keep)
    write_list_file(sentfile, sent, "a")

def fft_opt(m):
    # Optimal FFT size for clLucas
    
    if int(m) > 38000000:
	fft = 4096
    else:
	fft = 2048

    # clLucas 1.04 has automatic size incrementing. This script can
    # still be useful for finding more optimal values, but in the
    # meantime, start with something basic.
    fft = 2048
        
    # Format for clLucas
    return ["-f", str(fft) + "K"]

def network_getwork():
    global options, primenet, primenet_baseurl, primenet_login

    mersenne = ""
    
    try:
        # Log in to primenet
        login_data = {"user_login": options.username,
                      "user_password": options.password,
                  }
        
        # This makes a POST instead of GET
        data = urllib.urlencode(login_data)
        r = primenet.open(primenet_baseurl + "default.php", data)

        primenet_login = options.username + "<br>logged in" in r.read()

        # The order of get_assignment, then submit_work is important,
        # because we check resultsfile for finished work when handling
        # workfile. clLucas does not use lockfiles, so in the present
        # form we can ignore them.

        # This doesn't require login as it also gets tasks from the
        # file cache.
        mersenne = get_assignment()
        
        if primenet_login:
            submit_work()
        else:
            print("Login failed.")

    except urllib2.URLError:
        print("Primenet URL open error")

    return mersenne
        
import argparse
parser = argparse.ArgumentParser()

parser.add_argument("-o", "--cllopts", help="CLLucas options in a single string, e.g. '-d 0 -polite 0 -threads 128 -sixstepfft'")

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

# mersenne.org limit is about 4 KB; stay on the safe side
sendlimit = 3500

# adapted from http://stackoverflow.com/questions/923296/keeping-a-session-in-python-while-making-http-requests
primenet_cj = cookielib.CookieJar()
primenet = urllib2.build_opener(urllib2.HTTPCookieProcessor(primenet_cj))

primenet_login = False

# Assuming clLucas in the workdir, could be generalized for any path
# and alternatives like CudaLucas...
binary = os.path.join(workdir, "clLucas")
    
while True:
    work = network_getwork()
    
    if len(work) == 0:
        print("Out of work")
        break
    else:
        worklist = [binary] + fft_opt(work) + options.cllopts.split() + [work]
        
    # Run clLucas in the foreground
    ecode = os.spawnvp(os.P_WAIT, worklist[0], worklist)
    
    if ecode != 0:
        print("Worker error")
        break

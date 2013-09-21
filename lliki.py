#!/usr/bin/env python

# by teknohog

# Automatic assignment handler for clLucas and manual testing at
# mersenne.org. Should also work with CUDALucas and similar programs.

import sys
import os.path
import re
import os

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

def debug_print(text):
    if options.debug:
        print(progname + ": " + text)

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

def write_list_file(filename, l):
    # Assume we put the lock in upon reading the file, so we can
    # safely write the file and remove the lock
    lockfile = filename + ".lck"

    content = "\n".join(l) + "\n"
    File = open(filename, "w")
    File.write(content)
    File.close()

    os.remove(lockfile)

def primenet_fetch(num_to_get):
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
        debug_print("URL open error at primenet_fetch")
        return []

def get_assignment():
    w = read_list_file(workfile)
    if w == "locked":
        return "locked"

    tasks = greplike(workpattern, w)
    tasks_keep = []

    # If the work is finished, remove it from tasks
    tasks = filter(unfinished, tasks)

    num_to_get = num_topup(tasks, int(options.num_cache))

    if num_to_get < 1:
        debug_print("Cache full, not getting new work")
    else:
        debug_print("Fetching " + str(num_to_get) + " assignments")
        tasks += primenet_fetch(num_to_get)

    # Output work for cllucas
    if len(tasks) > 0:
        mersenne = mersenne_find_task(tasks[0])
    else:
        # Clear the shell variable
        mersenne = ""
        debug_print("Out of work")

    print("MERSENNE=" + mersenne)

    write_list_file(workfile, tasks)

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
                write_list_file(files[i], rs[i])
                
        return "locked"

    (results, sent) = rs

    # Example: M( 110503 )P, n = 6144, clLucas v1.00
    results_send = greplike(r"M\( ([0-9]*) \).*", results)

    results_keep = []

    # Use the textarea form to submit several results at once.

    if len(results_send) == 0:
        debug_print("No complete results found to send.")
        # Don't just return here, files are still locked...
    else:
        while len(results_send) > 0:
            sendbatch = []
            while sum(map(len, sendbatch)) < sendlimit and \
                  len(results_send) > 0:
                sendbatch.append(results_send.pop(0))

            data = "\n".join(sendbatch)
        
            debug_print("Submitting\n" + data)

            try:
                r = primenet.open(primenet_baseurl + "manual_result/default.php?data=" + cleanup(data) + "&B1=Submit")
                if "Processing result" in r.read():
                    sent += sendbatch
                else:
                    results_keep += sendbatch
                    debug_print("Submission failed.")
            except urllib2.URLError:
                results_keep += sendbatch
                debug_print("URL open error")

    write_list_file(resultsfile, results_keep)
    write_list_file(sentfile, sent)

from optparse import OptionParser
parser = OptionParser()

parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="Display debugging info")

parser.add_option("-u", "--username", dest="username", help="Primenet user name")
parser.add_option("-p", "--password", dest="password", help="Primenet password")
parser.add_option("-w", "--workdir", dest="workdir", default=".", help="Working directory with worktodo.txt and result.txt, default current")

parser.add_option("-N", "--nonetwork", action="store_true", dest="nonet", default=False, help="Do not access Primenet, only clean up workfile and print the next task")

parser.add_option("-n", "--num_cache", dest="num_cache", default="1", help="Number of assignments to cache, default 1")

# -t is reserved for timeout as in mfloop.py, although not currently used here
parser.add_option("-T", "--worktype", dest="worktype", default="101", help="Worktype code, default 101 for DC, alternatively 100 or 102 for first-time LL")

(options, args) = parser.parse_args()

progname = os.path.basename(sys.argv[0])
workdir = os.path.expanduser(options.workdir)

workfile = os.path.join(workdir, "worktodo.txt")

resultsfile = os.path.join(workdir, "result.txt")

# A cumulative backup
sentfile = os.path.join(workdir, "result_sent.txt")

workpattern = r"(DoubleCheck|Test)=.*(,[0-9]+){3}"

# mersenne.org limit is about 4 KB; stay on the safe side
sendlimit = 3500

if options.nonet:
    options.num_cache = 0
    get_assignment()
    sys.exit()

# Make nonet faster by deferring these
import cookielib
import urllib2
import urllib
from time import sleep

# adapted from http://stackoverflow.com/questions/923296/keeping-a-session-in-python-while-making-http-requests
primenet_cj = cookielib.CookieJar()
primenet = urllib2.build_opener(urllib2.HTTPCookieProcessor(primenet_cj))

try:
    # Log in to primenet
    r = primenet.open(primenet_baseurl + "account/?user_login=" + options.username + "&user_password=" + options.password + "&B1=GO")
    
    if not options.username + " logged-in" in r.read():
        primenet_login = False
        debug_print("Login failed.")
    else:
        primenet_login = True

        # The order is important, because we check resultsfile for
        # finished work when handling workfile
        for f in [get_assignment, submit_work]:
            while f() == "locked":
                debug_print("Waiting for file access...")
                sleep(2)

except urllib2.URLError:
    debug_print("Primenet URL open error")

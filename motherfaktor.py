#!/usr/bin/env python

# by teknohog

# Automatic assignment handler for manual testing at
# mersenne.org. Written with mfakto in mind, might work with other
# similar applications.

import sys
import os.path

primenet_base = "http://www.mersenne.org/"

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

def exp_increase(l, max_exp):
    output = []
    for line in l:
        # Increase the upper limit to max_exp
        s = re.search(r",([0-9]+)$", line)
        if s:
            exp = int(s.groups()[0])
            new_exp = str(max(exp, max_exp))
            output.append(re.sub(r",([0-9]+)$", "," + new_exp, line))
    return output

def greplike(pattern, l):
    output = []
    for line in l:
        s = re.search(r".*(" + pattern +")$", line)
        if s:
            output.append(s.groups()[0])
    return output

def ReadFile(file):
    File = open(file, "r")
    contents = File.read()
    File.close()
    return contents

def ReadLines(file):
    File = open(file, "r")
    contents = File.readlines()
    File.close()
    return map(lambda x: x.rstrip(), contents)

def num_topup(l, targetsize):
    num_existing = len(l)
    num_needed = targetsize - num_existing
    return max(num_needed, 0)

def write_list_file(filename, l):
    content = "\n".join(l) + "\n"
    File = open(filename, "w")
    File.write(content)
    File.close()

import cookielib
import urllib2
import re

def get_assignment():
    # Parse Factor= lines, add new tasks at the end of workfile

    pattern = r"Factor=.*"

    tasks = [[]]*2

    if os.path.exists(workfile[0]):
        tasks[0] = greplike(pattern, ReadLines(workfile[0]))
    else:
        tasks[0] = []

    # First top up l1 cache from l2 if possible, no matter what options
    if os.path.exists(workfile[1]):
        tasks[1] = ReadLines(workfile[1])
        num_to_get = num_topup(tasks[0], int(options.num_cache))
        for i in range(num_to_get):
            if len(tasks[1]) > 0:
                tasks[0].append(tasks[1].pop(0))

        for i in [0, 1]:
            write_list_file(workfile[i], tasks[i])
    else:
        # Only needed if l2 activated in the following stage, but
        # simplifies overall code
        tasks[1] = []

    # Then fetch from network to the desired cache level
    if int(options.l2cache) > 0:
        level = 1
        cachesize = options.l2cache
    else:
        level = 0
        cachesize = options.num_cache

    num_to_get = num_topup(tasks[level], int(cachesize))

    if num_to_get < 1:
        print("Cache full, not getting new work")
        return

    # Manual assignment settings; trial factoring = 2
    assignment = {"cores": "1",
                  "num_to_get": str(num_to_get),
                  "pref": "2",
                  "exp_lo": "",
                  "exp_hi": "",
              }

    if options.debug:
        print("Fetching " + str(num_to_get) + " assignments")

    r = opener.open(primenet_base + "manual_assignment/?" + ass_generate(assignment) + "B1=Get+Assignments")
    tasks[level] += exp_increase(greplike(pattern, r.readlines()), int(options.max_exp))

    write_list_file(workfile[level], tasks[level])

def submit_work():
    # Only submit completed work, i.e. the exponent must not exist in
    # worktodo.txt any more
    
    if os.path.exists(workfile[0]):
        work = ReadFile(workfile[0])
    else:
        work = ""

    results = ReadLines(resultsfile)

    if os.path.exists(sentfile):
        sent = ReadLines(sentfile)
    else:
        sent = []

    # Need to preserve the original list while traversing it
    results_copy = results

    # Sending the textarea is probably simpler than getting file
    # upload to work.

    # Sending several results at a time is probably better, for both
    # server load, and the acceptance of extra exponent
    # ranges. Probably best to group these by the M# though, to avoid
    # excessive payloads.

    sendgroup = {}

    for line in results:
        s = re.search(r"M([0-9]*) ", line)
        if s:
            mersenne = s.groups()[0]
            if not "," + mersenne + "," in work:
                if not mersenne in sendgroup:
                    sendgroup[mersenne] = []

                sendgroup[mersenne].append(line)
        else:
            # Useless lines, like date stamps, can be removed, but
            # save the backups as usual
            sent.append(line)
            results_copy.remove(line)

    for mersenne in sendgroup:
        data = "\n".join(sendgroup[mersenne])
        
        if options.debug:
            print("Submitting\n" + data)

        r = opener.open(primenet_base + "manual_result/default.php?data=" + cleanup(data) + "&B1=Submit")
        if "Processing result" in r.read():
            sent += sendgroup[mersenne]
            for line in sendgroup[mersenne]:
                results_copy.remove(line)
        else:
            print("Submission failed.")

    write_list_file(resultsfile, results_copy)
    write_list_file(sentfile, sent)

from optparse import OptionParser
parser = OptionParser()

parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="Display debugging info")

parser.add_option("-e", "--exp", dest="max_exp", default="0", help="Upper limit of exponent, to optionally replace the assigned one")

parser.add_option("-u", "--username", dest="username", help="Your Primenet user name")
parser.add_option("-p", "--password", dest="password", help="Your Primenet password")
parser.add_option("-w", "--workdir", dest="workdir", default=".", help="Working directory with worktodo.txt and results.txt, default current")

parser.add_option("-n", "--num_cache", dest="num_cache", default="1", help="Number of assignments to cache, default 1")

parser.add_option("-l", "--l2cache", dest="l2cache", default="0", help="Level 2 (offline) work cache size, default 0")

parser.add_option("-g", "--getwork", action="store_true", dest="get_assignment", default=False, help="Get new assignments")

parser.add_option("-s", "--submit", action="store_true", dest="submit_work", default=False, help="Submit completed work")

(options, args) = parser.parse_args()

workdir = os.path.expanduser(options.workdir)

workfile = [os.path.join(workdir, "worktodo.txt"),
            os.path.join(workdir, "l2cache.txt")]

resultsfile = os.path.join(workdir, "results.txt")

# A cumulative backup
sentfile = os.path.join(workdir, "results_sent.txt")

# adapted from http://stackoverflow.com/questions/923296/keeping-a-session-in-python-while-making-http-requests
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

# Log in
r = opener.open(primenet_base + "account/?user_login=" + options.username + "&user_password=" + options.password + "&B1=GO")

# Check for succesful login
if not options.username + " logged-in" in r.read():
    print("Login failed.")
    sys.exit()

# Allow both operations with the same login
if options.get_assignment:
    get_assignment()

if options.submit_work:
    submit_work()


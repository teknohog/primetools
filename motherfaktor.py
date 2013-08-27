#!/usr/bin/env python

# by teknohog

# Automatic assignment handler for manual testing at
# mersenne.org. Written with mfakto in mind, might work with other
# similar applications.

import sys
import os.path
import cookielib
import urllib2
import re

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

def num_topup(l, targetsize):
    num_existing = len(l)
    num_needed = targetsize - num_existing
    return max(num_needed, 0)

def read_list_file(filename):
    if os.path.exists(filename):
        File = open(filename, "r")
        contents = File.readlines()
        File.close()
        return map(lambda x: x.rstrip(), contents)
    else:
        return []

def write_list_file(filename, l):
    content = "\n".join(l) + "\n"
    File = open(filename, "w")
    File.write(content)
    File.close()

def get_assignment(flushonly=False):
    # Parse Factor= lines, add new tasks at the end of workfile

    # Top up both caches with their desired sizes. So what if l2 size
    # is 0. This makes the logic simple, and solves the problem where
    # both caches are empty upon startup.

    cachesizes = map(int, [options.num_cache, options.l2cache])

    tasks = [greplike(workpattern, read_list_file(workfile[level])) for level in [0, 1]]

    # Flush first to maintain the temporal ordering of assignments
    while len(tasks[0]) < cachesizes[0] and len(tasks[1]) > 0:
        tasks[0].append(tasks[1].pop(0))

    if not flushonly:
        num_to_get = sum([num_topup(tasks[level], cachesizes[level]) for level in [0, 1]])

        if num_to_get < 1:
            print("Caches full, not getting new work")
        else:
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

            new_tasks = exp_increase(greplike(workpattern, r.readlines()), int(options.max_exp))

            # Prioritize l1 -- we may get fewer tasks than asked for
            while len(tasks[0]) < cachesizes[0] and len(new_tasks) > 0:
                tasks[0].append(new_tasks.pop(0))

            tasks[1] += new_tasks

    for level in [0, 1]:
        write_list_file(workfile[level], tasks[level])

def mersenne_find(line, complete=True):
    # This is only for spotting the M# exponent, so formatting
    # newlines etc. is not important
    work = "\n".join(read_list_file(workfile[0]))

    s = re.search(r"M([0-9]*) ", line)
    if s:
        mersenne = s.groups()[0]
        if not "," + mersenne + "," in work:
            return complete
        else:
            return not complete
    else:
        return False

def submit_work():
    # Only submit completed work, i.e. the exponent must not exist in
    # worktodo.txt any more

    results = read_list_file(resultsfile)
    
    sent = read_list_file(sentfile)

    # Sending the textarea is probably simpler than getting file
    # upload to work.

    # Sending several results at a time is probably better, for both
    # server load, and the acceptance of extra exponent
    # ranges.

    # Useless lines (not including a M#) are now discarded completely.

    results_send = filter(mersenne_find, results)
    results_keep = filter(lambda x: mersenne_find(x, complete=False), results)

    if len(results_send) == 0:
        print("No complete results found to send.")
        return

    while len(results_send) > 0:
        sendbatch = []
        while sum(map(len, sendbatch)) < sendlimit and len(results_send) > 0:
            sendbatch.append(results_send.pop(0))

        data = "\n".join(sendbatch)
        
        if options.debug:
            print("Submitting\n" + data)

        r = opener.open(primenet_base + "manual_result/default.php?data=" + cleanup(data) + "&B1=Submit")
        if "Processing result" in r.read():
            sent += sendbatch
        else:
            results_keep += sendbatch
            print("Submission failed.")

    write_list_file(resultsfile, results_keep)
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

# Trial factoring
workpattern = r"Factor=.*"

# mersenne.org limit is about 4 KB; stay on the safe side
sendlimit = 3500

# First, flush l2 cache into l1 if possible, no matter what options
# given. This is especially important when quitting work, so nothing
# is left in either cache -- it may take a few rounds to flush it
# completely.
if not options.get_assignment:
    get_assignment(flushonly=True)

    if not options.submit_work:
        # No network action needed, so skip login
        sys.exit()

# adapted from http://stackoverflow.com/questions/923296/keeping-a-session-in-python-while-making-http-requests
cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

# Log in
r = opener.open(primenet_base + "account/?user_login=" + options.username + "&user_password=" + options.password + "&B1=GO")

# Check for succesful login
if not options.username + " logged-in" in r.read():
    print("Login failed.")

    # Flushing is now integrated into get_assignment(), so need to
    # force a login-less version
    if options.get_assignment:
        get_assignment(flushonly=True)

    sys.exit()

# Allow both operations with the same login
if options.get_assignment:
    get_assignment()

if options.submit_work:
    submit_work()




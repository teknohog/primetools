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
    return output

def exp_increase(line, max_exp):
    # Increase the upper limit to max_exp
    s = re.search(r",([0-9]+)$", line)
    if s:
        exp = int(s.groups()[0])
        new_exp = str(max(exp, max_exp))
        return re.sub(r",([0-9]+)$", "," + new_exp, line)

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

def WriteFile(filename, content):
    File = open(filename, "w")
    File.write(content)
    File.close()

import cookielib
import urllib2
import re

def get_assignment():
    r = opener.open(primenet_base + "manual_assignment/?" + ass_generate(assignment) + "B1=Get+Assignments")

    # Parse Factor= lines, add new tasks at the end of workfile

    if os.path.exists(workfile):
        tasks = ReadLines(workfile)
    else:
        tasks = []

    for line in r.readlines():
        s = re.search(r".*(Factor=.*)$", line)
        if s:
            task = s.groups()[0]
            tasks.append(exp_increase(task, int(options.max_exp)))

    WriteFile(workfile, "\n".join(tasks))

def submit_work():
    # Only submit completed work, i.e. the exponent must not exist in
    # worktodo.txt any more
    
    if os.path.exists(workfile):
        work = ReadFile(workfile)
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
    # upload to work. Also, line-wise submit is easier to get working
    # than the full blob, especially as we need to traverse the list anyway.
    for line in results:
        s = re.search(r"M([0-9]*) ", line)
        if s:
            mersenne = s.groups()[0]
            if not "," + mersenne + "," in work:
                r = opener.open(primenet_base + "manual_result/default.php?data=" + cleanup(line) + "&B1=Submit")
                
                if "Processing result" in r.read():
                    sent.append(line)
                    results_copy.remove(line)
                else:
                    print("Submission failed.")
        else:
            # Useless lines, like date stamps, can be removed, but
            # save the backups as usual
            sent.append(line)
            results_copy.remove(line)

    WriteFile(resultsfile, "\n".join(results_copy))
    WriteFile(sentfile, "\n".join(sent))

from optparse import OptionParser
parser = OptionParser()

parser.add_option("-e", "--exp", dest="max_exp", default="0", help="Upper limit of exponent, to optionally replace the assigned one")

parser.add_option("-u", "--username", dest="username", help="Your Primenet user name")
parser.add_option("-p", "--password", dest="password", help="Your Primenet password")
parser.add_option("-d", "--dir", dest="basedir", default=".", help="Working directory with worktodo.txt and results.txt, default current")

parser.add_option("-n", "--num_to_get", dest="num_to_get", default="1", help="Number of assignments, default 1")

parser.add_option("-g", "--getwork", action="store_true", dest="get_assignment", default=False, help="Get new assignments")

parser.add_option("-s", "--submit", action="store_true", dest="submit_work", default=False, help="Submit completed work")

(options, args) = parser.parse_args()

basedir = os.path.expanduser(options.basedir)

workfile = os.path.join(basedir, "worktodo.txt")
resultsfile = os.path.join(basedir, "results.txt")

# A cumulative backup
sentfile = os.path.join(basedir, "results_sent.txt")

# Manual assignment settings; trial factoring = 2
assignment = {"cores": "1",
              "num_to_get": options.num_to_get,
              "pref": "2",
              "exp_lo": "",
              "exp_hi": "",
              }

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


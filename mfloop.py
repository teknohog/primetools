#!/usr/bin/env python

# by teknohog

# Automatic assignment handler for manual testing at mersenne.org and
# optionally gpu72.com.

# Written with mfakto in mind, this only handles trial factoring work
# for now. It should work with mfaktc as well.

# This version can run in parallel with the factoring program, as it
# uses lockfiles to avoid conflicts when updating files.

import sys
import os.path
import cookielib
import urllib2
import re
from time import sleep
import os
import urllib
import math
from optparse import OptionParser


primenet_baseurl = "https://www.mersenne.org/"
gpu72_baseurl = "https://www.gpu72.com/"

def ass_generate(assignment):
    output = ""
    for key in assignment:
        output += key + "=" + assignment[key] + "&"
    #return output.rstrip("&")
    return output

def debug_print(text):
    if options.debug:
        print(progname + ": " + text)

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
        s = re.search(r"(" + pattern + ")$", line)
        if s:
            output.append(s.groups()[0])
    return output

def num_topup(l, targetsize):
    num_existing = len(l)
    num_needed = targetsize - num_existing
    return max(num_needed, 0)

def ghzd_topup(l, ghdz_target):
    ghzd_existing = 0.0
    for line in l:
        pieces = line.split(",")
        # calculate ghz-d http://mersenneforum.org/showpost.php?p=152280&postcount=204
        exponent = int(pieces[1])
        first_bit = int(pieces[2]) + 1
        for bits in range(first_bit, int(pieces[3]) + 1):
            if bits > 65:
                timing = 28.50624 # 2.4 * 0.00707 * 1680.0
            elif bits == 64:
                timing = 28.66752 # 2.4 * 0.00711 * 1680.0
            elif bits == 63 or bits == 62:
                timing = 29.95776 # 2.4 * 0.00743 * 1680.0
            elif bits >= 48:
                timing = 18.7488 # 2.4 * 0.00465 * 1680.0
            else:
                continue

            bit_ghzd = timing * (1 << (bits - 48)) / exponent

            # if there is a checkpoint file, subtract the work done
            if bits == first_bit:
                checkpoint_file = os.path.join(workdir, "M"+str(exponent)+".ckp")
                if os.path.isfile(checkpoint_file):
                    File = open(checkpoint_file, "r")
                    checkpoint = File.readline()
                    File.close()
                    checkpoint_pieces = checkpoint.split(" ")
                    if checkpoint_pieces[4] == "mfakto":
                        progress_index = 6
                    else:
                        progress_index = 5

                    percent_done = float(checkpoint_pieces[progress_index]) / float(checkpoint_pieces[3])
                    bit_ghzd *= 1 - percent_done
                    debug_print("Found checkpoint file for assignment M"+str(exponent)+" indicating "+str(round(percent_done*100,2))+"% done.")

            ghzd_existing += bit_ghzd

    debug_print("Found " + str(ghzd_existing) + " of existing GHz-days of work")

    return max(0, math.ceil(ghdz_target - ghzd_existing))

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
    if not primenet_login:
        return []

    # Manual assignment settings; trial factoring = 2
    assignment = {"cores": "1",
                  "num_to_get": str(num_to_get),
                  "pref": "2",
                  "exp_lo": "",
                  "exp_hi": "",
    }

    try:
        r = primenet.open(primenet_baseurl + "manual_assignment/?" + ass_generate(assignment) + "B1=Get+Assignments")
        return exp_increase(greplike(workpattern, r.readlines()), int(options.max_exp))
    except urllib2.URLError:
        debug_print("URL open error at primenet_fetch")
        return []

def gpu72_fetch(num_to_get, ghzd_to_get = 0):
    if options.gpu72_type == "dctf":
        gpu72_type = "dctf"
    else:
        gpu72_type = "lltf"

    if options.gpu72_option == "lowest_tf_level":
        option = "1"
    elif options.gpu72_option == "highest_tf_level":
        option = "2"
    elif options.gpu72_option == "lowest_exponent":
        option = "3"
    elif options.gpu72_option == "oldest_exponent":
        option = "4"
    elif gpu72_type == "dctf" and options.gpu72_option == "no_p1_done":
        option = "5"
    elif gpu72_type == "lltf" and options.gpu72_option == "lhm_bit_first":
        option = "6"
    elif gpu72_type == "lltf" and options.gpu72_option == "lhm_depth_first":
        option = "7"
    elif options.gpu72_option == "let_gpu72_decide":
        option = "9"
    else:
        option = "0"

    if ghzd_to_get > 0:
        num_to_get_str = "0"
        ghzd_to_get_str = str(ghzd_to_get)
    else:
        num_to_get_str = str(num_to_get)
        ghzd_to_get_str = ""

    assignment = {"Number": num_to_get_str,
                  "GHzDays": ghzd_to_get_str,
                  "Low": "0",
                  "High": "10000000000",
                  "Pledge": str(max(70, int(options.max_exp))),
                  "Option": option,
    }

    # This makes a POST instead of GET
    data = urllib.urlencode(assignment)
    req = urllib2.Request(gpu72_baseurl + "account/getassignments/" + gpu72_type + "/", data)

    try:
        r = gpu72.open(req)
        new_tasks = greplike(workpattern, r.readlines())
        # Remove dupes
        return list(set(new_tasks))

    except urllib2.URLError:
        debug_print("URL open error at gpu72_fetch")

    return []

def get_assignment():
    w = read_list_file(workfile)
    if w == "locked":
        return "locked"

    fetch = {True: gpu72_fetch,
             False: primenet_fetch,
         }

    tasks = greplike(workpattern, w)

    if use_gpu72 and options.ghzd_cache != "":
        ghzd_to_get = ghzd_topup(tasks, int(options.ghzd_cache))
        num_to_get = 0
    else:
        ghzd_to_get = 0
        num_to_get = num_topup(tasks, int(options.num_cache))

    if num_to_get < 1 and ghzd_to_get == 0:
        debug_print("Cache full, not getting new work")
        # Must write something anyway to clear the lockfile
        new_tasks = []
    else:
        if use_gpu72 and ghzd_to_get > 0:
            debug_print("Fetching " + str(ghzd_to_get) + " GHz-days of assignments")
            new_tasks = fetch[use_gpu72](num_to_get, ghzd_to_get)
        else:
            debug_print("Fetching " + str(num_to_get) + " assignments")
            new_tasks = fetch[use_gpu72](num_to_get)

        # Fallback to primenet in case of problems
        if use_gpu72 and options.fallback == "1" and num_to_get and len(new_tasks) == 0:
            debug_print("Error retrieving from gpu72.")
            new_tasks = fetch[not use_gpu72](num_to_get)

    write_list_file(workfile, new_tasks, "a")

def mersenne_find(line, complete=True):
    work = readonly_file(workfile)

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

    files = [resultsfile, sentfile]
    rs = map(read_list_file, files)

    if "locked" in rs:
        # Remove the lock in case one of these was unlocked at start
        for i in range(len(files)):
            if rs[i] != "locked":
                write_list_file(files[i], [], "a")

        return "locked"

    results = rs[0]

    # Only for new results, to be appended to results_sent
    sent = []

    # Use the textarea form to submit several results at once.

    # Useless lines (not including a M#) are now discarded completely.

    results_send = filter(mersenne_find, results)
    results_keep = filter(lambda x: mersenne_find(x, complete=False), results)

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
                post_data = urllib.urlencode({"data": data})
                r = primenet.open(primenet_baseurl + "manual_result/default.php", post_data)
                res = r.read()
                if "processing:" in res or "Accepted" in res:
                    sent += sendbatch
                else:
                    results_keep += sendbatch
                    debug_print("Submission failed.")
            except urllib2.URLError:
                results_keep += sendbatch
                debug_print("URL open error")

    write_list_file(resultsfile, results_keep)
    write_list_file(sentfile, sent, "a")


parser = OptionParser()

parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="Display debugging info")

parser.add_option("-e", "--exp", dest="max_exp", default="72", help="Upper limit of exponent, default 72")

parser.add_option("-T", "--gpu72type", dest="gpu72_type", default="lltf", help="GPU72 type of work, lltf or dctf, default lltf.")

parser.add_option("-o", "--gpu72option", dest="gpu72_option", default="what_makes_sense", help="GPU72 Option to fetch, default what_makes_sense. Other valid values are lowest_tf_level, highest_tf_level, lowest_exponent, oldest_exponent, no_p1_done (dctf only), lhm_bit_first (lltf only), lhm_depth_first (lltf only), and let_gpu72_decide (let_gpu72_decide may override max_exp).")

parser.add_option("-u", "--username", dest="username", help="Primenet user name")
parser.add_option("-p", "--password", dest="password", help="Primenet password")
parser.add_option("-w", "--workdir", dest="workdir", default=".", help="Working directory with worktodo.txt and results.txt, default current")

parser.add_option("-U", "--gpu72user", dest="guser", help="GPU72 user name", default="")
parser.add_option("-P", "--gpu72pass", dest="gpass", help="GPU72 password")

parser.add_option("-n", "--num_cache", dest="num_cache", default="1", help="Number of assignments to cache, default 1")
parser.add_option("-g", "--ghzd_cache", dest="ghzd_cache", default="", help="GHz-days of assignments to cache, taking into account checkpoint files. Overrides num_cache.")
parser.add_option("-f", "--fallback", dest="fallback", default="1", help="Fall back to mersenne.org when GPU72 fails or has no work, default 1.")

parser.add_option("-t", "--timeout", dest="timeout", default="3600", help="Seconds to wait between network updates, default 3600. Use 0 for a single update without looping.")

(options, args) = parser.parse_args()

use_gpu72 = (len(options.guser) > 0)

progname = os.path.basename(sys.argv[0])
workdir = os.path.expanduser(options.workdir)
timeout = int(options.timeout)

workfile = os.path.join(workdir, "worktodo.txt")

resultsfile = os.path.join(workdir, "results.txt")

# A cumulative backup
sentfile = os.path.join(workdir, "results_sent.txt")

# Trial factoring
workpattern = r"Factor=[^,]*(,[0-9]+){3}"

# mersenne.org limit is about 4 KB; stay on the safe side
sendlimit = 3000

# adapted from http://stackoverflow.com/questions/923296/keeping-a-session-in-python-while-making-http-requests
primenet_cj = cookielib.CookieJar()
primenet = urllib2.build_opener(urllib2.HTTPCookieProcessor(primenet_cj))

if use_gpu72:
    # Basic http auth
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, gpu72_baseurl + "account/", options.guser, options.gpass)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    gpu72 = urllib2.build_opener(handler)

while True:
    # Log in to primenet
    try:
        login_data = {"user_login": options.username,
                      "user_password": options.password,
                  }

        # This makes a POST instead of GET
        data = urllib.urlencode(login_data)
        r = primenet.open(primenet_baseurl + "default.php", data)

        if not options.username + "<br>logged in" in r.read():
            primenet_login = False
            debug_print("Login failed.")
        else:
            primenet_login = True
            while submit_work() == "locked":
                debug_print("Waiting for results file access...")
                sleep(2)

    except urllib2.URLError:
        debug_print("Primenet URL open error")

    while get_assignment() == "locked":
        debug_print("Waiting for worktodo.txt access...")
        sleep(2)

    if timeout <= 0:
        break

    sleep(timeout)


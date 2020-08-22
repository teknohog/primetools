#!/usr/bin/env python

# by teknohog

# Automatic assignment handler for manual testing at mersenne.org and
# optionally gpu72.com.

# Written with mfakto in mind, this only handles trial factoring work
# for now. It should work with mfaktc as well.

# This version can run in parallel with mfakto, as it uses lockfiles
# to avoid conflicts when updating files.

# Mfaktc does not use lockfiles, so this can only be used when mfaktc
# is not running, using -t 0 for a single update without looping.

from primetools import *

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
                    print_status("Found checkpoint file for assignment M"+str(exponent)+" indicating "+str(round(percent_done*100,2))+"% done.")

            ghzd_existing += bit_ghzd

    print_status("Found " + str(ghzd_existing) + " of existing GHz-days of work")

    return max(0, math.ceil(ghdz_target - ghzd_existing))


def primenet_fetch(num_to_get):
    if not primenet_logged_in:
        return []

    # Manual assignment settings
    assignment = {"num_to_get": str(num_to_get),
                  "pref": options.workpref,
                  "exp_lo": "",
                  "exp_hi": "",
    }

    try:
        r = primenet.open(primenet_baseurl + "manual_gpu_assignment/?" + ass_generate(assignment))
        return exp_increase(greplike(workpattern, r.readlines(), r.headers.get_content_charset()), int(options.max_exp))
    except urllib.error.URLError:
        print_status("URL open error at primenet_fetch")
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
    data = urllib.parse.urlencode(assignment).encode('utf-8')
    req = urllib.request.Request(gpu72_baseurl + "account/getassignments/" + gpu72_type + "/", data)
    
    try:
        r = gpu72.open(req)
        new_tasks = greplike(workpattern, r.readlines(), r.headers.get_content_charset())
        # Remove dupes
        return list(set(new_tasks))

    except urllib.error.URLError:
        print_status("URL open error at gpu72_fetch")

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
        print_status("Cache full, not getting new work")
        # Must write something anyway to clear the lockfile
        new_tasks = []
    else:
        if use_gpu72 and ghzd_to_get > 0:
            print_status("Fetching " + str(ghzd_to_get) + " GHz-days of assignments")
            new_tasks = fetch[use_gpu72](num_to_get, ghzd_to_get)
        else:
            print_status("Fetching " + str(num_to_get) + " assignments")
            new_tasks = fetch[use_gpu72](num_to_get)

        # Fallback to primenet in case of problems
        if use_gpu72 and options.fallback == "1" and num_to_get and len(new_tasks) == 0:
            print_status("Error retrieving from gpu72.")
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

    if not primenet_logged_in:
        return
    
    files = [resultsfile, sentfile]
    rs = list(map(read_list_file, files))

    if "locked" in rs:
        # Remove the lock in case one of these was unlocked at start
        for i in range(len(files)):
            if rs[i] != "locked":
                write_list_file(files[i], [], "a")

        return "locked"

    results = rs[0]

    # Useless lines (not including a M#) are now discarded completely.

    results_send = list(filter(mersenne_find, results))
    results_keep = [x for x in results if mersenne_find(x, complete=False)]

    (sent, unsent) = primenet_submit(results_send)

    results_keep += unsent
    
    write_list_file(resultsfile, results_keep)
    write_list_file(sentfile, sent, "a")

from optparse import OptionParser
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

parser.add_option("-W", "--workpref", dest="workpref", default="2", help="Primenet work preference: 2 = double check trial factoring (default), 3 = first time TF, 4 = TF for 100M digit Mersenne numbers")

(options, args) = parser.parse_args()

# Default to silent output, as this is intended to run in the
# background of a worker, and it might clutter the display.
#if not options.debug:
#    print_status = lambda x: None
# Hmm... this does not apply to primetools functions that call it :-/
# So comment out for now, but leave the option for compatibility.

use_gpu72 = (len(options.guser) > 0)

workdir = os.path.expanduser(options.workdir)
timeout = int(options.timeout)

workfile = os.path.join(workdir, "worktodo.txt")

resultsfile = os.path.join(workdir, "results.txt")

# A cumulative backup
sentfile = os.path.join(workdir, "results_sent.txt")

# Trial factoring
workpattern = r"Factor=[^,]*(,[0-9]+){3}"

if use_gpu72:
    # Basic http auth
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, gpu72_baseurl + "account/", options.guser, options.gpass)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    gpu72 = urllib.request.build_opener(handler)

while True:
    primenet_logged_in = primenet_login(primenet, options)

    if primenet_logged_in:
        while submit_work() == "locked":
            print_status("Waiting for results file access...")
            time.sleep(2)
    
    while get_assignment() == "locked":
        print_status("Waiting for worktodo.txt access...")
        time.sleep(2)

    if timeout <= 0:
        break

    time.sleep(timeout)


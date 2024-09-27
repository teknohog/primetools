#!/usr/bin/env python3

# by teknohog

# Common functions for primetools such as mfloop.py and llloop.py. Put
# this in the same directory with the main Python scripts; it should
# not have executable permissions.

import sys
import http.cookiejar
import urllib.request, urllib.error, urllib.parse
import re
import time
import os
import math

gpu72_baseurl = "https://www.gpu72.com/"

def ass_generate(assignment):
    output = ""
    for key in assignment:
        output += key + "=" + assignment[key] + "&"
    #return output.rstrip("&")
    return output

def print_status(text):
    progname = os.path.basename(sys.argv[0])
    print(progname + " " + time.strftime("%Y-%m-%d %H:%M") + " " + text)

def greplike(pattern, l, charset = ""):
    output = []
    for line in l:

        if len(charset) > 0:
            line_str = line.decode(charset)
        else:
            line_str = line
            
        s = re.search(r"(" + pattern + ")$", line_str)
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
            return [x.rstrip() for x in contents]
        else:
            return []

    except OSError as e:
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

class PrimeNet():
    def __init__(self, options):
        self.baseurl = "https://www.mersenne.org/"

        # mersenne.org limit is about 4 KB; stay on the safe side
        self.sendlimit = 3000

        # adapted from http://stackoverflow.com/questions/923296/keeping-a-session-in-python-while-making-http-requests
        self.cookiejar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))

        self.login_data = {"user_login": options.username,
                           "user_password": options.password,
        }

        self.workpref = options.workpref
        
    def login(self):
        try:
            # This makes a POST instead of GET
            data = urllib.parse.urlencode(self.login_data).encode("utf-8")
            r = self.opener.open(self.baseurl, data)
            res = r.read().decode(r.headers.get_content_charset())
            
            if self.login_data["user_login"] + "<br>logged in" in res:
                print_status("Logged in to Primenet")
                self.logged_in = True
            else:
                print_status("Primenet login failed")
                self.logged_in = False
            
        except urllib.error.URLError:
            print_status("Primenet URL open error")
            self.logged_in = False
        
    def submit(self, results):
        # Copy the list so we can pop() it freely without changing the original
        sendlist = list(results)

        # Keep track of succesful and failed sends
        sent = []
        unsent = []
    
        # Use the textarea form to submit several results at once. Due
        # to sendlimit, a large set of results is split into batches
        # that are sent separately.
    
        if len(sendlist) == 0:
            print_status("No complete results found to send.")
        else:
            while len(sendlist) > 0:
                sendbatch = []
                while sum(map(len, sendbatch)) <= self.sendlimit and len(sendlist) > 0:
                    sendbatch.append(sendlist.pop(0))

                data = "\n".join(sendbatch)

                print_status("Submitting\n" + data)

                try:
                    post_data = urllib.parse.urlencode({"data": data}).encode("utf-8")
                    r = self.opener.open(self.baseurl + "manual_result/", post_data)
                    res = r.read().decode(r.headers.get_content_charset())
                
                    if "processing:" in res or "Accepted" in res:
                        sent += sendbatch
                    else:
                        unsent += sendbatch
                        print_status("Submission failed.")
                except urllib.error.URLError:
                    unsent += sendbatch
                    print_status("URL open error")

        return (sent, unsent)

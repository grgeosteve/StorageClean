#!/usr/bin/python
import hashlib
import sys
import getopt
import os
import time
import stat


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def isGrpReadable(filepath):
    st = os.stat(filepath)
    return bool(st.st_mode & stat.S_IRGRP)


def crawl(basedir, recursive):
    for filename in os.listdir(basedir):
        filename = basedir+filename
        if os.path.isdir(filename):
            if recursive and isGrpReadable(filename):
                crawl(filename + "/", recursive)
            else:
                continue
        elif os.path.isfile(filename) and isGrpReadable(filename):
            filehash = md5(filename)
            lastmod = os.path.getmtime(filename)
            print("{0} {1} {2}".format(filehash, lastmod, filename))
        else:
            continue

            
def main(argv):
    inputdir = ''
    recursive = False
    try:
        opts, args = getopt.getopt(argv, "d:r", ["idir=", "recursive"])
    except getopt.GetoptError:
        print("dMd5sum.py -d <inputdir> [-r]")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-d", "--idir"):
            inputdir = arg
        elif opt in ("-r", "--recursive"):
            recursive = True
        else:
            print("Wrong argument")
            sys.exit(2)

    print(inputdir)
    crawl(inputdir, recursive)


if __name__ == "__main__":
    main(sys.argv[1:])

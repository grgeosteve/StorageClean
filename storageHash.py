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


class Crawler:
    """A class for filesystem crawling / computing md5 hash"""

    def __init__(self, basedir, recursive=False, verbose=False):
        self.verbose = verbose
        self.recursive = recursive
        self.basedir = basedir
        self.depth = 0 # Depth in directory from original

    def crawl(self):
        for filename in os.listdir(self.basedir):
            filename = self.basedir+filename
            if os.path.isdir(filename):
                if self.recursive and isGrpReadable(filename):
                    subcrawler = Crawler(filename+"/", self.recursive,
                                         self.verbose)
                    subcrawler.execute()
                else:
                    continue
            elif os.path.isfile(filename) and isGrpReadable(filename):
                filehash = md5(filename)
                lastmod = os.path.getmtime(filename)
                if self.verbose:
                    print("{0} {1} {2}".format(filehash, lastmod, filename))
            else:
                continue

    def testCrawl(self):
        for filename in os.listdir(self.basedir):
            filename = self.basedir+filename
            if os.path.isdir(filename):
                if self.recursive and isGrpReadable(filename):
                    subcrawler = Crawler(filename+"/", self.recursive,
                                         self.verbose)
                    subcrawler.execute()
                else:
                    continue
            elif os.path.isfile(filename) and isGrpReadable(filename):
                filehash = md5(filename)
                lastmod = os.path.getmtime(filename)
                if self.verbose:
                    print("{0} {1} {2}".format(filehash, lastmod, filename))
            else:
                continue
            
    def execute(self):
        self.testCrawl()


def main(argv):
    inputdir = ''
    verbose = False
    recursive = False
    try:
        opts, args = getopt.getopt(argv, "d:rv",
                                   ["idir=", "recursive", "verbose"])
    except getopt.GetoptError:
        print("dMd5sum.py -d <inputdir> [-r]")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-d", "--idir"):
            inputdir = arg
        elif opt in ("-r", "--recursive"):
            recursive = True
        elif opt in ("-v", "--verbose"):
            verbose = True
        else:
            print("Wrong argument")
            sys.exit(2)

    print(inputdir)
    crawler = Crawler(inputdir, recursive, verbose)
    crawler.execute()


if __name__ == "__main__":
    main(sys.argv[1:])

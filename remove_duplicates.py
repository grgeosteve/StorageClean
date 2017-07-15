#!/usr/bin/python3

import os
import sys
import find_duplicates


if __name__ == '__main__':
    mypath = sys.argv[1]

    dirs = find_duplicates.listDirectories(mypath)
    if dirs == []:
        print("Exiting")
        exit()

    rmlist_files = []
    for d in dirs:
        rmfile = d + ".removelist"
        if os.path.isfile(rmfile):
            rmlist_files.append(rmfile)

    for rmfile in rmlist_files:
        print(rmfile)
        with open(rmfile, 'r') as f:
            for line in f:
                fname = line.split("\n")[0]
                if find_duplicates.is_writable(fname):
                    try:
                        os.remove(fname)
                    except KeyboardInterrupt:
                        if os.path.isfile(fname):
                            os.remove(fname)
                        print("Exiting")
                        exit()

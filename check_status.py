#!/usr/bin/python3

import sys
from os import path
import find_duplicates


def print_hr(sz):
    SZ_MULTI = 1024

    increments = [[SZ_MULTI, "B"],
                  [SZ_MULTI**2, "KB"],
                  [SZ_MULTI**3, "MB"],
                  [SZ_MULTI**4, "GB"],
                  [SZ_MULTI**5, "TB"],
                  [SZ_MULTI**6, "PB"]]
    
    for inc in increments:
        if sz < inc[0]:
            print("%.2f %s" % (sz / (float(inc[0])/SZ_MULTI), inc[1]))
            break

if __name__ == '__main__':
    mypath = sys.argv[1]

    files = find_duplicates.listFiles(mypath)
    rmfiles = [f[1] for f in files if f[1].endswith(".removelist")]

    total_size = 0
    for rmf in rmfiles:
        print(rmf)
        part_size = 0
        with open(rmf, "r") as f:
            for line in f:
                fname = line.split("\n")[0]
                part_size += path.getsize(fname)
        print_hr(part_size)
        total_size += part_size
    print("Total size")
    print_hr(total_size)

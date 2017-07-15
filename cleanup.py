#!/usr/bin/python3

import os
import sys
import find_duplicates


def retrieve_temporary_files(path):
    dirs = find_duplicates.listDirectories(mypath)
    if dirs == []:
        return []

    tmp_files = []
    for d in dirs:
        listfile = d + ".filelist"
        if os.path.isfile(listfile):
            tmp_files.append(listfile)

        hashfile = d + ".hash"
        if os.path.isfile(hashfile):
            tmp_files.append(hashfile)
        
        rmfile = d + ".removelist"
        if os.path.isfile(rmfile):
            tmp_files.append(rmfile)

    return tmp_files
    

if __name__ == '__main__':
    mypath = sys.argv[1]
    tmp_files = retrieve_temporary_files(mypath)

    for f in tmp_files:
        if find_duplicates.is_writable(f):
            try:
                os.remove(f)
            except KeyboardInterrupt:
                if os.path.isfile(f):
                    os.remove(f)
                print("Exiting")
                exit()

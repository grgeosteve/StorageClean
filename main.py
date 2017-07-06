from os import listdir
from os.path import isfile, isdir, islink, join
import sys
import os
import stat
import hashlib
import time

def isgroupreadable(path):
    st = os.stat(path)
    return bool(st.st_mode & stat.S_IRGRP)

def isuserreadable(path):
    st = os.stat(path)
    return bool(st.st_mode & stat.S_IRUSR)

def iswritable(path):
    return os.access(path, os.W_OK)

def isreadable(path):
    return os.access(path, os.R_OK)

def isDir(path):
    return isdir(path) and (not islink(path))

def listFiles(path, recursive=False):
    files = []
    if not isreadable(path):
        return files

    for f in listdir(path):
        tmppath = join(path, f)
        if isfile(tmppath):
            filesize = os.path.getsize(tmppath)
            files.append([filesize, tmppath])
        elif isDir(tmppath) and recursive:
            if isreadable(tmppath):
                try:
                    print(tmppath)
                except UnicodeEncodeError:
                    pass
                files.extend(listFiles(tmppath, recursive))

    return files

def md5sum(path):
    if (not isfile(path)) and (not isreadable(path)) :
        return -1

    # BUF_SIZE = 65536 # 64Kb
    BUF_SIZE = 1048576
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def listDirectories(path):
    dirs = []
    for f in listdir(path):
        tmppath = join(path, f)
        if isdir(tmppath):
            dirs.append(tmppath)

    return dirs

def getDirCreationTime(path):
    cdate = os.stat(path)[stat.ST_CTIME]
    return cdate

def saveFlattenDir(path):

    files = listFiles(path, True)
    files.sort(key=lambda f: f[0])
    filepath = path + ".filelist"
    with open(filepath, "w") as fp:
        print("Writing file %s" % filepath)
        for f in files:
            try:
                fp.write("%d,%s\n" % (f[0], f[1]))
            except UnicodeEncodeError:
                pass
    return filepath

def readEntry(f):
    line = f.readline()
    if line == "":
        return []

    line_split = line.split(",")
    filename = line_split[-1].split("\n")[0]
    filesize = int(line_split[0])
    return [filesize, filename]

def compareDirs(listfile_1, listfile_2):
    print(listfile_1)
    print(listfile_2)
    try:
        f1 = open(listfile_1, "r")
        f2 = open(listfile_2, "r")

        entry1 = readEntry(f1)
        entry2 = readEntry(f2)
        if entry1 == [] or entry2 == []:
            f1.close()
            f2.close()
            return []

        list_same_1 = []
        list_same_2 = []

        prev_size = 0

        while True:
            if entry1[0] == entry2[0]:
                list_same_1.append(entry1[1])
                list_same_2.append(entry2[1])

                prev_size = entry1[0]

                entry1 = readEntry(f1)
                while entry1 != [] and entry1[0] == prev_size:
                    list_same_1.append(entry1[1])
                    entry1 = readEntry(f1)

                entry2 = readEntry(f2)
                while entry2 != [] and entry2[0] == prev_size:
                    list_same_2.append(entry2[1])
                    entry2 = readEntry(f2)

                if entry1 == [] or entry2 == []:
                    break
            elif entry1[0] < entry2[0]:
                entry1 = readEntry(f1)
                if entry1 == []:
                    break
            elif entry1[0] > entry2[0]:
                entry2 = readEntry(f2)
                if entry2 == []:
                    break

        f1.close()
        f2.close()

        if list_same_1 == []:
            return []

        return [list_same_1, list_same_2]
        
    except IOError:
        return []

def readHashes(filename):
    hashdict = {}
    with open(filename, "r") as f:
        for line in f:
            line_split = line.split(",")
            fname = line_split[-1].split("\n")[0]
            tmphash = line_split[0]

            hashdict[fname] = tmphash
    return hashdict        

def writeHashes(filename, hashdict):
    with open(filename, "w") as f:
        for elem in hashdict.items():
            f.write("%s,%s\n" %(elem[1], elem[0]))

def removeFiles(listfname, removefname, remove_list):
    # append the file for removal
    remove_dict = {}
    for item in remove_list:
        remove_dict[item] = 1

    with open(removefname, "r") as f:
        for line in f:
            item = line.split("\n")[0]
            remove_dict[item] = 1
    
    with open(removefname, "w") as f:
        for elem in remove_dict.keys():
            f.write("%s\n" % elem)

    file_dict = {}
    with open(listfname, "r") as f:
        for line in f:
            line_split = line.split(",")
            fname = line_split[-1].split("\n")[0]
            fsize = int(line_split[0])

            file_dict[fname] = fsize

    for elem in remove_list:
        file_dict.pop(elem, None)

    # write the list of remaining files
    file_list = [[k, v] for k, v in file_dict.items()]
    file_list.sort(key=lambda f:f[1])
    with open(listfname, "w") as f:
        for elem in file_list:
            f.write("%d,%s\n" %(elem[1], elem[0]))


def compareHashes(md5list1, md5list2):
    md5list1.sort(key=lambda f:f[0])
    md5list2.sort(key=lambda f:f[0])

    elems1 = len(md5list1)
    elems2 = len(md5list2)

    idx1 = 0
    idx2 = 0

    prev_hash = ""

    list_same_1 = []
    list_same_2 = []
    while True:
        if md5list1[idx1][0] == md5list2[idx2][0]:
            list_same_1.append(md5list1[idx1][1])
            list_same_2.append(md5list2[idx2][1])

            prev_hash = md5list1[idx1][0]

            idx1 += 1
            while idx1 < elems1 and md5list1[idx1][0] == prev_hash:
                list_same_1.append(md5list1[idx1][1])
                idx1 += 1

            idx2 += 1
            while idx2 < elems2 and md5list2[idx2][0] == prev_hash:
                list_same_2.append(md5list2[idx2][1])
                idx2 += 1

            if idx1 >= elems1 or idx2 >= elems2:
                break

        elif md5list1[idx1][0] < md5list2[idx2][0]:
            idx1 += 1
            if idx1 >= elems1:
                break
        else:
            idx2 += 1
            if idx2 >= elems2:
                break

    if list_same_1 == []:
        return []

    return [list_same_1, list_same_2]


if __name__ == '__main__':
    mypath = sys.argv[1]

    dirs = listDirectories(mypath)

    remove_fname = os.path.join(mypath, "removelist.filelist")

    timed_dirs = []
    for d in dirs:
        cdate = getDirCreationTime
        timed_dirs.append([cdate, d])

    listfiles = []
    for cdate, d in timed_dirs:
        # listfiles.append(saveFlattenDir(d))
        listfiles.append(d + ".filelist")

    # Compare the files
    for i in range(len(timed_dirs) - 1):
        listfile_i = listfiles[i]

        for j in range(i + 1, len(timed_dirs)):
            listfile_j = listfiles[j]

            comparison_lists = compareDirs(listfile_i, listfile_j)
            if comparison_lists == []:
                continue
            print(len(comparison_lists[0]))

            hashdict_1 = {}
            hashdict_2 = {}
            filename_1 = timed_dirs[i][1] + ".hash"
            filename_2 = timed_dirs[j][1] + ".hash"
            if os.path.exists(filename_1):
                hashdict_1 = readHashes(filename_1)
            if os.path.exists(filename_2):
                hashdict_2 = readHashes(filename_2)

            prev_percent = 0
            md5list1 = []
            for k in range(len(comparison_lists[0])):
                if not iswritable(comparison_lists[0][k]):
                    continue

                tmpmd5 = ""
                if comparison_lists[0][k] in hashdict_1:
                    tmpmd5 = hashdict_1[comparison_lists[0][k]]
                else:
                    tmpmd5 = md5sum(comparison_lists[0][k])

                if tmpmd5 == -1:
                    continue
                percent = round(float(k) / len(comparison_lists[0]) * 100)
                if percent > prev_percent:
                    print("%6d - (%d / %d)" %(percent, k+1, len(comparison_lists[0])))
                    prev_percent = percent
                md5list1.append([tmpmd5, comparison_lists[0][k]])
                hashdict_1[comparison_lists[0][k]] = tmpmd5

            # Save the computed hashes
            # if len(md5list1) > 0:
            #     writeHashes(filename_1, md5list1)
            if len(hashdict_1) > 0:
                print("Writing hashes to file %s" % filename_1)
                writeHashes(filename_1, hashdict_1)

            prev_percent = 0
            md5list2 = []
            for k in range(len(comparison_lists[1])):
                if not iswritable(comparison_lists[1][k]):
                    continue

                tmpmd5 = ""
                if comparison_lists[1][k] in hashdict_2:
                    tmpmd5 = hashdict_2[comparison_lists[1][k]]
                else:
                    tmpmd5 = md5sum(comparison_lists[1][k])

                if tmpmd5 == -1:
                    continue
                percent = round(float(k) / len(comparison_lists[1]) * 100)
                if percent > prev_percent:
                    print("%6d - (%d / %d)" %(percent, k+1, len(comparison_lists[1])))
                    prev_percent = percent
                md5list2.append([tmpmd5, comparison_lists[1][k]])
                hashdict_2[comparison_lists[1][k]] = tmpmd5

            # Save computed hashes
            if len(hashdict_2) > 0:
                print("Writing hashes to file %s" % filename_2)
                writeHashes(filename_2, hashdict_2)

            list_remove = compareHashes(md5list1, md5list2)
            if len(list_remove) == 0:
                continue
            
            print(len(list_remove[0]))
            total_size = 0
            for elem in list_remove[0]:
                filesize = os.path.getsize(elem)
                total_size += filesize
            print(total_size)

            # Remove files
            removeFiles(listfile_i, remove_fname, list_remove[0])
        
            

    # Remove temporary files
    # for f in listfiles:
    #     os.remove(f)

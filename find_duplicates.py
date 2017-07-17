#!/usr/bin/python3

from os import listdir
from os.path import isfile, isdir, islink, join
import sys
import os
import stat
import hashlib


def is_writable(path):
    return os.access(path, os.W_OK)


def is_readable(path):
    return os.access(path, os.R_OK)


def is_dir(path):
    return isdir(path) and (not islink(path))


def is_valid_dir(path):
    return is_dir(path) and is_readable(path)


def listFiles(path, recursive=False):
    files = []
    if not is_valid_dir(path):
        return files

    for f in listdir(path):
        tmppath = join(path, f)
        if isfile(tmppath):
            filesize = os.path.getsize(tmppath)
            files.append([filesize, tmppath])
        elif is_valid_dir(tmppath) and recursive:
            try:
                print(tmppath)
            except UnicodeEncodeError:
                pass
            files.extend(listFiles(tmppath, recursive))

    return files


def computeHash(path):
    if (not isfile(path)) or (not is_readable(path)):
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
            f.write("%s,%s\n" % (elem[1], elem[0]))


def removeFiles(listfname, removefname, remove_list):
    # append the file for removal
    remove_dict = {}
    for item in remove_list:
        remove_dict[item] = 1

    if os.path.exists(removefname):
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
    file_list.sort(key=lambda f: f[1])
    with open(listfname, "w") as f:
        for elem in file_list:
            f.write("%d,%s\n" % (elem[1], elem[0]))


def compareFiles(filepath1, filepath2):
    try:
        BUF_SIZE = 4096  # 4Kbytes
        with open(filepath1, "rb") as f1, open(filepath2, "rb") as f2:
            while True:
                data1 = f1.read(BUF_SIZE)
                data2 = f2.read(BUF_SIZE)
                if data1 != data2:
                    return False
                if not data1:
                    return True
            
    except IOError:
        return False


def fileInList(filepath, filelist):
    for f in filelist:
        if compareFiles(filepath, f):
            return True

    return False


def compareMultiFiles(filelist1, filelist2):
    list_same = []
    for f in filelist1:
        if fileInList(f, filelist2):
            list_same.append(f)

    return list_same


def compareSimilarHashedFiles(hashdict1, hashdict2):
    list_same = []

    idx = 0
    prev_percent = 10
    for k1, v1 in hashdict1.items():
        percent = (idx + 1) / float(len(hashdict1)) * 100

        if k1 in hashdict2:
            list_same.extend(compareMultiFiles(v1, hashdict2[k1]))
            if percent > prev_percent:
                prev_percent += 10
                print("Index: %.2f - %d/%d" % (percent,
                                               len(v1),
                                               len(hashdict2[k1])))

        idx += 1

    return list_same


def compareHashes(md5list1, md5list2):
    md5list1.sort(key=lambda f: f[0])
    md5list2.sort(key=lambda f: f[0])

    elems1 = len(md5list1)
    elems2 = len(md5list2)

    idx1 = 0
    idx2 = 0

    prev_hash = ""

    list_same_1 = []
    list_same_2 = []
    while True:
        if md5list1[idx1][0] == md5list2[idx2][0]:
            list_same_1.append(md5list1[idx1])
            list_same_2.append(md5list2[idx2])

            prev_hash = md5list1[idx1][0]

            idx1 += 1
            while idx1 < elems1 and md5list1[idx1][0] == prev_hash:
                list_same_1.append(md5list1[idx1])
                idx1 += 1

            idx2 += 1
            while idx2 < elems2 and md5list2[idx2][0] == prev_hash:
                list_same_2.append(md5list2[idx2])
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

    timed_dirs = []
    for d in dirs:
        cdate = os.path.getmtime(d)  # Get last modification of the directory
        timed_dirs.append([cdate, d])
    timed_dirs.sort(key=lambda f: f[0])

    listfiles = []
    for cdate, d in timed_dirs:
        listfiles.append(saveFlattenDir(d))
        # listfiles.append(d + ".filelist")

    # Compare the files
    for i in range(len(timed_dirs) - 1):
        listfile_i = listfiles[i]

        remove_fname = timed_dirs[i][1] + ".removelist"

        for j in range(i + 1, len(timed_dirs)):
            listfile_j = listfiles[j]

            comparison_lists = compareDirs(listfile_i, listfile_j)
            if comparison_lists == []:
                continue
            print("%d - %d" % (len(comparison_lists[0]),
                               len(comparison_lists[1])))

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
                if not is_writable(comparison_lists[0][k]):
                    continue

                tmpmd5 = ""
                if comparison_lists[0][k] in hashdict_1:
                    tmpmd5 = hashdict_1[comparison_lists[0][k]]
                else:
                    tmpmd5 = computeHash(comparison_lists[0][k])

                if tmpmd5 == -1:
                    continue
                percent = round(float(k) / len(comparison_lists[0]) * 100)
                if percent > prev_percent and percent % 10 == 0:
                    msg = "(%d,%d)/%d : %6d - (%d / %d)"
                    print(msg % (i+1, j+1, len(timed_dirs), percent,
                                 k+1, len(comparison_lists[0])))
                    prev_percent = percent
                md5list1.append([tmpmd5, comparison_lists[0][k]])
                hashdict_1[comparison_lists[0][k]] = tmpmd5

            # Save the computed hashes
            if len(hashdict_1) > 0:
                print("Writing hashes to file %s" % filename_1)
                writeHashes(filename_1, hashdict_1)

            prev_percent = 0
            md5list2 = []
            for k in range(len(comparison_lists[1])):
                if not is_writable(comparison_lists[1][k]):
                    continue

                tmpmd5 = ""
                if comparison_lists[1][k] in hashdict_2:
                    tmpmd5 = hashdict_2[comparison_lists[1][k]]
                else:
                    tmpmd5 = computeHash(comparison_lists[1][k])

                if tmpmd5 == -1:
                    continue
                percent = round(float(k) / len(comparison_lists[1]) * 100)
                if percent > prev_percent and percent % 10 == 0:
                    msg = "(%d/%d)/%d : %6d - (%d / %d)"
                    print(msg % (j+1, i+1, len(timed_dirs), percent,
                                 k+1, len(comparison_lists[1])))

                    prev_percent = percent
                md5list2.append([tmpmd5, comparison_lists[1][k]])
                hashdict_2[comparison_lists[1][k]] = tmpmd5

            # Save computed hashes
            if len(hashdict_2) > 0:
                print("Writing hashes to file %s" % filename_2)
                writeHashes(filename_2, hashdict_2)

            print("%d - %d" % (len(md5list1), len(md5list2)))

            if len(md5list1) == 0 or len(md5list2) == 0:
                continue
            list_similar = compareHashes(md5list1, md5list2)
            if len(list_similar) == 0:
                continue
            list_similar_1 = list_similar[0]
            list_similar_2 = list_similar[1]
            print("%d - %d" % (len(list_similar_1), len(list_similar_2)))

            # Convert lists to dicts
            hash_similar_1 = {}
            for elem in list_similar_1:
                if elem[0] in hash_similar_1:
                    hash_similar_1[elem[0]].append(elem[1])
                else:
                    hash_similar_1[elem[0]] = [elem[1]]

            hash_similar_2 = {}
            for elem in list_similar_2:
                if elem[0] in hash_similar_2:
                    hash_similar_2[elem[0]].append(elem[1])
                else:
                    hash_similar_2[elem[0]] = [elem[1]]

            list_remove = compareSimilarHashedFiles(hash_similar_1,
                                                    hash_similar_2)
            
            print(len(list_remove))
            total_size = 0
            for elem in list_remove:
                filesize = os.path.getsize(elem)
                total_size += filesize
            print(total_size)

            # Remove files
            removeFiles(listfile_i, remove_fname, list_remove)

#!/usr/bin/env python3
import datetime
import json


# can be done with logging instead
def write_to_log(data):
    with open("./files/log.txt", "w") as f:
        f.write("{} {:%d-%m-%Y %H:%M:%S}".format(data, datetime.datetime.now()))


def open_file(file_name):
    with open(file_name, "r") as f:
        return f.read()


def append_to_file(file_name, data):
    with open(file_name, "a") as f:
        f.write(f' {data}')


def write_to_file(file_name, data):
    with open(file_name, "w") as f:
        f.write(data)


def open_json(file_name):
    with open(file_name, "r") as f:
        file_contents = json.load(f)

    return file_contents


def write_to_json(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)


# remove
def find(array, target):
    lo = 0
    hi = len(array) - 1

    while lo <= hi:
        middle = (lo + hi) // 2
        midpoint = array[middle]

        if midpoint > target:
            hi = middle - 1
        elif midpoint < target:
            lo = middle + 1
        else:
            return True

    return False


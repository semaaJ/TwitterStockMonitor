#!/usr/bin/env python3
import datetime
import json


def write_to_log(input):
    with open("./files/log.txt", "r+") as f:
        f.write("{} {:%d-%m-%Y %H:%M:%S}".format(input, datetime.datetime.now()))


def open_file(file_name):
    with open(file_name, "r") as f:
        return f.read()


def write_to_file(file_name, input):
    with open(file_name, "r+") as f:  # possibly try "a" here
        f.write(input)


def write_to_file_for_loop(file_name, input):
    with open(file_name, "w") as f:
        for item in input:
            f.write("{} \n".format(item))


def open_json():
    with open("./files/monitor.json", "r") as f:
        file_contents = json.load(f)
    return file_contents


def write_to_json(info):
    with open("./files/monitor.json", "r+") as f:
        json.dump(info, f, sort_keys = True, indent = 4,ensure_ascii=False)

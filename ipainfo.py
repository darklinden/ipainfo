#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import shutil
import subprocess
import plistlib
import tempfile

def run_cmd(cmd):
    # print("run cmd: " + " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        # print(err)
        pass
    return out.strip()

def self_install(file, des):
    file_path = os.path.realpath(file)

    filename = file_path

    pos = filename.rfind("/")
    if pos:
        filename = filename[pos + 1:]

    pos = filename.find(".")
    if pos:
        filename = filename[:pos]

    to_path = os.path.join(des, filename)

    print("installing [" + file_path + "] \n\tto [" + to_path + "]")
    if os.path.isfile(to_path):
        os.remove(to_path)

    shutil.copy(file_path, to_path)
    run_cmd(['chmod', 'a+x', to_path])

def regex_find(path, rgstr):
    # open the file
    f = open(path, "r")
    content = f.read()
    f.close()

    # replace
    pattern = re.compile(rgstr)
    results = pattern.findall(content)
    return results

def plist_to_dictionary(filename):
    "Pipe the binary plist through plutil and parse the JSON output"
    with open(filename, "rb") as f:
        content = f.read()
    args = ["/usr/bin/plutil", "-convert", "json", "-o", "-", "--", "-"]
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p.communicate(content)
    return json.loads(out)

def __main__():

    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("ipainfo.py", "/usr/local/bin")
        return

    param = ""
    if len(sys.argv) > 1:
        param = sys.argv[1]

    if not str(param).startswith("/"):
        param = os.path.join(os.getcwd(), param)

    if not os.path.isfile(param):
        print("using: ipainfo [ipa-path] to read ipa info")
        return

    tmp_path = tempfile.mkdtemp()
    run_cmd(["unzip", param, "-d", tmp_path])

    plist_files = []
    mobile_provision = ""

    for root, dirs, files in os.walk(tmp_path):
        for file in files:
            file_path = os.path.join(root, file)
            if str(file).lower().find("info") != -1 and file.lower().endswith(".plist"):
                plist_files.append(file_path)
            elif str(file).lower().endswith(".mobileprovision"):
                mobile_provision = file_path

    f = open(mobile_provision, "r")
    content = f.read()
    f.close()

    start = content.find("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    end = content.find("</plist>")

    content = content[:(end + len("</plist>"))][start:]

    plist_obj = plistlib.readPlistFromString(content)

    getinfo = False
    for plist_path in plist_files:
        # run_cmd(["plistutil", "-i", plist_path, "-o", plist_path])
        info_plist_obj = plist_to_dictionary(plist_path) #plistlib.readPlist(plist_path)
        if info_plist_obj.get("CFBundleDisplayName", "") != "" and \
                        info_plist_obj.get("CFBundleShortVersionString", "") != "" and \
                        info_plist_obj.get("CFBundleVersion", "") != "" and \
                        info_plist_obj.get("CFBundleIdentifier", "") != "":
            CFBundleDisplayName = info_plist_obj.get("CFBundleDisplayName", "")
            CFBundleShortVersionString = info_plist_obj.get("CFBundleShortVersionString", "")
            CFBundleVersion = info_plist_obj.get("CFBundleVersion", "")
            CFBundleIdentifier = info_plist_obj.get("CFBundleIdentifier", "")
            getinfo = True
            break

    print("ipa info")
    print("***********************************")
    print("app name: [" + CFBundleDisplayName + "]")
    print("bundle id: [" + CFBundleIdentifier + "]")
    print("version: [" + CFBundleShortVersionString + "]")
    print("build: [" + CFBundleVersion + "]")
    print("provison profile: [" + str(plist_obj["Name"]) + "]")
    print("codesign team name: [" + str(plist_obj["TeamName"]) + "]")

    Entitlements = plist_obj["Entitlements"]
    print("using entitlements:")
    print(json.dumps(Entitlements, sort_keys=True, indent=2))

    print("***********************************")

    if os.path.isdir(tmp_path):
        shutil.rmtree(tmp_path)

    print("Done")

__main__()

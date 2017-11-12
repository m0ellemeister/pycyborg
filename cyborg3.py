#!/usr/bin/env python3


###############################################################################
#                                                                             #
#       Copyright (c) 2014 EnTr0p1sT (entr0p1st@worldwidewyrd dot net,        #
#                          TODO: replace MD5 sum                              #
#                          MD5 ID: 75cf1b154d75ea8a4dd4f91d82133f21)          #
#                                                                             #
###############################################################################

# TODO: Update this short documentation to reflect the Yaml config
#Config file format is an initial line with anything you like, followed by:
#
#Cx=/path/to/command
#
#for as many commands as you want to define, where 'x' is the number of the
#macro key, and without the hash at the beginning.

# <-- forked by m0ellemeister, ported to Python 3 + rewritten some code -->

from binascii import hexlify
from subprocess import Popen
from os.path import expanduser
import argparse
import pyudev
import sys
import yaml

#defining some constants
EVENT_LENGTH = 192 #magic number from playing with contents of hiddev0
# DEVICE_ABBR = "Madcatz Mad Catz V.7 Keyboard" #key word relating to keyboard to get from dmesg
BACK_STEPS = 7 #the number of characters preceeding the char of interest
SIGNATURE = b'01' #the unique characters identifying a keypress


def loadconfig(configfile):
    """
    Load Subject Settings from Yaml File
    :param configfile:
    :return: dict
    """
    myconfigfile = {}
    with open(configfile, 'r') as stream:
        try:
            myconfigfile = yaml.safe_load(stream)
            return myconfigfile
        except yaml.YAMLError as e:
            print('Error Loading Config File: {0}'.format(e))
            return "LoadError"
        except IOError as e:
            print('Error Loading Config File: {0}'.format(e))
            return "LoadError"

def get_keyboard_addr(model="Mad_Catz_V.7_Keyboard", type="usb"):
    """
    Get the hiddev device path by searching the udev db.
    1. get all devices filtered by subsystem = usb + model name
    2. got DEVPATH by first step, match this DEVPATH on devices by udev subsystem usbmisc
    3. return DEVNAME which is the hiddev device path
    :param model: defaults to Cyborg Keyboard
    :param type: defaults to usb
    :return:
    """
    context = pyudev.Context()
    for device in context.list_devices(subsystem=type, ID_MODEL=model):
        mykeyboard = device['DEVPATH']
    for device in context.list_devices(subsystem='usbmisc'):
        if mykeyboard in device['DEVPATH']:
            print(device['DEVNAME'])
            return device['DEVNAME']

def lookup_keypress(keys, event):
    """
    gets the index of the signature, and backsteps to get the number
    :param event: by pressed key
    :return:
    """
    index = event.find(SIGNATURE)
    # print(type(event))
    # print(str(event[index-BACK_STEPS]))
    hex = '0x' + str(event[index-BACK_STEPS])
    # print(str(int(hex, 0)))
    # print("MACRO: {0}".format(MACRO))
    # print(type(MACRO))
    # print(keys['cyborg'])
    # print(keys['cyborg']['keycodes'])
    # print("Taste")
    # print(keys['cyborg']['keycodes'][int(hex, 0)][0]['command'].split())
    return keys['cyborg']['keycodes'][int(hex, 0)][0]['command'].split()

# TODO: re-implement this by using argparse
def parse_cmd(args):
    """
    If no args, read default file, else read given file, or fail
    :param args: optional file name of config file
    :return: macro => list of commands defined in configuration file
    """
    file_err = "Unable to read default config in "
    usage_help = "Usage: python3 cyborg3.py [optional: config file path]"
    if len(args) == 1:
        try:
            macro=read_macros(RC_FILE)
        except:
            print("{0}: {1}".format(file_err + RC_FILE))
            sys.exit(1)
    elif len(args) == 2:
        try:
            macro=read_macros(args[1])
        except:
            print("{0}: {1}".format(file_err + args[1]))
            print(usage_help)
            sys.exit(1)
    else:
        print(usage_help)
        sys.exit(1)
    return macro

# TODO: put everything after this line into main()
# TODO: this should be covered in a way like a daemon works
#Read contents of file, then run infinite loop
ckeys = loadconfig(expanduser('~') + '/.config/cyborg3.yml')
with open(get_keyboard_addr(), 'rb') as stream:
 while True: #shameless infinite loop!
  event=hexlify(stream.read(EVENT_LENGTH))
  #event=b2a_hex(stream.read(EVENT_LENGTH))
  Popen(lookup_keypress(ckeys, event))


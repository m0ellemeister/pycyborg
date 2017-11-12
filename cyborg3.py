#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
#                                                                             #
#       Copyright (c) 2014 EnTr0p1sT entr0p1st@worldwidewyrd dot net,         #
# <-- forked by m0ellemeister, ported to Python 3 + rewritten some code   --> #
#                     2017 Sven Möller smoeller@nichthelfer dot de,           #
#                          TODO: replace MD5 sum                              #
#                          MD5 ID: 75cf1b154d75ea8a4dd4f91d82133f21)          #
#                                                                             #
###############################################################################

#Config file is in Yaml Format:

# Example cyborg3.yml:
# =============================================================================
# First Node "cyborg" stands for the Keyboard itself.
# Second Node is for, as the name shows, for the corresponding key codes of the
# "Cyborg" Keys C1 - C12
# the number represents the Key Code received by the keyboard when a C Key is pressed.
# - command: is, I guess self explaining, the command that should be executed when the
# corresponding C-Key is pressed.
# cyborg:
#   keycodes:
#     # Key C1
#     73:
#       - command: /usr/bin/xmessage "C1"
#     # Key C2
#     80:
#       - command: /usr/bin/xmessage "C2"
#     # Key C3
#     81:
#       - command: /usr/bin/xmessage "C3"
#     # Key C4
#     82:
#       - command: /usr/bin/xmessage "C4"
#     # Key C5
#     83:
#       - command: /usr/bin/xmessage "C5"
#     # Key C6
#     84:
#       - command: /usr/bin/xmessage "C6"
#     # Key C7
#     85:
#       - command: /usr/bin/xmessage "C7"
#     # Key C8
#     86:
#       - command: /usr/bin/xmessage "C8"
#     # Key C9
#     87:
#       - command: /usr/bin/xmessage "C9"
#     # Key C10
#     151:
#       - command: /usr/bin/xmessage "C10"
#     # Key C11
#     152:
#       - command: /usr/bin/xmessage "C11"
#     # Key C12
#     153:
#       - command: /usr/bin/rhythmbox



__author__ = 'Sven Möller'

from binascii import hexlify
from subprocess import Popen
from os.path import expanduser
import argparse
import asyncio
import functools
import pyudev
import signal
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
    with open(expanduser(configfile), 'r') as stream:
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
    hex = '0x' + str(event[index-BACK_STEPS])
    try:
        return keys['cyborg']['keycodes'][int(hex, 0)][0]['command'].split()
    except KeyError:
        pass


def read_keypress(hiddev, ckeys):
    event = hexlify(hiddev.read(EVENT_LENGTH))
    try:
        Popen(lookup_keypress(ckeys, event))
    except FileNotFoundError as e:
        print("ERROR: {0}".format(e.strerror))
    except PermissionError as e:
        print("ERROR: can't execute {0}: {1}".format(e.filename, e.strerror))
    asyncio.sleep(1)


def ask_exit(loop, signame):
    print("got signal {0}: exit".format(signame))
    loop.stop()


def main():
    # TODO: this should be covered in a way like a daemon works
    parser = argparse.ArgumentParser(description='This console App enables the Cyborg Keys on a Mad_Catz_V.7 Keyboard')
    parser.add_argument('--config-file', dest='conffile', required=False, action='store',
                        default='~/.config/pycyborg/cyborg3.yml', metavar='<Config File>',
                        help='Path to Config File. Default: ~/.config/pycyborg/cyborg3.yml')
    args = parser.parse_args()
    ckeys = loadconfig(args.conffile)
    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                functools.partial(ask_exit, loop=loop, signame=signame))
    try:
        hiddev = open(get_keyboard_addr(), 'rb')
        loop.add_reader(hiddev, functools.partial(read_keypress, hiddev=hiddev, ckeys=ckeys))
        loop.run_forever()
    finally:
        hiddev.close()
        loop.close()

if __name__ == '__main__':
    main()

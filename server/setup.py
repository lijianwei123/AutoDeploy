#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''

import os
import sys

import time

sys.path.append("..")

import common.util as util


# check if python version >= 2.6 and < 3.0
if sys.version_info < (2, 6):
    sys.stderr.write("Sorry, autodeploy requires at least Python 2.6\n")
    sys.exit(0)
if sys.version_info >= (3, 0):
    sys.stderr.write("Sorry, Python 3.0+ is unsupported at present。\n")
    sys.exit(0)

# check if linux kernel supports inotify
if not os.path.exists("/proc/sys/fs/inotify"):
    sys.stderr.write("Sorry, your linux kernel doesn't support inotify。\n")
    sys.exit(0)

print "Start to install necessary modules ..."

# check if easy_install has been installed
exitCode = os.system("easy_install -h")
if exitCode > 0:
    os.system("yum -y install python-setuptools")

#install pyinotify
os.system("easy_install pyinotify")

#install python-devel
os.system("yum -y install python-devel")

#install setproctitle
os.system("easy_install setproctitle")

#install cherrypy
os.system("easy_install cherrypy")

#install jinja2
os.system("easy_install jinja2")

#install psutil
os.system("easy_install psutil")

#sleep 3
print util.getNowTime()
time.sleep(3)
print util.getNowTime()  


reload(sys)

# check if pyinotify has been installed
try:
    import pyinotify
    print "Installation complete successfully!" 
except ImportError as e:
    sys.stderr.write("Sorry, Installation pyinotify module failure! Please try to install it manually。\n")
    sys.exit(0)


    

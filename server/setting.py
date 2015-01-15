#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''

import os, sys
import pyinotify

#pack format
packet_format = "!LL64s128sL"


#监听目录     参照rsyncd.conf 模块配置
watchPath = {}
watchPath['test'] = '/data/test/f3.v.veimg.cn/'

#exclude path
excludePath = []

#是否开启api 服务
withInterface = 1

#是否监控daemon
monitorDaemon = 1


#sqlite
dbPath = os.getcwd() + os.sep + 'data/server.db'
#daemon log
daemonLogPath = os.getcwd() + os.sep + 'log/daemon.log'
#run pos file
runPosFile = os.getcwd() + os.sep + 'log/run.pos'
#mask
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO | pyinotify.IN_ATTRIB
#pid
runPidFile = os.getcwd() + os.sep + 'log/run.pid' 


#日志
logFileName = os.getcwd() + os.sep + 'log/app.log'
maxBytes = 104857600
backupCount = 5


#Tcp
TcpPort = 11597
ApiPort = 12597


#组播ip
#224.0.0.0到239.255.255.255
groupIp = '239.0.0.1'
groupPort = 11598
#ttl
multicast_ttl = 1



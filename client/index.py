#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''


import socket
import time
import os
import sys
import struct
import threading
import Queue

import signal

import traceback

sys.path.append("..")
from common.argv_opt import argv_opt
import common.util as util
import common.command as command

import asyncore

import setting

import client

import g

from  EnvCheck import EnvCheck



def signHandler(signum = None, frame=None):
    #保存run pos
    global tcpClientObj
    if client.TcpClient.run_pos:
        tcpClientObj.flushRunPos(client.TcpClient.run_pos)
    
    
    g.logger.info('quit')
    sys.exit()

def regSignal():
    #CTRL+C
    signal.signal(signal.SIGINT, signHandler)
    #kill
    signal.signal(signal.SIGTERM, signHandler)
    #quit
    signal.signal(signal.SIGQUIT, signHandler) 

                
if __name__ == '__main__':
    #utf-8
    util.set_sys_to_utf8()
    
    global tcpClientObj
    
    #选项检测
    opt = argv_opt(longopts = ['host=', 'port=', 'user=', 'group='])
    opt.analysis()
    
    g.TcpIp = opt.getOptValue('host', setting.TcpIp)
    g.TcpPort = opt.getOptValue('port', setting.TcpPort)
    
    g.user = opt.getOptValue('user', setting.user)
    g.group = opt.getOptValue('group', setting.group)
    
    addr = (g.TcpIp, g.TcpPort)
    
    g.events_queue = Queue.Queue()
    
    g.logger = util.get_logger(setting.logFileName)
    
    #are you ready
    e = EnvCheck(addr)
    
    #信号
    regSignal()
    
    g.logger.debug('addr:%s:%d' %addr)
    #开启两个线程,玩起来
    tcpClientObj = client.TcpClient(addr)
    tcpClientObj.start()

    udpClientObj = client.UdpClient(tcpClientObj)
    udpClientObj.start()
    
    asyncore.loop(use_poll=True)
    g.logger.info('asyncore loop finish')

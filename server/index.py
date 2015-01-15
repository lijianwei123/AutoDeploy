# /usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''

import asyncore
import socket
import time
import os
import sys
import struct
import threading
import Queue
import signal
import pyinotify
import sqlite3
import itertools
import json
import pickle

import collections


sys.path.append("..")
import common.util as util


import server
import watchdir

import g
import setting

import api


def watchDirByDb():
    #udp 组播
    server.RunUdpServer(g.addr).start()
    
    wm = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(wm, watchdir.DbEventHandler(setting.dbPath))
    for moduleName in setting.watchPath:
        path = setting.watchPath[moduleName]
        wdd = wm.add_watch(path, setting.mask, rec=True, auto_add = True)
    notifier.loop()
    sys.exit(0)


def daemonDoSomeThing(callback=None):
    #检测守护进程是否已经启动
    if util.checkProcessStatusByName("AutoDeployServer-watchDirByDb"):
        return
    util.createFile(setting.daemonLogPath)
     
    try:
        pid = os.fork()
    except OSError, e:
        print e
    
    if pid == 0:
        #child
        util.daemonize(setting.daemonLogPath, setting.daemonLogPath, setting.daemonLogPath)
        util.setProcName("AutoDeployServer-watchDirByDb")
        callback()
    else:
        #parent
        g.logger.debug("fork pid: " + str(pid))

#监控daemon  挂掉自动重启      
def monitorDaemon():
    if util.checkProcessStatusByName("AutoDeployServer-monitorDaemon"):
        return
     
    try:
        pid = os.fork()
    except OSError, e:
        print e
    
    if pid == 0:
        #child
        util.daemonize(setting.daemonLogPath, setting.daemonLogPath, setting.daemonLogPath)
        util.setProcName("AutoDeployServer-monitorDaemon")
        
        #定时器
        signal.signal(signal.SIGALRM, _intervalMonitorDaemon)
        signal.setitimer(signal.ITIMER_REAL, 5, 5)
        
        while True:
            time.sleep(10000)
        
    else:
        g.logger.debug("AutoDeployServer-monitorDaemon start")
        
def _intervalMonitorDaemon(signum = None, frame=None):
    if not util.checkProcessStatusByName("AutoDeployServer-watchDirByDb"):
        g.logger.critical('AutoDeployServer-watchDirByDb down!')
        #启动
        daemonDoSomeThing(watchDirByDb)
        
        try:
            pid, status = os.wait()
            g.logger.debug("wait success: %d, %d" %(pid, status))
        except OSError, e:
            g.logger.debug("wait error: %s" %e)

 
def signChldHandler(signum = None, frame=None):
    try:
        pid, status =  os.waitpid(-1, os.WNOHANG)
        g.logger.debug("waitpid success: %d, %d" %(pid, status))
    except (OSError, IOError), e:
        g.logger.debug("waitpid error: %s" %e)

def signHandler(signum = None, frame=None):
    import cherrypy
    cherrypy.engine.exit()
    sys.exit("quit")
        
def regSignal():
    #子进程结束  使用这个会造成   os.popen  subprocess.popen 一些蛋疼的问题
    #signal.signal(signal.SIGCHLD, signChldHandler)
    #CTRL+C
    signal.signal(signal.SIGINT, signHandler)
    #kill
    signal.signal(signal.SIGTERM, signHandler)
    #quit
    signal.signal(signal.SIGQUIT, signHandler) 

def logPid(runPidFile):
    pid = os.getpid()
    f = open(runPidFile, 'w')
    f.write(str(pid))
    f.close() 
    

class EnvCheck():
    def __init__(self):
        self.checkWatchPath()
    
    def checkWatchPath(self):
        for moduleName in setting.watchPath:
            path = setting.watchPath[moduleName]
            if not os.path.exists(path):
                g.logger.error("module:%s path:%s don't exist" %(moduleName, path))
                sys.exit(1)
                
            #还需要检测   /data/test/f3.v.veimg.cn   /data/test 这种包含关系的监控
            if util.haveParentPath(path, setting.watchPath):
                g.logger.error("setting path:%s have parent path" %path)
                sys.exit(1)
            
        
        
      
if __name__ == '__main__':
    #utf-8
    util.set_sys_to_utf8()
    
    #环境检测
    EnvCheck()
    
    #获取host  port
    try:
        host = sys.argv[1]
        port = int(sys.argv[2])
    except IndexError, e:
        host = '0.0.0.0'
        port = setting.TcpPort
    #addr
    g.addr = (host, port)
    #队列
    g.events_queue = Queue.Queue()
    #日志
    g.logger = util.get_logger(setting.logFileName)
    #线程锁
    g.condLock = threading.Condition()
   
    #信号处理
    regSignal()
    
    #记录pid
    logPid(setting.runPidFile)
    
    #修改进程名称
    util.setProcName("AutoDeployServer")
 
    #db记录目录变化
    daemonDoSomeThing(watchDirByDb)
    
    if setting.monitorDaemon:
        monitorDaemon()
    
    #api 服务
    if setting.withInterface:
        apiThread = threading.Thread(target = api.start)
        apiThread.setDaemon(True)
        apiThread.start()
    
    
    #最多2个子进程
    for i in range(2):
        try:
            pid, status = os.wait()
            g.logger.debug("wait success: %d, %d" %(pid, status))
        except OSError, e:
            g.logger.debug("wait error: %s" %e)
    #print pid
    #print status
    #print os.WIFEXITED(status)    
    
    #开启服务
    server.StartServer((host, port))
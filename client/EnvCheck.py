#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''

import os
import sys
import socket

import g
import setting

#环境监测
class EnvCheck():
    def __init__(self, tcpServerAddr, rsyncPort = 873):
        self.tcpServerAddr = tcpServerAddr
        self.rsyncPort = rsyncPort
        
        self.checkRsyncServer()
        self.checkTcpServer()
    
    #rsync server
    def checkRsyncServer(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.tcpServerAddr[0], self.rsyncPort))
        except socket.error, e:
            raise
        except Exception, e:
            raise
        else:
            g.logger.info("check rsync server status normal")
        finally:
            s.close()
            
    def checkTcpServer(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.tcpServerAddr)
        except socket.error, e:
            raise
        except Exception, e:
            raise
        else:
            g.logger.info("check tcp server status normal")
        finally:
            s.close()
    @staticmethod
    def checkWatchPath():
        if  not  g.watchPath:
            g.logger.error('watch path dict is empty')
            sys.exit(1)
        for moduleName in g.watchPath:
            path = g.watchPath[moduleName]
            if not os.path.exists(path):
                g.logger.error("watch path:%s don't exist" %path)
                sys.exit(1)

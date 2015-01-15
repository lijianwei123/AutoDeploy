#/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import time
import os
import sys
import struct
import threading
import Queue

import signal

import traceback

import commands

sys.path.append("..")
from common.argv_opt import argv_opt
import common.util as util
import common.command as command

import asyncore

import setting

import g

from EnvCheck import EnvCheck

class BaseClient():
    def __init__(self):
        pass
    
    def _packData(self, command, extraInfo = '', pos = 0):
        return struct.pack(setting.packet_format, len(command), len(extraInfo), command, extraInfo, pos)
    
    def _unpackData(self, respStr):
        commandLen, extraLen, command, extra, pos = struct.unpack(setting.packet_format, respStr)
        return (command[:commandLen], extra[:extraLen], pos)
    
    #请求
    def _request(self, data):
        self._dataWriteList.append(data)
    
    #响应
    def _response(self):
        packet_size = struct.calcsize(setting.packet_format)
        data,address = self.socket.recvfrom(packet_size + 200)
      	 
        return self._unpackData(data) if data else data

class UdpClient(BaseClient):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.set_reuse_addr()
        
        #加入到组播组  
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(setting.groupIp) + socket.inet_aton('0.0.0.0'))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton('0.0.0.0'))
        #self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)
        
        self.socket.bind((setting.groupIp, setting.groupPort))
	#print socket.MSG_PEEK
	
	while True:
        	print self.socket.recvfrom(10)
        	data, sender = self.socket.recvfrom(1500)
        	while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
        	print (str(sender) + '  ' + repr(data))

if __name__ == '__main__':
	UdpClient()

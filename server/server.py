#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''



import asyncore
import socket
from socket import errno

import time
import sys
import struct
import os
import threading
from SocketServer import ForkingMixIn, TCPServer

sys.path.append("..")
import common.util as util
import common.command as command

import g
import setting

import watchdir

class BaseCommand():
    def __init__(self):
        pass
    def methodExist(self, methodName):
        return hasattr(self, methodName) and callable(getattr(self, methodName))

#成功
class SuccessCommand(BaseCommand):
    def __init__(self):
        BaseCommand.__init__(self)
        
    def sysAddFilePathWPriv(self, *args):
        g.condLock.acquire()
        g.flag = 1
        g.condLock.notify()
        g.condLock.release()
        
        
    def sysForceSync(self, *args):
        g.condLock.acquire()
        g.flag = 1
        g.condLock.notify()
        g.condLock.release()
        
    #同步的状态
    def sysSyncStatus(self, *args):
        tcpRequestHandlerObj = args[1]
        addr = RunTcpServer.getAddrByFileno(tcpRequestHandlerObj.fileno)
        
        g.condLock.acquire() 
        
        g.resppDict[str(addr)] = '已同步'
        if len(g.resppDict) == RunTcpServer.clientSockSize():
            g.condLock.notify()
        
        g.condLock.release()

#失败
class FailCommand(BaseCommand):
    def __init__(self):
        BaseCommand.__init__(self)
        
    def sysAddFilePathWPriv(self, *args):
        g.condLock.acquire()
        g.flag = 0
        g.condLock.notify()
        g.condLock.release()
        
    def sysForceSync(self, *args):
        g.condLock.acquire()
        g.flag = 0
        g.condLock.notify()
        g.condLock.release()
        
    #同步的状态
    def sysSyncStatus(self, *args):
        tcpRequestHandlerObj = args[1]
        addr = RunTcpServer.getAddrByFileno(tcpRequestHandlerObj.fileno)
        
        g.condLock.acquire()
        
        g.resppDict[str(addr)] = '未同步'
        if len(g.resppDict) == RunTcpServer.clientSockSize():
            g.condLock.notify()
            
        g.condLock.release()

class CommandSet(BaseCommand):
    def __init__(self):
        BaseCommand.__init__(self)
        
        self.sCommand = SuccessCommand()
        self.fCommand = FailCommand()
        
   
    
    #####################处理客户端发过来的命令###############################
    def sysGetWatchPath(self, *args):
        g.logger.debug('sysGetWatchPath starting')
        watchPathStr = util.serialize(setting.watchPath)
        g.logger.debug('watchPathStr: %s' %watchPathStr)
        self._request(self._packData(command.server['sysSendWatchPath'], str(len(watchPathStr))) + watchPathStr)
    
    def sysPullByDbPos(self, *args):
        startPos = int(args[1])
        endPos = int(args[0])
        
        sqlite = watchdir.SqliteDbModel(setting.dbPath)
        
        while True:
            row = sqlite.getDirChangeByPos(startPos)
            g.logger.debug('sqlite pos:%d row:%s' %(startPos, row))
            
            if (row == None) or (endPos != -1 and startPos > endPos):
                g.logger.debug('server command: %s' %command.server['sysPullByDbPosDone'])
                self._request(self._packData(command.server['sysPullByDbPosDone']))
                break
            else:
                self._request(self._packData(row['command'], row['file_path'], int(row['id'])))
                startPos += 1
        
     
    def success(self, *args):
        command = str(args[0])
        pos = int(args[1])
        
        g.logger.debug('success: %s, %d' %(command, pos))
        
        if self.sCommand.methodExist(command):
            getattr(self.sCommand, command)(pos, self)
        else:
            pass
        
        
    def fail(self, *args):
        command = str(args[0])
        pos = int(args[1])
        
        g.logger.debug('fail: %s, %d' %(command, pos))

        if self.fCommand.methodExist(command):
            getattr(self.fCommand, command)(pos, self)
        else:
            pass
    #####################处理客户端发过来的命令###############################
    
class BaseRequestHandler():
    def __init__(self):
        pass
    
    
    #######################################################################
    @staticmethod
    def _packData(command, extraInfo = '', pos = 0):
        return struct.pack(setting.packet_format, len(command), len(extraInfo), command, extraInfo, pos)
    
    @staticmethod
    def _unpackData(respStr):
        commandLen, extraLen, command, extra, pos = struct.unpack(setting.packet_format, respStr)
        return (command[:commandLen], extra[:extraLen], pos)
     
    #请求
    def _request(self, data):
        self._dataWriteList.append(data)
        
    #响应
    def _response(self):
        packet_size = struct.calcsize(setting.packet_format)
        data = self.recv(packet_size)
        
        g.logger.debug("recive data:" + data)
        
        return self._unpackData(data) if data else data
    #######################################################################
    

class TcpRequestHandler(BaseRequestHandler, CommandSet, asyncore.dispatcher):
    def __init__(self, sock=None, map=None, chunk_size=2048):
        BaseRequestHandler.__init__(self)
        CommandSet.__init__(self)
        asyncore.dispatcher.__init__(self, sock, map)
        
        self.chunk_size = chunk_size
        
        self._dataWriteList = list()
        
        self.fileno = self.socket.fileno()

    #######################################################################
    def readable(self):
        return True
        
    def writable(self):
        response = (not self.connected) or len(self._dataWriteList)
        return response
        
    def handle_write(self):
        data = self._dataWriteList.pop(0)
        sent = self.send(data[:self.chunk_size])
        if sent < len(data):
            remaining = data[sent:]
            self._dataWriteList.append(remaining)
        
    def handle_read(self):
        respList = self._response()
        if not respList:
            return
        

        execCommand, extraInfo, pos = respList
        g.logger.debug("command:%s, extraInfo: %s, pos: %d" %respList)
        if execCommand.startswith('exec') and self.methodExist(execCommand):
            getattr(self, execCommand)(extraInfo, pos)
        elif execCommand.startswith('sys') and self.methodExist(execCommand):	
            getattr(self, execCommand)(extraInfo, pos)
        elif execCommand in (command.success, command.fail) and self.methodExist(execCommand):
            getattr(self, execCommand)(extraInfo, pos)
            
    def handle_close(self):
        RunTcpServer.removeSock(self.fileno)
        asyncore.dispatcher.handle_close(self)
    #######################################################################

class RunTcpServer(threading.Thread, asyncore.dispatcher):
    
    clients = {}
    
    def __init__(self, addr):
        asyncore.dispatcher.__init__(self)
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.debug = True
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(addr)
        self.listen(2000)
    
    def run(self):
        g.logger.debug('start sendServerOnlinePacket')
        #通知孩儿们
        RunUdpServer.sendServerOnlinePacket()
        
        
    def handle_accept(self):
        sock, addr = self.accept()
        if sock is None:
            pass
        else:
            g.logger.debug("sock:%s - addr:%s" %(sock, addr))
            g.logger.debug('client sock size: %d' %self.clientSockSize())
            
            self.pushSock(sock, addr)
            handler = TcpRequestHandler(sock=sock)
            
    @staticmethod         
    def pushSock(sock, addr):
        if not sock.fileno() in RunTcpServer.clients.keys():
            RunTcpServer.clients[sock.fileno()] = {'sock': sock, 'addr': addr}
            
    @staticmethod
    def removeSock(fileno):
        if fileno in RunTcpServer.clients.keys():
            RunTcpServer.clients.pop(fileno)
            
    @staticmethod
    def clientSockSize():
        return len(RunTcpServer.clients)
    
    @staticmethod
    def getAddrByFileno(fileno):
        if fileno in RunTcpServer.clients.keys():
            return  RunTcpServer.clients[fileno]['addr']
        
    
    
#组播  发送
class RunUdpServer(threading.Thread,  BaseRequestHandler):
    def __init__(self, addr):
        threading.Thread.__init__(self)
        BaseRequestHandler.__init__(self)
        
        self._dataWriteList = []
        
        self.daemon = True
        
        self.socket = self.__class__.connectMultiCastServer()
        
        self.sqlite = watchdir.SqliteDbModel(setting.dbPath)
    
    @staticmethod
    def connectMultiCastServer():
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        ttl_bin = struct.pack('@i', setting.multicast_ttl)
        udpSocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
        return udpSocket
    
    
    @staticmethod
    def sendServerOnlinePacket():
        '''孩儿们，老大王者归来了.
        '''
        g.logger.debug('sendServerOnlinePacket sending')
        udpSocket = RunUdpServer.connectMultiCastServer()
        udpSocket.sendto(RunUdpServer._packData(command.server['sysServerOnline']), (setting.groupIp, setting.groupPort))
        #发送    watchPath
        watchPathStr = util.serialize(setting.watchPath)
        udpSocket.sendto(RunUdpServer._packData(command.server['sysSendWatchPath'], str(len(watchPathStr))) + watchPathStr, (setting.groupIp, setting.groupPort))
        
        udpSocket.close()
        
    @staticmethod
    def addFilePathWPriv(filePath):
        '''添加可写权限.
        '''
        g.logger.debug('addFilePathWPriv sending')
        udpSocket = RunUdpServer.connectMultiCastServer()
        udpSocket.sendto(RunUdpServer._packData(command.server['sysAddFilePathWPriv'], filePath), (setting.groupIp, setting.groupPort))

        udpSocket.close()
        
    @staticmethod
    def delFilePathWPriv(filePath):
        '''取消可写权限.
        '''
        g.logger.debug('delFilePathWPriv sending')
        udpSocket = RunUdpServer.connectMultiCastServer()
        udpSocket.sendto(RunUdpServer._packData(command.server['sysDelFilePathWPriv'], filePath), (setting.groupIp, setting.groupPort))

        udpSocket.close()
        
    @staticmethod
    def forceSync(filePath):
        '''强制同步目录
        '''
        g.logger.debug('forceSync sending')
        udpSocket = RunUdpServer.connectMultiCastServer()
        udpSocket.sendto(RunUdpServer._packData(command.server['sysForceSync'], filePath), (setting.groupIp, setting.groupPort))

        udpSocket.close()
    
    @staticmethod
    def syncStatus(filePath):
        '''同步状态
        '''
        g.logger.debug('syncStatus sending')
        udpSocket = RunUdpServer.connectMultiCastServer()
        udpSocket.sendto(RunUdpServer._packData(command.server['sysSyncStatus'], filePath), (setting.groupIp, setting.groupPort))

        udpSocket.close()
    
    def run(self):
        while True:
            try:     
                taskInfo = g.events_queue.get()
                g.logger.debug(taskInfo)
                self.socket.sendto(self._packData(taskInfo['action'], taskInfo['filePath'], taskInfo['pos']), (setting.groupIp, setting.groupPort))
                #告诉sqlite 
                self.sqlite.updateMcastStatus(taskInfo['pos'])
            except IndexError, e:
                pass
            
    def __del__(self):
        if self.socket:
            self.socket.close()
        if self.sqlite:
            self.sqlite.close()

#开启监听
def StartServer(addr):
    #tcp
    RunTcpServer(addr).start()
    asyncore.loop(use_poll=True)
    
if __name__ == '__main__':
    StartServer(('0.0.0.0', 11597))

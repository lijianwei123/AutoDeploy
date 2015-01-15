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


#线程锁
taskCondLock = threading.Condition()

serverCondLock = threading.Condition()

fatherSonCondLock = threading.Condition()

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
        g.logger.debug("start response")
        packet_size = struct.calcsize(setting.packet_format)
        data = self.recv(packet_size)
        
        g.logger.debug("recive data:" + data)
        
        return self._unpackData(data) if data else data
    
    #成功
    def respSuccess(self, pos = 0, execCommand = ''):
        g.logger.debug('respSuccess: %s' %execCommand)
        self._request(self._packData(command.success, str(execCommand), pos))
    
    #失败
    def respFail(self, pos = 0, execCommand = ''):
        g.logger.debug('respFail: %s' %execCommand)
        self._request(self._packData(command.fail, str(execCommand), pos))


class CommandSet():
    def __init__(self):
        pass
    
    ##############################辅助办法###############################
    def methodExist(self, methodName):
        return hasattr(self, methodName) and callable(getattr(self, methodName))
    
    
    def _getRelativePath(self, filePath):
        g.logger.debug('_getRelativePath watchPath:%s' %g.watchPath)
        filePath = filePath.rstrip('/')
        for moduleName in g.watchPath:
            path = g.watchPath[moduleName]
            path = path.rstrip('/')
            g.logger.debug('filePath:%s' %filePath)
            g.logger.debug('path:%s' %path)
            if filePath.startswith(path):
                relativePath = filePath.replace(path, '').lstrip('/')
                return (moduleName, relativePath)
        return (None, None)
    
    #command
    def rsyncFile(self, *args):
        filePath = args[0]
        
        moduleName, relativePath = self._getRelativePath(filePath)
        
        if not moduleName:
            g.logger.error('filePath:%s get moduleName error' %filePath)
            return False
        
        command = '/usr/bin/rsync -zrt --delete  --password-file=%s %s@%s::%s/%s %s' \
            %(setting.password_file, setting.auth_user, g.TcpIp, moduleName, \
              util.escapeshellarg(relativePath), util.escapeshellarg(os.path.dirname(filePath))) 
            
        status, output = commands.getstatusoutput(command)
        
        if status:
            g.logger.error('rsync command:%s error:%s' %(command, output))
            return False
        else:
            g.logger.info('rsync command:%s success' %command)
            return True
    ##############################辅助办法###############################
    
    
    ##############################处理服务端发送过来的命令###############################
    #tcp create
    def execCreate(self, *args):
        #args = map(util.escapeshellarg, args)
       
        filePath = args[0]

        if self.rsyncFile(*args):
            command = "chown -R %s:%s %s" %(g.user, g.group, util.escapeshellarg(filePath))
            status, output = commands.getstatusoutput(command)
            if not status:
                return True
            else:
                g.logger.error('create filePath: %s fail msg: %s' %(filePath, output))
        
        g.logger.error('create filePath: %s rsync fail' %filePath)
        return False
            
    #tcp 删除
    def execDelete(self, *args):
        #args = map(util.escapeshellarg, args)

        filePath = util.escapeshellarg(args[0])
        
        command = 'mv ' + filePath + ' ' + os.path.dirname(filePath) + os.path.sep + "." + os.path.basename(filePath)
        command = 'rm -rf ' + filePath
        status, output = commands.getstatusoutput(command)
        if not status:
            return True
        else:
            g.logger.error('delete filepath: %s fail msg: %s' %(filePath, output))
            return False
        
    #tcp 修改    
    def execModify(self, *args):
        #args = map(util.escapeshellarg, args)

        return self.rsyncFile(*args)
    
    #tcp 文件移出被监测的目录
    def execMoveFrom(self, *args):
        #args = map(util.escapeshellarg, args)

        return self.execDelete(*args)
    
    #tcp 文件移入被监测的目录
    def execMoveTo(self, *args):
        #args = map(util.escapeshellarg, args)

        return self.rsyncFile(*args)
    
    #tcp 获取watch path
    def sysSendWatchPath(self, *args):
        watchPathStrLen = int(args[0])
        
        watchPathStr = self.recv(watchPathStrLen)
        
        g.watchPath = util.unserialize(watchPathStr)
        
        g.logger.debug('get watchPath: %s' %g.watchPath)
        
        #检测watch path
        EnvCheck.checkWatchPath()
        
        return True
    
    #tcp db拉取日志完成
    def sysPullByDbPosDone(self, *args):
        global taskCondLock
        taskCondLock.acquire()
        taskCondLock.notify()
        taskCondLock.release()
        
        return True
    
    #udp 系统online
    def sysServerOnline(self, *args):
        global serverCondLock
        serverCondLock.acquire()
        serverCondLock.notify()
        serverCondLock.release()
        
        return True
    
    #udp 添加写权限
    def sysAddFilePathWPriv(self, *args):
        filePath = args[0]

        command = 'chmod  u+w ' + filePath
        
        status, output = commands.getstatusoutput(command)
        if not status:
            return True
        else:
            g.logger.error('execAddFilePathWPriv filepath: %s fail msg: %s' %(filePath, output))
            return False
        
    #udp 取消写权限
    def sysDelFilePathWPriv(self, *args):
        filePath = args[0]

        command = 'chmod  ugo-w ' + filePath
        
        status, output = commands.getstatusoutput(command)
        if not status:
            return True
        else:
            g.logger.error('execDelFilePathWPriv filepath: %s fail msg: %s' %(filePath, output))
            return False
    
    #udp  强制同步目录
    def sysForceSync(self, *args):
        filePath = args[0]
        
        if self.rsyncFile(*args):
            command = "chown -R %s:%s %s" %(g.user, g.group, util.escapeshellarg(filePath))
            status, output = commands.getstatusoutput(command)
            return not status
        else:
            return False
    
    #udp 同步状态   
    def sysSyncStatus(self, *args):
        filePath = args[0]
        
        isDir = os.path.isdir(filePath)
        
        moduleName, relativePath = self._getRelativePath(filePath)
        
        localPath = os.path.dirname(filePath) if isDir else filePath
         
        command = '/usr/bin/rsync -zrtni  --password-file=%s %s@%s::%s/%s %s' \
            %(setting.password_file, setting.auth_user, g.TcpIp, moduleName, \
              util.escapeshellarg(relativePath), util.escapeshellarg(localPath))
        
        status, output = commands.getstatusoutput(command)
        
        g.logger.debug('sysSyncStatus command: %s, output: %s' %(command, output))
        return not bool(output)
    ##############################处理服务端发送过来的命令###############################
    

class TcpClient(asyncore.dispatcher, threading.Thread, BaseClient, CommandSet):
    
    success_counts = 0
    
    run_pos = 0

    def __init__(self, addr, chunk_size=1024):
        asyncore.dispatcher.__init__(self)
        threading.Thread.__init__(self)
        BaseClient.__init__(self)
        CommandSet.__init__(self)
        
        self.debug = True
        self.setDaemon(True)
        
        self.addr = addr
        self.chunk_size = chunk_size
        self._dataWriteList = []
        
        self.logPid()
        
        self.haveConnected = False
        self.connectThread = threading.Thread(target = self.connectServer)
        self.connectThread.start()
        
        self.connectThread.join()
        
        self.getServerWatchPath()
        
    #######################################################################
    def handle_connect(self):
        g.logger.debug('handle connect')
        
    
    
    #create socket  connect server
    #block connect
    def connect(self, address):
        self.connected = False
        self.connecting = True
        self.socket.connect(address)
        
    def create_socket(self, family, type):
        self.family_and_type = family, type
        self.socket = socket.socket(family, type)   
        
    def getServerWatchPath(self):
        self._request(self._packData(command.client['sysGetWatchPath']))
        
        
    def connectServer(self):
        g.logger.debug('start connect server')
        global serverCondLock
        
        while True:
            serverCondLock.acquire()
            try:
                self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
                self.socket.setblocking(1)
                self.connect(self.addr)
                self.socket.setblocking(0)
            except socket.error, e:
                if not self.haveConnected:
                    g.logger.debug('connect server exception')
                    raise
                else:
                    g.logger.debug('connect server fail')
                    #等着吧
                    serverCondLock.wait()
            else:
                g.logger.debug('connected:%d' %self.connected)
                g.logger.debug('connect server success')
                
                self.set_socket(self.socket)
                
                self.handle_connect_event()
                
                self.haveConnected = True
                break;
            finally:
                serverCondLock.release()
                
            
    
    #检测状态
    def initCheckStatus(self):
        haveDoPos= 0
        
        #之前没有成功执行事件重做  或  第一次启动
        if not os.path.exists(setting.runPosFile):
            self.workFromServerDb(1, -1)
            
        g.logger.debug('initCheckStatus step 1')
        
        haveDoPos = self.readRunPos()
        
        #取队列头
        try:
            queueHead = self.readQueueHead()
        except Queue.Empty, e:
            #没有取到数据
            queueHead = None
        finally:
            if queueHead is not None:
                queueHeadPos = int(queueHead['pos'])
                self.workFromServerDb(haveDoPos + 1, queueHeadPos)
            else:
                queueHeadPos = 0
                self.workFromServerDb(haveDoPos + 1, -1)
        
        g.logger.debug('initCheckStatus step 2')
        
        haveDoPos = self.readRunPos()
        
        #如果执行位置大于队列头部位置
        if haveDoPos >= queueHeadPos:
            #从queue取数据  直到  haveDoPos  取数据执行event
            self.workFromQueue(haveDoPos + 1)
        else:
            raise Exception('An unknown error')
            

    
    #读取pos
    def readRunPos(self):
        g.logger.debug("readRunPos: %d" %int(TcpClient.run_pos))
        if not TcpClient.run_pos:
            try:
                f = open(setting.runPosFile, 'r')
                pos = f.readline()
                f.close()
            except IOError, e:
                pos = 0
            else:
                pos = int(pos)
                
            TcpClient.run_pos = pos
            return pos
        else:
            return TcpClient.run_pos
        
    #更新pos
    def updateRunPos(self, pos):
        g.logger.debug("updateRunPos: %d" %pos)
        TcpClient.run_pos = pos
        TcpClient.success_counts = TcpClient.success_counts + 1
        if TcpClient.success_counts >= setting.flush_pos_cond:
            self.flushRunPos(pos)
            TcpClient.success_counts = 0
            
    def flushRunPos(self, pos):
        f = open(setting.runPosFile, 'w')
        f.write(str(pos))
        f.close()
    
    #读取队头  raise Empty
    def readQueueHead(self):
        return g.events_queue.get(True, 3)
    
    def workFromQueue(self, startPos):
        g.logger.debug('start workFromQueue startPos:%d' %startPos)
        prevPos = startPos
                
        while True:
            eventList = g.events_queue.get().values()
            
            g.logger.debug('eventList:%s' %eventList)
            
            command = eventList.pop(0)
            pos = int(eventList[-1])
            
            if pos < startPos:
                continue
            else:
                if pos - prevPos > 1:
                    g.logger.debug('detect have skip')
                    #有翘班现象 
                    self.workFromServerDb(prevPos + 1, pos - 1)
                self.eventRoute(command, eventList)
                
                prevPos = pos
        g.logger.debug('end workFromQueue startPos:%d' %startPos)
    
    #从db中读取数据    
    def workFromServerDb(self, startPos, endPos = -1):
        startPos = int(startPos)
        endPos = int(endPos)
        g.logger.debug('start workFromServerDb startPos:%d, endPos:%d' %(startPos, endPos))
        self._request(self._packData(command.client['sysPullByDbPos'], str(endPos), startPos))
        while True:
            if endPos != -1 and self.readRunPos() >= endPos:
                break
            elif endPos == -1:
                global taskCondLock
                if taskCondLock.acquire():
                    taskCondLock.wait()
                    taskCondLock.release()
                    break;
            time.sleep(3)
        g.logger.debug('end workFromServerDb startPos:%d, endPos:%d' %(startPos, endPos))
                
        
    
    #event route
    def eventRoute(self, command = '', respList = []):
        g.logger.debug('eventRoute command:%s, respList:%s' %(command, respList))
        if command.startswith('exec') and self.methodExist(command):
            pos = respList[-1]
            #如果执行成功
            if getattr(self, command)(*respList):
                g.logger.debug('eventRoute command:%s, respList:%s success' %(command, respList))
                self.updateRunPos(pos)
                self.respSuccess(pos, execCommand=command)
            else:
                g.logger.debug('eventRoute command:%s, respList:%s fail' %(command, respList))
                self.updateRunPos(pos)
                self.respFail(pos, execCommand=command)
        elif command.startswith('sys') and self.methodExist(command):
            if getattr(self, command)(*respList):
                self.respSuccess(execCommand = command)
            else:
                self.respFail(execCommand = command)
                
    
    #记录当前进程
    def logPid(self):
        pid = os.getpid()
        f = open(setting.runPidFile, 'w')
        f.write(str(pid))
        f.close()
        
    def run(self):
        t = None
        while True:
            t = threading.Thread(target=self.doNothing)
            g.logger.debug("start thread doNothing isDaemon:%d" %t.isDaemon())
            t.start()
            t.join()
            
    def doNothing(self):
        global fatherSonCondLock
        fatherSonCondLock.acquire()
        
        #time.sleep(3)
        
        self.connectThread.join()
        self.connectThread = None
        
        t = threading.Thread(target=self.initCheckStatus)
        g.logger.debug("start thread initCheckStatus isDaemon:%d" %t.isDaemon())
        t.start()
        
        #等着吧
        fatherSonCondLock.wait()
        fatherSonCondLock.release()
    
    #关闭父线程，子线程自动关闭    
    def closeCheckStatusThread(self):
        global fatherSonCondLock
        fatherSonCondLock.acquire()
        fatherSonCondLock.notify()
        fatherSonCondLock.release()
    #######################################################################
    
    
    
    #######################################################################
    def readable(self):
        return True
        
    def writable(self):
        return len(self._dataWriteList) > 0
    
    def handle_write(self):
        data = self._dataWriteList.pop(0)
        sent = self.send(data[:self.chunk_size])
        if sent < len(data):
            remaining = data[sent:]
            self._request(remaining)
    
    def handle_read(self):
        g.logger.debug("start handle_read")
        respList = list(self._response())
        if not respList:
            return
        
        g.logger.debug('client recevice data:%s' %str(respList))
        
        command = respList.pop(0)
        
        self.eventRoute(command, respList)  
    
    def handle_close(self):
        g.logger.debug("client sock close")
        asyncore.dispatcher.handle_close(self)
        g.logger.debug("socket_map: %s" %asyncore.socket_map)
        
        self._dataWriteList = []
        
        self.connectThread = threading.Thread(target = self.connectServer)
        self.connectThread.setDaemon(False)
        self.connectThread.start()
        
        self.closeCheckStatusThread() 
    
    def __del__(self):
        g.logger.debug('TcpClient __del__')
        #把run_pos写到硬盘中
        if TcpClient.run_pos:
            self.flushRunPos(TcpClient.run_pos)
       


class UdpClient(asyncore.dispatcher, threading.Thread, BaseClient, CommandSet):
    def __init__(self, tcpClient, chunk_size = 1024):
        asyncore.dispatcher.__init__(self)
        threading.Thread.__init__(self)
        BaseClient.__init__(self)
        CommandSet.__init__(self)
        
        self.tcpClient = tcpClient
        self.chunk_size = chunk_size
        
        self._dataWriteList = []
        self._dataRead = None
        
        self.daemon = True
        
        self.debug = True
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_reuse_addr()
        
        #加入到组播组  
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(setting.groupIp) + socket.inet_aton('0.0.0.0'))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton('0.0.0.0'))
        #self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1)
        
        self.bind((setting.groupIp, setting.groupPort))
        
    def run(self):
        g.logger.debug('udpclient thread running')
        #设置防火墙  不需要重启防火墙   会话级
        os.system("iptables -D " + setting.multicast_iptables_rule %setting.groupIp) #删除已有的
        os.system("iptables -I " + setting.multicast_iptables_rule %setting.groupIp) #加到头部
            
    #udp 响应
    def _response(self):
        self._dataRead = None
        
        g.logger.debug("UdpClient start response")
        packet_size = struct.calcsize(setting.packet_format)
        data, address= self.socket.recvfrom(self.chunk_size)
       	g.logger.debug("udp _response data: %s" %data) 
        packData = data[:packet_size]

        self._dataRead = data[packet_size:]
        
        g.logger.debug("recive data:" + packData)
        
        return self._unpackData(packData) if packData else packData
    
    #udp sysSendWatchPath
    def sysSendWatchPath(self, *args):
        watchPathStrLen = int(args[0])
        
        watchPathStr = self._dataRead[:watchPathStrLen]
        
        g.watchPath = util.unserialize(watchPathStr)
        
        g.logger.debug('get watchPath: %s' %g.watchPath)
        
        #检测watch path
        EnvCheck.checkWatchPath()
    
    #接收组播数据
    def handle_read(self):
        g.logger.debug('udpclient thread handle_read')
        commandStr, extraInfo, pos = self._response()
        
        g.logger.debug('udp command:%s - extraInfo:%s - pos:%d' % (commandStr, extraInfo, pos))
        
        specialSysCommand = [command.client['sysServerOnline'], command.client['sysSendWatchPath'], command.client['sysAddFilePathWPriv'], 
                             command.client['sysDelFilePathWPriv'], command.client['sysForceSync'], command.client['sysSyncStatus']]

        #特殊的一些命令   直接执行
        if commandStr in specialSysCommand and commandStr.startswith('sys') and self.methodExist(commandStr):
            if getattr(self, commandStr)(*(extraInfo, pos)):
                self.tcpClient.respSuccess(execCommand = commandStr)
            else:
                self.tcpClient.respFail(execCommand = commandStr)
        else:
            g.events_queue.put({'action': commandStr, 'extraInfo': extraInfo, 'pos': pos})

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
import pyinotify
import sqlite3
import itertools

sys.path.append("..")
import common.util as util
import common.command as command

import g
import setting



class EventHandler(pyinotify.ProcessEvent):
    def __init__(self):
        pyinotify.ProcessEvent.__init__(self)
        
    def process_IN_DELETE(self, event):
        self.process_event(event, command.delete)
        
    def process_IN_CREATE(self, event):
        self.process_event(event, command.create)
    
    def process_IN_MODIFY(self, event):
        self.process_event(event, command.modify)
    
    def process_IN_MOVED_FROM(self, event):
        self.process_event(event, command.movedFrom)
        
    def process_IN_MOVED_TO(self, event):
        self.process_event(event, command.movedTo)

    def process_IN_ATTRIB(self, event):
        self.process_event(event, 'attrib')

    def process_event(self, event, action):
        filePath = self._getFilePathByEvent(event)
        if self._filter_filepath(filePath):
            g.logger.debug('action:' + action + ' filePath:' + filePath)
    
    def _filter_filepath(self, filePath):
        '''暂时过滤.开头的文件、目录
        '''
        basename = os.path.basename(filePath).lower()
        if basename.startswith('.') or basename.endswith('~') or filePath.find('/.svn/') != -1 or self._filter_exclude(filePath):
            return False
        else:
            return True
        
    def _filter_exclude(self, filePath):
        if not setting.excludePath:
            return False
        else:
            if filePath in setting.excludePath or util.haveParentPath(filePath, setting.excludePath):
                return True
        
    
    def _getFilePathByEvent(self, event):
        '''获取文件路径
        '''
        return os.path.join(event.path, event.name)

#@see:  http://www.dbafree.net/?p=1118  queue
class QueueHandler():
    @staticmethod
    def saveQueue(action, filePath, pos):
        g.events_queue.put({'action': action, 'filePath': filePath, 'pos': pos})       

class SqliteDbModel():
    def __init__(self, dbPath):
        self.dbPath = dbPath
        self.open()
        
    def open(self):
        self.conn = sqlite3.connect(self.dbPath, check_same_thread = False)
        #self.conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
        
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def saveDirChangeLog(self, data={"command": "", "filePath": ""}):
        if(len(data) == 0):
            return False
        self.cursor.execute('insert into changelog (command, file_path, add_time, modify_time) values(?, ?, ?, ?)', (data['command'], data['filePath'], util.getNowTime(), util.getNowTime()))
        self.conn.commit()
        
    def getCurrentPos(self):
        self.cursor.execute("select seq from sqlite_sequence where name = ?", ("changelog",))
        return int(self.cursor.fetchone()[0])
        
    def getDirChangeByPos(self, posId):
        self.cursor.execute('select * from changelog where id = ? limit 1', (posId, ))
        result = self._map_fields(self.cursor)
        if len(result) > 0:
            return result[0]
        return None
    
    def updateMcastStatus(self, pos):
        self.cursor.execute("update changelog set is_mcast = 1, modify_time = ? where id = ?", (util.getNowTime(), pos))
        self.conn.commit()
    
    def isCanForceSync(self, filePath):
        self.cursor.execute('select count(1) from changelog where is_mcast = 0 and file_path like ?', (filePath + '%', ))
        return not int(self.cursor.fetchone()[0])

        
    def findAll(self, status): 
        self.cursor.execute('select * from changelog where 1=1')
        result = self._map_fields(self.cursor)
        if len(result) > 0:
            return result
        return None
            
    def _map_fields(self, cursor):
        """将结果元组映射到命名字段中"""
        filednames = [d[0].lower() for d in cursor.description]
        result = []
        while True:
            rows = cursor.fetchmany()
            if not rows:
                break
            for row in rows:
                #row = map(util.encode, row)
                result.append(dict(itertools.izip(filednames, row)))
        return result
    
    def isTableExist(self, tableName):
        self.cursor.execute("SELECT  count(1)   FROM sqlite_master WHERE type = 'table' AND name = ?", (tableName, ))
        row = self.cursor.fetchone()
        return row[0] > 0
    
    def __del__(self):
        self.close()
      
class DbEventHandler(EventHandler, SqliteDbModel):
    def __init__(self, dbPath):
        EventHandler.__init__(self)
        SqliteDbModel.__init__(self, dbPath)
        
        self.initDb()
        
        self.bufferSet = ChangeLogSet()
        
        self.lock = threading.RLock()
        
        self.regAlarm()	
        #t = threading.Thread(target=self.regAlarm)
        #t.setDaemon(True)
        #t.start()
        
    def regAlarm(self):
        #注册定时器   0.5 s
        signal.signal(signal.SIGALRM, self.handleAlarm)
        #signal.setitimer(signal.ITIMER_VIRTUAL, 1, 0.5)
        signal.alarm(1)
        
        
    def handleAlarm(self, signum, frame):
        g.logger.debug('handleAlarm starting')
        
        if len(self.bufferSet):
            self.lock.acquire()
            
            g.logger.debug('handleAlarm: %d' %len(self.bufferSet))
    
            for filePath in self.bufferSet:
                action = self.bufferSet.getLogAction(filePath)
                self.saveChangeLog(action, filePath)
                
            #删除所有元素
            self.bufferSet.clear()
                   
            self.lock.release()
            
        signal.alarm(1)
        g.logger.debug('handleAlarm end')
        
    def saveChangeLog(self, action, filePath):
        self.saveDirChangeLog({'command': action, 'filePath': filePath})
        if g.events_queue != None:
            pos = self.getCurrentPos()
            QueueHandler.saveQueue(action, filePath, pos)
            
        
    def process_event(self, event, action):
        EventHandler.process_event(self, event, action)
        
        
        filePath = self._getFilePathByEvent(event)
    
        if self._filter_filepath(filePath):
            
            g.logger.debug('bufferSet add starting')
            
            self.lock.acquire()
            
            g.logger.debug('bufferSet add action: %s, filePath: %s' %(action, filePath))
            #重复的操作合并
            self.bufferSet.add(action, filePath)
            
            self.lock.release()
            
            g.logger.debug('bufferSet add end')
            
        else:
            pass
        
    
    def initDb(self):
        createSql = '''CREATE TABLE "changelog" (
"id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
"command"  TEXT NOT NULL,
"file_path"  TEXT NOT NULL,
"is_mcast"  INTEGER NOT NULL DEFAULT 0,
"add_time"  TEXT NOT NULL,
"modify_time"  TEXT NOT NULL
)'''
        indexSql = '''CREATE INDEX "file_path"
ON "changelog" ("file_path" ASC)'''
        
        if not self.isTableExist('changelog'):
            self.cursor.execute(createSql)
            self.cursor.execute(indexSql)
        
        #清空数据
        self.cursor.execute("delete from changelog")
        #自增值为0
        self.cursor.execute("update sqlite_sequence set seq = 0 where name = ?", ("changelog",))
        
        self.conn.commit()


class ChangeLogSet(set):
    def __init__(self):
        set.__init__(self)
        
        self.changeDict = dict()
        
         
    def add(self, action, filePath):
        if filePath not in self:
            if self.isNeedRsync(filePath):
                super(self.__class__, self).add(filePath)
                self.changeDict[filePath] = action

    
    #清除所有元素
    def clear(self):
        super(self.__class__, self).clear()
        
        self.changeDict.clear()
        
    def getLogAction(self, filePath):
        return self.changeDict[filePath]
                
    
    #/data/test/f3.v.veimg.cn
    def isNeedRsync(self, filePath):
        return not util.haveParentPathNotRecur(filePath, self)
        
        
        
         
if __name__ == '__main__':
    pass

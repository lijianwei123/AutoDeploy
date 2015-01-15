#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''

#common
success = "success"
fail = "fail"


delete  = "execDelete"
create  = "execCreate"
modify  = "execModify"
movedFrom = "execMoveFrom"
movedTo = "execMoveTo"
attrib  = "execAttrib"


#server command
server = {}

#从pos拉取数据
server['sysPullByDbPos'] = 'sysPullByDbPos'
server['sysPullByDbPosDone'] = 'sysPullByDbPosDone'

#服务端上线了
server['sysServerOnline'] = 'sysServerOnline'

#sysSendWatchPath
server['sysSendWatchPath'] = 'sysSendWatchPath'

#获取watchPath
server['sysGetWatchPath'] = 'sysGetWatchPath'

#可写权限
server['sysAddFilePathWPriv'] = 'sysAddFilePathWPriv'

#取消可写权限
server['sysDelFilePathWPriv'] = 'sysDelFilePathWPriv'

#强制同步目录
server['sysForceSync'] = 'sysForceSync'

#同步的状态
server['sysSyncStatus'] = 'sysSyncStatus'


#client  command
client = server



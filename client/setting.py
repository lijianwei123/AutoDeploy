#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-7-18

@author: lijianwei
'''

import os, sys

#pack format
packet_format = "!LL64s128sL"


#日志
logFileName = os.getcwd() + os.sep + 'log/app.log'
maxBytes = 104857600
backupCount = 5


#组播ip
#@see  http://baike.baidu.com/link?url=1t_ZwB8wkjNre69C5PZRGwn22kV-XMnG2n56Ltj4fOI5YPChaP5PtX_apMGsAxHf
# 224.0.0.0～224.0.0.255为预留的组播地址（永久组地址），地址224.0.0.0保留不做分配，其它地址供路由协议使用。
# 224.0.1.0～238.255.255.255为用户可用的组播地址（临时组地址），全网范围内有效。
# 239.0.0.0～239.255.255.255为本地管理组播地址，仅在特定的本地范围内有效。常用的预留组播地址列表如下：

#官方示例
#see  http://svn.python.org/projects/python/trunk/Demo/sockets/mcast.py
#224.0.0.0到239.255.255.255
groupIp = '239.0.0.1'
groupPort = 11598
#防火墙规则
multicast_iptables_rule = 'INPUT -p udp -s 168.192.122.0/24 -d %s -m pkttype --pkt-type multicast -j ACCEPT'


#Tcp
TcpIp = '168.192.122.29'
TcpPort = 11597

#run pos file
runPosFile = os.getcwd() + os.sep + 'log/run.pos'
#pid
runPidFile = os.getcwd() + os.sep + 'log/run.pid'
#什么时候把run pos写到硬盘
flush_pos_cond = 10

#rsync
user='www'
group='www'

auth_user = "dfws_rsync"
#权限一定要是  600
password_file = 'data/rsync.pass'




# /usr/bin/python
# -*- coding: utf-8 -*-


import time
import os
import sys
import logging
import logging.handlers
import signal

try:
	from setproctitle import setproctitle,getproctitle
except ImportError, e:
	pass


def set_sys_to_utf8():
	reload(sys)
	sys.setdefaultencoding('utf-8')

def getNowTime():
	return time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))
	

def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='dev/null'):
    '''Fork当前进程为守护进程，重定向标准文件描述符
        （默认情况下定向到/dev/null）
    '''
    # Perform first fork.
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # first parent out
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # 从母体环境脱离
    os.chdir("/")
    os.umask(0)
    os.setsid()
    # 执行第二次fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)  # second parent out
    except OSError, e:
        sys.stderr.write("fork #2 failed: (%d) %s]n" % (e.errno, e.strerror))
        sys.exit(1)

    # 进程已经是守护进程了，重定向标准文件描述符
    for f in sys.stdout, sys.stderr: f.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    
def get_logger(logFileName, maxBytes = 104857600, backupCount = 5):
	'''@see http://www.cnblogs.com/dkblog/archive/2011/08/26/2155018.html.
	'''
	formatStr = '%(asctime)s [processId:%(process)d] [threadName:%(threadName)s] %(filename)s[line:%(lineno)3d] %(levelname)-10s  %(message)s'
	
	#默认会输出到控制台
	logging.basicConfig(level=logging.DEBUG, format=formatStr)
	logger = logging.getLogger('AutoDeploy')
	handler1 = logging.handlers.RotatingFileHandler(logFileName, maxBytes = 104857600, backupCount = 5)
	format1 = logging.Formatter(formatStr)
	handler1.setFormatter(format1)
	logger.addHandler(handler1)
	return logger

def createFile(filePath):
	'''创建文件
	'''
	if os.path.exists(filePath):
		return False
	else:
		f = open(filePath, 'w')
		f.close()
		return True

def escapeshellarg(arg):
	if type(arg).__name__ == 'str':
		return "\\'".join("'" + p + "'" for p in arg.split("'")) 
	else:
		return arg

def setProcName(procName = ''):
	setproctitle(procName)

#获取局域网ip 依赖eth0配置   不一定准确
def getLanIp(ifname = 'eth0'):   
    import socket, fcntl, struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))   
    ret = socket.inet_ntoa(inet[20:24])   
    return ret
   

def compact(*names):
    import inspect
    caller = inspect.stack()[1][0] # caller of compact()
    vars = {}
    for n in names:
        if n in caller.f_locals:
            vars[n] = caller.f_locals[n]
        elif n in caller.f_globals:
            vars[n] = caller.f_globals[n]
    return vars

def checkProcessStatusByName(procName = ''):
	import commands
	command = "ps -ef|grep " + procName + "|grep -v grep"
	(status, output) = commands.getstatusoutput(command)
	return not bool(status)

def serialize(obj):
	import cPickle
	return cPickle.dumps(obj)

def unserialize(str):
	import cPickle
	return cPickle.loads(str)

#转换成utf8
def encode(str):
	if isinstance(str, unicode):
		return str.encode('utf-8', 'ignore')
	else:
		return str

#转换成unicode	
def decode(str):
	try:
		return str.decode('utf-8')
	except UnicodeDecodeError, e:
		return str.decode('gb2312')


def haveParentPath(path, paths):
    if path == '/' or not path: 
        return False
    
    if not haveParentPathNotRecur(path, paths):
        return haveParentPath(os.path.dirname(path), paths)
    return True
   
def haveParentPathNotRecur(path, paths):
    if path == '/' or not path: 
        return False
    
    return os.path.dirname(path) in paths

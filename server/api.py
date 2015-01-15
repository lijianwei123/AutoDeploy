#/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2014-8-11

@author: Administrator
'''
import struct
import socket
import os
import sys
import json
import time


import cherrypy
from cherrypy import request, response, tools



sys.path.append("..")
import common.util as util

#服务端
from server import RunUdpServer, RunTcpServer
import setting
import watchdir
import g

#前端模板
import web

#decorate
def skipAuth(func):
    if not hasattr(func, '_cp_config'):
            func._cp_config = dict()
                  
    func._cp_config['checkAuth'] = False
    
    return func

#decorate
def jsonOutput(func):
    def func_wrapper(*args, **kwargs):
        response.headers['Content-Type']= 'application/json'
        return json.dumps(func(*args, **kwargs))
    return func_wrapper

def renderTemplate(template, **kwargs):
    from jinja2 import Environment, PackageLoader
    jinja_env = Environment(loader=PackageLoader('web', 'templates'))
    
    import time
    defVars = {
               'base': '/static', 
               'js_path': '/static/js/', 
               'seajs_path': '/static/js/seajs/', 
               'js_plugins_path': '/static/js/plugins/', 
               'css_path' : '/static/css/',
               'image_path': '/static/img/',
               'cdn_version': time.time(),
               'cherrypy': cherrypy
               }
    
    kwargs.update(defVars)
    
    return jinja_env.get_template(template).render(**kwargs)

#查询目录
def listDirWithModule(module = None, path = None):
    realPath = os.path.join(setting.watchPath.get(module), path)
    l= os.listdir(realPath)
    dirs = []
    files = []
    
    l =  map(util.decode, l)
    
    for file in l:
        if not file.startswith('.'):
            tmpFile = os.path.join(realPath, file)
            file = os.path.join(path, file)
            if not os.path.exists(tmpFile):
                tmpFile = tmpFile.encode("gb2312")

            if os.path.isdir(tmpFile):
                dirs.append(file)
            else:
                files.append(file)
    return [map(util.encode, dirs), map(util.encode, files)]
        
def humanSize(byteSize = 0, unit = 'M'):
    units = {'M': 1024 * 1024, 'G': 1024 * 1024 * 1024}
    size = float(byteSize) / units[unit]
    return "%.2f" %size


#模板使用 Jinja2
class api():
    
    _cp_config = {
                  "tools.auth.on": True,
                  "checkAuth": True,
                  }

    
    def __init__(self):
        pass
    
    def checkAuth(self):
        if  request.config.get('checkAuth'):
            addr = request.headers['Remote-Addr']
            #if  addr != '183.129.151.66':
            #    raise  cherrypy.InternalRedirect('/deny')
            
            if not cherrypy.session.get('isLogin'):
                raise   cherrypy.HTTPRedirect(cherrypy.url('/login', {'referer': request.path_info + '?' + request.query_string}))
            
     
    @cherrypy.expose
    @skipAuth
    #@tools.json_out
    def deny(self):
        return self.ajaxError(-1, 'deny access')
    
    
    @cherrypy.expose
    @skipAuth
    def login(self, **kwargs):
        if request.method == 'GET':
            #渲染模板
            return renderTemplate("login.html")
        elif request.method == 'POST':
            token = kwargs.get('token')

            if token == 'dfws_lijianwei':
                cherrypy.session['isLogin'] = True
                
                referer = request.params.get('referer')
                if not referer:
                    raise cherrypy.HTTPRedirect('/') 
                else:
                    raise cherrypy.HTTPRedirect(referer)
            else:
                return self.ajaxError(-1, '登陆失败')
            
    
    @cherrypy.expose
    def index(self, **kwargs):
        #读取搜有模块
        return renderTemplate('index.html', modules = setting.watchPath)
    
    
    #文件列表
    @cherrypy.expose
    def list(self, **kwargs):
        path = kwargs.get('path', '')
        module = kwargs.get('module')
        
        if module not in setting.watchPath.keys():
            return self.ajaxError(-1, str(module) + '不存在')
        
        
        files = listDirWithModule(module, path)
 
        return renderTemplate("list.html", files = files, module = module, parentPath = os.path.dirname(path), path = path)
    
    
       
    #添加可写权限
    @cherrypy.expose
    def addWPriv(self, **kwargs):
        path = kwargs.get('path', '')
        module = kwargs.get('module')
        
        if module not in setting.watchPath.keys():
            return self.ajaxError(-1, str(module) + '不存在')
        
        realPath = os.path.join(setting.watchPath.get(module), path)
        g.logger.debug('addWPriv: %s' %realPath)

        #链接udp server  发送命令
        g.condLock.acquire()
        RunUdpServer.addFilePathWPriv(util.encode(realPath))
        g.condLock.wait(3)
        g.condLock.release()
        
        if g.flag == 1:
            g.flag = 0
            return self.ajaxOutput()
        elif g.flag == 0:
            g.flag = 0
            return self.ajaxError(-1, '操作失败')
        
    #取消可写权限
    @cherrypy.expose
    def delWPriv(self, **kwargs):
        path = kwargs.get('path', '')
        module = kwargs.get('module')
        
        if module not in setting.watchPath.keys():
            return self.ajaxError(-1, str(module) + '不存在')
        
        realPath = os.path.join(setting.watchPath.get(module), path)
        g.logger.debug('delWPriv: %s' %realPath)

        #链接udp server  发送命令
        g.condLock.acquire()
        RunUdpServer.delFilePathWPriv(util.encode(realPath))
        g.condLock.wait(3)
        g.condLock.release()
        
        if g.flag == 1:
            g.flag = 0
            return self.ajaxOutput()
        elif g.flag == 0:
            g.flag = 0
            return self.ajaxError(-1, '操作失败')

    
    #强制同步目录   当发现目录不一致的时候执行
    @cherrypy.expose
    def forceSync(self, **kwargs):
        path = kwargs.get('path', '')
        module = kwargs.get('module')
        
        if module not in setting.watchPath.keys():
            return self.ajaxError(-1, str(module) + '不存在')
        
        realPath = os.path.join(setting.watchPath.get(module), path)
        

        sqlite = watchdir.SqliteDbModel(setting.dbPath)
        if sqlite.isCanForceSync(realPath):
            
            g.condLock.acquire()
            RunUdpServer.forceSync(util.encode(realPath))
            g.condLock.wait(10)
            g.condLock.release()
            if g.flag == 1:
                g.flag = 0
                return self.ajaxOutput()
            elif g.flag == 0:
                g.flag = 0
            return self.ajaxError(-1, '操作失败')

        else:
            return self.ajaxError(-1, '暂时不可以同步')
        
    #同步的状态
    @cherrypy.expose
    def syncStatus(self, **kwargs):
        path = kwargs.get('path', '')
        module = kwargs.get('module')
        
        if module not in setting.watchPath.keys():
            return self.ajaxError(-1, str(module) + '不存在')
        
        realPath = os.path.join(setting.watchPath.get(module), path)
        
        g.condLock.acquire()
        RunUdpServer.syncStatus(util.encode(realPath))
        g.condLock.wait(10)
        g.condLock.release()
        
        data = g.resppDict
        g.resppDict = {}
        
        return self.ajaxOutput(data)

    
    #监控信息
    @cherrypy.expose
    def monitorInfo(self):
        pidFile = setting.runPidFile
        if not os.path.exists(pidFile):
            return self.ajaxError(-1, '进程好像没有运行')
        
        fp = open(pidFile, 'r')
        pid = int(fp.readline())
        fp.close()
        
        if not pid:
            return self.ajaxError(-1, '进程好像没有运行')
            
        try:
            import psutil
        except ImportError, e:
            return self.ajaxError(-1, 'psutil 模块未安装')
        
        #总的系统内存   namedtuple
        vm = psutil.virtual_memory()
        totalMem = {'total': humanSize(vm.total), 'used': humanSize(vm.used)}
        
        #总的cpu 
        cpuPercent = psutil.cpu_percent(interval = 1)
        
        #计算当前进程占有
        process = psutil.Process(pid)
        proCpuPercent = process.cpu_percent(interval = 1)
        proMemPercent = process.memory_percent()
        proMem = humanSize(process.memory_info().rss)
        
    
        
        #连接的客户端
        clientNum = len(RunTcpServer.clients)
        addrs = []
        
        if clientNum:
            for fileno, sockInfo in RunTcpServer.clients.items():
                addrs.append(sockInfo.get('addr'))
        
        return self.ajaxOutput({'clientNum': clientNum, 'addrs': addrs, 'totalMem': totalMem, 'cpuPercent': cpuPercent, 'proc': {'proMem': proMem, 'proCpuPercent': proCpuPercent, 'proMemPercent': proMemPercent} })
        
 
    @jsonOutput
    def ajaxOutput(self, data = []):
        return {'status': 1, 'data': data}
    
    @jsonOutput
    def ajaxError(self, errcode = -1, errmsg = ''):
        return {'status': 0, 'errcode': errcode, 'errMsg': errmsg}
        
  
        
def start():
  
    current_dir = os.path.dirname(os.path.abspath(__file__))
    staticRootDir = os.path.join(current_dir, 'web')  
    
    onLineRootDir = ""
    
    globalSettings = { 
            'global': {
                'server.socket_port' : 12597,
                'server.socket_host': '0.0.0.0',
                'server.socket_file': '',
                'server.socket_queue_size': 100,
                'server.protocol_version': 'HTTP/1.1',
                'server.log_to_screen': True,
                'server.log_file': '',
                'server.reverse_dns': False,
                'server.thread_pool': 200,
                'server.environment': 'local',
                'engine.timeout_monitor.on': False,
                
                
                'tools.sessions.on': True,
                #'tools.sessions.secure': True,
                'tools.sessions.httponly': True,
                
                'tools.staticdir.root': staticRootDir,
  
                
            }
    }
    
    appSettings = {
            '/': {
                'response.headers.server': "AutoDeploy-Api",
            },
            '/static': {
                'tools.gzip.on': True,
                'tools.staticdir.on': True,
                'tools.staticdir.dir': ''
            },
            '/static/css': {
                'tools.gzip.mime_types':['text/css'],
                'tools.staticdir.dir': 'css'
            },
            '/static/js': {
                'tools.gzip.mime_types': ['application/javascript'],
                'tools.staticdir.dir': 'js'
            },
            '/static/img': {
                'tools.staticdir.dir': 'img'
            }
    }
    cherrypy.engine.autoreload.stop()
    cherrypy.engine.autoreload.unsubscribe()
    
    apiObj = api()
    cherrypy.tools.auth = cherrypy.Tool('before_handler', apiObj.checkAuth)
    
    cherrypy.config.update(globalSettings)
    cherrypy.config["tools.encode.on"] = True
    cherrypy.config["tools.encode.encoding"] = "utf-8"
    
    productionSetting = {"production": {'tools.staticdir.root': onLineRootDir}}
    cherrypy.config.update(productionSetting)
    
    cherrypy.tree.mount(apiObj, '/', config = appSettings)
    cherrypy.engine.start()
        
if __name__ == '__main__':
    #utf-8
    util.set_sys_to_utf8()
    start()

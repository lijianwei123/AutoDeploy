@see   https://github.com/lijianwei123/AutoDeploy

python 队列 http://www.dbafree.net/?p=1118




http://bbs.aliyun.com/read/149251.html?spm=0.0.0.0.qghOlQ


http://blog.csdn.net/tianmohust/article/details/7896976

django   http://www.ibm.com/developerworks/cn/linux/l-django/




有些服务器中xinetd 已经启动了rsync daemon

需要关闭

vim /etc/xinetd/rsync 
disable = yes

service xinetd restart




rsync 自带服务端  客户端


服务端配置 示例  新建配置文件  rsyncd.conf

#log日志
log file=/usr/local/rsync/log/rsyncd.log
#pid
pid file=/usr/local/rsync/log/rsyncd.pid
#描述文字
comment=dfws rsync

address=168.192.122.29

#运行时daemon使用的用户  setuid
uid=www
gid=www


port=873

#允许上传
read only=no
#允许下载
write only=no


#验证的用户名
auth users=dfws_rsync
#验证的用户密码文件
secrets file=/usr/local/rsync/etc/rsyncd.pass

hosts allow=168.192.122.0/24
hosts deny=*


list=no

outgoing chmod=Dugo-w, Fugo-wx
#D 代表目录  F 代表文件   ugo  用户  组  其他

[test]
path=/data/test/f3.v.veimg.cn/



密码文件格式
dfws_rsync:123456
权限一定要是  600

启动服务端
rsync --daemon --config=/usr/local/rsync/etc/rsyncd.conf
#开启端口
iptables -I INPUT -m state --state NEW -m tcp -p tcp --dport 873 -j ACCEPT



客户端
这里只是用到拉取文件

/usr/bin/rsync -zrtopg --delete --password-file=/home/www/rsync.pass  dfws_rsync@168.192.122.29::test/a  ./

拉取的速度还是可以的


密码文件格式  妈的这里以为和服务端一样呢，坑
123456 




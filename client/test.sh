#/bin/sh

. /etc/rc.d/init.d/functions

. /etc/sysconfig/network

[ ${NETWORKING} = "no" ] && exit 1
exit 0

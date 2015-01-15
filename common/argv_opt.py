#encoding: utf8
import getopt
import sys

class argv_opt():
    '''命令行选项.
    
    @param shortopts: string 短选项.
    @param longopts: list 长选项 .
    '''
    def __init__(self, shortopts = '', longopts =[]):
        self.shortopts = shortopts
        self.longopts = longopts
        
    
    def analysis(self):
        '''分析选项.
        
        @return: True or False
        '''
        try:
            opts,args = getopt.getopt(sys.argv[1:], self.shortopts, self.longopts)
        except getopt.GetoptError:
            return False
        
        self.opts = opts
        self.args = args
        return True
        
    def getOptValue(self, optName, defValue = None):
        '''获取选项值.
        
        @param optName: 选项名称   不带-、--
        @param defaultValue: 默认值
        @return string or defaultValue
        '''
        optName = str(optName)
        if len(optName) == 1:
            optName = '-' + optName
        else:
            optName = '--' + optName
        
        for opt, optValue in self.opts:
            if opt == optName:
                return optValue
            else:
                continue
        
        return defValue
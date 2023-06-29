#!/usr/bin/python3
#coding:utf8

#设置为自己的redis
REDIS_HOST='127.0.0.1'
REDIS_PORT='6379'
REDIS_PASSWD=''
KEY_HOLD_STOCK='stock:hold'
KEY_NEW_STOCK='stock:newstock'
CHAR_SET='utf-8'
FORMAT_STR="%Y-%m-%d"
DATE_TIME_FORMAT_STR="%Y-%m-%d %H:%M:%S"
HOLD_STOCKS_FILE_NAME='HoldStocks.txt'

# 邮箱配置
HOST="smtp.qq.com"            #使用的邮箱的smtp服务器地址，这里是163的smtp地址，经过测试网易和搜狐的邮箱可用
SENDER="1291322508@qq.com"                           #用户名
PASSWORD="jgwufzjuhyqfhbed"                          #密码:stmp生成 非登录密码
POSTFIX="qq.com"                     #邮箱的后缀，网易就是163.com
RECIPS=["1291322508@qq.com"]   #这里接收人也设置为自己

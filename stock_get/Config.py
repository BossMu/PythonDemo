#!/usr/bin/python3
#coding:utf8

#线程配置
THREAD_NUMS = 3

# 策略
MACD = "macd"
MA20 = "MA20"
STRATEGIES = {
    MACD : True,
    MA20 : False
}

# redis_keys
STRATEFIES_NAME = "strategies"

# tushare
TUSHARE_TOKEN='99d18f17dfe5955f8817df95528bad6f223092b52cb76a4293d4fb6a'

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
EMAIL_HOST="smtp.qq.com"                  #使用的邮箱的smtp服务器地址，这里是163的smtp地址，经过测试网易和搜狐的邮箱可用
EMAIL_SENDER="1291322508@qq.com"          #用户名
EMAIL_PASSWORD="jgwufzjuhyqfhbed"         #密码:stmp生成 非登录密码
EMAIL_POSTFIX="qq.com"                    #邮箱的后缀，网易就是163.com
EMAIL_RECIPS=["1291322508@qq.com"]        #接受者

#策略
#【MACD】
MACD_STRATEGY_NAME = 'MACD'
MACD_DATE_DELTA = 300
MACD_BUY_KEY = 'buy:MACD'
MACD_SELL_KEY = 'sell:MACD'

MACD_FAST_PERIOD = 12 
MACD_SLOW_PERIOD = 26
MACD_SIGNAL_PERIOD = 9


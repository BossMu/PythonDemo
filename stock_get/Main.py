#!/usr/bin/python  
# coding: UTF-8
import time
import threading
import math
import Config
import datetime
import sys

import Utils as ut
import EmailService
from RedisService import redisService as rs
from SchedulerService import schedulerService
from MonitorStrategy import monitorStrategy
from StockService import stockService
from RedisService import RedisService
import tushare as ts  
import numpy as np

from Ma20Strategy import ma20Strategy
from MacdStrategy import macdStrategy

	
def getStrategies():
    return [macdStrategy]
	# return [ma20Strategy,macdStrategy]
	
def func(strategies, stocks):
	#如果是交易时间，则直接返回----------
	if stockService.isTradeTime():
		print('交易时间，不执行非实时策略')
		return None
	# --------------------------------			
	# strategies = getStrategies()
	# stocks = ut.getStocks(start_pos, deal_nums)
	# emailContent=''
	for strategy in strategies :
		for index in range(0,len(stocks)):
			stockNo=str(stocks[index])
			strategy.strategy(stockNo)
		# tmpContent = strategy.getEmailContent()
		# if tmpContent is not None:
		# 	emailContent=emailContent+tmpContent
		# 	#发送结果邮件
		# 	# EmailService.sendTextOrHtml('stock策略结果',emailContent)
		# strategy.clearRedis()	

def monitor():
	needEmail=monitorStrategy.strategy()
	if needEmail:
		emailContent=monitorStrategy.getEmailContent()
		monitorStrategy.clearRedis()
		#发送结果邮件
		EmailService.sendTextOrHtml('stock监控结果',emailContent,['yantaozhou@qq.com'])
	print('监控一次',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))
#非实时
def strategyScheduler(rows):
    # 自动调度执行
	# schedulerService.timming_exe(func,after=3)


	# 创建一个线程列表
	threads = []
	deal_nums = math.ceil(rows / Config.THREAD_NUMS)

	strategies = getStrategies()	# 获取策略
 
	# 代码定位：每个线程处理固定的代码，策略可以变
	for i in range(Config.THREAD_NUMS):
		start_pos = i * deal_nums
  
		ret,stocks,rows = ut.getStocks(start_pos, deal_nums)	# 获取线程执行股票

		t = threading.Thread(target=func,args=(strategies, stocks))
		threads.append(t)
		t.start()

	# 等待所有线程完成
	for t in threads:
		t.join()

	# 所有线程完成后发送邮件
	print("所有线程已选股完成，发送邮件")
	emailContent=''
	for strategy in strategies :
		tmpContent = strategy.getEmailContent()
		if tmpContent is not None:
			emailContent=emailContent+tmpContent
			#发送结果邮件
			# EmailService.sendTextOrHtml('stock策略结果',emailContent)
		strategy.clearRedis()	
	EmailService.sendTextOrHtml('stock策略结果',emailContent)
	
 
 
#实时
def monitorScheduler():
	schedulerService.timming_exe(monitor,after=6,interval=5*60)

def selectStocksMain():        
    # 清理redis
	rs.flushdb()
 
	# 记录股票代码
	rows = ut.saveStocks()
 
	threads=[]
	
	strategyThread=threading.Thread(target=strategyScheduler, args=(rows,))
	# monitorThread=threading.Thread(target=monitorScheduler)
 
	threads.append(strategyThread)
	#threads.append(monitorThread)
 
	for thread in threads :
		thread.setDaemon(True)
		thread.start()
	for thread in threads :
		thread.join()
  
	print("执行结束了。\n")

def downloadHqInfo(rows):
	thread_id = int(threading.current_thread().name)
	rs1=RedisService(1)
	
 	#处理代码
	deal_nums = math.ceil(rows / Config.THREAD_NUMS)
	begin_index = thread_id * deal_nums
	ret,stocks,rows = ut.getStocks(begin_index, deal_nums)
  
	#获取行情
	nowDate=datetime.datetime.now()	
	endDateStr=nowDate.strftime("%Y%m%d")
	startDateStr=(nowDate-datetime.timedelta(days=Config.MACD_DATE_DELTA)).strftime("%Y%m%d")
	try:
		for stock in stocks:
			df = ts.pro_bar(ts_code=stock, start_date=startDateStr,end_date=endDateStr)
			# df = round(df, 3)
			close =df.close.iloc[::-1].values
			close = np.array2string(close, separator=',',floatmode='fixed', precision=3).replace('\n', '').replace(' ', '')
   
			close = str(stock) + " " + str(close)
			# close = '[' + ', '.join(map(lambda x: "{:.4f}".format(x), close)) + ']'
			# close_str = np.array2string(close, floatmode='fixed')
			print("记录行情数据 代码：" + stock)
			# 存到redis
			rs1.sadd(str(stock),str(close))
	except:
		print("函数名：",sys._getframe().f_code.co_name, " 存储行情失败:",sys.exc_info()[0],"\n")
	finally:
		rs1.close()
	
    
if __name__ == '__main__':
	RUN_FLAG_0 = False
	FILE_EXIT_DROP_FLAG = False
	RUN_FLAG_1 = False
	RUN_FLAG_2 = False
	RUN_FLAG_3 = False
    
	ret = False
	while True:
		if(FILE_EXIT_DROP_FLAG):
			choice = "0"
		else:
			choice = input("【选股策略】 请输入功能选项：\n0 - 下载股票代码\n1 - 下载行情数据\n2 - 选股策略\n3 - 代码验证\n" )
		# 下载股票
		if choice == "0" or FILE_EXIT_DROP_FLAG:
			# 记录股票代码
			rows,FILE_EXIT_DROP_FLAG = ut.saveStocks(FILE_EXIT_DROP_FLAG)
			RUN_FLAG_0 = True
		# 下载行情
		elif choice == "1":
			# 
			ret,stocks,rows = ut.getStocks()	# 获取所有代码
			if(ret):
				rs1=RedisService(1)
				rs1.flushdb()
				rs1.close()
				ut.func_threads(downloadHqInfo, args=(rows,))
				
				rows = ut.savePrices()
				print("行情记录完毕，共记录 " + str(rows) + " 个代码行情")
				
			else:
				print("获取股票失败，请下载股票代码")
    
		elif choice == "2":
			# 运行功能2的代码
			pass
		elif choice == "3":
			# 运行功能3的代码
			pass
		else:
			print("无效的选项，请重新输入。")




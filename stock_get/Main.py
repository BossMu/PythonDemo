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

from Ma20Strategy import Ma20Strategy
from MacdStrategy import MacdStrategy

# 全局变量
STRATEGIES = []	# 策略
	
def loadStrategies(): 
	for i, (key, value) in enumerate(Config.STRATEGIES.items()):
		#创建实例
		strategy = None
		if(key == Config.MACD):
			strategy = MacdStrategy()
		elif(key == Config.MA20):
			strategy = Ma20Strategy()
		else:
			print("未定义的策略类型")
		
		# 更新策略信息
		strategy.id = i
		if(value):
			# rs.sadd(Config.STRATEFIES_NAME, key)
			strategy.status = True
   
		if(strategy != None):
			STRATEGIES.append(strategy)
			
	# return rs.smembers(Config.STRATEFIES_NAME)

	
def func(strategies, stocks):
	#如果是交易时间，则直接返回----------
	if stockService.isTradeTime():
		print('交易时间，不执行非实时策略')
		return None
	# --------------------------------			
	# strategies = getStrategies()
	# stocks = ut.getStocksFromDoc(start_pos, deal_nums)
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

	strategies = loadStrategies()	# 获取策略
 
	# 代码定位：每个线程处理固定的代码，策略可以变
	for i in range(Config.THREAD_NUMS):
		start_pos = i * deal_nums
  
		ret,stocks,rows = ut.getStocksFromDoc(start_pos, deal_nums)	# 获取线程执行股票

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
	rs1=RedisService(1)
	
 	#处理代码
	begin_index,deal_nums = ut.getCurrentThreadIndex(rows)
	ret,stocks,rows = ut.getStocksFromDoc(begin_index, deal_nums)
  
	#获取行情
	nowDate=datetime.datetime.now()	
	endDateStr=nowDate.strftime("%Y%m%d")
	startDateStr=(nowDate-datetime.timedelta(days=Config.MACD_DATE_DELTA)).strftime("%Y%m%d")
	for stock in stocks:
		while(True):
			try:
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
				break # 无异常时跳出循环
			except:
				print("函数名：",sys._getframe().f_code.co_name, " 存储行情失败:",sys.exc_info()[0],"\n")
				time.sleep(10)
	# finally:
	rs1.close()
	
def runStrategies(beforeDays = 0):
	rs.flushdb()
    
    # 读取文件中行情到redis
	rows,stocks = ut.loadHqToRedis()
    
    # 每个策略分成多个线程去执行不同股票
	emailContent=''
	for strategy in STRATEGIES:
		if(strategy.status == True):
			ut.func_threads(strategy.strategy, args=(rows,stocks,beforeDays))

			tmpContent = strategy.getEmailContent()
			if tmpContent is not None:
				emailContent=emailContent+"\n"+tmpContent
			
			# 记录策略结果
			ut.saveStrategyResult(strategy)
   
			strategy.clearRedis()
	if(beforeDays == 0):
		EmailService.sendTextOrHtml('stock策略结果',emailContent)
	print("基于当日行情前 " + str(beforeDays) + " 日的策略执行完成\n")

def checkResult(beforeDays):
	rs1=RedisService(1)
    # 读取文件中行情到redis
	rows,stocks = ut.loadHqToRedis()
	
	for strategy in STRATEGIES:
		if(strategy.status == True):
			# 读取策略结果
			buy_result,sell_result = ut.loadStrategyResult(strategy)
			buy_sum_rate,buy_real_sum_rate = checkPrice(buy_result,beforeDays,True)
			sell_sum_rate,sell_real_sum_rate = checkPrice(sell_result,beforeDays,False)

			print("策略名：",strategy.strategyName," 买入准确率：",buy_sum_rate,"买入有效准确率：",buy_real_sum_rate," 卖出准确率：",sell_sum_rate," 卖出有效准确率：",sell_real_sum_rate)
			# strategy.clearRedis()
	rs1.close()
	print("策略结果校验完成\n")

def checkPrice(result,beforeDays,bIsBuy):
	rate = 0
	sum_count = 0
	real_sum_count = 0
	right_count = 0
    
    # redis 获取行情数据
	rs1=RedisService(1)
	for stock in result:
		stock_price = rs1.smembers(stock) #字符串
		# 未找到该股票
		if(len(stock_price) <= 0):
			continue
		price = ut.dealStrtoNum(stock_price[0], beforeDays) # 处理成数组 并减去日期
		sum_count = len(price)
  
		if(price and len(price) >= 2):
			real_sum_count += 1

			if(bIsBuy):
				if(price[-1] >= price[-2]):
					right_count += 1
			else:
				if(price[-1] <= price[-2]):
					right_count += 1
		
	sum_rate = round(right_count / sum_count, 2)
	real_sum_rate = round(right_count / real_sum_count, 2)
 
	rs1.close()
	return sum_rate,real_sum_rate
          
if __name__ == '__main__':
	RUN_FLAG_0 = False
	RUN_FLAG_1 = False
	FILE_EXIT_DROP_FLAG = False
	RUN_FLAG_2 = False
	RUN_FLAG_3 = False
	RUN_FLAG_4 = False
	BEFOREDAYS = 0
    
    # 加载策略到内存
	loadStrategies()
    
	ret = False
	while True:
		if(FILE_EXIT_DROP_FLAG):
			choice = "1"
		else:
			choice = input("\n【选股策略】 请输入功能选项：\n0 - 绑定策略\n1 - 下载股票代码\n2 - 下载行情数据\n3 - 策略选股\n4 - 策略历史选股\n5 - 代码验证\n" )
		# 绑策略
		if(choice == "0"):	
			for strategy in STRATEGIES:
				print("编号：" + str(strategy.id) + " 状态：" + str(strategy.status) + " 策略名称：" + strategy.strategyName)
			s_id = input("\n输入策略编号改变策略状态，回车退出\n" )
			if(s_id != ""):
				for strategy in STRATEGIES:
					if(strategy.id == int(s_id)):
						strategy.status = not strategy.status
					print("编号：" + str(strategy.id) + " 状态：" + str(strategy.status) + " 策略名称：" + strategy.strategyName)
			
		# 下载股票
		elif(choice == "1" or FILE_EXIT_DROP_FLAG):
			# 记录股票代码
			rows,FILE_EXIT_DROP_FLAG = ut.saveStocks(FILE_EXIT_DROP_FLAG)
			RUN_FLAG_1 = True
		# 下载行情
		elif(choice == "2"):
			in_type = input("\n请再次敲击回车确认下载行情\n" )
			if(in_type == ""):
				ret,stocks,rows = ut.getStocksFromDoc()	# 获取所有代码
				if(ret):
					rs1=RedisService(1)
					rs1.flushdb()
					rs1.close()
					ut.func_threads(downloadHqInfo, args=(rows,))
					
					rows = ut.savePrices()
					print("行情记录完毕，共记录 " + str(rows) + " 个代码行情")
					
				else:
					print("获取股票失败，请下载股票代码")
		# 运行策略
		elif(choice == "3"):
			runStrategies()

		elif(choice == "4"):
			BEFOREDAYS = int(input("\n输入想要当日行情数据前几日选股模拟（不建议距离当前日太久，例如上个交易日选股，输入：1）\n" ))
			if(BEFOREDAYS >= 0 ):
				runStrategies(BEFOREDAYS)
			else:
				print("输入错误")
		elif(choice == "5"):
			if(BEFOREDAYS <= 0):
				print("请先进行策略历史选股")
			else:
				print("历史选股日期为当前日期的前 " + str(BEFOREDAYS) + " 日，因此使用当前日期前 " + str(BEFOREDAYS-1) + " 日数据进行核对")
				checkResult(BEFOREDAYS-1)
		else:
			print("无效的选项，请重新输入。")




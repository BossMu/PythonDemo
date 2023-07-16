#!/usr/bin/python  
# coding: UTF-8
import sys   
import tushare as ts  
import time
import datetime
import Signal
import Config
import EmailService
import talib
import Utils as ut
import numpy as np
# import pandas as pd
from RedisService import RedisService
from RedisService import redisService
from StockService import stockService
class MacdStrategy():
	id = -1
	status = False
	strategyName=Config.MACD
	buyKey='buy:' + Config.MACD
	sellKey='sell:' + Config.MACD
	dateDelta=52
	
	def __init__(self):
		pass
	#计算快速平滑移动均线
	# def cal_EMA(self,df,EMA_days,days):
	# 	#当前收盘价
	# 	close=float(df[EMA_days-days])
	# 	#递归结束条件（如果计算天数为1时，则返回df的行数为12+2的收盘价(第一个EMA取前一日收盘价)）
	# 	if 1 >= days :
	# 		return float(df.ix[EMA_days+2,:].close)
	# 	return 2*close/(EMA_days+1) + (EMA_days-1)*self.cal_EMA(df,days-1)/(EMA_days+1)
		
	# def cal_DEA(self,df):
	# 	sum=0
	# 	for num in range(0,9):
	# 		EMA=self.cal_EMA(df,num+1,num+1)
	# 		sum=sum+EMA
	# 	return sum/9

	def cal_ema(self,values, n):
		emas = [sum(values[:n]) / n]
		alpha = 2 /(n+1)
		prev_ema = emas[-1]
		for val in values[n:]:
			cur_ema = alpha * val + (1 - alpha) * prev_ema
			emas.append(cur_ema)
			prev_ema = cur_ema
		return emas

	def cal_macd(self,prices, fast_n, slow_n, signal_n):
		fast_ema = self.cal_ema(prices, fast_n)
		slow_ema = self.cal_ema(prices, slow_n)
		
		macd = []
		for i in range(len(slow_ema)):
			macd.append(fast_ema[i+fast_n-1] - slow_ema[i])
		
		# macd = macd[-signal_n:] 
		signal_line = self.cal_ema(macd, signal_n)
		hist = [macd[i] - signal_line[i] for i in range(len(signal_line))]

		return macd, signal_line, hist
	def calculateEMA(self,period, closeArray, emaArray=[]):
		"""计算指数移动平均"""
		length = len(closeArray)
		nanCounter = np.count_nonzero(np.isnan(closeArray))
		if not emaArray:
			emaArray.extend(np.tile([np.nan],(nanCounter + period - 1)))
			firstema = np.mean(closeArray[nanCounter:nanCounter + period - 1])    
			emaArray.append(firstema)    
			for i in range(nanCounter+period,length):
				ema=(2*closeArray[i]+(period-1)*emaArray[-1])/(period+1)
				emaArray.append(ema)        
		return np.array(emaArray)
		
	def calculateMACD(self,closeArray,shortPeriod = 12 ,longPeriod = 26 ,signalPeriod =9):
		ema12 = self.calculateEMA(shortPeriod ,closeArray,[])
		# print ema12
		ema26 = self.calculateEMA(longPeriod ,closeArray,[])
		# print ema26
		diff = ema12-ema26
		
		dea= self.calculateEMA(signalPeriod ,diff,[])
		macd = 2*(diff-dea)
		return macd,diff,dea 

	def get_macd(symbol,start_time,end_time):
		# 取历史数据
		data = history(symbol = symbol,frequency = '1d',start_time = '1997-01-20',end_time = end_time,fields = 'symbol,bob,close',df = True)
		index = data['bob'].apply(lambda x: x.strftime('%Y-%m-%d')).tolist()
	
		# 编写计算函数
		# 上市首日，DIFF、DEA、MACD = 0
		# 用来装变量的list
		EMA12 = []
		EMA26 = []
		DIFF = []
		DEA = []
		BAR = []
		# 如果是上市首日
		if len(data) == 1:
			# 则DIFF、DEA、MACD均为0
			DIFF = [0]
			DEA = [0]
			BAR = [0]
	
		# 如果不是首日
		else:
			# 第一日的EMA要用收盘价代替
			EMA12.append(data['close'].iloc[0])
			EMA26.append(data['close'].iloc[0])
			DIFF.append(0)
			DEA.append(0)
			BAR.append(0)
	
			# 计算接下来的EMA
			# 搜集收盘价
			close = list(data['close'].iloc[1:])    # 从第二天开始计算，去掉第一天
			for i in close:
				ema12 = EMA12[-1] * (11/13) + i * (2/13)
				ema26 = EMA26[-1] * (25/27) + i * (2/27)
				diff = ema12 - ema26
				dea = DEA[-1] * (8/10) + diff * (2/10)
				bar = 2 * (diff - dea)
	
				# 将计算结果写进list中
				EMA12.append(ema12)
				EMA26.append(ema26)
				DIFF.append(diff)
				DEA.append(dea)
				BAR.append(bar)
	
		# 返回全部的macd
		MACD = pd.DataFrame({'DIFF':DIFF,'DEA':DEA,'BAR':BAR, 'time':index},index = index)
	
	# 按照时间筛选子集
		MACD = MACD[(MACD['time'] >= start_time) & (MACD['time'] <= end_time)]
	
		return MACD
	def macd(self,close):
		macdDIFF, macdDEA, macd = talib.MACDEXT(close, fastperiod=12, fastmatype=1, slowperiod=26,    slowmatype=1, signalperiod=9, signalmatype=1)
		macd = macd * 2
		
		return (macdDIFF, macdDEA, macd)
	def strategy(self,rows,stocks,beforeDays):
		rs1=RedisService(1)
  
		begin_index,deal_nums = ut.getCurrentThreadIndex(rows)
		stocks = ut.getDataByIndex(stocks,begin_index,deal_nums)
  
		for stock in stocks:
			try:
				stock_price = rs1.smembers(stock)
				# 未找到该股票
				if(len(stock_price) <= 0):
					continue
				close = ut.dealStrtoNum(stock_price[0], beforeDays)
				if(close):
					macdDIFF, macdDEA, macd = talib.MACD(np.array(close), fastperiod=Config.MACD_FAST_PERIOD, slowperiod=Config.MACD_SLOW_PERIOD, signalperiod=Config.MACD_SIGNAL_PERIOD)
					macd = macd * 2

					if(macd is not None and len(macd) > 5):
						macdDIFF_front = macdDIFF[-2] 
						macdDIFF = macdDIFF[-1]
						macdDEA_front = macdDEA[-2]
						macdDEA = macdDEA[-1]
						macd_front = macd[-2]
						macd = macd[-1]
						if(macdDIFF_front is None or macdDIFF is None or
         					macdDEA_front is None or macdDEA is None or
              				macd_front is None or macd is None):
							continue
						if(macdDIFF_front <= macdDEA_front and macdDIFF >= macdDEA):
							redisService.sadd(self.buyKey,stock)
						elif(macdDIFF_front >= macdDEA_front and macdDIFF <= macdDEA):
							redisService.sadd(self.sellKey,stock)
       
						print("stock:" + stock + " macdDIFF:" + str(macdDIFF) +" macdDEA:" + str(macdDEA) + " macd:" + str(macd))
						
					
					# print(signal)
					# print(hist)
					# for index in range(len(macd) - 10):
					# 	if(macd[index]):
							
					
					# #最少需要28行数据
					# if df and (len(df.index) >= 28) :
					# front_EMA12=self.cal_EMA(df.ix[1:-1,:],12,12)
					# front_EMA26=self.cal_EMA(df.ix[1:-1,:],26,26)
					#前日差离率
					# front_DIF=EMA12-EMA26
					# EMA12=self.cal_EMA(close,12,12)
					# EMA26=self.cal_EMA(close,26,26)
					# #今日差离率
					# DIF=EMA12-EMA26
					# DEA=self.cal_DEA(close)
					# BAR=2*(DIF-DEA)
					# 	#根据离差率判断是否属于上升趋势
					# 	if front_DIF <= DIF and DIF >= DEA :
					# 		#如果离差率上穿DEA则为金叉，发出买入信号
					# 		#存入买入股票编码
					# 		redisService.sadd(self.buyKey,stockNo)
					# 	#如果离差率下破DEA则为死叉，发出卖出信号
					# 	if front_DIF >= DIF and DIF <= DEA :
					# 		#如果当前股票在持股里面，则发出卖出信号
					# 		holdStocks=redisService.smembers(Config.KEY_HOLD_STOCK)
					# 		for holdNo in holdStocks:
					# 			if holdNo == stockNo :
					# 				redisService.sadd(self.sellKey,stockNo)
					# return None
			except Exception as e:
				print(self.strategyName,"股票代码：" + stock + " 策略出现异常:", str(e),sys.exc_info()[0])
				flag = input("\n是否继续计算后续代码？Y/y - 继续  N/n/else - 退出\n" )
				if(flag != "Y" and flag != "y"):
					break
			# finally:
				#让出线程
				# time.sleep(0.01)
				# return None
		rs1.close()
		return None
		
	# def strategy(self,stockNo):
	# 	if stockNo is not None:
	# 		try:
	# 			# nowDate=datetime.datetime.now()
	# 			# endDateStr=nowDate.strftime(Config.FORMAT_STR)
	# 			# startDateStr=(nowDate-datetime.timedelta(days=Config.MACD_DATE_DELTA)).strftime(Config.FORMAT_STR)
	# 			# df = ts.get_hist_data(stockNo,start=startDateStr,end=endDateStr) 
	# 			nowDate=datetime.datetime.now()	
	# 			endDateStr=nowDate.strftime("%Y%m%d")
	# 			startDateStr=(nowDate-datetime.timedelta(days=Config.MACD_DATE_DELTA)).strftime("%Y%m%d")
	# 			df = ts.pro_bar(ts_code=stockNo, start_date=startDateStr,end_date=endDateStr)
	# 			#最少需要28行数据
	# 			if df and (len(df.index) >= 28) :
	# 				front_EMA12=cal_EMA(df.ix[1:-1,:],12,12)
	# 				front_EMA26=cal_EMA(df.ix[1:-1,:],26,26)
	# 				#前日差离率
	# 				front_DIF=EMA12-EMA26
	# 				EMA12=cal_EMA(df,12,12)
	# 				EMA26=cal_EMA(df,26,26)
	# 				#今日差离率
	# 				DIF=EMA12-EMA26
	# 				DEA=cal_DEA(df)
	# 				BAR=2*(DIF-DEA)
	# 				#根据离差率判断是否属于上升趋势
	# 				if front_DIF <= DIF and DIF >= DEA :
	# 					#如果离差率上穿DEA则为金叉，发出买入信号
	# 					#存入买入股票编码
	# 					redisService.sadd(self.buyKey,stockNo)
	# 				#如果离差率下破DEA则为死叉，发出卖出信号
	# 				if front_DIF >= DIF and DIF <= DEA :
	# 					#如果当前股票在持股里面，则发出卖出信号
	# 					holdStocks=redisService.smembers(Config.KEY_HOLD_STOCK)
	# 					for holdNo in holdStocks:
	# 						if holdNo == stockNo :
	# 							redisService.sadd(self.sellKey,stockNo)
	# 			return None
	# 		except:
	# 			print(self.strategyName,"策略出现异常:", sys.exc_info()[0])
	# 		finally:
	# 			#让出线程
	# 			time.sleep(1)
	# 			return None
	# 	return None
			
	def getEmailContent(self):
		content=None
		buyList=redisService.smembers(self.buyKey)
		sellList=redisService.smembers(self.sellKey)
		if len(buyList) > 0 or len(sellList) > 0 :
			content='策略名称：' + self.strategyName
			content=content+'<br/>'
			content=content+'买入('+str(len(buyList))+'支)：<br/>'
			content = content + ','.join(buyList)
			content=content+'\r\n<br/>'
			content=content+'卖出('+str(len(sellList))+'支)：<br/>'
			content = content + ','.join(sellList)
		return content
	
	
	def clearRedis(self):
		redisService.delete(self.buyKey)
		redisService.delete(self.sellKey)

macdStrategy=MacdStrategy()

if __name__=='__main__':
	print('请确保当日收盘后再运行，否则需要调整历史行情数据的获取截止日期为前一天')
	print("MACD策略开始时间：",datetime.datetime.now().strftime(Config.DATE_TIME_FORMAT_STR))
	# macdStrategy.clearRedis()
	stockNos=ut.getStocksFromDoc()
	for index in range(0,len(stockNos)):
		stockNo=stockNos[index]
		macdStrategy.strategy(stockNo)
	emailContent=macdStrategy.getEmailContent()
	if emailContent :
		#发送结果邮件
		EmailService.sendTextOrHtml('MACD策略结果',emailContent,['yantaozhou@qq.com'])
	else:
		print('MACD策略结束，无需发送邮件')
	#清理redis缓存
	macdStrategy.clearRedis()
	print("MACD策略结束时间：",datetime.datetime.now().strftime(Config.DATE_TIME_FORMAT_STR))
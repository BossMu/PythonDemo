#!/usr/bin/python  
# coding: UTF-8
import sys   
import tushare as ts  
import time
import datetime
import Signal
import Config
import EmailService
from RedisService import redisService
from StockService import stockService
class Ma20Strategy():
	id = -1
	status = False
	strategyName='ma_strategy'
	buyKey='buy:ma_strategy'
	sellKey='sell:ma_strategy'
	dateDiff=100
	dateDelta=4			# 拉抬前n日
	def __init__(self):
		pass
	def strategy(self,stockNo):
		if stockNo is not None:
			try:
				nowDate=datetime.datetime.now()
				# endDateStr=nowDate.strftime(Config.FORMAT_STR)	
				endDateStr=nowDate.strftime("%Y%m%d")
				startDateStr=(nowDate-datetime.timedelta(days=self.dateDiff)).strftime("%Y%m%d")
				df = ts.pro_bar(ts_code=stockNo, start_date=startDateStr,end_date=endDateStr, ma=[5, 20, 50])
				df = round(df, 3)
    			# if (df is not None) and (len(df.index) >= self.dateDelta):
				if (df is not None):
					ma = df[u'ma5']
					close = df[u'close']
					underline=True
     
					# 当日冲破均线
					for index in range(1,self.dateDelta-1):
						if close[index] > ma[index]:
							underline=False
							break
					if underline and close[0] > ma[0]:
						#存入买入股票编码
						redisService.sadd(self.buyKey,stockNo)
						return Signal.Signal(stockNo=stockNo,buy=True,dateStr=endDateStr)
					
     				# 当日跌破均线
					upline=True
					for index in range(1,self.dateDelta-1):
						if close[index] < ma[index]:
							upline=False
							break
					if upline and close[0] < ma[0]:
						#存入买入股票编码
						redisService.sadd(self.sellKey,stockNo)
						return Signal.Signal(stockNo=stockNo,sell=True,dateStr=endDateStr)				
				return None
			except:
				print(self.strategyName,"策略出现异常:", sys.exc_info()[0])
			finally:
				#让出线程
				time.sleep(1)
				return None
		return None
			
	def getEmailContent(self):
		content=None
		buyList=redisService.smembers(self.buyKey)
		sellList=redisService.smembers(self.sellKey)
		if len(buyList) > 0 or len(sellList) > 0 :
			content='策略名称：' + self.strategyName
			content=content+'<br/>'
			content=content+'买入('+str(len(buyList))+'支)：<br/>'
			content = content + ','.join(buyList)
			content=content+'\r\n'
			content=content+'卖出('+str(len(sellList))+'支)：<br/>'
			content = content + ','.join(sellList)
		return content
		
	def clearRedis(self):
		redisService.delete(self.buyKey)
		redisService.delete(self.sellKey)

ma20Strategy=Ma20Strategy()

if __name__=='__main__':
	print("Ma20策略开始时间：",datetime.datetime.now().strftime(Config.DATE_TIME_FORMAT_STR))
	ma20Strategy.clearRedis()
	stockNos=stockService.getStockCodes()
	for index in range(0,len(stockNos)):
		stockNo=stockNos[index]
		ma20Strategy.strategy(stockNo)
	emailContent=ma20Strategy.getEmailContent()
	if emailContent :
		#发送结果邮件
		EmailService.sendTextOrHtml('Ma20策略结果',emailContent,['yantaozhou@qq.com'])
	else:
		print('Ma20策略结束，无需发送邮件')
	#清理redis缓存
	ma20Strategy.clearRedis()
	print("Ma20策略结束时间：",datetime.datetime.now().strftime(Config.DATE_TIME_FORMAT_STR))
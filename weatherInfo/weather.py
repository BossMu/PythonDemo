# encoding:utf-8
import requests, json
from bs4 import BeautifulSoup
#api地址

def getWeather(city):
  f = open('city.json', 'rb')
  cities = json.load(f)
  citycode = cities.get(city)
  url = 'http://www.weather.com.cn/weather/'+ citycode +'.shtml'
  response = requests.get(url)
  response.encoding ='utf-8'

  # d = response.json()
  # f = open('./response.json','w')
  # f.write(response.text)
  soup=BeautifulSoup(response.text,"lxml")
  # weather_lis = soup.select('.c7d > ul li p.wea')

  # 获取天气信息和温度信息
  weather_lis = soup.select('.c7d > ul li')
  weather_info = []
  for li in weather_lis:
      date = li.select('h1')[0].text
      weather = li.select('p.wea')[0].text
      high_temp = li.select('p.tem span')[0].text
      low_temp = li.select('p.tem i')[0].text
      weather_info.append((date, weather, high_temp, low_temp))

  # 7天的天气
  return weather_info




# print(soup.select('.c7d > ul li p.wea')[0].string.find('雨') != -1)
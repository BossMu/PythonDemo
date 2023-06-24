import pyautogui,pyperclip
from weather import *
import time

# document url https://pyautogui.readthedocs.io/en/latest/quickstart.html
# TK_SILENCE_DEPRECATION=1
# print(pyautogui.position())# current mouse x and y
# print(pyautogui.size())
# print(pyautogui.size())# current screen resolution width and height
# print(pyautogui.onScreen(10000, 20)) # True if x & y are within the screen.
# pyautogui.FAILSAFE = True
# pyautogui.PAUSE = 0.01
# pyautogui.moveTo(10, 10,0)

# pyautogui.moveRel(20,200,0)
# pyautogui.dragRel(20, 20,1,button='left')  # drag mouse to XY
# pyautogui.scroll(10)
# pyautogui.alert(text='123', title='123', button='OK')
# button7location = pyautogui.locateOnScreen('123.png', grayscale=False,confidence=0.7)
def paste():
  pyautogui.hotkey('command','v')

def postMsg(city):
  wea7info = getWeather(city)
  # print(wea7info)

  msg = city + "\n"
  for info in wea7info:
    msg = msg + " " + info[0] + " 天气：" + info[1] + " 温度：" + info[3] + "-" + info[2] + "℃\n"

  # print(msg)

  # 打开微信 ctrl+alt+w
  openOrCloseWx()

  # 最大化  win+↑
  pyautogui.keyDown('win')
  pyautogui.press('up')
  pyautogui.keyUp('win')

  # 移动鼠标
  wide_ratio = 0.0938
  high_ratio = 0.1250
  screenSize = pyautogui.size()
  pyautogui.moveTo(screenSize[0] * wide_ratio, screenSize[1] * high_ratio)
  # 点击
  pyautogui.click()

  #发送文本
  pyperclip.copy(msg)
  pyautogui.hotkey('ctrl', 'v') 
  pyautogui.press('enter')

  #关闭界面
  openOrCloseWx()
  
  time.sleep(PAUSE_TIME)
  
  
def openOrCloseWx():
  # 打开微信 ctrl+alt+w
  pyautogui.keyDown('ctrl')
  pyautogui.keyDown('alt')
  pyautogui.press('w')
  pyautogui.keyUp('ctrl')
  pyautogui.keyUp('alt')


if __name__ == '__main__':
  # print(pyautogui.position())# current mouse x and y
  # print(pyautogui.size())
  PAUSE_TIME = 0.1
  
  pyautogui.FAILSAFE = True
  pyautogui.PAUSE = PAUSE_TIME

  postMsg('苏州')
  postMsg('深圳')






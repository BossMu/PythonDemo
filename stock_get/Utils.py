import os
import tushare as ts   
import Config
import datetime
import itertools
import sys
import threading
import time
from RedisService import RedisService

# 业务 ---------------------------------------------------------------------------
def savePrices():
    rs1=RedisService(1)
    date = datetime.datetime.now().strftime("%Y%m%d")
    folder = "data"
    filename = date + "-prices.txt"
    rows = 0
    
    ret, rows_tmp = check_file_path(folder, filename, True, True)   #无论在不在，创建清空等待行情更新

    # 循环写入到data
    full_filename = folder + "/" + filename
    full_filename = dealWinOrLinux(full_filename)
    with open(full_filename, 'w') as f:
        # 遍历redis所有key，记到文件中
        keys = rs1.keys('*')
        # 遍历所有的键并获取对应的值
        for key in keys:
            value = rs1.smembers(key)
            # print(f"{key}: {value}")
            f.write(value[0] + '\n')
        rows = len(keys)
    
    rs1.flushdb() 
    rs1.close()
    
    return rows

def saveStocks(file_exit_drop_flag):
    try:
        date = datetime.datetime.now().strftime("%Y%m%d")
        folder = "data"
        # filename = date + "-stocks.txt"
        filename = "stocks.txt"
        
        ret, rows = check_file_path(folder, filename, True, file_exit_drop_flag)
        if(ret == False):
            # 获取股票代码
            ts.set_token(Config.TUSHARE_TOKEN)
            pro = ts.pro_api()
            data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
            
            # 循环写入到data
            full_filename = folder + "/" + filename
            full_filename = dealWinOrLinux(full_filename)
            with open(full_filename, 'w') as f:
                for element in data["ts_code"]:
                    f.write(element + '\n')
            rows = len(data["ts_code"])
            file_exit_drop_flag = False
        else:
            print("股票代码已经下载,是否重新下载")

            choice = input("【选股策略】 请输入功能选项：\nY/y - 重新下载股票代码\nN/n/else - 不下载\n" )
            if(choice == "Y" or choice == "y"):
                file_exit_drop_flag = True
                
            else:
                file_exit_drop_flag = False
                
    except:
        print("函数名：",sys._getframe().f_code.co_name, " 存储股票失败:",sys.exc_info()[0],"\n")
        rows = 0
        file_exit_drop_flag = False

    return rows,file_exit_drop_flag
 
# 无参数时默认为0，表示查询所有代码       
def getStocks(start_pos = 0, deal_nums = 0):
    ret = False
    date = datetime.datetime.now().strftime("%Y%m%d")
    folder = "data"
    filename = date + "-stocks.txt"
    full_filename = folder + "/" + filename
    # 读取文件内容到data变量
    data = []
    rows = 0  # 添加行数计数器
    try:
        with open(full_filename, 'r') as f:
            if deal_nums == 0:  # 添加此条件判断
                lines = f.readlines()  # 读取所有行
            else:
                lines = itertools.islice(f, start_pos, start_pos + deal_nums)
            for line in lines:
                data.append(line.strip())
                rows += 1  # 每读取一行，计数器加1
            ret = True
    except:
        print("函数名：",sys._getframe().f_code.co_name, " 获取股票代码时发生错误:",sys.exc_info()[0],"\n")
        
    return ret,data,rows
    # return ["600000.SH"]




    
# --------------------------------------------------------------------------------------
# pub

# 多线程封装函数
# func的入参必须和调用func一样
# 赋值了线程名，使用threading.current_thread().name获取，类型str
def func_threads(func, args=()):
    threads = []
    
    for i in range(Config.THREAD_NUMS):
        t = threading.Thread(target=func, name=str(i), args=args)
        threads.append(t)
        t.start()
        time.sleep(0.1)

    for t in threads:
        t.join()
    print("线程全部运行结束")


# 查找文件，file_null_creat_flag:找不到是否默认创建;file_exit_drop_flag:找得到默认不清空
# folder "data/data"或""data\\data"
def check_file_path(folder, filename, file_null_creat_flag = True , file_exit_drop_flag = False):
    ret_flag = False
    # win
    folder = dealWinOrLinux(folder)
    
    folder = os.path.abspath(folder)
    file_path = os.path.join(folder, filename)
    rows = 0
    
    if not os.path.exists(folder):
        os.makedirs(folder)

    if not os.path.exists(file_path):
        if(file_null_creat_flag == True):
            open(file_path, 'w').close()
    else:
        with open(file_path) as f:
            rows = sum(1 for line in f)  
        if rows > 0:
            if(file_exit_drop_flag):
                open(file_path, 'w').close()
            ret_flag = True
        else:
            pass
        # print("股票数量：%d" % rows)
        # if os.path.getsize(file_path) == 0:
        #     print("文件为空")
        # else:
        #     print("文件存在且不为空")
        #     # 清空
        #     # open(file_path, 'w').close()
        #     ret_flag = True
            
    return ret_flag,rows
    
def dealWinOrLinux(folder):
    if os.name == 'nt':
        folder = folder.replace('/', '\\')
    return folder
import os

def find_file_stocks(filename):
    if not os.path.exists(filename):
        with open(filename, 'w') as file:
            return False
            # file.write('')  # 可以在创建文件时写入一些内容
        # print(f"文件 '{filename}' 不存在，已成功创建。")
    else:
        # print(f"文件 '{filename}' 已存在。")
        with open(filename, 'r') as file:
            content = file.read()
            if content.strip() == "":
                return False
    return True
    
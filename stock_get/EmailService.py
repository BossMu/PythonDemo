#coding:utf-8

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email
from smtplib import SMTP
import smtplib
import os.path
import mimetypes
import time
import Config

#设置为自己的邮箱服务器
EMAIL_HOST=Config.EMAIL_HOST
EMAIL_SENDER=Config.EMAIL_SENDER
EMAIL_PASSWORD=Config.EMAIL_PASSWORD
EMAIL_POSTFIX=Config.EMAIL_POSTFIX
EMAIL_RECIPS=Config.EMAIL_RECIPS


# 一个包含文本和html的多部分邮件。多部分消息通常包含纯文本和html格式，客户端自行选择显示哪个。（web客户端显示html，命令行客户端显示纯文本）
def make_mpa_msg(content):
    myemail = MIMEMultipart('alternative')
    text = MIMEText(content+'\r\n', 'plain',_charset="utf-8")  #纯文本的邮件消息正文
    myemail.attach(text)  #消息正文绑定到邮件对象
    html = MIMEText(   #html邮件消息正文
        '<html><body><h4>'+content+'</h4>'
        '</body></html>', 'html')
    myemail.attach(html)  #消息正文绑定到邮件对象
    return myemail

# 创建一个文本和图片的邮件
def make_img_msg(imgfile):
    f = open(imgfile, 'rb')  #创建文件指针,这里要以rb的模式取读
    data = f.read()  #读取图片成字节流
    f.close()  #文件关闭
    ctype, encoding = mimetypes.guess_type(imgfile)   #ctype为根据文件获取的数据传输类型image/jpeg，encoding应该为None
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)   #maintype为文件所属类image，subtype为具体文件类型jpeg
    myemail = MIMEImage(data, name=subtype)  #生成图片邮件,name=文件类型jpeg
    basename = os.path.basename(imgfile)  #basename为文件名，不包含路径
    myemail.add_header('Content-Disposition','attachment; filename="%s"' % basename)  #添加邮件头
    return myemail

# 创建一个文本和文件的邮件
def make_file_msg(file_name):
    # 构造MIMEBase对象做为文件附件内容并附加到根容器
    ctype, encoding = mimetypes.guess_type(file_name)  # ctype为根据文件获取的数据传输类型image/jpeg，encoding应该为None
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)  # maintype为文件所属类image，subtype为具体文件类型jpeg
    print(maintype,subtype)
    ## 读入文件内容并格式化
    f = open(file_name, 'rb')  # 创建文件指针,这里要以rb的模式取读
    myemail = MIMEBase(maintype, subtype)
    myemail.set_payload(f.read())  #设置负载数据
    f.close()
    email.encoders.encode_base64(myemail)  #将邮件编码
    #设置附件头
    basename = os.path.basename(file_name) #basename为文件名，不包含路径
    myemail.add_header('Content-Disposition','attachment; filename="%s"' % basename)  #添加邮件头
    return myemail

def sendMsg(fr, to, message):
    sendSvr = smtplib.SMTP_SSL(EMAIL_HOST,465)
    #sendSvr.connect(EMAIL_HOST)  # 连接服务器
    sendSvr.login(EMAIL_SENDER, EMAIL_PASSWORD)  # 登录操作
    errs = sendSvr.sendmail(fr, to, message)  #参数：发件人，收件人，消息正文
    sendSvr.quit()

def sendTextOrHtml(subject,content):
	msg = make_mpa_msg(content)
	msg['From'] = EMAIL_SENDER
	msg['To'] = ', '.join(EMAIL_RECIPS)
	msg['Subject'] = subject
	sendMsg(EMAIL_SENDER,EMAIL_RECIPS, msg.as_string())

if __name__ == '__main__':
	EMAIL_RECIPS=['test@qq.com','test@qq.com']
	sendTextOrHtml('人生苦短，我用python!','Life is short,you need Python!',EMAIL_RECIPS)
	#time.sleep(1);
	#msg = make_mpa_msg('Life is short,you need Python!')
	#msg['From'] = EMAIL_SENDER
	#msg['To'] = ', '.join(EMAIL_RECIPS)
	#msg['Subject'] = '人生苦短，我用python!'
	#sendMsg(EMAIL_SENDER, EMAIL_RECIPS, msg.as_string())
    #print('发送图片消息体')
    #msg = make_img_msg(r'D:/test.jpg')
    #msg['From'] = EMAIL_SENDER
    #msg['To'] = ', '.join(EMAIL_RECIPS)
    #msg['Subject'] = '图片消息邮件'
    #sendMsg(EMAIL_SENDER, EMAIL_RECIPS, msg.as_string())
    #
    #print('发送文件消息体')
    #msg = make_file_msg(r'D:/test.mp4')
    #msg['From'] = EMAIL_SENDER
    #msg['To'] = ', '.join(EMAIL_RECIPS)
    #msg['Subject'] = '文件消息邮件'
    #sendMsg(EMAIL_SENDER, EMAIL_RECIPS, msg.as_string())

import os
import re
import sys
import time
import poplib
import pickle
import configparser
from email.parser import Parser
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class Spider:
    def __init__(self, config_path, cookie_dir, generateAll):
        chrome_options = Options()
        s = Service(executable_path="../chrome/chromedriver_119.exe")
        self.web_driver = webdriver.Chrome(options= chrome_options, service=s)
        cf = configparser.ConfigParser()
        cf.read(config_path)
        self.password = cf.get('Amazon', 'password')
        self.username = cf.get('Amazon', 'username')
        self.url = cf.get('Amazon', 'console')
        self.popserver = cf.get('Email', 'popserver')
        self.emailpass = cf.get('Email', 'token')
        self.home_page = 'https://www.amazon.com/'
        if generateAll == True or not os.path.exists(cookie_dir):
            self.__generate_cookie(cookie_dir)
        print("open amazon")

    def __dump_cookie(self, cookie_dir, webdriver):
        new_cookies = webdriver.get_cookies()
        cookie1 = {}
        cookie2 = {}
        cookie3 = {}
        cookie4 = {}
        #cookies = {}
        for cookie_tmp in new_cookies:
            if cookie_tmp['name'] == 'ubid-main':
                cookie1['name'] = cookie_tmp['name']
                cookie1['value'] = cookie_tmp['value']
            elif cookie_tmp['name'] == 'x-main':
                cookie2['name'] = cookie_tmp['name']
                cookie2['value'] = cookie_tmp['value']
            elif cookie_tmp['name'] == 'at-main':
                cookie3['name'] = cookie_tmp['name']
                cookie3['value'] = cookie_tmp['value']
            elif cookie_tmp['name'] == 'sess-at-main':
                cookie4['name'] = cookie_tmp['name']
                cookie4['value'] = cookie_tmp['value']
            #cookies[cookie_tmp['name']] = cookie_tmp['value']
        new_cookies = [cookie1, cookie2, cookie3, cookie4]
        cookie_file = open(cookie_dir, 'wb')
        pickle.dump(new_cookies, cookie_file)
        #pickle.dump(cookies, cookie_file)
        cookie_file.close()


    def __generate_cookie(self, cookie_dir):  # 生成cookie_console7.pkl文件
        if os.path.exists(cookie_dir):
            return
        self.web_driver.get(self.home_page)
        time.sleep(5)
        try:
            log_in_button = self.web_driver.find_element(By.XPATH, '//*[@id="nav-link-accountList"]')
            self.web_driver.execute_script("arguments[0].click()", log_in_button)
        except:
            print(self.web_driver.page_source)
            print('enter www.amazon.com error!')
            sys.exit()
        # self.auto_login()
        time.sleep(2)
        self.web_driver.find_element(By.ID, 'ap_email').send_keys(self.username)
        self.web_driver.find_element(By.ID, 'ap_email').send_keys(Keys.ENTER)
        time.sleep(10)
        self.web_driver.find_element(By.ID, 'ap_password').send_keys(self.password)
        self.web_driver.find_element(By.ID, 'ap_password').send_keys(Keys.ENTER)
        time.sleep(5)
        if self.web_driver.current_url != "https://www.amazon.com/?ref_=nav_ya_signin":
            time.sleep(20)
            if self.web_driver.current_url.startswith("https://www.amazon.com/ap/cvf/transactionapproval"):
                code = self.__get_link()
                print(code)
                if code != '':
                    time.sleep(2)
                    self.web_driver.find_element(By.ID, 'input-box-otp').send_keys(code)
                    self.web_driver.find_element(By.ID, 'input-box-otp').send_keys(Keys.ENTER)
        self.__dump_cookie(cookie_dir, self.web_driver)

    def __get_link(self):
        pop3Server = poplib.POP3(self.popserver)
        pop3Server.user(self.username)
        pop3Server.pass_(self.emailpass)

        messageCount, mailboxSize = pop3Server.stat()
        """ 获取任意一封邮件的邮件对象【第一封邮件的编号为1，而不是0】"""
        msgIndex = messageCount
        # 获取第msgIndex封邮件的信息
        response, msgLines, octets = pop3Server.retr(msgIndex)
        # msgLines中为该邮件的每行数据,先将内容连接成字符串，再转化为email.message.Message对象
        msgLinesToStr = b"\r\n".join(msgLines).decode("utf8", "ignore")
        messageObject = Parser().parsestr(msgLinesToStr)
        msgDate = messageObject["date"]
        senderContent = messageObject["From"]

        if messageObject.is_multipart():  # 判断邮件是否由多个部分构成
            messageParts = messageObject.get_payload()  # 获取邮件附载部分
            for messagePart in messageParts:
                bodyContent = self.__decodeBody(messagePart)
                if bodyContent:
                    res1 = re.findall(r'''<td colspan="2" align="left" style="background-color: \#D3D3D3; text-align: left; font-size:20px; font-weight: bold; font-family: 'Amazon Ember', Arial, sans-serif; padding-top: 15px; padding-bottom: 10px; padding-left: 10px; padding-right: 1px; border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;">(.*?)</td>''', str(bodyContent), re.S)
                    if len(res1) > 0:
                        code = re.findall(r'''<p>(.*?)</p>''', res1[0], re.S)
                    if len(code) > 0:
                        pop3Server.quit()
                        return code[0].strip()
        else:
            bodyContent = self.__decodeBody(messageObject)
            if bodyContent:
                res1 = re.findall(r'''<td colspan="2" align="left" style="background-color: \#D3D3D3; text-align: left; font-size:20px; font-weight: bold; font-family: 'Amazon Ember', Arial, sans-serif; padding-top: 15px; padding-bottom: 10px; padding-left: 10px; padding-right: 1px; border-top-left-radius: 10px; border-top-right-radius: 10px; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;">(.*?)</td>''', str(bodyContent), re.S)
                if len(res1) > 0:
                    code = re.findall(r'''<p>(.*?)</p>''', res1[0], re.S)
                if len(code) > 0:
                    pop3Server.quit()
                    return code[0].strip()
        pop3Server.quit()
        return ''
    
    def __decodeBody(self, msgPart):
        contentType = msgPart.get_content_type()  # 判断邮件内容的类型,text/html
        textContent = ""
        if contentType == 'text/plain' or contentType == 'text/html':
            content = msgPart.get_payload(decode=True)
            charset = msgPart.get_charset()
            if charset is None:
                contentType = msgPart.get('Content-Type', '').lower()
                position = contentType.find('charset=')
                if position >= 0:
                    charset = contentType[position + 8:].strip()
            if charset:
                textContent = content.decode(charset)
        return textContent
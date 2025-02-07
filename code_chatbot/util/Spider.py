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
import util.deal_with_UI as UI
import util.Constant as Constant
from distutils.version import StrictVersion


class Spider:
    def __init__(self, config_path):
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        if StrictVersion(selenium.__version__) < StrictVersion("4.0.0"):
            self.web_driver = webdriver.Chrome(options= chrome_options)#, executable_path=Constant.CHROME_PATH)
        else:
            s = Service()#executable_path=Constant.CHROME_PATH)
            self.web_driver = webdriver.Chrome(options= chrome_options, service=s)
        cf = configparser.ConfigParser()
        cf.read(config_path)
        secs = cf.sections()
        self.password = cf.get('Amazon', 'password')
        self.username = cf.get('Amazon', 'username')
        self.url = cf.get('Amazon', 'console')
        self.emailpass = cf.get('Email', 'token')
        self.popserver = cf.get('Email', 'popserver')
        self.home_page = 'https://www.amazon.com/'
        self.log_out_page = 'https://developer.amazon.com/alexa/console/logout?language=en_US/'
        if not os.path.exists(Constant.COOKIE_DIR):
            self.__generate_cookie()
        cookie_file = open(Constant.COOKIE_DIR, 'rb')
        self.cookie_list = pickle.load(cookie_file)
        cookie_file.close()
        print("open amazon")

    def deal_with_cookie_wrong(self):
        self.web_driver.get(self.log_out_page)
        time.sleep(1)
        self.web_driver.get('https://developer.amazon.com/alexa/console/ask')
        time.sleep(2)
        no_pass = False
        no_email = False
        time_tmp = time.time()
        while time.time() - time_tmp < 1*60 and self.web_driver.current_url != self.url and (no_pass == False or no_email == False):
            try:
                email = self.web_driver.find_element(By.ID, 'ap_email')
                email.send_keys(self.username)
                time.sleep(1)
                no_email = False
            except:
                no_email = True
            try:
                passw = self.web_driver.find_element(By.ID, 'ap_password')
                passw.send_keys(self.password)
                passw.send_keys(Keys.ENTER)
                time.sleep(15)
                no_pass = False
            except:
                no_pass = True
        self.web_driver.get(self.url)
        time.sleep(15)
        if not self.web_driver.current_url.startswith(self.url):
            print(self.web_driver.current_url)
            print("open console error!")
            sys.exit()
        deviceLevel_element = self.web_driver.find_element(By.ID, 'deviceLevel-label')
        self.web_driver.execute_script("arguments[0].click()", deviceLevel_element)
        time.sleep(1)
        
    def __refresh(self):
        self.web_driver.get(self.home_page)
        self.judge_curUrl()
        time.sleep(15)
        # 打开 log 窗口
        self.web_driver.find_element(By.ID, 'deviceLevel-label').click()
        deviceLevel_element = self.web_driver.find_element(By.ID, 'deviceLevel-label')
        self.web_driver.execute_script("arguments[0].click();", deviceLevel_element)
        time.sleep(1)

    def load_cookie(self):
        for cookie in self.cookie_list:
            self.web_driver.add_cookie(cookie)
        time.sleep(2)
        self.web_driver.refresh()
        time.sleep(3)

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

    def __auto_login_bak(self):
        try:
            # self.web_driver.get(self.home_page)
            log_in_button = self.web_driver.find_element(By.XPATH, '//*[@id="nav-link-accountList"]')
            self.web_driver.execute_script("arguments[0].click()", log_in_button)
            self.load_cookie()
            self.web_driver.find_element(By.ID, 'ap_password').send_keys(self.password)
            self.web_driver.find_element(By.ID, 'ap_password').send_keys(Keys.ENTER)
            # self.web_driver.find_element_by_class_name('a-button-input').click()
        except selenium.common.exceptions.NoSuchElementException:
            return

    def __auto_login(self):
        try:
            self.web_driver.find_element(By.ID, 'ap_password').send_keys(self.password)
            self.web_driver.find_element(By.ID, 'ap_password').send_keys(Keys.ENTER)
        except selenium.common.exceptions.NoSuchElementException:
            return

    def __auto_login_2(self):
        try:
            self.web_driver.find_element(By.ID, 'ap_email').send_keys(self.username)
            self.web_driver.find_element(By.ID, 'ap_email').send_keys(Keys.ENTER)
            time.sleep(5)
            self.web_driver.find_element(By.ID, 'ap_password').send_keys(self.password)
            # 记住登录
            rem = self.web_driver.find_element(By.XPATH,
                '//*[@id="authportal-main-section"]/div[2]/div/div/div/form/div/div[2]/div/div/label/div/label/input')
            self.web_driver.execute_script("arguments[0].click()", rem)
            self.web_driver.find_element(By.ID, 'ap_password').send_keys(Keys.ENTER)
            # self.web_driver
            # self.web_driver.find_element_by_class_name('a-button-input').click()
        except selenium.common.exceptions.NoSuchElementException:
            return

    def judge_curUrl(self):
        if self.web_driver.current_url != self.home_page:
            self.web_driver.get(self.home_page)
        # 加载 cookie 并刷新页面
        time_tmp = time.time()
        while time.time() - time_tmp < 1*60:
            try:
                self.load_cookie()
                break
            except selenium.common.exceptions.InvalidArgumentException:
                self.web_driver.get(self.home_page)
                self.web_driver.refresh()
                time.sleep(3)
        time.sleep(3)
        # 跳转console页面
        #print(self.url)
        try:
            self.web_driver.get(self.url)
            time.sleep(15)
        except selenium.common.exceptions.WebDriverException:
            print("wait for opening the simulator")
            time.sleep(60)
        try:
            if self.web_driver.current_url == self.url:
                return
        except selenium.common.exceptions.WebDriverException:
            print("wait for getting the current url")
            time.sleep(60)
        time_tmp = time.time()
        while time.time() - time_tmp < 1*60 and self.web_driver.current_url != self.url:
            try:
                email = self.web_driver.find_element(By.ID, 'ap_email')
                email.send_keys(self.username)
                time.sleep(1)
            except:
                pass
            try:
                passw = self.web_driver.find_element(By.ID, 'ap_password')
                passw.send_keys(self.password)
                passw.send_keys(Keys.ENTER)
                time.sleep(1)
            except:
                pass
            if self.web_driver.current_url.startswith("https://www.amazon.com/ap/cvf/transactionapproval"):
                code = self.__get_link()
                print(code)
                if code != '':
                    time.sleep(2)
                    self.web_driver.find_element(By.ID, 'input-box-otp').send_keys(code)
                    self.web_driver.find_element(By.ID, 'input-box-otp').send_keys(Keys.ENTER)
                else:
                    code = input("code:")
                    self.web_driver.find_element(By.ID, 'input-box-otp').send_keys(code)
                    self.web_driver.find_element(By.ID, 'input-box-otp').send_keys(Keys.ENTER)
                    time.sleep(2)
                self.web_driver.get(self.url)
                time.sleep(2)
        return

    def open_log_page(self):
        self.judge_curUrl()
        # 打开 log 窗口
        # spider.web_driver.find_element_by_id('deviceLevel-label').click()
        if not self.web_driver.current_url.startswith(self.url):
            print(self.web_driver.current_url)
            print("open console error!")
            sys.exit()
        time.sleep(5)
        deviceLevel_element = self.web_driver.find_element(By.ID, 'deviceLevel-label')
        self.web_driver.execute_script("arguments[0].click()", deviceLevel_element)
        time.sleep(1)

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

    def __get_link(self):
        try:
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
        except:
            return ''

    def __approve(self, link):
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        driver = webdriver.Chrome(options= chrome_options, executable_path=Constant.CHROME_PATH)
        driver.get(link)
        time.sleep(5)
        try:
            approve_botton = driver.find_element(By.XPATH, '//input[@name="customerResponseApproveButton"]')
            driver.execute_script("arguments[0].click();", approve_botton)
        except:
            pass
        time.sleep(5)
        driver.close()
        driver.quit()

    def __generate_email_cookie(self):
        self.email_driver.switch_to.frame(self.email_driver.find_element(By.XPATH, '//iframe[starts-with(@id,"x-URS")]'))
        self.email_driver.find_element(By.NAME, 'email').send_keys(self.username)
        self.email_driver.find_element(By.NAME, 'password').send_keys(self.emailpass)
        self.email_driver.find_element(By.NAME, 'un-login').click()
        time.sleep(2)
        self.email_driver.find_element(By.ID, 'dologin').click()
        time.sleep(10)
        tmp_cookie = self.email_driver.execute_script('return document.cookie')
        new_cookie = []
        for line in tmp_cookie.split(';'):
            cookie = {}
            key,value = line.split('=',1)
            cookie['name'] = key
            cookie['value'] = value
            new_cookie.append(cookie)
        cookie_file = open(EMAIL_COOKIE_DIR, 'wb')
        pickle.dump(new_cookie, cookie_file)
        cookie_file.close()
        self.email_driver.switch_to.default_content()
        name = self.email_driver.find_element(By.ID, "spnUid").text
        print(name)
        if name == (self.username):
            print('登录成功')
        else:
            print('登录失败')
            sys.exit()

    def __generate_cookie(self):  # 生成cookie_console7.pkl文件
        if os.path.exists(Constant.COOKIE_DIR):
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
        self.__dump_cookie(Constant.COOKIE_DIR, self.web_driver)

    def __if_login(self, url):
        # 当前网页是不是有登录，有的话就回到homepage,更新cookie,并跳转到当前页面
        self.url = url
        self.web_driver.get(self.url)
        if self.url != self.web_driver.current_url:
            return False
        time.sleep(5)
        source = self.web_driver.page_source
        log_info = re.findall(UI.RE_DIC['log_info'], source)
        if self.web_driver.current_url == self.url and log_info and ('登录' in log_info[0] or 'Sign in' in log_info[0]):
            self.web_driver.get(Constant.LOGOUT_URL)
            time.sleep(3)
            self.__auto_login()
            self.__dump_cookie(Constant.COOKIE_DIR, self.web_driver)
            self.web_driver.get(self.url)
            time.sleep(5)
            source = self.web_driver.page_source
            log_info = re.findall(UI.RE_DIC['log_info'], source)
            if log_info and ('登录' in log_info[0] or 'Sign in' in log_info[0]):
                return False
            return True
        elif self.web_driver.current_url == self.url and not log_info:
            return False
        else:
            return True

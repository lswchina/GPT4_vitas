
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
        s = Service(executable_path="../chrome/chromedriver_94")
        self.web_driver = webdriver.Chrome(options= chrome_options, service=s)
        cf = configparser.ConfigParser()
        cf.read(config_path)
        self.password = cf.get('Amazon', 'password')
        self.username = cf.get('Amazon', 'username')
        self.url = cf.get('Amazon', 'console')
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
        time.sleep(2)
        self.web_driver.find_element(By.ID, 'ap_password').send_keys(self.password)
        self.web_driver.find_element(By.ID, 'ap_password').send_keys(Keys.ENTER)
        time.sleep(5)
        if self.web_driver.current_url != self.url:
            time.sleep(80)
            # link = self.get_link()
            # print(link)
            # if link != '':
            #     self.approve(link)
        self.__dump_cookie(cookie_dir, self.web_driver)

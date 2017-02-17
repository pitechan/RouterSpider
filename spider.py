# -*- coding: utf-8 -*-

import re
import requests
import logging
import time
from urlparse import urljoin
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from config import BROWSERMOBPROXYPATH, PHANTOMJSPATH, HEADERS, URLSUFFIXLIST, AUTHURL, BASEURL, INDEXURL, LOGINURL, MAINSUFFIXLIST, FORBIDDENELEMENTLIST, FORBIDDENURLLIST, PROXYSETTINGS, JSINTERCEPTOR


class RouterSpider:

    def __init__(self):
        self.all_urls = []
        self.main_urls = []
        self.server = Server(path=BROWSERMOBPROXYPATH)
        self.server.start()
        self.proxy = self.server.create_proxy()
        self.proxy.add_to_capabilities(webdriver.DesiredCapabilities.PHANTOMJS)
        dcap = dict(webdriver.DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.resourceTimeout"] = 5000
        dcap["phantomjs.page.settings.loadImages"] = False
        self.browser = webdriver.PhantomJS(executable_path=PHANTOMJSPATH, desired_capabilities=dcap)
        self.browser.set_page_load_timeout(10)
        self.requests_session = requests.session()

    # 路由器厂商自己写的登录界面，account：账号，password：密码，account_field_xpath：账号输入框的xpath，password_field_xpath：密码输入框的xpath
    # 如果路由器登录后会在URL中添加字段，可以加入pattern，使用正则提取该字段
    def webdriver_login(self, password, password_field_xpath, login_button_xpath, account=None, account_field_xpath=None, pattern=None):
        self.browser.get(LOGINURL)
        time.sleep(2)
        if account_field_xpath is not None:
            try:
                self.browser.find_element_by_xpath(account_field_xpath).send_keys(account)
            except:
                logging.error('Cannot locate account field.')
        try:
            self.browser.find_element_by_xpath(password_field_xpath).send_keys(password)
        except:
            logging.error('Cannot locate password field')
        try:
            self.browser.find_element_by_xpath(login_button_xpath).click()
        except:
            logging.error('Cannot locate login button.')
        time.sleep(5)
        logging.debug('Login complete.')
        if pattern is not None:
            auth = re.findall(pattern, self.browser.current_url)
            return auth

    # 没有登录界面，使用http-auth登录，例如http://admin:password@192.168.1.1
    def webdriver_login_with_auth(self):
        self.browser.get(AUTHURL)
        logging.debug('Login complete.')

    # 路由器登陆后http headers中有"Authorization"字段，例如headers = {"Authorization":"Basic YWRtaW46cGFzc3dvcmQ="}
    # pattern用来提取前缀，例如http://192.168.1.1/start.html中的start
    def extract_urls_with_auth_headers(self, pattern, target_url=None):
        index_res = requests.get(INDEXURL, headers=HEADERS)
        for url_suffix in URLSUFFIXLIST:
            url_preffix_list = re.findall(pattern, index_res.text, re.IGNORECASE)
            for url_preffix in url_preffix_list:
                url = urljoin(BASEURL, url_preffix, url_suffix)
                if url not in self.all_urls and url not in FORBIDDENURLLIST:
                    self.all_urls.append(url)
                if url not in self.main_urls and url_suffix in MAINSUFFIXLIST and url not in FORBIDDENURLLIST:
                    self.main_urls.append(url)
                self.extract_urls_with_auth_headers(pattern, target_url=url)

    # 路由器厂商自己写的登录界面，创建session，POST账号密码
    # pattern用来提取前缀，例如http://192.168.1.1/start.html中的start
    def extract_urls_with_data(self, pattern, data=None, target_url=None, index=True):
        if index:
            res = self.requests_session.post(LOGINURL, data=data)
        else:
            res = self.requests_session.get(pattern, target_url=target_url)
        for url_suffix in URLSUFFIXLIST:
            url_preffix_list = re.findall(pattern, res.text, re.IGNORECASE)
            for url_preffix in url_preffix_list:
                url = urljoin(BASEURL, url_preffix, url_suffix)
                if url not in self.all_urls and url not in FORBIDDENURLLIST:
                    self.all_urls.append(url)
                if url not in self.main_urls and url_suffix in MAINSUFFIXLIST and url not in FORBIDDENURLLIST:
                    self.main_urls.append(url)
                self.extract_urls_with_data(pattern, target_url=url, index=False)

    def extract_none_suffix_urls_with_data(self, pattern, data=None, target_url=None, index=True):
        if index:
            res = self.requests_session.post(LOGINURL, data=data)
        else:
            res = self.requests_session.get(target_url)
        urls = re.findall(pattern, res.text)
        for url in urls:
            full_url = BASEURL + url
            if full_url not in self.main_urls and full_url not in FORBIDDENURLLIST and 'logout' not in url and 'reboot' not in url:
                self.main_urls.append(full_url)
                self.extract_none_suffix_urls_with_data(pattern, target_url=full_url, index=False)

    # 操作浏览器访问页面，并返回网页源码
    def webdriver_fetchpage(self, target_url):
        self.browser.get(target_url)
        logging.debug("Get url %s" % target_url)
        return self.browser.page_source

    # 从网页源码中提取按钮，下拉菜单等元素
    # pattern用于提取源码中的按钮，下拉菜单的name或id属性
    @staticmethod
    def extract_element(pattern, page_source):
        filtered_list = []
        element_list = re.findall(pattern, page_source, re.IGNORECASE)
        for element in element_list:
            if element not in FORBIDDENELEMENTLIST:
                filtered_list.append(element)
        logging.debug('Extract elements complete.')
        return filtered_list

    # 处理下拉菜单，需要传入下拉菜单的name或id属性
    def handle_selectfield(self, name=None, id=None):
        selectfield = None
        if name is None and id is None:
            raise ValueError("Name and id can not be left None at same time.")
        try:
            if name is not None:
                selectfield = WebDriverWait(self.browser, 5).until(ec.presence_of_element_located((By.NAME, name)))
                logging.debug("Handle selectfield named %s" % name)
            else:
                selectfield = WebDriverWait(self.browser, 5).until(ec.presence_of_element_located((By.ID, id)))
                logging.debug("Handle selectfield id %s" % id)
        except:
            logging.error("Cannot locate element.")
        if selectfield is not None:
            for i in range(0, len(selectfield.options)):
                try:
                    self.proxy.new_har(options=PROXYSETTINGS)
                    Select(selectfield).select_by_index(i)
                    time.sleep(3)
                    self.handle_har(self.proxy.har)
                except:
                    logging.error("Cannot select option by index %s" % i)

    # 处理按钮，需要传入按钮的name，id属性，需要刷新页面时：refresh=True
    def handle_button(self, name=None, id=None, refresh=False):
        button = None
        if name is None and id is None:
            raise ValueError("Name and id can not be left None at same time.")

        try:
            if name is not None:
                button = WebDriverWait(self.browser, 5).until(ec.presence_of_element_located((By.NAME, name)))
                logging.debug("Handle button named %s" % name)
            else:
                button = WebDriverWait(self.browser, 5).until(ec.presence_of_element_located((By.ID, id)))
                logging.debug("Handle button id %s" % id)
        except:
            logging.error("Cannot locate element.")
        if button is not None:
            self.proxy.new_har(options=PROXYSETTINGS)
            try:
                button.click()
                self.handle_har(self.proxy.har)
                if refresh:
                    self.browser.refresh()
            except:
                logging.error("Cannot click button")

    # 处理Har文件，提取POST请求的信息
    @staticmethod
    def handle_har(har):
        method = har['log']['entries'][0]['request']['method']
        if method == 'POST':
            logging.debug('Capture a POST request.')
            try:
                post_data = har['log']['entries'][0]['request']['postData']['params']
                post_url = har['log']['entries'][0]['request']['url']
                print post_data
                print post_url
            except:
                post_request = har['log']['entries'][0]['request']
                print post_request

    def stop(self):
        self.proxy.close()
        self.server.stop()
        self.browser.quit()

if __name__ == '__main__':
    spider = RouterSpider()
    data = {
        'action_mode': 'apply',
        'action_url': 'http://192.168.2.1/cgi-bin/luci',
        'username': 'admin',
        'password': 'MzE2MzE2MzE2'
    }
    spider.browser.maximize_window()
    spider.webdriver_login('316316316', '//div/input', '/html/body/form/div/div[2]/button')
    spider.proxy.request_interceptor(JSINTERCEPTOR)
    time_stamp = re.findall(r'stok=(\w+)/', spider.browser.current_url)[0]
    spider.extract_none_suffix_urls_with_data(r'/(cgi-bin/luci/;stok=\w+/admin/.*?)\"', data, None, True)
    logging.debug('Extract urls complete.')
    for url in spider.main_urls:
        url = re.sub(r'stok=\w+', 'stok='+time_stamp, url)
        page_source = None
        try:
            page_source = spider.webdriver_fetchpage(url)
        except:
            logging.warning("Timeout when get %s" % url)
        if page_source is not None:
            for button_id in spider.extract_element(r'.*button.*id="(.*?)".*', page_source):
                spider.handle_button(id=button_id)
    spider.stop()

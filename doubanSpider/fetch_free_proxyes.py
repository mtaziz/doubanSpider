#!/usr/bin/python
# -*- coding: utf-8 -*-
# @see https://github.com/kohn/HttpProxyMiddleware/blob/master/HttpProxyMiddlewareTest/HttpProxyMiddlewareTest/fetch_free_proxyes.py
import urllib.request
import socket
from bs4 import BeautifulSoup
import pdb
import random
from fake_useragent import UserAgent
from scrapy.conf import settings
from doubanSpider.logConfig import *
# import logging

timeout = 3
socket.setdefaulttimeout(timeout)
# userAgent = UserAgent(verify_ssl=False)
# userAgent = UserAgent(cache=False) 
# userAgent.update()
userAgent = settings['USER_AGEN']
testUrl = "https://movie.douban.com/subject/25849049/"
# testUrl="http://www.mmjpg.com/hot/"

class proxyObject(object):
    protocol = 'http'
    def  __init__(self,ip,port,protocol,speed ,latency="None"):
        self.ip = ip
        self.port = port
        if 'HTTPS' == protocol:
            self.protocol = 'https'
        self.speed = speed
        self.latency = latency

    def getFullInfo(self):
        return self.protocol+"://"+self.ip+":"+self.port +"  speed:"+self.speed+"  latency:"+self.latency

    def getProxy(self):
        return self.protocol+"://"+self.ip+":"+self.port 


# check proxy
def check(proxyObject):
    proxy = {proxyObject.protocol : proxyObject.ip+":"+proxyObject.port}
    proxies = urllib.request.ProxyHandler(proxy) # 创建代理处理器
    opener = urllib.request.build_opener(proxies,urllib.request.HTTPHandler) # 创建特定的opener对象
    opener.addheaders = [("Host","movie.douban.com"),("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),("Accept-Language","en-US,en;q=0.5"),("Connection","keep-alive"),('User-agent', random.choice(userAgent))]
    # print("random.choice(userAgent): %s "% random.choice(userAgent))
    # opener.addheaders = [("Host","www.mmjpg.com"),("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),("Accept-Language","en-US,en;q=0.5"),("Connection","keep-alive"),('User-agent',userAgent.random)]
    urllib.request.install_opener(opener) 
    isgoodIp = False
    try:
        data = urllib.request.urlopen(testUrl)
        # pdb.set_trace()
        isgoodIp = data.code == 200 and "超人总动员2" in data.read().decode("utf-8")
        # return data.code == 200 and "浏览排行榜" in data.read().decode("utf-8")
    except Exception as e:
        logging.error(str(e)+proxyObject.getFullInfo())
    return isgoodIp


def get_html(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', random.choice(userAgent))
    response = urllib.request.urlopen(req)
    return response.read()

def get_soup(url):
    logging.info("start to get %s ",url)
    soup = BeautifulSoup(get_html(url), "lxml")
    return soup

def fetch_xici():
    """
    http://www.xicidaili.com/nn/
    """
    proxyes = []
    try:
        url = "http://www.xicidaili.com/nn/"
        soup = get_soup(url)
        # pdb.set_trace()
        table = soup.find("table", attrs={"id": "ip_list"})
        trs = table.find_all("tr")
        for i in range(1, len(trs)):
            tr = trs[i]
            tds = tr.find_all("td")
            ip = tds[1].text
            port = tds[2].text
            protocol = tds[5].text
            speed = tds[6].div["title"][:-1]
            latency = tds[7].div["title"][:-1]
            if float(speed) < 2.6 and float(latency) < 0.5:
                proxyes.append(proxyObject(ip,port,protocol,speed,latency))
    except Exception as e:
        logging.error("fail to fetch from xici")
        logging.error(e)
    logging.info(" fetch_xici get %s proxys",str(len(proxyes)))
    return proxyes

def fet_ip3366():
    '''
    http://www.ip3366.net/free/?stype=1&page=
    '''
    proxyes = []
    try:
        url = "http://www.ip3366.net/free/?stype=1&page="
        soup = get_soup(url)
        # pdb.set_trace()
        trs = soup.find("div", attrs={"id": "list"}).table.tbody.find_all("tr")
        for i, tr in enumerate(trs):
            # if 0 == i:
            #     continue
            tds = tr.find_all("td")
            ip = tds[0].string.strip()
            port = tds[1].string.strip()
            protocol = tds[3].string.strip()
            speed = tds[5].string.strip()[:-1]
            if float(speed) < 5:
                proxyes.append(proxyObject(ip,port,protocol,speed))
            # if i == 20:
            #     break  #-----------------------------------------
    except Exception as e:
        logging.error("fail to fetch from fet_ip3366")
        logging.error(e)
    logging.info(" fet_ip3366 get %s proxys",str(len(proxyes)))
    return proxyes

def fet_kuaidaili():
    '''
    https://www.kuaidaili.com/free/inha/
    '''
    proxyes = []
    try:
        url = "https://www.kuaidaili.com/free/inha/"
        soup = get_soup(url)
        # pdb.set_trace()
        trs = soup.find("div", attrs={"id": "list"}).table.tbody.find_all("tr")
        for i, tr in enumerate(trs):
            # if 0 == i:
            #     continue
            tds = tr.find_all("td")
            ip = tds[0].string.strip()
            port = tds[1].string.strip()
            protocol = tds[3].string.strip()
            speed = tds[5].string.strip()[:-1]
            if float(speed) < 5:
                proxyes.append(proxyObject(ip,port,protocol,speed))
    except Exception as e:
        logging.error("fail to fetch from fet_kuaidaili")
        logging.error(e)
    logging.info(" fet_kuaidaili get %s proxys",str(len(proxyes)))
    return proxyes

def fetch_all():
    proxyes = []
    # proxyes += fetch_xici()
    # proxyes += fet_ip3366()
    proxyes += fet_kuaidaili()
    logging.info("get proxyes : %s",len(proxyes))
    valid_proxyes = []
    for p in proxyes:
        if check(p):
            valid_proxyes.append(p.getProxy())
            logging.info("good proxy:"+p.getFullInfo()) 
    logging.info("get total proxy:"+str(len(valid_proxyes)))
    return valid_proxyes

if __name__ == '__main__':
    fetch_all()


#!/usr/bin/python
# -*- coding: utf-8 -*-
# @see https://github.com/kohn/HttpProxyMiddleware/blob/master/HttpProxyMiddlewareTest/HttpProxyMiddlewareTest/fetch_free_proxyes.py
import urllib.request
import socket
from bs4 import BeautifulSoup
import pdb
from fake_useragent import UserAgent

timeout = 4
socket.setdefaulttimeout(timeout)
userAgent = UserAgent()
testUrl = "https://movie.douban.com/"

class proxyObject(object):
    protocol = 'http'
    def  __init__(self,ip,port,protocol,speed ,latency):
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
    opener.addheaders = [("Host","movie.douban.com"),("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),("Accept-Language","en-US,en;q=0.5"),("Connection","keep-alive"),('User-agent',userAgent.random)]
    urllib.request.install_opener(opener) 
    try:
        data = urllib.request.urlopen(testUrl)
        # print(data.read().decode("utf8"))
        return data.code == 200
    except Exception as e:
        print(e)
        return False


def get_html(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/6.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/8.0 Mobile/10A5376e Safari/8536.25')
    response = urllib.request.urlopen(req)
    return response.read()

def get_soup(url):
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
        print("fail to fetch from xici")
        print(e)
    return proxyes

def fetch_all():
    proxyes = []
    proxyes = fetch_xici()
    valid_proxyes = []
    for p in proxyes:
        if check(p):
            valid_proxyes.append(p.getProxy())
            print(p.getFullInfo()) 
    return valid_proxyes

if __name__ == '__main__':
    fetch_all()

#!/usr/bin/python
# -*- coding: utf-8 -*-

from scrapy.shell import inspect_response
import os
from scrapy import signals
from twisted.internet import defer
from twisted.internet.error import *
from twisted.web.client import ResponseFailed
from doubanSpider.logConfig import *
from fake_useragent import UserAgent
import random
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider
from datetime import datetime, timedelta
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError
from . import  fetch_free_proxyes
import threading

class UseragentMiddleware(object):
    # 该函数必须返回一个数据-None/request，如果返回的是None,表示处理完成，交给后续的中间件继续操作
    # 如果返回的是request,此时返回的request会被重新交给引擎添加到请求队列中，重新发起
    ua = None

    def process_request(self, request, spider):
        if not self.ua:
            self.ua = UserAgent()
        # 给request请求头中添加user-agent配置
        request.headers.setdefault('User-agent', self.ua.random)
        # logging.error ('request.headers %s ',str(request.headers))



class HttpProxyMiddleware(object):

    def __init__(self, settings):
        # 保存上次不用代理直接连接的时间点
        self.last_no_proxy_time = datetime.now()
        # 一定分钟数后切换回不用代理, 因为用代理影响到速度
        self.recover_interval = 20
        # 一个proxy如果没用到这个数字就被发现老是超时, 则永久移除该proxy. 设为0则不会修改代理文件.
        self.dump_count_threshold = 20
        # 存放代理列表的文件, 每行一个代理, 格式为ip:port, 注意没有http://, 而且这个文件会被修改, 注意备份
        self.proxy_file = "proxyes.dat"
        # 是否在超时的情况下禁用代理
        self.invalid_proxy_flag = True
        # 当有效代理小于这个数时(包括直连), 从网上抓取新的代理, 可以将这个数设为为了满足每个ip被要求输入验证码后得到足够休息时间所需要的代理数
        # 例如爬虫在十个可用代理之间切换时, 每个ip经过数分钟才再一次轮到自己, 这样就能get一些请求而不用输入验证码.
        # 如果这个数过小, 例如两个, 爬虫用A ip爬了没几个就被ban, 换了一个又爬了没几次就被ban,
        # 这样整个爬虫就会处于一种忙等待的状态, 影响效率
        self.extend_proxy_threshold = 5
        # 初始化代理列表
        self.proxyes = [{"proxy": None, "valid": True, "count": 0}]
        # 初始时使用0号代理(即无代理)
        self.proxy_index = 0
        # 表示可信代理的数量(如自己搭建的HTTP代理)+1(不用代理直接连接)
        self.fixed_proxy = len(self.proxyes)
        # 上一次抓新代理的时间
        self.last_fetch_proxy_time = datetime.now()
        # 每隔固定时间强制抓取新代理(min)
        self.fetch_proxy_interval = 120
        # 一个将被设为invalid的代理如果已经成功爬取大于这个参数的页面， 将不会被invalid
        self.invalid_proxy_threshold = 200
        # 在开始执行爬虫时,先另起线程去抓代理ip
        self.threadLock = threading.Lock()
        self.proxysStatus = 0  # 0:未爬取代理,1:正在爬取代理,2:已经抓完代理ip
        self.max_retry_times = settings.getint('RETRY_TIMES')
        # 有fail_count_threadhold次爬取失败就移除该代理
        self.fail_count_threadhold = 5

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def url_in_proxyes(self, url):
        """
        返回一个代理url是否在代理列表中
        """
        for p in self.proxyes:
            if url == p["proxy"]:
                return True
        return False

    def reset_proxyes(self):
        """
        将所有count>=指定阈值的代理重置为valid,
        """
        logging.info("reset proxyes to valid")
        for p in self.proxyes:
            if p["count"] >= self.dump_count_threshold:
                p["valid"] = True

    def fetch_new_proxyes(self):
        """
        从网上抓取新的代理添加到代理列表中
        """
        logging.info("extending proxyes using fetch_free_proxyes.py")
        new_proxyes = fetch_free_proxyes.fetch_all()
        logging.info("new proxyes: %s" % new_proxyes)
        self.last_fetch_proxy_time = datetime.now()

        for np in new_proxyes:
            if self.url_in_proxyes(np):
                continue
            else:
                # count: success count, failCount: fail count
                self.proxyes.append({"proxy": np,
                                     "valid": True,
                                     "count": 0, 
                                     "failCount": 0})
        if self.len_valid_proxy() < self.extend_proxy_threshold:  # 如果发现抓不到什么新的代理了, 缩小threshold以避免白费功夫
            self.extend_proxy_threshold -= 1

    def len_valid_proxy(self):
        """
        返回proxy列表中有效的代理数量
        """
        count = 0
        for p in self.proxyes:
            if p["valid"]:
                count += 1
        return count

    def inc_proxy_index(self):
        """
        将代理列表的索引移到下一个有效代理的位置
        如果发现代理列表只有fixed_proxy项有效, 重置代理列表
        如果还发现已经距离上次抓代理过了指定时间, 则抓取新的代理
        """
        assert self.proxyes[0]["valid"]
        # # 代理数量太少,先抓取代理
        # if len(self.proxyes) < 3:
        #     self.fetch_new_proxyes()

        while True:
            self.proxy_index = (self.proxy_index + 1) % len(self.proxyes)
            if self.proxyes[self.proxy_index]["valid"]:
                break

        # 两轮proxy_index==0的时间间隔过短， 说明出现了验证码抖动，扩展代理列表
        if self.proxy_index == 0 and datetime.now() < self.last_no_proxy_time + timedelta(minutes=2):
            logging.info("captcha thrashing")
            self.fetch_new_proxyes()

        if self.len_valid_proxy() <= self.fixed_proxy or self.len_valid_proxy() < self.extend_proxy_threshold:  # 如果代理列表中有效的代理不足的话重置为valid
            self.reset_proxyes()

        if self.len_valid_proxy() < self.extend_proxy_threshold:  # 代理数量仍然不足, 抓取新的代理
            logging.info("valid proxy < threshold: %d/%d" %
                         (self.len_valid_proxy(), self.extend_proxy_threshold))
            self.fetch_new_proxyes()

        logging.info("now using new proxy: %s" %
                     self.proxyes[self.proxy_index]["proxy"])

        # 一定时间没更新后可能出现了在目前的代理不断循环不断验证码错误的情况, 强制抓取新代理
        # if datetime.now() > self.last_fetch_proxy_time + timedelta(minutes=self.fetch_proxy_interval):
        #    logging.info("%d munites since last fetch" % self.fetch_proxy_interval)
        #    self.fetch_new_proxyes()

    def set_proxy(self, request):
        """
        将request设置使用为当前的或下一个有效代理
        """
        proxy = self.proxyes[self.proxy_index]
        if not proxy["valid"]:
            self.inc_proxy_index()
            proxy = self.proxyes[self.proxy_index]

        if self.proxy_index == 0:  # 每次不用代理直接下载时更新self.last_no_proxy_time
            self.last_no_proxy_time = datetime.now()

        if proxy["proxy"]:
            request.meta["proxy"] = proxy["proxy"]
            logging.info("change proxy: %s ", proxy["proxy"])
        elif "proxy" in request.meta.keys():
            del request.meta["proxy"]
        request.meta["proxy_index"] = self.proxy_index
        proxy["count"] += 1

    def invalid_proxy(self, index):
        """
        将index指向的proxy设置为invalid,
        并调整当前proxy_index到下一个有效代理的位置
        """
        if index < self.fixed_proxy:  # 可信代理永远不会设为invalid
            self.inc_proxy_index()
            return

        if self.proxyes[index]["valid"]:
            self.proxyes[index]["failCount"] += 1
            self.proxyes[index]["valid"] = False
            logging.info("proxyes %s ,fail count %d" % (self.proxyes[index],self.proxyes[index]["failCount"]))
            logging.info("invalidate %s" % self.proxyes[index])
            if  self.proxyes[index]["failCount"] >=  self.fail_count_threadhold: 
                del self.proxyes[index] #delect
                
        if index == self.proxy_index:
            self.inc_proxy_index()

    # 刚开始启动时起线程异步爬取代理ip
    # proxysStatus: 0:未爬取代理,1:正在爬取代理,2:已经抓完代理ip
    def initProxys(self):
        class ProxysThread (threading.Thread):

            def __init__(self,parent):
                threading.Thread.__init__(self)
                self.parent = parent

            def run(self):
                # 获取锁，用于线程同步
                self.parent.threadLock.acquire()
                if self.parent.proxysStatus == 0:
                    self.parent.proxysStatus = 1
                    self.parent.fetch_new_proxyes()
                    self.parent.proxysStatus = 2
                self.parent.threadLock.release()

        if self.proxysStatus == 0:
            ProxysThread(self).start()
            # ProxysThread(self).run()
        return self.proxysStatus == 2

    def process_request(self, request, spider):
        """
        将request设置为使用代理
        """
        # 等到代理初始化完成
        if not self.initProxys():
            return None

        if "retry_times" in request.meta:
            # last retry use no proxy
            if self.max_retry_times-1 <= request.meta['retry_times']  :
                self.proxy_index = 0
                logging.info("last retry use no proxy :retry_times: "+str(request.meta['retry_times'])+"max_retry_times:"+str(self.max_retry_times))
            else:
                self.inc_proxy_index()
                logging.info("retry_times: "+str(request.meta['retry_times'])+"max_retry_times:"+str(self.max_retry_times))
        # use no proxy every a period of time
        elif self.proxy_index > 0 and datetime.now() > (self.last_no_proxy_time + timedelta(minutes=self.recover_interval)):
            logging.info("recover from using proxy")
            self.proxy_index = 0
        elif random.randint(1, 5) == 1:  # 1/5的概率切换ip
            request.meta["change_proxy"] = True
        request.meta["dont_redirect"] = True  # 有些代理会把请求重定向到一个莫名其妙的地址

        # 更换代理, 在第一次请求时没有proxy_index,所以初次请求不会更换代理
        if "change_proxy" in request.meta.keys() and request.meta["change_proxy"]:
            logging.info("change proxy request get by spider: %s" % request)
            self.inc_proxy_index()  # 改为只是更换代理,而不是设置代理无效
            request.meta["change_proxy"] = False
        self.set_proxy(request)

    def process_response(self, request, response, spider):
        # download picture
        if '.jpg' in response.url:
            return response
        """
        检查response.status, 根据status是否在允许的状态码中决定是否切换到下一个proxy, 或者禁用proxy
        """
        logging.error("process_response:request.meta.keys(): %s",str(request.meta.keys()))
        if "proxy" in request.meta.keys():
            logging.debug("%s %s %s" %
                          (request.meta["proxy"], response.status, request.url))
        else:
            logging.debug("None %s %s" % (response.status, request.url))

        if response.status != 200 or "douban" not in response.url or "豆瓣" not in response.text:
            logging.error(
                "invaild proxy, response status:%s url:%s", (response.status, response.url))
            self.invalid_proxy(request.meta["proxy_index"])
            new_request = request.copy()
            new_request.dont_filter = True
            return new_request
        else:
            return response

    def process_exception(self, request, exception, spider):
        """
        处理由于使用代理导致的连接异常
        """
        logging.error("%s , url: %s, exception: %s" % (
            self.proxyes[request.meta["proxy_index"]]["proxy"], request.url, exception))
        if request_proxy_index > self.fixed_proxy - 1 and self.invalid_proxy_flag:  # WARNING 直连时超时的话换个代理还是重试? 这是策略问题
            if self.proxyes[request_proxy_index]["count"] < self.invalid_proxy_threshold:
                self.invalid_proxy(request_proxy_index)
            #     elif request_proxy_index == self.proxy_index:  # 虽然超时，但是如果之前一直很好用，也不设为invalid
            #         self.inc_proxy_index()
            # else:               # 简单的切换而不禁用
            #     if request.meta["proxy_index"] == self.proxy_index:
            #         self.inc_proxy_index()
            # new_request = request.copy()
            # # new_request.meta.get('retry_times', 0) + 1
            # new_request.dont_filter = True
            # return new_request

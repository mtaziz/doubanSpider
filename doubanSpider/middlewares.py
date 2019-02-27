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
from scrapy.exceptions import IgnoreRequest
from datetime import datetime, timedelta
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError
from . import  fetch_free_proxyes
import threading
from multiprocessing import Process
from twisted.internet import task
from scrapy.exceptions import NotConfigured
from scrapy import signals
import signal
import pdb
import sys
from  doubanSpider.util_mysql import MySQLUtil

class UseragentMiddleware(object):
    # 该函数必须返回一个数据-None/request，如果返回的是None,表示处理完成，交给后续的中间件继续操作
    # 如果返回的是request,此时返回的request会被重新交给引擎添加到请求队列中，重新发起
    # @see https://media.readthedocs.org/pdf/fake-useragent/latest/fake-useragent.pdf
    def __init__(self):
        # self.ua = UserAgent(cache=False) # 不希望缓存数据库或不需要可写文件系统
        # self.ua = UserAgent(use_cache_server=False) #不想使用宿主缓存服务器，可以禁用服务器缓存
        # self.ua = UserAgent(verify_ssl=False)
        # self.ua.update()
        self.ua = settings['USER_AGEN']

    def process_request(self, request, spider):
        # 给request请求头中添加user-agent配置
        request.headers.setdefault('User-agent', random.choice(self.ua))
        # print("UseragentMiddleware:"+random.choice(self.ua))
        # logging.error ('request.headers %s ',str(request.headers))



class HttpProxyMiddleware(object):
    '''
    see https://github.com/kohn/HttpProxyMiddleware/blob/master/HttpProxyMiddlewareTest/HttpProxyMiddlewareTest/fetch_free_proxyes.py
    '''
    def __init__(self, settings):
        self.i= 1
        # 保存上次不用代理直接连接的时间点
        self.last_no_proxy_time = datetime.now()
        # 一定分钟数后切换回不用代理, 因为用代理影响到速度
        self.recover_interval = 20
        # 一个proxy如果没用到这个数字就被发现老是超时, 则永久移除该proxy. 设为0则不会修改代理文件.
        self.dump_count_threshold = 20
        # 是否在超时的情况下禁用代理
        self.invalid_proxy_flag = True
        # 当有效代理小于这个数时(包括直连), 从网上抓取新的代理, 可以将这个数设为为了满足每个ip被要求输入验证码后得到足够休息时间所需要的代理数
        # 例如爬虫在十个可用代理之间切换时, 每个ip经过数分钟才再一次轮到自己, 这样就能get一些请求而不用输入验证码.
        # 如果这个数过小, 例如两个, 爬虫用A ip爬了没几个就被ban, 换了一个又爬了没几次就被ban,
        # 这样整个爬虫就会处于一种忙等待的状态, 影响效率
        self.extend_proxy_threshold = 3
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
        self.fail_count_threadhold = 3

        self.mysqlUtil = MySQLUtil()
        #先加载豆瓣陷阱url
        self.trickUrlDict = self.mysqlUtil.queryAllUrls()

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
        logging.info("fetch new proxyes: %s" % new_proxyes)
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
        logging.info("proxy info :%s" % self.proxyes)
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

        # logging.info("now using new proxy: %s" %
        #              self.proxyes[self.proxy_index]["proxy"])

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

        # if proxy["proxy"]:
        #     request.meta["proxy"] = proxy["proxy"]
        # elif "proxy" in request.meta.keys():
        #     del request.meta["proxy"]
        request.meta["proxy"] = proxy["proxy"]
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
            # when proxyes is not enough,reset_proxyes()will set some invalid proxyes  to valid
            self.proxyes[index]["valid"] = False 
            logging.info("invalidate proxy: %s ,fail count %d" % (self.proxyes[index],self.proxyes[index]["failCount"]))
            if  self.proxyes[index]["failCount"] >=  self.fail_count_threadhold: 
                logging.info("remove proxy: %s ,fail count %d" % (self.proxyes[index],self.proxyes[index]["failCount"]))
                del self.proxyes[index] #delete
                
        if index == self.proxy_index:
            self.inc_proxy_index()

    def initProxys(self):
        '''
        刚开始启动时起线程异步爬取代理ip
        proxysStatus: 0:未爬取代理,1:正在爬取代理,2:已经抓完代理ip
        '''
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
            # ProxysThread(self).start()
            ProxysThread(self).run()
        return self.proxysStatus == 2


    def process_request(self, request, spider):
        if request.url in self.trickUrlDict and self.trickUrlDict[request.url]>=5:
            self.updateTrickUrlDict(request.url)
            # 如果其raise一个 IgnoreRequest 异常，则安装的下载中间件的 process_exception() 方法会被调用
            logging.info("trick url,do not crawl:%s ,count:%s" % (request.url,self.trickUrlDict[request.url]))
            raise IgnoreRequest("trick url %s" % request.url)
        # """
        # 将request设置为使用代理
        # """
        # # 等到代理初始化完成
        # if not self.initProxys():
        #     return None

        # if "retry_times" in request.meta:
        #      self.invalid_proxy(request.meta["proxy_index"])
            # request.meta["change_proxy"] = True
        #     # last retry use no proxy
        #     if self.max_retry_times-1 <= request.meta['retry_times']  :
        #         self.proxy_index = 0
        #         logging.info("last retry use no proxy :retry_times: "+str(request.meta['retry_times'])+"max_retry_times:"+str(self.max_retry_times))
        #     else:
        #         logging.info("retry_times: "+str(request.meta['retry_times'])+"max_retry_times:"+str(self.max_retry_times))
        # # use no proxy every a period of time
        # elif self.proxy_index > 0 and datetime.now() > (self.last_no_proxy_time + timedelta(minutes=self.recover_interval)):
        #     logging.info("recover from using proxy")
            # request.meta["change_proxy"] = True
        #     self.proxy_index = 0
        # elif random.randint(1, 5) == 1:  # 1/5的概率切换ip
        #     request.meta["change_proxy"] = True
        # 

        # # 更换代理, 在第一次请求时没有proxy_index,所以初次请求不会更换代理
        # if "change_proxy" in request.meta.keys() and request.meta["change_proxy"]:
        #     logging.info("change proxy request get by spider: %s" % request)
            # self.set_proxy(request)

        self.initProxys()
        if self.i<3:
            self.i = self.i+1
            return None
        if "retry_times" in request.meta:
            logging.info("retry_times: "+str(request.meta['retry_times'])+"max_retry_times:"+str(self.max_retry_times)+" url:"+request.url)
            self.invalid_proxy(request.meta["proxy_index"])
        self.inc_proxy_index()
        self.set_proxy(request)
        logging.info("ip: %s ,start to crawl: %s" %(request.meta["proxy"],request.url))
        logging.info("request.headers: %s" % request.headers)
        
        return None


    def process_response(self, request, response, spider):
        logging.info('request.meta:%s' % request.meta)
        # download picture
        if '.jpg' in response.url:
            return response
        """
        检查response.status, 根据status是否在允许的状态码中决定是否切换到下一个proxy, 或者禁用proxy
        """
        if "proxy" in request.meta.keys():
            logging.debug("%s %s %s" %
                          (request.meta["proxy"], response.status, request.url))
        else:
            logging.debug("None %s %s" % (response.status, request.url))

        if response.status != 200 or "douban" not in response.url or "豆瓣" not in response.text:
            if "proxy" in request.meta.keys():
                logging.error("crawl failed : ip:%s ,  response status:%s, url:%s" % (request.meta["proxy"],response.status, response.url))
            else:
                logging.error("crawl failed : ip:%s ,  response status:%s, url:%s" % ("localhost",response.status, response.url))
            self.updateTrickUrlDict(request.url)
            # 如果是豆瓣的陷阱url
            if request.url in self.trickUrlDict and self.trickUrlDict[request.url]>=5:
                logging.info("trick url in process_response url:%s ,count:%s" % (request.url,self.trickUrlDict[request.url]))
                raise IgnoreRequest("trick url %s" % request.url)
            self.invalid_proxy(request.meta["proxy_index"])
            # new_request = request.copy()
            new_request.dont_filter = True
            return new_request
        else:
            if "proxy" in request.meta.keys():
                logging.info("crawl success : ip:%s ,  response status:%s, url:%s" % (request.meta["proxy"],response.status, response.url))
            else:
                logging.info("crawl success : ip:%s ,  response status:%s, url:%s" % ("localhost",response.status, response.url))
            return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, IgnoreRequest):
            logging.error("IgnoreRequest url: %s, exception: %s" % (request.url, exception))
            return
        """
        处理由于使用代理导致的连接异常
        """
        if "proxy" in request.meta.keys():
            logging.error("process_exception : ip:%s , url:%s exception:%s" % (request.meta["proxy"],request.url,exception))
            self.invalid_proxy(request.meta["proxy_index"])
        else:
            logging.error("process_exception : ip:%s, url:%s exception:%s" % ("localhost", request.url,exception))

        
            #     elif request_proxy_index == self.proxy_index:  # 虽然超时，但是如果之前一直很好用，也不设为invalid
            #         self.inc_proxy_index()
            # else:               # 简单的切换而不禁用
            #     if request.meta["proxy_index"] == self.proxy_index:
            #         self.inc_proxy_index()
            # new_request = request.copy()
            # # new_request.meta.get('retry_times', 0) + 1
            # new_request.dont_filter = True
            # return new_request

    def updateTrickUrlDict(self,url):
        '''
        同一个出现问题的url出现次数>=5次,认为这个url就是陷阱url
        '''
        if url in self.trickUrlDict:
            self.trickUrlDict[url] = self.trickUrlDict[url]+1
            if self.trickUrlDict[url] == 4:
                self.mysqlUtil.updateInsertTrickUrl(self.trickUrlDict)
        else:
            self.trickUrlDict[url] = 1


# #see scrapy/scrapy/contrib/logstats.py
class SpiderSmartCloseRestartExensions(object):
    """
    每interval秒检查一次页面爬取统计情况,若爬取<=pageIntervalMin,则暂停爬虫
    faild to start process , found ImportError: No module named 'doubanSpider'
    """
    def __init__(self, crawler,stats, interval=120.0,pageIntervalMin=0):
        self.crawler = crawler
        self.stats = stats
        self.interval = interval
        self.pageIntervalMin = pageIntervalMin
        self.startCount = 0
        self.isRestarted = False

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler,crawler.stats)
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_opened(self, spider):
        self.pagesprev = 0
        self.itemsprev = 0
        self.task = task.LoopingCall(self.check, spider)
        self.task.start(self.interval)

    def check(self, spider):
        items = self.stats.get_value('item_scraped_count', 0)
        pages = self.stats.get_value('response_received_count', 0)
        itemsPeriod = items - self.itemsprev
        pagePeriod = pages - self.pagesprev
        self.pagesprev, self.itemsprev = pages, items
        msg = "Crawled %d pages AND %d items in %d secs" \
            % (pagePeriod, itemsPeriod, self.interval,)
        logging.info(msg)
        logging.info("startCount: %d:" % self.startCount  )
        self.startCount  += 1
        localValue = self.startCount
        if pagePeriod<=self.pageIntervalMin and self.startCount >1:
            logging.error("stop spider:closespider_pagecount")
            # 另起线程,在一定时间后重启spider
            if  not self.isRestarted :
                self.isRestarted = True
                self.restartSpiderInDelayTime()
            # 执行关闭爬虫操作
            self.crawler.engine.close_spider(spider, 'closespider_errorcount')


    def restartSpiderInDelayTime(self):
        p = RestarProcess()
        p.start()

    def spider_closed(self, spider, reason):
        if self.task.running:
            self.task.stop()

class RestarProcess(Process):
    def run(self):
        # ImportError: No module named 'doubanSpider'
        os.system("gnome-terminal -e 'bash -c \"date;sleep 7;source /home/feng/software/venv/webscprit/bin/activate && cd /media/feng/资源/bigdata/doubanSpider/doubanSpider/ && scrapy crawl doubanmovies; exec bash\"'")
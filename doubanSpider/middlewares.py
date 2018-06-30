# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
from scrapy.shell import inspect_response
from scrapy import signals
from twisted.internet import defer
from twisted.internet.error import *
from twisted.web.client import ResponseFailed
from doubanSpider.logConfig import *
# import scrapy.exceptions as exception
from fake_useragent import UserAgent
import random
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider

class DoubanspiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        logging.error(
            "--------------------------------------------------------------------------------------------------------")
        logging.error('not contained exception: %s ' % exception)
        raise CloseSpider('exception :  %s ', exception)
        # pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logging.info('Spider opened: %s' % spider.name)

# todo not finish


class ProcessAllExceptionMiddleware(object):
    ALL_EXCEPTIONS = (defer.TimeoutError, TimeoutError, DNSLookupError,
                      ConnectionRefusedError, ConnectionDone, ConnectError,
                      ConnectionLost, TCPTimedOutError, ResponseFailed,
                      IOError)

    def process_response(self, request, response, spider):

        # 捕获状态码为40x/50x的response
        if str(response.status).startswith('4') or str(response.status).startswith('5'):
            # 随意封装，直接返回response，spider代码中根据url==''来处理response
            # response = HtmlResponse(url='')
            logging.error("response.status error %s , url : %s :",
                          (response.status, response.url))
            # raise CloseSpider('response.status error %s', response.status)
        # 其他状态码不处理
        return response

    # def process_exception(self, request, exception, spider):
        # 捕获几乎所有的异常
        # if isinstance(exception, self.ALL_EXCEPTIONS):
        #     # 在日志中打印异常类型
        #     logging.error('Got exception: %s' % (exception))
        #     # 随意封装一个response，返回给spider
        #     response = HtmlResponse(url='exception')
            # return response
        # 打印出未捕获到的异常
        # logging.error('exception: %s ' % exception)
        # raise CloseSpider('exception : %s ',str(exception))


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


class ProxyMiddleware(object):

    def process_request(self, request, spider):
        # 短评和影评页,豆列除第一页外,不用cookie，换IP
        if "comments" in request.url or "reviews" in request.url  or ("doulist" in request.url  and "start=" in request.url ):
            proxy = random.choice(settings['PROXY'])
            
            request.meta["dont_redirect"] = True
            request.meta['proxy'] = proxy.get('ip_port')
            logging.error('request.meta %s ', str(request.meta))
            logging.error('request.url %s ', str(request.url))

     # def process_exception(self,request,exception,spider):
     #    logger.info("ProxyMiddleware exception : %s",exception)
     #    # 出异常时重新加上代理,重新请求
     #    proxy = random.choice(PROXY)
     #    request.meta['proxy'] = proxy.get('ip_port')
     #    return request


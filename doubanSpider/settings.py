# -*- coding: utf-8 -*-

# Scrapy settings for doubanSpider project


BOT_NAME = 'doubanSpider'

SPIDER_MODULES = ['doubanSpider.spiders']
NEWSPIDER_MODULE = 'doubanSpider.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

COOKIES_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Connection': 'keep-alive',  # 保持链接状态
}


# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'doubanSpider.middlewares.UseragentMiddleware': 200,
    'doubanSpider.middlewares.HttpProxyMiddleware': 210,
}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'doubanSpider.pipelines.CleanItemPipeline': 100,
   'doubanSpider.pipelines.MovieImagePipeline': 310,
   'doubanSpider.pipelines.ReviewtToFilePipeline': 311,
   'doubanSpider.pipelines.MySQLStorePipeline':400,
}

# image config
IMAGES_STORE = '/media/feng/资源/bigdata/doubanSpider/file/images/'
IMAGES_MIN_HEIGHT = 100
IMAGES_MIN_WIDTH = 100
IMAGES_EXPIRES = 90                                   # 过期天数

# 日志默认开启,有默认设置
LOG_ENABLED = True
LOG_ENCODING = 'utf-8'
LOG_LEVEL = 'DEBUG'
# 用于设置日志配置文件，将程序运行的信息，保存在指定的文件中
LOG_STDOUT = True
LOG_FILE = 'doubanspider.log'

# database
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWD = 'feng'
MYSQL_DBNAME = 'bigdata'

DOWNLOAD_DELAY = 3
DOWNLOAD_TIMEOUT = 7
RETRY_TIMES=3
# stop spider 5h later
CLOSESPIDER_TIMEOUT = 3600*5

# crawls in  BFO order
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
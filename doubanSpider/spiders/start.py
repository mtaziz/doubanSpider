# start.py
from scrapy import cmdline

# 续爬模式，会自动生成一个crawls文件夹，用于存放断点文件
cmdline.execute('scrapy crawl doubanmovies -s JOBDIR=crawls/doubanmovieSpider')

# 非续爬模式
# cmdline.execute('scrapy crawl mySpider'.split())
# -*- coding: utf-8 -*-
from scrapy.shell import inspect_response
from scrapy.exporters import JsonItemExporter
from doubanSpider.items import *
import os
import scrapy
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class DoubanspiderPipeline(object):

    def process_item(self, item, spider):
        return item


class cleanItemPipeline(object):

    def process_item(self, item, spider):
        for (key, value) in item.items():
            item[key] = value.strip()
            if not value.strip():
                    self.logger.error('item value is none!  %s ', item)
        return item


class reviewtToFilePipeline(object):

    def __init__(self):
        self.separateLine = '-----------====------------'

    def process_item(self, item, spider):
        if isinstance(item, FilmCriticsItem):
            base_dir = os.getcwd()
            filePath = '../../file/reviews/' + item['movieid']
            with open(filePath, 'a') as f:
                f.write(item['film_critics_url'] + ':::')
                f.write(item['review'] + '\n')
                f.write(self.separateLine + '\n')
        return item

# class MySQLStorePipeline(object):

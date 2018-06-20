# -*- coding: utf-8 -*-
from scrapy.shell import inspect_response
from scrapy.exporters import JsonItemExporter
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
        return item


class reviewtToFilePipeline(object):

    def process_item(self, item, spider):
        base_dir = os.getcwd()
        print("===========================================================")
        print("base_dir : %s ", base_dir)
        filePath = '../../file/reviews/'+item['movieid']
        with open(filePath, 'a+') as f:
             f.write('dd '+ item['movieid'])
        return item

# class MySQLStorePipeline(object):

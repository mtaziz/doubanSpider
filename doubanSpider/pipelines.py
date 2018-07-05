# -*- coding: utf-8 -*-
from scrapy.shell import inspect_response
from scrapy.conf import settings
from scrapy.exporters import JsonItemExporter
from doubanSpider.items import *
from doubanSpider.logConfig import *
import os
import scrapy
import sys
import pymysql
import hashlib
from scrapy.exceptions import DropItem
from scrapy.http import Request

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
class DoubanspiderPipeline(object):

    def process_item(self, item, spider):
        return item


class CleanItemPipeline(object):

    def process_item(self, item, spider):
        for (key, value) in item.items():
            if isinstance(value,str) : 
                if not value.strip():
                    logging.error('item value is none!  %s ', item)
                else :
                    item[key] = value.strip()
        return item


class ReviewtToFilePipeline(object):

    def __init__(self):
        self.separateLine = '---==---'

    def process_item(self, item, spider):
        if isinstance(item, FilmCriticsItem):
            base_dir = os.getcwd()
            filePath = '/media/feng/资源/bigdata/doubanSpider/file/reviews/' + item['movieid']
            logging.error("FilmCriticsItem: moive:%s",item['movieid'])
            with open(filePath, 'a') as f:
                f.write(item['film_critics_url'] +
                        ':::' + item['review'] + '\n')
                f.write(self.separateLine + '\n')
        return item

class MySQLStorePipeline(object):

    insertFilmMovieDetailSql =  """INSERT INTO movie_detail (movieid,movie_url,movie_name,director,writers,stars,genres,country,official_site,language, 
        release_date,also_known_as,runtime,IMDb_url,douban_rate,rate_num,star_5,star_4,star_3,star_2,star_1,comparison_1,comparison_2,tags,
        storyline,also_like_1_name,also_like_1_url,also_like_2_name,also_like_2_url,also_like_3_name,also_like_3_url,also_like_4_name,also_like_4_url,
        also_like_5_name,also_like_5_url,also_like_6_name,also_like_6_url,also_like_7_name,also_like_7_url,also_like_8_name,also_like_8_url,
        also_like_9_name,also_like_9_url,also_like_10_name,also_like_10_url,essay_collect_url,film_critics_url,doulists_url,viewed_num,want_to_view_num,image_url) 
        VALUES  ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', 
        '%s','%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s','%s')"""  

    insertDoulistSql = '''INSERT INTO doulist (movieid,doulist_url,doulist_name,doulist_intr,user_name,
                            user_url,collect_num,recommend_num,movie_num,doulist_cratedDate,
                            doulist_updatedDate)
                        VALUES ('%s', '%s', '%s', '%s', '%s','%s' ,'%s', '%s', '%s', '%s', '%s')'''

    insertDoulistMovieDetailSql = """INSERT INTO doulist_movie_detail (movieid,
                                        doulist_url)
                                    VALUES ('%s', '%s')"""

    insertFilmCriticsSql = '''INSERT INTO film_critics (movieid,film_critics_url, title,
                                    user_name,user_url,comment_rate,comment_time,useless_num,
                                    useful_num,recommend_num)
                                VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s')'''   

    insertMovieEssaySql = '''INSERT INTO movie_essay (movieid,user_name, user_url,
                                    comment,comment_rate,comment_time)
                                VALUES ('%s', '%s', '%s', '%s', '%s', '%s')'''             

    insertMovieBaseInfoSql = """INSERT INTO movie_base_info (movieid,view_date,personal_rate,
                                            personal_tags,intro,isViewed)
                                        VALUES ('%s', '%s', '%s','%s', '%s', '%s')"""                    


    def __init__(self):
        self.host=settings['MYSQL_HOST']
        self.port=settings['MYSQL_PORT']
        self.user=settings['MYSQL_USER']
        self.passwd=settings['MYSQL_PASSWD']
        self.db=settings['MYSQL_DBNAME']
        self.conn =  pymysql.connect(host=self.host, user=self.user,  
            password=self.passwd, db=self.db,charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):  
        sql = ''
        values = ''
        if isinstance(item, MovieDetialItem):
            sql = MySQLStorePipeline.insertFilmMovieDetailSql
            values = (item["movieid"],item["movie_url"],item["movie_name"],item["director"],item["writers"],item["stars"],
                item["genres"],item["country"],item["official_site"],item["language"],item["release_date"],item["also_known_as"],
                item["runtime"],item["IMDb_url"],item["douban_rate"],item["rate_num"],item["star_5"],item["star_4"],
                item["star_3"],item["star_2"],item["star_1"],item["comparison_1"],item["comparison_2"],
                item["tags"],item["storyline"],item["also_like_1_name"],item["also_like_1_url"],
                item["also_like_2_name"],item["also_like_2_url"],item["also_like_3_name"],item["also_like_3_url"],item["also_like_4_name"],item["also_like_4_url"],
                item["also_like_5_name"],item["also_like_5_url"],item["also_like_6_name"],item["also_like_6_url"],item["also_like_7_name"],item["also_like_7_url"],
                item["also_like_8_name"],item["also_like_8_url"],item["also_like_9_name"],item["also_like_9_url"],item["also_like_10_name"],item["also_like_10_url"],
                item["essay_collect_url"],item["film_critics_url"],item["doulists_url"],item["viewed_num"],item["want_to_view_num"],item["image_url"])
        elif isinstance(item, MovieBaseInfoItem):
            sql = MySQLStorePipeline.insertMovieBaseInfoSql
            values = (item['movieid'],item['view_date'],item['personal_rate'],
                                item['personal_tags'],item['intro'],item['isViewed'])
        elif isinstance(item, MovieEssayItem):
            sql = MySQLStorePipeline.insertMovieEssaySql 
            values = (item['movieid'],item['user_name'],
                    item['user_url'],item['comment'],item['comment_rate'],item['comment_time'])
        elif isinstance(item, DoulistItem):
            sql = MySQLStorePipeline.insertDoulistSql
            values = (item['movieid'], 
                    item['doulist_url'],item['doulist_name'],item['doulist_intr'],item['user_name'],
                    item['user_url'],item['collect_num'],item['recommend_num'],
                    item['movie_num'],item['doulist_cratedDate'],
                    item['doulist_updatedDate'])      
        elif isinstance(item, DoulistMovieDetailItem):
            sql = MySQLStorePipeline.insertDoulistMovieDetailSql
            values =(item['movieid'],item['doulist_url'])
        elif isinstance(item, FilmCriticsItem):
            sql = MySQLStorePipeline.insertFilmCriticsSql
            values = (item['movieid'],
                    item['film_critics_url'],item['title'],item['user_name'],item['user_url'],
                    item['comment_rate'],item['comment_time'],item['useless_num'],
                    item['useful_num'],item['recommend_num'])
        else:
            logging.error("没有对应上item! : "+str(item)) 
            return 
        try:        
            logging.info(sql % values)
            self.cursor.execute(sql % self.conn.escape(values))
            self.conn.commit()
        except Exception as e:
            logging.error(e)
        return item

    def close_spider(self, spider):
        self.conn.close()

# from scrapy.exceptions import DropItem
# # 最早执行 越小越早执行
# class DuplicatesPipeline(object):

#     def __init__(self):
#         self.ids_seen = set()

#     def process_item(self, item, spider):
#         if item['id'] in self.ids_seen:
#             raise DropItem("Duplicate item found: %s" % item)
#         else:
#             self.ids_seen.add(item['id'])
#             return item


from scrapy.pipelines.images import ImagesPipeline
# download image
class MovieImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if isinstance(item, MovieDetialItem):
            image_url = item['image_url'] 
            yield scrapy.Request(image_url,meta={'item':item})

    #rename image
    def file_path(self,request,response=None,info=None):
        item=request.meta['item']
        filename = item['movieid']
        return filename 
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

logger = MyLogger().getlog()


class DoubanspiderPipeline(object):

    def process_item(self, item, spider):
        return item


class cleanItemPipeline(object):

    def process_item(self, item, spider):
        for (key, value) in item.items():
            item[key] = value.strip()
            if not value.strip():
                logger.error('item value is none!  %s ', item)
        return item


class reviewtToFilePipeline(object):

    def __init__(self):
        self.separateLine = '---==---'

    def process_item(self, item, spider):
        if isinstance(item, FilmCriticsItem):
            base_dir = os.getcwd()
            filePath = '../../file/reviews/' + item['movieid']
            with open(filePath, 'a') as f:
                f.write(item['film_critics_url'] +
                        ':::' + item['review'] + '\n')
                f.write(self.separateLine + '\n')
        return item

class MySQLStorePipeline(object):

    insertDoulistSql = """INSERT INTO doulist (movieid,movie_url,movie_name,doulist_url,doulist_name,doulist_intr,user_name,
                                user_url,collect_num,recommend_num,viewed_num,not_viewed_num,doulist_cratedDate,
                                doulist_updatedDate)
                            VALUES (%s, %s, %s, %s, %s,%s %s, %s, %s, %s, %s, %s, %s, %s)"""

    insertDoulistMovieDetailSql = """INSERT INTO doulist_movie_detail (movieid,movie_url,movie_name,
                                            doulist_url,comment)
                                        VALUES (%s, %s, %s, %s, %s)"""  

    insertFilmCriticsSql = """INSERT INTO film_critics (movieid,movie_url,movie_name,film_critics_url, title,
                                        user_name,user_url,comment_rate,comment_time,useless_num,
                                        useful_num,reply_num,recommend_num)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)"""   

    insertFilmMovieDetailSql =  """INSERT INTO movie_detail (movieid,movie_url,movie_name,director,
                                        writers,stars,genres,country,official_site,language,
                                        release_date,also_known_as,runtime,IMDb_url,douban_rate,rate_num,
                                        star_5,star_4,star_3,star_2,star_1,comparison_1,
                                        comparison_2,view_date,my_rate,my_tags,tags,storyline,
                                        also_like_1_name,also_like_1_url,also_like_2_name,also_like_2_url,also_like_3_name,also_like_3_url,
                                        also_like_4_name,also_like_4_url,also_like_5_name,also_like_5_url,also_like_6_name,also_like_6_url,
                                        also_like_7_name,also_like_7_url,also_like_8_name,also_like_8_url,also_like_9_name,also_like_9_url,
                                        also_like_10_name,also_like_10_url,essay_collect_url,film_critics_url,doulists_url,
                                        viewed_num,want_to_view_num,image_url
                                        )
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s, %s,
                                            %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,
                                            %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,
                                            %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,
                                            %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,
                                            %s, %s, %s, %s)"""          
    
    insertMovieEssaySql = """INSERT INTO movie_essay (movieid,movie_url,movie_name,user_name, user_url,
                                        comment,comment_rate,comment_time)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""                                  

    def __init__(self):
        self.host=settings['MYSQL_HOST']
        self.port=settings['MYSQL_PORT']
        self.user=settings['MYSQL_USER']
        self.passwd=settings['MYSQL_PASSWD']
        self.db=settings['MYSQL_DBNAME']

        self.conn = pymysql.connect(self.host, self.user, self.passwd, 
                                    self.db)
                                    # , charset="utf8",
                                    # use_unicode=True)
        self.conn = pymysql.connect(host=self.host, user=self.user,  
                password=self.passwd, db=self.db ,port=self.port, 
                charset="utf8",use_unicode=True)

        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):  
        # logger.error("======================================1111111============================================================")
        # logger.error("item: %s : ", str(item))
        # self.cursor.execute(MySQLStorePipeline.insertFilmMovieDetailSql,
        #             (item['movieid'],item['movie_url'],item['movie_name'],item['director'],item['writers'],item['stars'],
        #             item['genres'],item['country'],item['official_site'],item['language'],item['release_date'],item['also_known_as'],
        #             item['runtime'],item['IMDb_url'],item['douban_rate'],item['rate_num'],item['star_5'],item['star_4'],
        #             item['star_3'],item['star_2'],item['star_1'],item['comparison_1'],item['comparison_2'],item['view_date'],
        #             item['my_rate'],item['my_tags'],item['tags'],item['storyline'],item['also_like_1_name'],item['also_like_1_url'],
        #             item['also_like_2_name'],item['also_like_2_url'],item['also_like_3_name'],item['also_like_3_url'],item['also_like_4_name'],item['also_like_4_url'],
        #             item['also_like_5_name'],item['also_like_5_url'],item['also_like_6_name'],item['also_like_6_url'],item['also_like_7_name'],item['also_like_7_url'],
        #             item['also_like_8_name'],item['also_like_8_url'],item['also_like_9_name'],item['also_like_9_url'],item['also_like_10_name'],item['also_like_10_url'],
        #             item['essay_collect_url'],item['film_critics_url'],item['doulists_url'],item['viewed_num'],item['want_to_view_num'],item['image_url'])
        #             )
        try:    
            if isinstance(item, scrapy.Item):
                logger.error("==================================================================================================")
                self.cursor.execute(MySQLStorePipeline.insertFilmMovieDetailSql,
                    (item['movieid'],item['movie_url'],item['movie_name'],item['director'],item['writers'],item['stars'],
                    item['genres'],item['country'],item['official_site'],item['language'],item['release_date'],item['also_known_as'],
                    item['runtime'],item['IMDb_url'],item['douban_rate'],item['rate_num'],item['star_5'],item['star_4'],
                    item['star_3'],item['star_2'],item['star_1'],item['comparison_1'],item['comparison_2'],item['view_date'],
                    item['my_rate'],item['my_tags'],item['tags'],item['storyline'],item['also_like_1_name'],item['also_like_1_url'],
                    item['also_like_2_name'],item['also_like_2_url'],item['also_like_3_name'],item['also_like_3_url'],item['also_like_4_name'],item['also_like_4_url'],
                    item['also_like_5_name'],item['also_like_5_url'],item['also_like_6_name'],item['also_like_6_url'],item['also_like_7_name'],item['also_like_7_url'],
                    item['also_like_8_name'],item['also_like_8_url'],item['also_like_9_name'],item['also_like_9_url'],item['also_like_10_name'],item['also_like_10_url'],
                    item['essay_collect_url'],item['film_critics_url'],item['doulists_url'],item['viewed_num'],item['want_to_view_num'],item['image_url'])
                    )
            elif isinstance(item, MovieEssayItem):
                self.cursor.execute(MySQLStorePipeline.insertMovieEssaySql, 
                       (item['movieid'],item['movie_url'],item['movie_name'],item['user_name'],
                        item['user_url'],item['comment'],item['comment_rate'],item['comment_time']))
            elif isinstance(item, DoulistItem):
                self.cursor.execute(MySQLStorePipeline.insertDoulistSql, 
                       (item['movieid'], item['movie_url'],item['movie_name'],
                        item['doulist_url'],item['doulist_name'],item['doulist_intr'],item['user_name'],
                        item['user_url'],item['collect_num'],item['recommend_num'],
                        item['viewed_num'],item['not_viewed_num'],item['doulist_cratedDate'],
                        item['doulist_updatedDate']))            
            elif isinstance(item, DoulistMovieDetailItem):
                self.cursor.execute(MySQLStorePipeline.insertDoulistMovieDetailSql, 
                       (item['movieid'],item['movie_url'],item['movie_name'],
                        item['doulist_url'],item['comment']))
            elif isinstance(item, FilmCriticsItem):
                self.cursor.execute(MySQLStorePipeline.insertFilmCriticsSql, 
                       (item['movieid'],item['movie_url'],item['movie_name'],
                        item['film_critics_url'],item['title'],item['user_name'],item['user_url'],
                        item['comment_rate'],item['comment_time'],item['useless_num'],
                        item['useful_num'],item['reply_num'],item['recommend_num'])) 
            else:
                logger.error("没有对应上item!")  
            self.conn.commit()
        
        except Exception as e:
            logger.error("")
        logger.error("======================================222222============================================================")
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
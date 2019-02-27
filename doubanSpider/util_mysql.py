import scrapy
# from doubanSpider.transCookie import *
from scrapy.conf import settings
from scrapy.shell import inspect_response
from doubanSpider.logConfig import *
import scrapy.exceptions as exception
import pymysql
# import logging
import pdb

class MySQLUtil(object):
    '''
    目前主要用于存取豆瓣url陷阱
    '''  
    def __init__(self):
        # self.host = 'localhost'
        # self.port = 3306
        # self.user = 'root'
        # self.passwd = 'feng'
        # self.db = 'bigdata'
        self.host=settings['MYSQL_HOST']
        self.port=settings['MYSQL_PORT']
        self.user=settings['MYSQL_USER']
        self.passwd=settings['MYSQL_PASSWD']
        self.db=settings['MYSQL_DBNAME']
        self.conn =  pymysql.connect(host=self.host, user=self.user,  
            password=self.passwd, db=self.db,charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.conn.cursor()


    def updateInsertTrickUrl(self,trickUrls):
        '''
        数据库有更新,没有就insert
        '''
        updateUrls = []
        insertUrls = []  
        allUrls = self.queryAllUrls()
        for (u,c) in trickUrls.items():
            if u in allUrls:
                if allUrls[u] != c:
                    updateUrls.append((c,u))
            else:
                insertUrls.append((u,c))
        
        insertTrickUrlSql = '''INSERT INTO trick_url(url,count)VALUES(%s, %s)'''
        updateTrickUrlSql = ''' UPDATE trick_url SET count = %s WHERE url = %s'''
        # pdb.set_trace()
        self.updateInsertUrls(insertTrickUrlSql,insertUrls)
        self.updateInsertUrls(updateTrickUrlSql,updateUrls)
        
    
    def updateInsertUrls(self,sql,values):
        # 没有更新
        if not values:
            return
        try:        
            logging.info(sql)
            logging.info(values)
            # pdb.set_trace()
            self.cursor.executemany(sql , values)
            self.conn.commit()
        except Exception as e:
            logging.error(sql)
            logging.error(values)
            logging.error(e)


    def queryAllUrls(self):
        sql = 'select url,count from trick_url'
        return self.queryUrlInfo(sql)


    def queryTrickUrls(self):
        sql = 'select url,count from trick_url where count>=5'
        return self.queryUrlInfo(sql)


    def queryUrlInfo(self,queryTrickUrlSql):
        try:        
            # print(queryTrickUrlSql)
            logging.info(queryTrickUrlSql)
            self.cursor.execute(queryTrickUrlSql)
            results = self.cursor.fetchall()    #获取查询的所有记录
            logging.info('load TrickUrl: %s' % results)
            dictResults = {}
            for r in results:
                dictResults[r['url']] = r['count']
            return dictResults
        except Exception as e:
            logging.error(queryTrickUrlSql)
            logging.error(e)

if __name__ == '__main__':
    a = MySQLUtil()
    # a.queryAllUrls()
    d = {'aaaa': 9, 'aaa45a': 8, 'aaa454a': 1,'bbb':9,'bbbd':9,'fff':1}
    a.updateInsertTrickUrl(d)

    # print(a.queryTrickUrls())

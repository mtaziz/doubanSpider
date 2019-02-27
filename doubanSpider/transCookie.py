# -*- coding: utf-8 -*-

class transCookie:
    def __init__(self, cookie):
        self.cookie = cookie

    def stringToDict(self):
        '''
        将从浏览器上Copy来的cookie字符串转化为Scrapy能使用的Dict
        '''
        itemDict = {}
        items = self.cookie.split(';')
        for item in items:
            key = item.split('=')[0].replace(' ', '')
            value = item.split('=')[1]
            itemDict[key] = value
        return itemDict


import time, os, sched
import threading
from datetime import datetime, timedelta
from multiprocessing import Process
import signal
import sys

class MyProcess(Process):
    def run(self):
        os.system("gnome-terminal -e 'bash -c \"date;sleep 5;source /home/feng/software/venv/webscprit/bin/activate && pwd ; exec bash\"'")
    #  os.system("gnome-terminal -e 'bash -c \"source /home/feng/software/venv/webscprit/bin/activate && pwd && scrapy crawl doubanmovies; exec bash\"'")

if __name__ == '__main__':
    p = MyProcess()
    p.start()
    print("p.pid %s" % p.pid)
    # time.sleep(3)
    print("p.name %s" % p.name)
print("os.getpid() ddddddddddd:%s " % os.getpid() )

os.system("gnome-terminal -e 'bash -c \"date;sleep 5;source /home/feng/software/venv/webscprit/bin/activate && cd /media/feng/资源/bigdata/doubanSpider/doubanSpider/spiders && scrapy crawl doubanmovies -s JOBDIR=/media/feng/资源/bigdata/doubanSpider/file/job ; exec bash\"'")

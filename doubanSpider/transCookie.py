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

# if __name__ == "__main__":
#     cookie = "ue=1430657824@qq.com; ll=118282; bid=2ZAH2S2KiAo; ps=y; dbcl2=99678180:+xbhZwQ2hI4; push_noty_num=0; push_doumail_num=0; ap=1; __utma=30149280.2077450901.1528894521.1528894521.1528894521.1; __utmz=30149280.1528894521.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _vwo_uuid_v2=D0ABF7CE98FAAEFC16F17EB5D02FA904C|40d80dd9cb7725af334383e36649c6ae; ck=72gG"
#     trans = transCookie(cookie)
#     print(trans.stringToDict())

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
# os.system('ls')
# signal.signal(signal.SIGINT, CtrlC)
os.system("gnome-terminal -e 'bash -c \"date;sleep 5;source /home/feng/software/venv/webscprit/bin/activate && cd /media/feng/资源/bigdata/doubanSpider/doubanSpider/spiders && scrapy crawl doubanmovies -s JOBDIR=/media/feng/资源/bigdata/doubanSpider/file/job ; exec bash\"'")
# def signal_handler(sig, frame):
#     print('You pressed Ctrl+C!')
#     sys.exit(0)
# # signal.signal(signal.SIGINT, sys.exit(0))
# # signal.signal(signal.SIGINT, signal_handler)
# print('Press Ctrl+C')
# signal.pause()
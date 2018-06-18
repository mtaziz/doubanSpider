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

if __name__ == "__main__":
    cookie = "ue=1430657824@qq.com; ll=118282; bid=2ZAH2S2KiAo; ps=y; dbcl2=99678180:+xbhZwQ2hI4; push_noty_num=0; push_doumail_num=0; ap=1; __utma=30149280.2077450901.1528894521.1528894521.1528894521.1; __utmz=30149280.1528894521.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _vwo_uuid_v2=D0ABF7CE98FAAEFC16F17EB5D02FA904C|40d80dd9cb7725af334383e36649c6ae; ck=72gG"
    trans = transCookie(cookie)
    print(trans.stringToDict())
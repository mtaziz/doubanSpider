import scrapy
from doubanSpider.transCookie import *
from doubanSpider.items import *
from scrapy.conf import settings
from scrapy.shell import inspect_response
# Scrapy定向爬虫教程(五)——保持登陆状态 : https://blog.csdn.net/qq_30242609/article/details/52822190
# https://juejin.im/post/5a41a76b6fb9a04512393101
# https://www.xncoding.com/2016/04/12/scrapy-11.html
# 文件图片储存 https://www.xncoding.com/2016/03/20/scrapy-08.html

# 登录https://blog.csdn.net/qq_41020281/article/details/79437455
# https://www.cnblogs.com/jinxiao-pu/p/6670672.html tesseract


class DoubanMoviesSpider(scrapy.Spider):
    name = "doubanmovies"
    allowed_domains = ['movie.douban.com']
    cookie = transCookie("ue=1430657824@qq.com; ll=118282; bid=2ZAH2S2KiAo; ps=y; dbcl2=99678180:+xbhZwQ2hI4; push_noty_num=0; push_doumail_num=0; ap=1; _pk_id.100001.4cf6=6dca2b2485769e55.1528894519.1.1528894519.1528894519.; __utma=30149280.2077450901.1528894521.1528894521.1528894521.1; __utmz=30149280.1528894521.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utma=223695111.468546197.1528894521.1528894521.1528894521.1; __utmz=223695111.1528894521.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _vwo_uuid_v2=D0ABF7CE98FAAEFC16F17EB5D02FA904C|40d80dd9cb7725af334383e36649c6ae; ck=72gG").stringToDict()
    global aa 
    aa = 1

    def start_requests(self):
        url = 'https://movie.douban.com/subject/5308265/'
        self.logger.info('start_requests %s ', url)
        self.logger.info(
            '-----------------------------------------------------------------------------')
        yield scrapy.Request(url, self.parse, cookies=self.cookie, meta={'cookiejar': 1})

    def parse(self, response):
        self.logger.info('start crawl MovieDetialItem %s', response.url)

        movieItem = MovieDetialItem()
        movieItem['movieid'] = response.url  # 从url中取出movieid
        movieItem['director'] = '/'.join(response.xpath(
            '//a[contains(@rel, "v:directedBy")]/text()').extract())
        movieItem['writers'] = '/'.join(response.selector.xpath(
            '(//div[@id="info"]/span)[2]/span/a/text()').extract())
        movieItem['stars'] = '/'.join(response.selector.xpath(
            '(//div[@id="info"]/span)[3]/span/a/text()').extract())
        movieItem['genres'] = '/'.join(response.xpath(
            '//span[contains(@property, "v:genre")]/text()').extract())
        movieItem['country'] = response.xpath(
            '//span[contains(./text(), "制片国家/地区:")]/following::text()[1]').extract_first()
        movieItem['language'] = response.xpath(
            '//span[contains(./text(), "语言:")]/following::text()[1]').extract_first()
        movieItem['release_date'] = '/'.join(response.xpath(
            '//span[contains(@property, "v:initialReleaseDate")]/text()').extract())
        movieItem['runtime'] = response.xpath(
            '//span[contains(@property, "v:runtime")]/text()').extract_first()
        movieItem['also_known_as'] = response.xpath(
            '//span[contains(./text(), "又名:")]/following::text()[1]').extract_first()
        movieItem['IMDb_url'] = response.xpath(
            '//span[contains(./text(), "IMDb链接:")]/following::a/@href').extract_first()
        movieItem['douban_rate'] = response.xpath(
            '//strong[contains(@property, "v:average")]/text()').extract_first()
        movieItem['rate_num'] = response.xpath(
            '//span[contains(@property, "v:votes")]/text()').extract_first()
        movieItem['star_5'] = response.xpath(
            '//span[contains(@class, "stars5 starstop")]/following::text()[3]').extract_first()
        movieItem['star_4'] = response.xpath(
            '//span[contains(@class, "stars4 starstop")]/following::text()[3]').extract_first()
        movieItem['star_3'] = response.xpath(
            '//span[contains(@class, "stars3 starstop")]/following::text()[3]').extract_first()
        movieItem['star_2'] = response.xpath(
            '//span[contains(@class, "stars2 starstop")]/following::text()[3]').extract_first()
        movieItem['star_1'] = response.xpath(
            '//span[contains(@class, "stars1 starstop")]/following::text()[3]').extract_first()
        movieItem['comparison_1'] = response.xpath(
            '//div[contains(@class, "rating_betterthan")]/a[1]/text()').extract_first()
        movieItem['comparison_2'] = response.xpath(
            '//div[contains(@class, "rating_betterthan")]/a[2]/text()').extract_first()
        movieItem['tags'] = '/'.join(response.xpath(
            '//div[contains(@class, "tags-body")]/a/text()').extract())
        movieItem['storyline'] = response.xpath(
            '//span[contains(@property, "v:summary")]/text()').extract_first().strip()

        also_like_names = response.xpath(
            '(//div[contains(@class, "recommendations-bd")]/dl/dt/a)/@href').extract()
        also_like_urls = response.xpath(
            '(//div[contains(@class, "recommendations-bd")]/dl/dt/a)//img/@alt').extract()
        for i in range(0, 10):
            movieItem['also_like_' + str(i + 1) + '_name'] = also_like_names[i]
            movieItem['also_like_' + str(i + 1) + '_url'] = also_like_urls[i]
            # print('also_like_'+str(i + 1) + '_url')
        view_people = response.xpath(
            '//div[contains(@class, "subject-others-interests-ft")]/a/text()').extract()
        movieItem['viewed_num'] = view_people[0]  # test
        movieItem['want_to_view_num'] = view_people[1]

        movieItem['essay_collect_url'] = response.url + '/comments'  # 短评
        movieItem['film_critics_url'] = response.url + '/reviews'  # 影评
        movieItem['doulists_url'] = response.url + '/doulists'  # 豆列

        # inspect_response(response, self)

        # cookie
        if response.xpath('//span[contains(@class, "collection_date")]').extract_first():
            movieItem['view_date'] = response.xpath(
                '//span[contains(@class, "collection_date")]/text()').extract_first()
            movieItem['my_rate'] = response.xpath(
                '//input[contains(@id, "n_rating")]/@value').extract_first()
            movieItem['my_tags'] = response.xpath(
                '//input[contains(@id, "n_rating")]/following::text()[4]').extract_first()

        # # 如果是从豆列过来的
        # if 'fromDoulist' in response.meta:
        #     doulistMovieDetialItem = response.meta['doulistMovieDetialItem']
        #     movieItem['doulists_url'] = doulistMovieDetialItem['doulists_url']
        #     movieItem['comment'] = doulistMovieDetialItem['comment']
        #     movieItem['add_date'] = doulistMovieDetialItem['add_date']

        yield movieItem

        # meta={'cookiejar': response.meta['cookiejar']}
        # request.meta['movieid'] = response.url

        essayCollectRequest = scrapy.Request(movieItem['essay_collect_url'], callback=self.parseComments,
                                             errback=self.errback)
    #     filmCriticsRequest = scrapy.Request(movieItem['film_critics_url'], callback=self.parseReviews,
    #                                         errback=self.errback)

        essayCollectRequest.meta['movieid'] = response.url
    #     filmCriticsRequest.meta['movieid'] = response.url

        yield essayCollectRequest
    #     yield filmCriticsRequest

    #     # 不是从豆列中过来的,就说明是"我看"中的电影,只爬取 我看-豆列-电影这几层
    #     if not in response.meta:
    #         doulistsRequest = scrapy.Request(movieItem['doulists_url'], callback=self.parseDoulists,
    #                                          errback=self.errback)
    #         doulistsRequest.meta['movieid'] = response.url
    #         yield doulistsRequest
    
    # 短评
    def parseComments(self, response):
        movieid = response.meta['movieid']
        # inspect_response(response, self)
        users = response.xpath(
            '//div[contains(@class, "comment-item")]/div/a/@title').extract()
        user_urls = response.xpath(
            '//div[contains(@class, "comment-item")]/div/a/@href').extract()
        vote_nums = response.xpath(
            '//span[contains(@class, "votes")]/text()').extract()
        comment_times = response.xpath(
            '//span[contains(@class, "comment-time ")]/text()').extract()
        comments = response.xpath('//div[@class="comment"]/p/text()').extract()
        comments = list(filter(lambda x: x.strip() != "", comments))

        # 有些没有给出评分的
        comment_rates = response.xpath('//span[@class="comment-info"]')
        
        for i in range(0, len(users)):
            comment = MovieEssayItem()
            comment['movieid'] = movieid
            comment['user_name'] = users[i]
            comment['user_url'] = user_urls[i]
            comment['vote_num'] = vote_nums[i]
            comment['comment_time'] = comment_times[i]
            comment['comment'] = comments[i].strip()
            crs = comment_rates[i].xpath('./span[contains(@class, allstar)]/@title').extract()
            if len(crs)==2:
                comment['comment_rate'] = crs[0]
            yield comment
        global aa
        aa = aa+1
        if aa >20 :
            inspect_response(response, self)
        nextPageURL = response.xpath('//a[@class="next"]/@href').extract_first()
        if nextPageURL:
            commentRequest = scrapy.Request(response.urljoin(nextPageURL), callback=self.parseComments,
                                            errback=self.errback)
            commentRequest.meta['movieid'] = movieid
            yield commentRequest

    # # 影评
    # def parseReviews(self, response):
    #     movieid = response.meta['movieid']
    #     # 当前页面影评URL
    #     reviewsURLs = response.xpath()
    #     for url in reviewsURLs:
    #         request = scrapy.Request(url, callback=self.parseReviewDetail,
    #                                  errback=self.errback)
    #         request.meta['movieid'] = movieid
    #         yield request

    #     nextPageURL = response.xpath()  # 影评下一页
    #     if nextPageURL is not None:
    #         reviewRequest = scrapy.Request(nextPageURL, callback=self.parseReviews,
    #                                        errback=self.errback)
    #         reviewRequest.meta['movieid'] = movieid
    #         yield reviewRequest

    # # 文件储存files/
    # def parseReviewDetail(self, response):
    #     movieid = response.meta['movieid']
    #     filmCriticsItem = FilmCriticsItem()
    #     filmCriticsItem['film_critics_url'] = response.url
    #     # filmCriticsItem['film_critics'] = movieid 这个存文件吧
    #     filmCriticsItem['user_name'] = movieid
    #     filmCriticsItem['user_url'] = movieid
    #     filmCriticsItem['comment_rate'] = movieid
    #     filmCriticsItem['comment_time'] = movieid
    #     filmCriticsItem['useless_num'] = movieid
    #     filmCriticsItem['useful_num'] = movieid
    #     filmCriticsItem['like_num'] = movieid
    #     filmCriticsItem['like_num'] = movieid
    #     filmCriticsItem['reply_num'] = movieid

    # # 豆列
    # def parseDoulists(self, response):
    #     movieid = response.meta['movieid']
    #     # 获取当前页上所有豆列url
    #     # 豆列太多,就不爬取其他页面的豆列了,只找当前列
    #     douListUrls = response.xpath()

    #     # 只找当前页的豆列就好了
    #     for url in douListUrls:
    #         request = scrapy.Request(url, callback=self.parseDoulistDetail,
    #                                  errback=self.errback)
    #         request.meta['movieid'] = movieid
    #         yield request

    # def parseDoulistDetail(self, response):
    #     movieid = response.meta['movieid']
    #     doulistItem = DoulistItem()
    #     doulistItem['movieid'] = movieid
    #     doulistItem['doulist_url'] = movieid
    #     doulistItem['doulist_name'] = movieid
    #     doulistItem['doulist_intr'] = movieid
    #     doulistItem['user_name'] = movieid
    #     doulistItem['user_url'] = movieid
    #     doulistItem['collect_num'] = movieid
    #     doulistItem['recommend_num'] = movieid
    #     doulistItem['doulist_cratedDate'] = movieid
    #     doulistItem['doulist_updatedDate'] = movieid
    #     doulistItem['viewed_num'] = movieid
    #     doulistItem['not_viewed_num'] = movieid
    #     yield doulistItem

    #     # 这里读取出当前页所有电影信息,只取豆列上显示的
    #     # for 循环
    #         doulistMovieDetailItem = DoulistMovieDetailItem()
    #         doulistMovieDetailItem['movieid'] = movieid
    #         doulistMovieDetialItem =
    #         doulistMovieDetialItem['doulists_url'] =
    #         doulistMovieDetialItem['comment'] =
    #         doulistMovieDetialItem['add_date'] =
    #         yield doulistMovieDetailItem

    #     # 进详情页
    #     movieURLList = response.xpath()
    #     for url in movieURLList:
    #         doulistMovieRequest = scrapy.Request(url, callback=self.parseMovieDetial,
    #                                              errback=self.errback)
    #         doulistMovieRequest.meta['fromDoulist'] = true
    #         yield doulistMovieRequest

    #     nextPageURL = response.xpath()  # 豆列下一页
    #     if nextPageURL is not None:
    #         doulistRequest = scrapy.Request(nextPageURL, callback=self.parseDoulistDetail,
    #                                         errback=self.errback)
    #         doulistRequest.meta['movieid'] = movieid
    #         yield reviewRequest

    def errback(self, failure):
        self.logger.error(repr(failure))
        self.logger.error('detail info  : %s ', failure.value)

        # return self.parse(response) #retry

import scrapy
from doubanSpider.transCookie import *
from doubanSpider.items import *
from scrapy.conf import settings
from scrapy.shell import inspect_response
from doubanSpider.logConfig import *
import scrapy.exceptions as exception
import re

class DoubanMoviesSpider(scrapy.Spider):
    name = "doubanmovies"
    allowed_domains = ['douban.com']
# inspect_response(response, self)
    def start_requests(self):
        url = 'https://movie.douban.com/people/99678180/collect'
        logging.info('start_requests %s ', url)
        request = scrapy.Request(url, callback=self.getCollectMovies)
        # 标识是从我个人电影中过来的
        request.meta['fromMyCollect']  = 1
        yield request
        # url = "https://movie.douban.com/subject/10766459/"
        # yield scrapy.Request(url, callback=self.parseMovieDetial,errback=self.errback)

    def getCollectMovies(self, response):
        '''
        个人看过的所有电影列表页
        '''
        # inspect_response(response, self)
        template = 'https://movie.douban.com/subject/'
        itemNodes = response.xpath('//div[@class="item"]/div[@class="info"]/ul')
        for node in itemNodes:
            url = node.xpath('./li[@class="title"]/a/@href').extract_first()
            intro = node.xpath('./li[@class="intro"]/text()').extract_first()
            view_date = node.xpath('./li/span[@class="date"]/text()').extract_first()
            personal_rate = node.xpath('./li/span[contains(@class,"rating")]/@class').extract_first()
            personal_tags = node.xpath('./li/span[@class="tags"]/text()').extract_first()

            if template in url:
                movieBaseItem = MovieBaseInfoItem()
                movieBaseItem['isViewed'] = '0'
                movieBaseItem['movieid'] = self.getMovieid(url)  # 从url中取出movieid
                movieBaseItem['intro'] = intro
                movieBaseItem['view_date'] = view_date
                movieBaseItem['personal_rate'] = personal_rate[6] if personal_rate else None
                movieBaseItem['personal_tags'] = personal_tags[4:] if personal_tags else None
                if 'fromMyCollect' in response.meta: #如果是从我个人电影中过来的
                    movieBaseItem['isViewed'] = '1' #我看过该电影
                    # 只看自己看过的详情页,其他人的就只搜集电影基础信息
                    yield scrapy.Request(url, callback=self.parseMovieDetial,errback=self.errback)
                else:
                    movieBaseItem['isViewed'] = '0'

                yield movieBaseItem
                

        nextPage = response.xpath('//link[@rel="next"]/@href').extract_first()
        if nextPage:
            logging.info('getCollectMovies %s ', response.urljoin(nextPage))
            request =  scrapy.Request(response.urljoin(nextPage), callback=self.getCollectMovies,
                                               errback=self.errback)
            if 'fromMyCollect' in response.meta:
                request.meta['fromMyCollect']  = 1
            yield request

    def parseMovieDetial(self, response):
        '''
        电影详情页
        '''
        logging.info('start crawl MovieDetialItem %s', response.url)

        also_like_urls = response.xpath(
            '(//div[contains(@class, "recommendations-bd")]/dl/dt/a)/@href').extract()
        # 先做检测,看同类推荐,不标准就不爬取页面了
        if not also_like_urls or len(also_like_urls)!=10:
            logging.error("movie %s element miss, do not crawl ",response.url)
            return

        # inspect_response(response, self)
        movieItem =  MovieDetialItem()
        movieItem['movieid'] = self.getMovieid(response.url)  # 从url中取出movieid
        official_site = response.xpath('//a[@rel="nofollow"]/text()').extract()[2]
        movieItem['official_site'] = official_site if "www" in official_site else None
        movieItem['movie_url'] = response.url  
        movieItem['movie_name'] = response.xpath('//span[@property="v:itemreviewed"]/text()').extract_first()
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

        movieItem['storyline']  = "".join(response.xpath('//span[@property="v:summary"]/text()').extract())
        # also_like_urls = response.xpath(
        #     '(//div[contains(@class, "recommendations-bd")]/dl/dt/a)/@href').extract()
        also_like_names = response.xpath(
            '(//div[contains(@class, "recommendations-bd")]/dl/dt/a)//img/@alt').extract()
        for i in range(0, len(also_like_urls)):
            movieItem['also_like_' + str(i + 1) + '_name'] = also_like_names[i]
            movieItem['also_like_' + str(i + 1) + '_url'] = also_like_urls[i]
        view_people = response.xpath(
            '//div[contains(@class, "subject-others-interests-ft")]/a/text()').extract()
        movieItem['viewed_num'] = view_people[0][0:view_people[0].find('人看过')]
        movieItem['want_to_view_num'] = view_people[1][0:view_people[1].find('人想看')]
        movieItem['image_url'] = response.xpath(
            '//img[(@rel = "v:image")]/@src').extract_first()

        movieItem['essay_collect_url'] = response.url + '/comments '  # 短评
        movieItem['film_critics_url'] = response.url + '/reviews '  # 影评
        movieItem['doulists_url'] = response.url + '/doulists'  # 豆列
        yield movieItem

        # 短评
        essayCollectRequest = scrapy.Request(movieItem['essay_collect_url'], callback=self.parseComments,
                                             errback=self.errback)
        # 影评
        filmCriticsRequest = scrapy.Request(movieItem['film_critics_url'], callback=self.parseReviews,
                                            errback=self.errback)

        essayCollectRequest.meta['movieid'] = movieItem['movieid']
        filmCriticsRequest.meta['movieid'] = movieItem['movieid']
        yield essayCollectRequest
        yield filmCriticsRequest

        # 不是从豆列中过来的,就说明是自己看过的电影,爬取对应豆列;
        # 从豆列中过来的电影就不爬了,只爬取 我看-豆列-电影这几层
        if 'fromDoulist' not in response.meta:
            doulistsRequest = scrapy.Request(movieItem['doulists_url'],  callback=self.parseDoulists,
                                             errback=self.errback)
            doulistsRequest.meta['movieid'] = movieItem['movieid']
            yield doulistsRequest

    
    def parseComments(self, response):
        '''
        短评
        '''
        movieid = response.meta['movieid']
        commentItems =  response.xpath('//div[@class="comment"]')
        for ci in commentItems:
            comment = MovieEssayItem()
            comment['movieid'] = movieid
            comment['user_name'] = ci.xpath('./h3/span[@class="comment-info"]/a/text()').extract_first()
            comment['user_url'] = ci.xpath('./h3/span[@class="comment-info"]/a/@href').extract_first()
            comment['comment_time'] = ci.xpath('.//span[contains(@class, "comment-time ")]/text()').extract_first()
            comment['comment'] = ci.xpath('./p/text()').extract_first()
            comment['comment_rate'] = ci.xpath('.//span[contains(@class, allstar)]/@title').extract_first()
            yield comment

        nextPageURL = response.xpath(
            '//a[@class="next"]/@href').extract_first()
        if nextPageURL:
            commentRequest = scrapy.Request(response.urljoin(nextPageURL), callback=self.parseComments,
                                            errback=self.errback)
            commentRequest.meta['movieid'] = movieid
            yield commentRequest

    def parseReviews(self, response):
        '''
        影评
        '''
        movieid = response.meta['movieid']
        # 当前页面影评URL
        reviewsid = response.xpath(
            '//div[@class="review-short"]/@data-rid').extract()
        for rid in reviewsid:
            request = scrapy.Request("https://movie.douban.com/review/" + rid + "/",  callback=self.parseReviewDetail,
                                     errback=self.errback)
            request.meta['movieid'] = movieid
            yield request

        nextPage = response.xpath('//span[@class="next"]/a/@href').extract_first()
        if nextPage:
            logging.info('nextPage:%s', nextPage)
            reviewRequest = scrapy.Request(response.urljoin(nextPage), callback=self.parseReviews, 
                                           errback=self.errback)
            reviewRequest.meta['movieid'] = movieid
            yield reviewRequest

    def parseReviewDetail(self, response):
        '''
        影评详情页
        '''
        movieid = response.meta['movieid']
        filmCriticsItem = FilmCriticsItem()
        filmCriticsItem['movieid'] = movieid
        filmCriticsItem['film_critics_url'] = response.url
        filmCriticsItem['title'] = response.xpath(
            '//span[@property="v:summary"]/text()').extract_first()
        filmCriticsItem['review'] = ''.join(response.xpath(
            '//div[@property="v:description"]//text()').extract())
        filmCriticsItem['user_name'] = response.xpath(
            '//span[@property="v:reviewer"]/text()').extract_first()
        filmCriticsItem['user_url'] = response.xpath(
            '//header[@class="main-hd"]/a/@href').extract_first()
        filmCriticsItem['comment_rate'] = response.xpath('//span[@property="v:rating"]/text()').extract_first()
        filmCriticsItem['comment_time'] = response.xpath(
            '//span[@property="v:dtreviewed"]/text()').extract_first()
        useless_num = response.xpath('//button[contains(@class, useless_count)]/text()').extract()[1].strip()
        useful_num = response.xpath('//button[contains(@class, useful_count)]/text()').extract_first().strip()
        recommend_num = response.xpath('//span[@class="rec"]/a/text()').extract_first().strip()
        filmCriticsItem['useless_num'] = self.getNum(useless_num, " ")
        filmCriticsItem['useful_num'] = self.getNum(useful_num, " ")
        filmCriticsItem['recommend_num'] = self.getNum(recommend_num, " ")
        yield filmCriticsItem

    def parseDoulists(self, response):
        '''
        豆列
        '''
        movieid = response.meta['movieid']
        # 豆列太多,就不爬取其他页面的豆列了,只找当前页面的
        douListUrls = response.xpath('//li[@class="pl2"]/a/@href').extract()

        for url in douListUrls:
            requestDoulistDetail = scrapy.Request(url, callback=self.parseDoulistDetail,
                                                  errback=self.errback)
            requestDoulistDetail.meta['movieid'] = movieid
            yield requestDoulistDetail

    def parseDoulistDetail(self, response):
        '''
        豆列详情
        '''
        movieid = response.meta['movieid']
        
        if 'fromDoulist' not in response.meta:
            doulistItem = DoulistItem()
            doulistItem['movieid'] = movieid
            doulistItem['doulist_url'] = response.url
            doulistItem['doulist_name'] = response.xpath(
                '//div[@id="content"]/h1/text()').extract_first()
            doulist_intr = response.xpath('//div[@class="doulist-about"]/text()').extract()
            doulistItem['doulist_intr'] = ''.join(doulist_intr) if doulist_intr else ""
            doulistItem['user_name'] = response.xpath(
                '//div[@class="meta"]/a/text()').extract_first()
            doulistItem['user_url'] = response.xpath(
                '//div[@class="meta"]/a/@href').extract_first()
            doulistItem['collect_num'] = response.xpath(
                '//a[@class="doulist-followers-link"]/text()').extract_first()
            time = response.xpath('//span[@class="time"]/text()').extract_first().strip().split('\n            \xa0\xa0')
            doulistItem['doulist_cratedDate'] = time[0][0:-2]
            doulistItem['doulist_updatedDate'] = time[1][0:-2]
            recommend_num = response.xpath('//span[@class="rec-num"]/text()').extract_first()
            doulistItem['recommend_num'] = recommend_num[0:-1] if  recommend_num else 0
            doulistItem['movie_num']  = response.xpath('//div[@class="doulist-filter"]/a/span/text()').extract_first()[1:-1]
            yield doulistItem

        movie_urls = response.xpath('//div[@class="title"]/a/@href').extract()
        movie_names = response.xpath(
            '//div[@class="title"]/a/text()').extract()

        # 这里读取出当前页所有电影信息,只取豆列上显示的
        for i in range(0, len(movie_urls)) :
            if 'subject'  in movie_urls[i]:
                doulistMovieDetailItem = DoulistMovieDetailItem()
                doulistMovieDetailItem['movieid'] = self.getMovieid(movie_urls[i])
                doulistMovieDetailItem['doulist_url'] = response.url
                yield doulistMovieDetailItem

        # 进详情页
        for url in movie_urls:
            doulistMovieRequest = scrapy.Request(url,  callback=self.parseMovieDetial,
                                                 errback=self.errback)
            doulistMovieRequest.meta['fromDoulist'] = '1'
            yield doulistMovieRequest

        nextPageURL = response.xpath(
            '//span[@class="next"]/a/@href').extract_first()
        if nextPageURL:
            doulistRequest = scrapy.Request(nextPageURL, callback=self.parseDoulistDetail,
                                            errback=self.errback)
            doulistRequest.meta['fromDoulist'] = '1'
            doulistRequest.meta['movieid'] = movieid
            yield doulistRequest

    def errback(self, failure):
        logging.error(repr(failure))
        logging.error('detail info  : %s ', failure.value)

    def getMovieid(self, url):
        logging.info("getMovieid: %s ",url)
        return re.findall(r"(?<=/subject/)\d+(?=/)", url).pop()

    def getNum(self, strv, seperate):
        num  = 0
        if len(strv) > 3:
            num = strv[strv.find(" ")+1:len(strv)]
        return num
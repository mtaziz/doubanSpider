import scrapy
from doubanSpider.transCookie import *
from doubanSpider.items import *
from scrapy.conf import settings
from scrapy.shell import inspect_response
from doubanSpider.logConfig import *
import scrapy.exceptions as exception
import re

# Scrapy定向爬虫教程(五)——保持登陆状态 : https://blog.csdn.net/qq_30242609/article/details/52822190
# https://juejin.im/post/5a41a76b6fb9a04512393101
# https://www.xncoding.com/2016/04/12/scrapy-11.html
# 文件图片储存 https://www.xncoding.com/2016/03/20/scrapy-08.html

# 登录https://blog.csdn.net/qq_41020281/article/details/79437455


class DoubanMoviesSpider(scrapy.Spider):
    name = "doubanmovies"
    allowed_domains = ['douban.com']
# inspect_response(response, self)
    def start_requests(self):
        url = 'https://movie.douban.com/people/99678180/collect'
        # url = 'https://movie.douban.com/subject/4920389/'
        logging.info('start_requests %s ', url)
        yield scrapy.Request(url, callback=self.getCollectMovies)
        # yield scrapy.Request(url, callback=self.parseMovieDetial)


    def getCollectMovies(self, response):
        links = response.xpath('//li[@class="title"]/a/@href').extract()
        template = 'https://movie.douban.com/subject/'
        for url in links:
            if template in url:
                yield scrapy.Request(url, callback=self.parseMovieDetial)

        nextPage = response.xpath('//link[@rel="next"]/@href').extract_first()
        if nextPage:
            logging.info('getCollectMovies %s ', response.urljoin(nextPage))
            yield scrapy.Request(response.urljoin(nextPage), callback=self.getCollectMovies,
                                               errback=self.errback)

    def parseMovieDetial(self, response):
        logging.info('start crawl MovieDetialItem %s', response.url)

        also_like_urls = response.xpath(
            '(//div[contains(@class, "recommendations-bd")]/dl/dt/a)/@href').extract()
        if not also_like_urls or len(also_like_urls)!=10:
            logging.error("movie %s element miss, do not crawl ",response.url)
            return
        # inspect_response(response, self)
        movieItem = MovieDetialItem()
        official_site = response.xpath('//a[@rel="nofollow"]/text()').extract()[2]
        movieItem['official_site'] = official_site if "www" in official_site else None
        movieItem['movieid'] = self.getMovieid(response.url)  # 从url中取出movieid
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
        movieItem['storyline']  = response.xpath(
            '//span[contains(@property, "v:summary")]/text()').extract_first()

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

        # if response.xpath('//span[contains(@class, "collection_date")]').extract_first():
        movieItem['isViewed'] = '0' if 'fromDoulist' in response.meta else '1'
        yield movieItem

        essayCollectRequest = scrapy.Request(movieItem['essay_collect_url'], callback=self.parseComments,
                                             errback=self.errback)
        filmCriticsRequest = scrapy.Request(movieItem['film_critics_url'], callback=self.parseReviews,
                                            errback=self.errback)

        essayCollectRequest.meta['movieid'] = movieItem['movieid']
        filmCriticsRequest.meta['movieid'] = movieItem['movieid']
        yield essayCollectRequest
        yield filmCriticsRequest

        # 不是从豆列中过来的,就说明是"我看"中的电影,只爬取 我看-豆列-电影这几层
        if 'fromDoulist' not in response.meta:
            doulistsRequest = scrapy.Request(movieItem['doulists_url'],  callback=self.parseDoulists,
                                             errback=self.errback)
            doulistsRequest.meta['movieid'] = movieItem['movieid']
            yield doulistsRequest

    # 短评
    def parseComments(self, response):
        movieid = response.meta['movieid']
        users = response.xpath('//div[contains(@class, "comment-item")]/div/a/@title').extract()
        user_urls = response.xpath('//span[@class="comment-info"]/a/@href').extract()
        vote_nums = response.xpath('//span[contains(@class, "votes")]/text()').extract()
        comment_times = response.xpath(
            '//span[contains(@class, "comment-time ")]/text()').extract()
        comments = response.xpath('//div[@class="comment"]/p/text()').extract()
        comments = list(filter(lambda x: x.strip() != "", comments))

        # 有些没有给出评分的
        comment_rates = response.xpath('//span[@class="comment-info"]')
        if len(users) != len(vote_nums) or len(users) != len(comments) or len(users) != len(comment_times) :
            logging.error('comment item do not match: %s ',response.url)
        for i in range(0, len(users)):
            comment = MovieEssayItem()
            comment['movieid'] = movieid
            comment['user_name'] = users[i]
            comment['user_url'] = user_urls[i]
            comment['vote_num'] = vote_nums[i]
            comment['comment_time'] = comment_times[i]
            comment['comment'] = comments[i]
            crs = comment_rates[i].xpath('./span[contains(@class, allstar)]/@title').extract()
            comment['comment_rate'] = crs[0] if len(crs) == 2 else 0
            yield comment

        nextPageURL = response.xpath(
            '//a[@class="next"]/@href').extract_first()
        if nextPageURL:
            commentRequest = scrapy.Request(response.urljoin(nextPageURL), callback=self.parseComments,
                                            errback=self.errback)
            commentRequest.meta['movieid'] = movieid
            yield commentRequest

    # 影评
    def parseReviews(self, response):
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

    # 文件储存files
    def parseReviewDetail(self, response):
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

    # 豆列
    def parseDoulists(self, response):
        movieid = response.meta['movieid']
        # 豆列太多,就不爬取其他页面的豆列了,只找当前列
        douListUrls = response.xpath('//li[@class="pl2"]/a/@href').extract()

        # 只找当前页的豆列就好了
        for url in douListUrls:
            requestDoulistDetail = scrapy.Request(url, callback=self.parseDoulistDetail,
                                                  errback=self.errback)
            requestDoulistDetail.meta['movieid'] = movieid
            yield requestDoulistDetail

    def parseDoulistDetail(self, response):
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

        # return self.parse(response) #retry

    def getMovieid(self, url):
        logging.info("getMovieid: %s ",url)
        return re.findall(r"(?<=/subject/)\d+(?=/)", url).pop()

    def  getNum(self, strv, seperate):
        num  = 0
        if len(strv) > 3:
            num = strv[strv.find(" ")+1:len(strv)]
        return num


# todo
# HttpError: Ignoring non-200 response>

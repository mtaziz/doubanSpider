# -*- coding: utf-8 -*-
import scrapy


class MovieBase(scrapy.Item):
    movieid = scrapy.Field()  # 这是豆瓣的movieid
    movie_url = scrapy.Field()
    movie_name = scrapy.Field()


class MovieDetialItem(MovieBase):
    director = scrapy.Field()
    writers = scrapy.Field()
    stars = scrapy.Field()
    genres = scrapy.Field()  # 爱情/同性
    country = scrapy.Field()
    language = scrapy.Field()
    release_date = scrapy.Field()
    runtime = scrapy.Field()
    also_known_as = scrapy.Field()
    IMDb_url = scrapy.Field()
    douban_rate = scrapy.Field()
    rate_num = scrapy.Field()
    star_5 = scrapy.Field()
    star_4 = scrapy.Field()
    star_3 = scrapy.Field()
    star_2 = scrapy.Field()
    star_1 = scrapy.Field()
    comparison_1 = scrapy.Field()
    comparison_2 = scrapy.Field()
    storyline = scrapy.Field()
    also_like_1_name = scrapy.Field()
    also_like_1_url = scrapy.Field()
    also_like_2_name = scrapy.Field()
    also_like_2_url = scrapy.Field()
    also_like_3_name = scrapy.Field()
    also_like_3_url = scrapy.Field()
    also_like_4_name = scrapy.Field()
    also_like_4_url = scrapy.Field()
    also_like_5_name = scrapy.Field()
    also_like_5_url = scrapy.Field()
    also_like_6_name = scrapy.Field()
    also_like_6_url = scrapy.Field()
    also_like_7_name = scrapy.Field()
    also_like_7_url = scrapy.Field()
    also_like_8_name = scrapy.Field()
    also_like_8_url = scrapy.Field()
    also_like_9_name = scrapy.Field()
    also_like_9_url = scrapy.Field()
    also_like_10_name = scrapy.Field()
    also_like_10_url = scrapy.Field()
    prize = scrapy.Field()  # 直接把结构化数据仍在一起吧
    essay_collect_url = scrapy.Field()
    film_critics_url = scrapy.Field()
    doulists_url = scrapy.Field()
    viewed_num = scrapy.Field()
    want_to_view_num = scrapy.Field()
    view_date = scrapy.Field()
    my_rate = scrapy.Field()
    my_tags = scrapy.Field()
    tags = scrapy.Field()

# 短评
class MovieEssayItem(MovieBase):
    user_name = scrapy.Field()
    user_url = scrapy.Field()
    vote_num = scrapy.Field()
    comment_rate = scrapy.Field()
    comment_time = scrapy.Field()
    comment = scrapy.Field()

# 影评,默认将影评内容存储在文件中
# 以film_critics_url:::内容的形式储存
class FilmCriticsItem(MovieBase):
    film_critics_url = scrapy.Field()
    title = scrapy.Field()
    user_name = scrapy.Field()
    user_url = scrapy.Field()
    comment_rate = scrapy.Field()
    comment_time = scrapy.Field()
    useless_num = scrapy.Field()
    useful_num = scrapy.Field()
    # like_num = scrapy.Field()
    reply_num = scrapy.Field()
    review = scrapy.Field()
    recommend_num = scrapy.Field()

# 豆列
class DoulistItem(MovieBase):
    doulist_url = scrapy.Field()  # 当前豆列url
    doulist_name = scrapy.Field()
    doulist_intr = scrapy.Field()  # 简介
    user_name = scrapy.Field()
    user_url = scrapy.Field()
    collect_num = scrapy.Field()  # 收藏数
    recommend_num = scrapy.Field()  # 推荐数
    doulist_cratedDate = scrapy.Field()
    doulist_updatedDate = scrapy.Field()
    viewed_num = scrapy.Field()
    not_viewed_num = scrapy.Field()

# 豆列单项
class DoulistMovieDetailItem(MovieBase):
    doulist_url = scrapy.Field()
    comment = scrapy.Field()


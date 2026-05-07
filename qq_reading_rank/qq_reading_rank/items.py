# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class QqReadingRankItem(scrapy.Item):
    rank = scrapy.Field()
    book_url = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    update_time = scrapy.Field()
    tags = scrapy.Field()
    intro = scrapy.Field()

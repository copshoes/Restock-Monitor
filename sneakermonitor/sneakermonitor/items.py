import scrapy


class Sneaker(scrapy.Item):
    name = scrapy.Field()
    description = scrapy.Field()
    image = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    url = scrapy.Field()
    available = scrapy.Field()
    stock = scrapy.Field()
    sizes = scrapy.Field()
    tag = scrapy.Field()

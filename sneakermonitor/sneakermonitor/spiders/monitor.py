import scrapy
from twisted.internet import reactor
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy_splash import SplashRequest
from scrapy.http import Request
from scrapy.selector import Selector
from urlparse import urlparse
import jsonfinder
import re
import os.path
import tldextract
import random


class Monitor(scrapy.Spider):
    name = "monitor"
    settings = get_project_settings()
    url_file = "/../../urls.txt"
    non_shopify_file = r"/../../nonshopify.txt"
    bots_file = r"/../../bots.txt"
    page = 1

    # Load url list and start scraping
    def start_requests(self):
        urls = list()
        non_shopify_list = list()
        bots_list = list()

        # Get all urls to scrape
        with open(os.path.dirname(__file__) + self.url_file, "rt") as f:
            urls = [url.strip() for url in f.readlines()]

        # Supported non shopify sites list
        with open(os.path.dirname(__file__) + self.non_shopify_file, "rt") as f:
            non_shopify_list = [url.strip() for url in f.readlines()]

        # Supported bots sites list
        with open(os.path.dirname(__file__) + self.bots_file, "rt") as f:
            bots_list = [url.strip() for url in f.readlines()]

        for url in urls:
            t = tldextract.extract(url)
            root = t.domain + '.' + t.suffix
            proxy_enabled = self.settings.get('PROXY_ENABLED')
            adidas_proxy_enabled = self.settings.get('ADIDAS_PROXY_ENABLED')

            # Adidas site (uses scrapy-splash)
            if "adidas.com" in url:
                # With proxy
                if adidas_proxy_enabled:
                    yield SplashRequest(url, self.adidas_parse, headers=self.adidas_headers(),
                                        args={'images_enabled': 'false', 'proxy': self.random_proxy()})
                
                # Without proxy
                else:
                    yield SplashRequest(url, self.adidas_parse, headers=self.adidas_headers(),
                                        args={'images_enabled': 'false'})

            # Non shopify site
            elif any(root in s for s in non_shopify_list):
                # With proxy
                if proxy_enabled:
                    yield scrapy.Request(url, self.non_shoify, meta={'proxy': self.random_proxy()})

                # Without proxy
                else:
                    yield scrapy.Request(url, self.non_shoify)

            # Bots
            elif any(root in s for s in bots_list):
                # With proxy
                if proxy_enabled:
                    yield scrapy.Request(url, self.bots_parse, meta={'proxy': self.random_proxy()})
                
                # Without proxy
                else:
                    yield scrapy.Request(url, self.bots_parse)

            # Shopify sites
            else:
                # With proxy
                if proxy_enabled:
                    yield scrapy.Request(url, self.shopify_parse, meta={'proxy': self.random_proxy()})
                
                # Without proxy
                else:
                    yield scrapy.Request(url, self.shopify_parse)


    # Adidas headers with random useragents
    def adidas_headers(self):

        # Get useragent list
        with open(self.settings.get('USER_AGENT_LIST'), "r") as f:
            useragents = [url.strip() for url in f.readlines()]

        adidas_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Host": "www.adidas.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": random.choice(useragents)
        }
        
        return adidas_headers

    def random_proxy(self):
        # Get proxy list
        with open(self.settings.get('PROXY_LIST'), "r") as f:
            n = sum(1 for line in f if line.rstrip('\n'))
            rand_proxy = f.readlines()[random.randint(1, n)].rstrip('\n')
            ip, port, user, pw = rand_proxy.split(':')
            proxy = 'http://' + user + ':' + pw + '@' + ip + ':' + port
        return proxy

    # Adidas
    def adidas_parse(self, response):
        products = response.xpath('//*[@id="hc-container"]/div')

        for product in products:
            # If product don't have comming soon tag, scrape
            tag = product.xpath(
                "./div[2]/div[3]/div[2]/span/text()").extract_first()
            if "coming soon" not in tag.lower().strip():
                sneaker = Sneaker()
                root_url = "https://www.adidas.com"

                data = product.xpath("./div/@data-context").extract_first()

                # Name
                m = re.search('name:(.*);', data)
                sneaker["name"] = m.group(1)

                # Model
                m = re.search('model:(.*)', data)
                description = 'Model: ' + m.group(1)

                # Id
                m = re.search('id:(.*);name', data)
                description += ' ID: ' + m.group(1)

                sneaker["description"] = description

                sneaker["image"] = product.xpath(
                    "./div[2]/div[3]/div[3]/a/img[1]/@data-original").extract_first()

                sneaker["currency"] = product.xpath(
                    "./div[2]/div[3]/div[4]/div[4]/div/span[1]/text()").extract_first().strip()

                sneaker["price"] = product.xpath(
                    "./div[2]/div[3]/div[4]/div[4]/div/span[2]/text()").extract_first().strip()

                url = product.xpath(
                    "./div[2]/div[3]/div[3]/a/@href").extract_first()
                sneaker["url"] = root_url + url

                sneaker["tag"] = 'adidas'

                yield sneaker

        self.page += 120
        if products:
            next_page = "http://www.adidas.com/us/men-shoes?sz=120&start=" + str(self.page)

            # With proxy
            if self.settings.get('ADIDAS_PROXY_ENABLED'):
                yield SplashRequest(next_page, self.adidas_parse, headers=self.adidas_headers(),
                                    args={'images_enabled': 'false', 'proxy': self.random_proxy()})
            
            # Without proxy
            else:
                yield SplashRequest(next_page, self.adidas_parse, headers=self.adidas_headers(),
                                    args={'images_enabled': 'false'})


    # Adidas product (accepts selector instead of response)
    def adidas_parse_product(self, product):
        sneaker = Sneaker()
        root_url = "https://www.adidas.com"

        data = product.xpath("./div/@data-context").extract_first()

        # Name
        m = re.search('name:(.*);', data)
        sneaker["name"] = m.group(1)

        # Model
        m = re.search('model:(.*)', data)
        description = 'Model: ' + m.group(1)

        # Id
        m = re.search('id:(.*);name', data)
        description += ' ID: ' + m.group(1)

        sneaker["description"] = description

        sneaker["image"] = product.xpath(
            "./div[2]/div[3]/div[3]/a/img[1]/@data-original").extract_first()

        sneaker["currency"] = product.xpath(
            "./div[2]/div[3]/div[4]/div[4]/div/span[1]/text()").extract_first().strip()

        sneaker["price"] = product.xpath(
            "./div[2]/div[3]/div[4]/div[4]/div/span[2]/text()").extract_first().strip()

        url = product.xpath(
            "./div[2]/div[3]/div[3]/a/@href").extract_first()
        sneaker["url"] = root_url + url

        sneaker["tag"] = 'adidas'

        yield sneaker

    # Shopify
    def shopify_parse(self, response):

        url = response.url
        if url.endswith('/'):
            url = url.rstrip('/')

        o = urlparse(url)

        products = response.xpath(
            "//a[contains(@href, '/products/')]/@href").extract()

        # remove image urls
        for product in products[:]:
            if "cdn.shopify" in product:
                products.remove(product)

        for product in products:
            yield scrapy.Request(response.urljoin(product), self.shopify_parse_product)

        self.page += 1
        if products:
            next_page = o.path + "?page=" + str(self.page)
            yield scrapy.Request(response.urljoin(next_page), self.shopify_parse)

    # Shopify product
    def shopify_parse_product(self, response):
        sneaker = Sneaker()

        # name
        sneaker["name"] = response.xpath(
            "//meta[@property='og:title']/@content").extract_first()

        # description
        sneaker["description"] = response.xpath(
            "//meta[@name='description']/@content").extract_first()

        # image
        sneaker["image"] = response.xpath(
            "//meta[@property='og:image']/@content").extract_first()

        # price
        sneaker["price"] = response.xpath(
            "//meta[@property='og:price:amount']/@content").extract_first()

        # currency
        sneaker["currency"] = response.xpath(
            "//meta[@property='og:price:currency']/@content").extract_first()

        # URL
        sneaker['url'] = response.url
        sneaker['tag'] = "shopify"

        sizes = list()
        stock = 0

        # find stock details part
        script = response.xpath(
            "//script[contains(text(), 'inventory_quantity')]").extract_first()

        # if stock details found get stock details
        if script:
            script = re.sub(' +', ' ', script)
            raw_json = None
            try:
                raw_json = re.search("({\"id\".*})", script).group(0)
            except:
                pass

            if raw_json:
                json = jsonfinder.only_json(
                    re.search("({.*})", raw_json).group(0))[2]

                sneaker['available'] = json['available']

                for size in json['variants']:
                    size_str = str(size['option1']) + ' / Stock: ' + str(
                        size['inventory_quantity'])

                    stock += int(size['inventory_quantity'])
                    sizes.append(size_str)

        # else just find out if add to cart button is there
        else:
            add_to_cart = None
            try:
                add_to_cart = response.xpath(
                    "//*[@name='add' and @type='submit']").extract_first()
            except:
                pass

            if add_to_cart is None:
                sneaker['available'] = False
            else:
                sneaker['available'] = True

        sneaker['sizes'] = sizes
        sneaker['stock'] = stock

        return sneaker

    # Bots availability checker
    def bots_parse(self, response):
        t = tldextract.extract(response.url)
        bot = Sneaker()

        bot["name"] = response.xpath(
            "//meta[@property='og:title']/@content").extract_first()
        bot["description"] = response.xpath(
            "//meta[@name='description']/@content").extract_first()
        bot["image"] = response.xpath(
            "//meta[@property='og:image']/@content").extract_first()
        bot["price"] = response.xpath(
            "//meta[@property='og:price:amount']/@content").extract_first()
        bot["currency"] = response.xpath(
            "//meta[@property='og:price:currency']/@content").extract_first()
        bot['url'] = response.url
        bot['tag'] = 'bot'

        availability = response.xpath(
            '//span[contains(@id, "AddToCartText")]/text()').extract_first()

        # If bot is avaialable
        if "sold out" not in availability.lower().strip():
            bot['available'] = True
        else:
            bot['available'] = False

        return bot

    # Non shopify sites
    def non_shoify(self, response):
        t = tldextract.extract(response.url)
        root = t.domain + '.' + t.suffix

        if "footshop.com" in root:
            products = Selector(response).xpath(
                '//div[@class="col-xs-6 col-md-4 col-lg-3"]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('a/@title').extract()[0]
                item['url'] = product.xpath('a/@href').extract()[0]
                # item['image'] = product.xpath('a/div/img/@data-src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "caliroots.com" in root:
            products = Selector(response).xpath(
                '//ul[@class="product-list row"]//li[contains(@class,"product")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('.//a/p[2]/text()').extract()[0]
                item['url'] = "https://caliroots.com" + \
                    product.xpath('.//a/@href').extract()[0]
                # item['image'] = product.xpath('.//a/div/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "size.co.uk" in root:
            products = Selector(response).xpath(
                '//ul[@class="listProducts productList"]//li[contains(@class,"productListItem")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath(
                    './/span/span/span/a/text()').extract()[0]
                item['url'] = "https://www.size.co.uk" + \
                    product.xpath('.//span/span/span/a/@href').extract()[0]
                # item['image'] = product.xpath('.//span/a/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "jdsports.co.uk" in root:
            products = Selector(response).xpath(
                '//ul[@class="listProducts productList"]//li[contains(@class,"productListItem")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath(
                    './/span/a/img/@title').extract()[0]
                item['url'] = "https://www.jdsports.co.uk" + \
                    product.xpath('.//span/a/@href').extract()[0]
                # item['image'] = product.xpath('.//span/a/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "5pointz.co.uk" in root:
            products = Selector(response).xpath(
                '//ol[@class="listing listing--grid"]//li[contains(@class,"listing-item")]//article//figure')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('a/@title').extract()[0]
                item['url'] = product.xpath('a/@href').extract()[0]
                # item['image'] = product.xpath('a/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "footasylum.com" in root:
            products = Selector(response).xpath(
                '//div[@class="productDataOnPage_inner"]//ul[@class="main-list row"]//li[contains(@class,"left")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath(
                    'div/span[2]/img/@alt').extract()[0]
                item['url'] = product.xpath('div/span[1]/text()').extract()[0]
                # item['image'] = "https://www.footasylum.com" + product.xpath('div/span[2]/img/@data-original').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "asphaltgold.de" in root:
            products = Selector(response).xpath(
                '//div[@class="product-grid"]//section[contains(@class,"item")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('a/@title').extract()[0]
                item['url'] = product.xpath('a/@href').extract()[0]
                # item['image'] = product.xpath('a/img//@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "wellgosh.com" in root:
            products = Selector(response).xpath(
                '//div[@class="category-products row grid-mode"]//article[contains(@class,"small-6")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('.//figure/a/@title').extract()[0]
                item['url'] = product.xpath('.//figure/a/@href').extract()[0]
                # item['image'] = product.xpath('.//figure/a/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "hypedc.com" in root:
            products = Selector(response).xpath(
                '//div[@class="category-products row"]//div[contains(@class,"item")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('.//a/@title').extract()[0]
                item['url'] = product.xpath('.//a/@href').extract()[0]
                # item['image'] = product.xpath('.//a/div/img/@data-src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "bstnstore.com" in root:
            products = Selector(response).xpath(
                '//ul[@class="block-grid four-up mobile-two-up productlist"]//li[contains(@class,"item")]//div[@class="itemWrapper pOverlay"]//div[@class="pImageContainer"]//a[@class="plink image"]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('div/@data-alt').extract()[0]
                item['url'] = "https://www.bstnstore.com" + \
                    product.xpath('@href').extract()[0]
                # item['image'] = "https://www.bstnstore.com" + product.xpath('div/div[2]/@data-src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "allikestore.com" in root:
            products = Selector(response).xpath(
                '//ul[@class="products-grid"]//li[contains(@class,"item")]//div[@class="item-wrap"]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('a/@title').extract()[0]
                item['url'] = product.xpath('a/@href').extract()[0]
                # item['image'] = product.xpath('a/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "back-door.it" in root:
            products = Selector(response).xpath(
                '//ul[@class="products clearfix"]//li')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('a[1]/h6/text()').extract()[0]
                item['url'] = product.xpath('a[1]/@href').extract()[0]
                # item['image'] = product.xpath('div/a[2]/span/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "mrporter.com" in root:
            products = Selector(response).xpath(
                '//div[@class="pl-grid__column pl-grid__column--main"]//ul[@class="pl-products"]//li[contains(@class,"pl-products-item")]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath(
                    'a/div[2]/div/span[2]/text()').extract()[0].replace(" Sneakers", "")
                item['url'] = "https://www.mrporter.com" + \
                    product.xpath('a/@href').extract()[0]
                # item['image'] = product.xpath('a/div[1]/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "titolo.ch" in root:
            products = Selector(response).xpath(
                '//ul[@class="small-block-grid-2 medium-block-grid-3 large-block-grid-4 no-bullet"]//li[contains(@class,"item")]//div[@class="list-inner-wrapper"]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('a/@title').extract()[0]
                item['url'] = product.xpath('a/@href').extract()[0]
                # item['image'] = product.xpath('div[1]/a/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

        elif "xileclothing.com" in root:
            products = Selector(response).xpath(
                '//ul[@class="itemsList"]/li/div[1]')

            for product in products:
                item = Sneaker()
                item['name'] = product.xpath('a/img/@alt').extract()[0]
                item['url'] = product.xpath('a/@href').extract()[0]
                # item['image'] = "https://www.xileclothing.com" + product.xpath('a/img/@src').extract()[0]
                # item['size'] = '**NOT SUPPORTED YET**'
                yield item

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


process = CrawlerProcess(settings=get_project_settings())

def crawl():
    d = process.crawl(Monitor)
    d.addBoth(crawl_done)

def crawl_done(error):
    crawl()

crawl()
reactor.run()

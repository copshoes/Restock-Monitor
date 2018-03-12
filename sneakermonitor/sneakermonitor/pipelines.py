import pymongo
from scrapy.conf import settings
from scrapy.exceptions import DropItem
from slack import Slack
import os.path


class SneakermonitorPipeline(object):
    def process_item(self, item, spider):
        return item

# Filters old or unchanged products and notify for new or restocks
class FilterPipeline(object):
    keywords_file = "/../keywords.txt"
    keywords = list()
    slack = Slack()

    with open(os.path.dirname(__file__) + keywords_file) as file:
        for keyword in file:
            keywords.append(keyword.strip().lower())

    mongo_collection = "products"

    # Initialize connection settings
    def __init__(self):
        self.server = settings['MONGO_SERVER']
        self.port = settings['MONGO_PORT']

    # Open connection to database
    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.server, self.port)
        self.db = self.client[settings['MONGO_DB']]
        self.collection = self.db[self.mongo_collection]

    # Close connection to database
    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.url = item['url']
        self.product = self.collection.find_one({"url": self.url})

        tag = ""
        try:
            tag = item['tag']
        except:
            pass
        description = ""
        try:
            description = item['description']
        except:
            pass

        # if product already in database
        if self.product is not None:
            availablity = ""
            try:
                availablity = item['available']
            except:
                pass

            # if it was unavailable before but available now
            if availablity is True and self.product['available'] is False:
                # Item is sneaker
                if 'bot' not in tag:
                    text = item['name'] + " - " + description
                    for keyword in self.keywords:
                        if keyword in text.lower():
                            self.slack.post(item, keyword)
                            return item

                # Item is a bot product
                else:
                    # Availability already checked on parent if clause, so just notify
                    self.slack.post(item, "")
                    return item
                return item

            # or was available before but not now, return item to update
            elif availablity is False and self.product['available'] is True:
                return item
            elif availablity is None:
                return item
            else:
                raise DropItem("No changes in %s" % item['url'])

        # if a new product found
        else:
            # If item is sneaker
            if 'bot' not in tag:
                # if keyword matches, show notification
                text = item['name'] + " - " + description
                for keyword in self.keywords:
                    if keyword in text.lower():
                        self.slack.post(item, keyword)
                        return item

            # If item is a bot product
            else:
                if item['available']:
                    self.slack.post(item, "")
                    return item
            return item


# Save or update product in mongo database
class MongoSavePipeline(object):

    mongo_collection = "products"

    def __init__(self):
        self.server = settings['MONGO_SERVER']
        self.port = settings['MONGO_PORT']

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.server, self.port)
        self.db = self.client[settings['MONGO_DB']]
        self.collection = self.db[self.mongo_collection]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.url = item['url']
        self.product = self.collection.find_one({"url": self.url})

        # if product already in database, update
        if self.product is not None:
            try:
                self.collection.replace_one({"url": self.url}, dict(item))
            except:
                pass

        # product not in database, add
        else:
            self.collection.insert_one(dict(item))
        return item

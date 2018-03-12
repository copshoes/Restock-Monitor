import json
import requests
from urlparse import urlparse
import os.path


class Slack():

    # Add different slack channel's web hook url here:
    channels = {
        "supreme": "https://hooks.slack.com/services/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",
        "adidas": "https://hooks.slack.com/services/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",
        "bots": "https://hooks.slack.com/services/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",
        "shopify": "https://hooks.slack.com/services/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",
        "others": "https://hooks.slack.com/services/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"
    }

    non_shopify_file = r"/../nonshopify.txt"
    bots_file = r"/../bots.txt"
    non_shopify_list = list()
    bots_list = list()

    # Supported bots sites list
    with open(os.path.dirname(__file__) + bots_file, "rt") as f:
        bots_list = [url.strip() for url in f.readlines()]

    # Supported non shopify sites list
        with open(os.path.dirname(__file__) + non_shopify_file, "rt") as f:
            non_shopify_list = [url.strip() for url in f.readlines()]

    def post(self, item, keyword):
        currency = ""
        try:
            currency = item['currency']
        except:
            pass

        stock = "n/a"
        try:
            stock = item['stock']
        except:
            pass
        
        variations = list()
        try:
            variations = item['sizes']
        except:
            pass
        
        image = "https://upload.wikimedia.org/wikipedia/commons/c/ca/1x1.png"
        try:
            image = item['image']
        except:
            pass

        price = "n/a"
        if currency.lower() == "usd":
            price = '$' + str(item['price'])
        else:
            try:
                price = item['price']
            except:
                pass

        store = urlparse(item['url']).netloc

        sizes = "n/a"
        if stock > 0:
            for size in variations:
                quantity = size.split(' / Stock: ')[1]
                if int(quantity) > 0:
                    sizes += size + '\n'
        
        tag = ""
        try:
            tag = item['tag']
        except:
            pass

        # Item is a sneaker
        if 'bot' not in tag:
            
            # Set correct slack channel according to item's tag
            if 'shopify' in tag:
                webhook_url = self.channels['shopify']
            elif 'adidas' in tag:
                webhook_url = self.channels['adidas']
            elif 'supreme' in tag:
                webhook_url = self.channels['supreme']
            else:
                webhook_url = self.channels['others']

            slack_data = {
                "attachments": [
                    {
                        "title": item['name'],
                        "title_link":item['url'],
                        "color":"#3AA3E3",
                        "fields":[
                            {
                                "title": "Stock Count",
                                "value": stock,
                                "short": "true"},
                            {
                                "title": "Store",
                                "value": store,
                                "short": "true"},
                            {
                                "title": "Keyword matched",
                                "value": keyword,
                                "short": "true"},
                            {
                                "title": "Price",
                                "value": price,
                                "short": "true"},
                            {
                                "title": "Sizes",
                                "value": sizes,
                                "short": "true"}
                        ],
                        "actions": [
                            {
                                "type": "button",
                                "text": "Purchase",
                                "url": item['url'],
                                "style":"primary"}
                        ],
                        "thumb_url": image
                    }
                ]
            }

            response = requests.post(
                webhook_url, data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code != 200:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s'
                    % (response.status_code, response.text)
                )

        # Item is a bot product
        else:
            slack_data = {
                "attachments": [
                    {
                        "title": item['name'],
                        "title_link":item['url'],
                        "color":"#3AA3E3",
                        "fields":[
                            {
                                "title": "Status",
                                "value": "In stock",
                                "short": "true"},
                            {
                                "title": "Price",
                                "value": price,
                                "short": "true"}
                        ],
                        "actions": [
                            {
                                "type": "button",
                                        "text": "Purchase",
                                        "url": item['url'],
                                        "style":"primary"}],
                        "thumb_url": image
                    }
                ]
            }

            response = requests.post(
                self.channels['bots'], data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code != 200:
                raise ValueError(
                    'Request to slack returned an error %s, the response is:\n%s'
                    % (response.status_code, response.text)
                )

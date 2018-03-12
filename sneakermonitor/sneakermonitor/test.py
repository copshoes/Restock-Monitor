from slack import Slack
from items import Sneaker

sneaker = Sneaker()

sizes = list()
sizes.append("5 / Stock: 10")
sizes.append("10 / Stock: 0")
sizes.append("20 / Stock: 30")
sizes.append("30 / Stock: 0")
sizes.append("40 / Stock: 50")

sneaker['name'] = "Trip.io beta V2"
sneaker['price'] = 200
sneaker['currency'] = "USD"
sneaker['url'] = "https://shop.bdgastore.com/products/w-nike-air-max-plus-lux"
sneaker['image'] = "http://cdn.shopify.com/s/files/1/0049/9112/products/BTKA_15144940918813283_f79c0aa0e2825fd0d41629395bbb49_grande.jpg?v=1514494399"
sneaker['stock'] = 150
sneaker['sizes'] = sizes
# sneaker['tag'] = "supreme"

match_type = "New product"

slack = Slack()
slack.post(sneaker, match_type)

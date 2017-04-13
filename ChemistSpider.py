# -*- coding:utf-8 -*-

import sys
import logging
import time
import myutil
import ChemistDatabase
from lxml import html

CHEMIST_WAREHOUSE = "http://www.chemistwarehouse.com.au"
CATEGORIES = [
    "http://www.chemistwarehouse.com.au/Shop-Online/651/Veterinary",
    "http://www.chemistwarehouse.com.au/Shop-Online/256/Health",
    "http://www.chemistwarehouse.com.au/Shop-Online/257/Beauty",
    "http://www.chemistwarehouse.com.au/Shop-Online/258/Medicines",
    "http://www.chemistwarehouse.com.au/Shop-Online/259/Personal-Care",
    "http://www.chemistwarehouse.com.au/Shop-Online/260/Medical-Aids",
    # "http://www.chemistwarehouse.com.au/Shop-Online/261/Prescriptions",
    # "http://www.chemistwarehouse.com.au/Shop-Online/694/Confectionery",
]
LOG_FILE = myutil.get_cur_dir() + "\logging.txt"


class ChemistSpider:

    def __init__(self, coding='utf8'):
        reload(sys)
        sys.setdefaultencoding(coding)
        self.db = ChemistDatabase.ChemistDatabase()
        self.db.creatTable()

    def saveProductsInfo(self, url):
        # 获取并保存整个品类的产品信息
        count = 0
        page = url
        date = time.strftime("%Y-%m-%d", time.localtime())
        self.db.openDatabase()
        total_sale = total_save = 0
        while (page is not None):
            (products, sale, save) = self.getData(page)
            total_sale += sale
            total_save += save
            self.db.saveDatas(products, date)
            count += len(products)
            page = self.getNext(page)
        total_average = [["category-average " + url.split('/')[-1], round(total_sale / count, 2),
                          round(total_save / count, 2)]]
        self.db.saveDatas(total_average, date)
        self.db.closeDatabase()
        logging.info("Save {} products from {}".format(count, url))
        with open(LOG_FILE, 'a') as f:
            f.write("{}: Save {} products from {}\r".format(time.strftime("%Y-%m-%d %H:%M:%S",
                                                                          time.localtime()), count, url))
        return count

    def cookData(self, data):
        try:
            val = []
            val.append(myutil.trim_str(data[0]))
            price = float(myutil.get_number_in_str(data[1]))
            val.append(price)
            try:
                save = float(myutil.get_number_in_str(data[2]))
            except:
                save = 0
            # 取小数点后两位的精度
            val.append(save)
            return val
        except Exception as e:
            logging.error("product:" + data)
            logging.error(e)
            with open(LOG_FILE, 'a') as f:
                f.write("cookData: {}\r".format(data))
                f.write("error: {}\r".format(e))

    def getData(self, url):
        try:
            # 获取当前页面的产品信息(名称, 售价, 折扣)
            products = []
            page_sale = page_save = 0
            root = html.parse(url)
            results = root.xpath('//a[@class="product-container"]')
            for result in results:
                product = result.xpath(
                    ' ./@title \
                    | .//div[@class="prices"]/span[@class="Price"]/text() \
                    | .//div[@class="prices"]/span[@class="Save"]/text()')
                product = self.cookData(product)
                products.append(product)
                page_sale += product[1]
                page_save += product[2]
            if len(products) == 0:
                logging.error("No Products! url=" + url)
            return (products, page_sale, page_save)
        except Exception as e:
            logging.error("url:" + url)
            logging.error(e)
            with open(LOG_FILE, 'a') as f:
                f.write("getData: {}\r".format(url))
                f.write("error: {}\r".format(e))

    def getNext(self, url):
        # 获取下一页的网址
        try:
            root = html.parse(url)
            nextPage = root.xpath('//a[@class="next-page"]/@href')
            if len(nextPage) > 0:
                nextUrl = CHEMIST_WAREHOUSE + nextPage[0]
                if nextUrl == url:
                    nextUrl = None
            else:
                nextUrl = None
            return nextUrl
        except Exception as e:
            logging.error("url:" + url)
            logging.error(e)
            with open(LOG_FILE, 'a') as f:
                f.write("getNext: {}\r".format(url))
                f.write("error: {}\r".format(e))


if __name__ == "__main__":
    myutil.logging_init()
    spider = ChemistSpider()
    spider.saveProductsInfo(
        "http://www.chemistwarehouse.com.au/Shop-Online/651/Veterinary")

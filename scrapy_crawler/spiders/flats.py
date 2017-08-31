# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
import re
import requests
import psycopg2
from lxml import html

to_key = {"map.complex": "map_complex",
          "flat.building": "building",
          "flat.floor": "floor",
          "live.square": "all_space",
          "flat.renovation": "state",
          "flat.toilet": "toilet",
          "flat.balcony": "balcony",
          "flat.door": "door",
          "flat.phone": "phone",
          "inet.type": "internet",
          "flat.parking": "parking",
          "live.furniture": "furniture",
          "flat.flooring": "flooring",
          "flat.security": "security",
          "flat.priv_dorm": "priv_dorm",
          "ceiling": "ceiling",
          "flat.balcony_g": "balcony_glass"}

conn = None
CREATE_TABLE_STATEMENT = "create table flats( krisha_id VARCHAR(25)," \
                                            "building VARCHAR(25)," \
                                            "room_count VARCHAR(25)," \
                                            "floor VARCHAR(25)," \
                                            "all_space VARCHAR(25)," \
                                            "state VARCHAR(25)," \
                                            "built_time VARCHAR(25)," \
                                            "address VARCHAR(25)," \
                                            "region VARCHAR(25)," \
                                            "map_complex VARCHAR(25)," \
                                            "phone VARCHAR(25)," \
                                            "balcony VARCHAR(25)," \
                                            "balcony_glass VARCHAR(25)," \
                                            "internet VARCHAR(25)," \
                                            "toilet VARCHAR(25)," \
                                            "door VARCHAR(25)," \
                                            "security VARCHAR(25)," \
                                            "parking VARCHAR(25)," \
                                            "furniture VARCHAR(25)," \
                                            "ceiling VARCHAR(25)," \
                                            "priv_dorm VARCHAR(25)," \
                                            "geo_long VARCHAR(25)," \
                                            "geo_lat VARCHAR(25));"


class FlatsSpider(scrapy.Spider):
    name = 'flats'
    allowed_domains = ['krisha.kz']

    def get_data(self, response):
        keys = response.xpath('//dl[@class="a-parameters"]/dt/@data-name').extract()
        vals = response.xpath('//dl[@class="a-parameters"]/dd/text() | //dl[@class="a-parameters"]/dd/a/text()').extract()

        i = 0
        while i < len(vals):
            if vals[i].strip() == '':
                del vals[i]
            else:
                i += 1

        for i in range(len(vals)):
            if "кухня" in vals[i]:
                del vals[i]
                break
        for i in range(len(vals)):
            if "жилая" in vals[i]:
                del vals[i]
                break

        try:
            region = response.xpath('//div[@class="a-where-region"]/text()').extract_first()
            keys.append("region")
            vals.append(region)
        except Exception:
            pass

        price = response.xpath('//span[@class="price"]/text()').extract_first()
        keys.append("price")
        vals.append(price.replace("\xa0", ""))

        h1s = response.xpath('//h1/text()').extract()
        for h1 in h1s:
            keys.append("room_count")
            vals.append(h1[0])
            if re.match("^[0-9]-комнатная квартира.*$", h1):
                keys.append("address")
                vals.append(h1[21:].strip())

        for i in range(len(keys)):
            if keys[i] in to_key:
                keys[i] = to_key[keys[i]]

        print(response.url)

        # Refactoring building text
        building_i = keys.index("building")
        tmp = list(map(str.strip, vals[building_i].split(',')))

        if not tmp[0][0].isdigit():
            vals[building_i] = tmp[0]
            if len(tmp) > 1:
                keys.append("built_time")
                vals.append(tmp[1])
        else:
            keys[building_i] = "built_time"
            vals[building_i] = tmp[0]

        try:
            cur = conn.cursor()
            INSERT_STATEMENT = "INSERT INTO flats({0}) VALUES ({1});".format(",".join(keys),
                                                                             ",".join(["'%s'" % x for x in vals]))
            print(INSERT_STATEMENT)
            cur.execute(INSERT_STATEMENT)
            conn.commit()
            cur.close()
        except Exception:
            print("Bolyp turad..")

    def start_requests(self):
        global conn, CREATE_TABLE_STATEMENT
        conn = psycopg2.connect(
            database="aybek",
            user="aybek",
            password="aybek",
            host="localhost",
            port=5432)

        try:
            cur = conn.cursor()
            print("LOL")
            cur.execute(CREATE_TABLE_STATEMENT)
            print("NET LOLA")
            conn.commit()
            cur.close()
        except Exception:
            print("I think, table was created before!")

        city_links = ['https://krisha.kz/prodazha/kvartiry/almaty/',
                      'https://krisha.kz/prodazha/kvartiry/astana/']

        initial_requests = [Request(url) for url in city_links]
        for url in city_links:
            page = requests.get(url)
            response = html.fromstring(page.content)
            last_p = int(response.xpath('//a[@class="btn paginator-page-btn"]/@data-page')[-1])
            for i in range(2, last_p + 1):
                initial_requests.append(Request("{0}?page={1}".format(url, i)))
        return initial_requests

    def parse(self, response):
        if re.match("^.*/a/show/[0-9]+$", response.url):
            self.get_data(response)
        else:
            house_links = response.xpath(
                '//div[contains(@class,"a-item") and contains(@class, "a-list-item")]/@data-id').extract()
            for house_id in house_links:
                yield Request(response.urljoin('/a/show/%s' % house_id), callback=self.parse)

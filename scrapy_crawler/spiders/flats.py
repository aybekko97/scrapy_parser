# -*- coding: utf-8 -*-
import scrapy
import sys
from bs4 import BeautifulSoup
from scrapy import Request
import re
import requests
from lxml import html


class FlatsSpider(scrapy.Spider):
    name = 'flats'
    allowed_domains = ['krisha.kz']

    def parse_data(self, content):
        # 200 - page loaded succesfully
        # print(page.content)
        room_count = -1
        address = -1
        map_complex = -1
        building = -1
        built_time = -1
        floor = -1
        space = -1
        renovation = -1
        toilet = -1
        balcony = -1
        door = -1
        phone = -1
        ceiling = -1
        security = -1
        priv_dorm = -1
        internet = -1
        furniture = -1
        flooring = -1
        balcony_glass = -1
        parking = -1
        price = -1
        region = -1
        longitude = 0.0
        latitude = 0.0

        soup = BeautifulSoup(content, 'html.parser')
        # print(soup.prettify())

        rmc = soup.find('div', class_='a-header company')
        if (rmc is None):
            rmc = soup.find('div', class_='a-header specialist')
            if (rmc is None):
                rmc = soup.find('div', class_='a-header owner')

        pattern = re.compile(r'"lat":')
        script_text = soup.find('script', text=pattern)
        if (script_text != None):
            all_script_text = script_text.string
            lat = re.search('"lat":(.+?),"lon":', all_script_text)
            if lat:
                latitude = lat.group(1)

            lon = re.search('"lon":(.+?),"zoom"', all_script_text)
            if lon:
                longitude = lon.group(1)

        district = soup.find('div', class_='a-where-region')
        district = district.text

        room_count = rmc.h1.text[0]
        address = rmc.h1.text[21:]

        dt = soup.find_all('dt')
        dd = soup.find_all('dd')
        for i in range(len(dt)):
            if (dt[i].text == "Жилой комплекс"):
                map_complex = dd[i].text
            elif (dt[i].text == "Дом"):
                home = dd[i].text
                divider = home.split(',')
                if len(divider) < 2:
                    if divider[0][0].isdigit():
                        built_time = divider[0]
                        building = -1
                    else:
                        built_time = -1
                        building = divider[0]
                else:
                    if "г.п." in divider[0]:
                        built_time = divider[0]
                        building = -1
                    else:
                        building = divider[0]
                        built_time = divider[1]
            elif (dt[i].text == "Этаж"):
                floor = dd[i].text
            elif (dt[i].text == "Площадь"):
                living_space = dd[i].text
                d_space = living_space.split(',')
                space = d_space[0]
            elif (dt[i].text == "Состояние"):
                renovation = dd[i].text
            elif (dt[i].text == "Санузел"):
                toilet = dd[i].text
            elif (dt[i].text == "Балкон"):
                balcony = dd[i].text
            elif (dt[i].text == "Дверь"):
                door = dd[i].text
            elif (dt[i].text == "Телефон"):
                phone = dd[i].text
            elif (dt[i].text == "Потолки"):
                ceiling = dd[i].text
            elif (dt[i].text == "Безопасноть"):
                security = dd[i].text
            elif (dt[i].text == "В прив. общежитии"):
                priv_dorm = dd[i].text
            elif (dt[i].text == "Интернет"):
                internet = dd[i].text
            elif (dt[i].text == "Мебель"):
                furniture = dd[i].text
            elif (dt[i].text == "Пол"):
                flooring = dd[i].text
            elif (dt[i].text == "Балкон остеклен"):
                balcony_glass = dd[i].text
            elif (dt[i].text == "Парковка"):
                parking = dd[i].text

        price = soup.find('span', class_='price').text
        region = soup.find('div', class_='a-where-region').string

        ans = "district:" + str(district) + "|" + "address: " + str(address) + "|" + " room_count: " + str(
            room_count) + "|" + " price: " + str(price) + "|" + " Жилой комплекс: " + str(
            map_complex) + "|" + " Дом: " + str(building) + "|" + "Время постройки: " + str(
            built_time) + "|" + " Этаж: " + str(floor) + "|" + " Площадь: " + str(space) + "|" + " Состояние: " + str(
            renovation) + "|" + " Санузел: " + str(toilet) + "|" + " Балкон: " + str(
            balcony) + "|" + " Балкон остеклен: " + str(balcony_glass) + "|" + " Дверь: " + str(
            door) + "|" + " Телефон: " + str(phone) + "|" + " Потолки: " + str(ceiling) + "|" + " Безопасноть: " + str(
            security) + "|" + " В прив. общежитии: " + str(priv_dorm) + "|" + " Интернет: " + str(
            internet) + "|" + " Мебель: " + str(furniture) + "|" + " Пол: " + str(flooring) + "|" + " Парковка: " + str(
            parking) + "|" + " Latitude: " + str(latitude) + "|" + " Longitude: " + str(longitude) + "\n"
        return ans

    def get_data(self, response):
        keys = response.xpath('//dl[@class="a-parameters"]/dt/@data-name').extract()
        vals = response.xpath('//dl[@class="a-parameters"]/dd/text()').extract()
        print(keys)
        print(vals)



    def start_requests(self):
        
        city_links = ['https://krisha.kz/prodazha/kvartiry/almaty/',
                      'https://krisha.kz/prodazha/kvartiry/astana/']

        initial_requests = [Request(url) for url in city_links]

        for url in city_links:
            page = requests.get(url)
            response = html.fromstring(page.content)
            last_p = int(response.xpath('//a[@class="btn paginator-page-btn"]/@data-page')[-1])
            for i in range(2,last_p+1):
                initial_requests.append(Request("{0}?page={1}".format(url, i)))
        return initial_requests


    def parse(self, response):
        if re.match("^.*/a/show/[0-9]+$", response.url):
            with open('data.txt', 'a') as f:
                f.write(self.parse_data(response.text))
        else:
            house_links = response.xpath('//div[contains(@class,"a-item") and contains(@class, "a-list-item")]/@data-id').extract()
            for house_id in house_links:
                yield Request(response.urljoin('/a/show/%s' % house_id), callback=self.parse)
import base64
import json
import scrapy
from scrapy_selenium import SeleniumRequest
from urllib.parse import urljoin
import requests
import urllib.parse

class InfobelSpider(scrapy.Spider):
    name = "infobel"

    def start_requests(self):
        for keyword in ['Matériaux de couverture', 'Matériaux de construction']:
        # for keyword in ['Matériaux de construction']:
            payload = {"CurrentPage":1, "RecordsPerPage":0, "CountryCode": None, "BusinessType":1, "SortBy": None, "SearchTerm": keyword, "SearchLocation": None, "ResidentialSearchTerm": None, "SearchCategories":{},"CategoryCode": None,"CategoryLevel":0,"IsMeta": False, "Latitude": None,"Longitude": None,"Order08": None,"Order09": None,"NearBy": None,"StrictLocation": False, "CategorySearch": False, "TopCitiesNumber":0,"TopCitiesArea":0,"TopCategoriesNumber":0,"TopCompetitorsNumber":0,"TopCompetitorsArea":0,"ValidForEncryption": False, "LocationWithProvince": False}
            token = base64.b64encode(json.dumps(payload).encode('utf-8')).decode("utf-8")
            url = "https://www.infobel.com/fr/france/Search/BusinessResults?token={}".format(token)
            request = SeleniumRequest(url=url, callback=self.parse_list, dont_filter=True, wait_time=20)
            request.cb_kwargs['keyword'] = keyword
            yield request

    def parse_list(self, response, keyword):
        print(response.request.url)
        for url in response.css(".customer-item-info h2 > a::attr(href)").extract():
            request = scrapy.Request(url=urljoin('https://www.infobel.com/', url), callback=self.parse_results)
            request.cb_kwargs['keyword'] = keyword
            yield request
        # Get next page
        next_page = response.css(".pagination li > a::attr(href)")
        if next_page:
            request = scrapy.Request(url=urljoin('https://www.infobel.com/', next_page.extract()[-1]), callback=self.parse_list)
            request.cb_kwargs['keyword'] = keyword
            yield request

    def parse_results(self, response, keyword):
        url = response.request.url
        name = response.css(".customer-item-inner .customer-item-name::text").extract_first()
        address = ", ".join(response.css(".customer-item-inner .address .detail-text::text").extract())
        phone = None
        phone_div = response.css(".customer-item-inner div > span.customer-info-detail")
        if phone_div:
            for p in phone_div:
                if p.css('.icon-phone').extract() or p.css('.icon-mobile-phone').extract():
                    phone = self.decrypt_phone(p.css('.detail-text::text').extract_first())
        web = response.css("a.customer-info-detail::attr(href)").extract_first()
        products = "; ".join(response.css('#customer-details-panelbar div:nth-child(4) > div p::text').extract())
        yield {
            'url': url,
            'name': name,
            'address': address,
            'phone': phone,
            'web': web,
            'products': products,
            'keyword': keyword,
        }

    def decrypt_phone(self, string):
        result = requests.get('https://www.infobel.com/fr/france/Search/Decrypt?encryptedString={}'.format(urllib.parse.quote(string)))
        if result:
            return json.loads(result.content)['result']
        return None

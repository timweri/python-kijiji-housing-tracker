#!/usr/bin/python3

import json
import logging
import re
import time
from datetime import datetime

import requests
from lxml import html

from htmlscraper.listing import Listing

logger = logging.getLogger(__name__)


class KijijiScraper():
    KIJIJI_URL_PREFIX = 'kijiji.ca'

    def __init__(self):
        # declare class variable
        self._cur_url = -1
        self._cur_page = -1
        self._html_tree = -1

        # unique id of a category
        self._cur_cat_id = -1

        # unique id of a location
        self._cur_loc_id = -1

    # prepare to scrape the category of the given url
    # returns nothing
    def scrape_cat_page_ini(self, url, page=1):
        if type(url) != str:
            logger.error('TypeError: The url has to be a str')
            raise TypeError('The url has to be a str')

        # ini class parameters
        self._cur_url = url
        self._cur_page = page

        # fetch the webpage
        page = requests.get(url)

        # parse the webpage
        self._html_tree = html.fromstring(page.content)

        self._cur_cat_id = self.get_cat_id(url)
        self._cur_loc_id = self.get_loc_id(url)

    # extract the cat_id from the given url
    # return the cat_id as an int
    @staticmethod
    def get_cat_id(url):
        logger.debug('Extracting cat_id from url')
        if type(url) != str:
            logger.error('TypeError: The url has to be a str')
            raise TypeError('The url has to be a str')

        tmp = re.search('(?<=/c)[0-9]+(?=l[0-9]{4})', url)
        if not tmp:
            logger.error('ValueError: cat_id extraction unsuccessful')
            raise ValueError('cat_id extraction unsuccessful')

        tmp = int(tmp.group(0))

        logger.debug('cat_id extraction successful')
        return tmp

    # extract the loc_id from the given url
    # return the loc_id as an int
    @staticmethod
    def get_loc_id(url):
        logger.debug('Extracting loc_id from url')
        if type(url) != str:
            logger.error('TypeError: The url has to be a str')
            raise TypeError('The url has to be a str')

        tmp = re.search('(?<=/c)[0-9]+l[0-9]+', url)
        if not tmp:
            logger.error('ValueError: cat_id extraction unsuccessful')
            raise ValueError('cat_id extraction unsuccessful')

        tmp = re.search('(?<=l)[0-9]+', tmp.group(0))
        if not tmp:
            logger.error('ValueError: cat_id extraction unsuccessful')
            raise ValueError('cat_id extraction unsuccessful')

        tmp = int(tmp.group(0))

        logger.debug('loc_id extraction successful')
        return tmp

    # parse the description and return a string
    @staticmethod
    def get_listing_description(html_tree):
        raw = html_tree.xpath(
            '//div[@class="descriptionContainer-2832520341"]//div//*/text() | //div[@class="descriptionContainer-2832520341"]//div/text()')
        if not raw:
            raise UserWarning('"description" attribute not found')

        value = ""

        for s in raw:
            value += s + '\n'

        logger.debug('"description" attribute extraction successful')
        return value

    # parse the address and return a string
    @staticmethod
    def get_listing_addr(html_tree):
        raw = html_tree.xpath('//span[@class="address-2932131783"]/text()')
        if raw:
            value = raw[0].strip()
        else:
            logger.error('"address" attribute not found')
            raise UserWarning('"address" attribute not found')

        logger.debug('"address" attribute extraction successful')
        return value

    # parse the value of "Pet Friendly" and return a bool
    @staticmethod
    def get_listing_pet_friendly(html_tree):
        raw = html_tree.xpath(
            '//dl[@class="itemAttribute-304821756" and contains(.,"Pet Friendly")]/dd[@class="attributeValue-1550499923"]/text()')
        if raw:
            value = raw[0].strip()
        else:
            logger.debug('"pet friendly" attribute not found')
            return -1

        if value == 'No':
            logger.debug('"pet_friendly" attribute extraction successful')
            return False
        elif value == 'Yes':
            logger.debug('"pet_friendly" attribute extraction successful')
            return True
        else:
            logger.error('ValueError: invalid "pet friendly" attribute value')
            raise ValueError('Invalid "pet friendly" attribute value')

    # parse the value of "Furnished" and return an int
    @staticmethod
    def get_listing_size(html_tree):
        raw = html_tree.xpath(
            '//dl[@class="itemAttribute-304821756" and contains(.,"Size")]/dd[@class="attributeValue-1550499923"]/text()')
        if not raw:
            logger.debug('"size" attribute not found')
            return -1

        value = raw[0].strip()

        logger.debug('"size" attribute extraction successful')
        return float(value)

    # parse the value of "Furnished" and return a bool
    @staticmethod
    def get_listing_furnished(html_tree):
        raw = html_tree.xpath(
            '//dl[@class="itemAttribute-304821756" and contains(.,"Furnished")]/dd[@class="attributeValue-1550499923"]/text()')
        if raw:
            value = raw[0].strip()
        else:
            logger.debug('"furnished" attribute not found')
            return -1

        if value == 'No':
            logger.debug('"furnished" attribute extraction successful')
            return False
        elif value == 'Yes':
            logger.debug('"furnished" attribute extraction successful')
            return True
        else:
            logger.error('ValueError: invalid "furnished" attribute value')
            raise ValueError('Invalid "furnished" attribute value')

    # parse the number of bathrooms and return an int identifier
    # called in listing scraping
    @staticmethod
    def get_listing_bathroomqty(html_tree):
        value_dict = {'1 bathroom': 1, '1.5 bathrooms': 2, '2 bathrooms': 3, '2.5 bathrooms': 4, '3 bathrooms': 5,
                      '3.5 bathrooms': 6, '4 bathrooms': 7, '4.5 bathrooms': 8, '5 bathrooms': 9, '5.5 bathrooms': 10,
                      '6 or more bathrooms': 11}
        raw = html_tree.xpath(
            '//dl[@class="itemAttribute-304821756" and contains(.,"Bathroom")]/dd[@class="attributeValue-1550499923"]/text()')
        if raw:
            key = raw[0].strip()
            return value_dict[key]

        logger.debug('"bathroom quantity" attribute not found')
        return -1

    # parse the number of bedrooms and return an int identifier
    # called in listing scraping
    @staticmethod
    def get_listing_bedroomqty(html_tree):
        value_dict = {'1 Bedroom': 1, '1 bedroom': 1, '1 bedroom + den': 2, '1 bedroom and den': 2,
                      '1 Bedroom + Den': 2, '2 bedrooms': 3, '2 Bedroom': 3, '2 bedrooms and den': 4, '3 Bedroom': 5,
                      '3 bedrooms': 5, '4 bedrooms': 6, '5 bedrooms': 7, '6 or more bedrooms': 8,
                      'Bachelor or studio': 9,
                      '4+ Bedroom': 10, 'Bachelor & Studio': 9}
        keys = ['1 Bedroom', '1 Bedroom + Den', '2 Bedroom', '3 Bedroom', '4+ Bedroom', 'Bachelor & Studio']
        raw = html_tree.xpath(
            '//dl[@class="itemAttribute-304821756" and contains(.,"Bedroom")]/dd[@class="attributeValue-1550499923"]/text()')
        if raw:
            key = raw[0].strip()
            return value_dict[key]

        raw = html_tree.xpath(
            '//li[@class="crumbItem-1566965652"]//h1[@class="crumbH1-75073251"]//a[@class="crumbLink-3348846382"]//span[@itemprop="name"]/text()')
        if raw:
            for k in keys:
                if raw[0].find(k) != -1:
                    return value_dict[k]

        logger.debug('"bedroom quantity" attribute not found')
        return -1

    # get price
    # called in listing parsing
    @staticmethod
    def get_listing_price(html_tree):
        raw = html_tree.xpath(
            '//span[@class="currentPrice-2872355490"]/text() | //span[@class="currentPrice-2872355490"]//span/text()')
        if not raw:
            logger.error('price not found')
            raise ValueError('price not found')
        if raw[0] == "Please Contact" or raw[0] == "Swap/Trade":
            price = 0.0
        else:
            price = re.sub('[$,]', '', raw[0])
            price = float(price)

        logger.debug('price extraction successful')
        return price

    # get listing title
    # called in listing parsing
    @staticmethod
    def get_listing_title(html_tree):
        # extract product names into a list of names
        raw = html_tree.xpath(
            '//h1[@class="title-3283765216"]/text()')

        if not raw:
            print(raw)
            logger.error('title not found')
            return -1

        # process the raw strings:
        value = ' '.join(raw)

        value = re.sub(' +', ' ', value)

        logger.debug('title extraction successful')
        return value

    # get listing ids
    # called in listing parsing
    @staticmethod
    def get_listing_id(html_tree):
        raw = html_tree.xpath(
            '//li[@class="currentCrumb-2617455686"]//span/text()')
        if not raw:
            logger.error('id not found')
            raise ValueError('id not found')

        value = int(raw[0])
        logger.debug('id extraction successful')
        return value

    # scrape the individual listing
    # return a Listing object
    def scrape_listing(self, listing_url):
        if type(listing_url) != str:
            logger.error('TypeError: listing_url has to be a str')
            raise TypeError('listing_url has to be a str')

        listing = Listing(url=listing_url, loc_id=self._cur_loc_id, cat_id=self._cur_cat_id)

        html_tree = self.get_html_tree(listing_url)

        # scrape all the individual listing attributes
        listing.title = self.get_listing_title(html_tree)

        # retry one time if requested data is not properly downloaded
        if listing.title == -1:
            logger.info('Re-parsing the listing')
            html_tree = self.get_html_tree(listing_url)
            listing.title = self.get_listing_title(html_tree)
            if listing.title == -1:
                raise ValueError('title not found')

        listing.id = self.get_listing_id(html_tree)
        listing.addr = self.get_listing_addr(html_tree)
        listing.price = self.get_listing_price(html_tree)
        listing.pubdate = datetime.now()

        listing.bedroomqty = self.get_listing_bedroomqty(html_tree)
        listing.bathroomqty = self.get_listing_bathroomqty(html_tree)

        listing.furnished_flag = self.get_listing_furnished(html_tree)
        listing.pet_friendly_flag = self.get_listing_pet_friendly(html_tree)

        listing.description = self.get_listing_description(html_tree)

        logger.debug('Listing successfully scraped')
        return listing

    def parse_all_category(self, filename):
        self.subcategory_url_fetcher(self._cur_url, filename)
        with open(filename, 'r') as fp:
            data = json.load(fp)
        for url in data['url']:
            self.parse_url(url, 1)
            self.par

    # fetch all Kijiji subcategories on the given Kijiji page
    # organize these subcategories into a dict
    # dump this dict into a JSON file titled <filename>
    def subcategory_url_fetcher(self, url, filename):
        page = requests.get(url)
        html_tree = html.fromstring(page.content)

        urls = html_tree.xpath(
            '//div[@class="content"]//li//a[@class="category-selected" and @data-event="ChangeCategory"]/@href')
        urls = list(map(lambda x: "https://www.kijiji.ca" + x, urls))
        titles = html_tree.xpath(
            '//div[@class="content"]//li//a[@class="category-selected" and @data-event="ChangeCategory"]/text()')
        titles = list(map(lambda x: x.strip(), titles))
        ids = html_tree.xpath(
            '//div[@class="content"]//li//a[@class="category-selected" and @data-event="ChangeCategory"]/@data-id')
        ids = list(map(lambda x: int(x.strip()), ids))

        d = dict()
        d['category'] = []

        for i in range(0, len(urls)):
            cat = dict()
            cat['id'] = ids[i]
            cat['title'] = titles[i]
            cat['url'] = urls[i]
            d['category'].append(cat)

        return d

    # parse the next page of the given url
    def scrape_next_page(self):
        # check if the current page is already the last page
        if self._is_last_cat_page():
            logger.info('Last page reached')
            return -1

        self._cur_page += 1
        logger.info('Scraping page number: {:d}'.format(self._cur_page))

        # generate the url of the next page
        next_url = self._gen_cat_page_url(self._cur_url, self._cur_page)

        # parse the generated url
        self.scrape_cat_page_ini(next_url, self._cur_page)
        return self.get_cat_page_listings()

    # generate url to the specified page
    def _gen_cat_page_url(self, url, page):
        start = re.search(self.KIJIJI_URL_PREFIX + '/[a-zA-Z-]+/[a-zA-Z-]+/', url)
        end = re.search('/[a-zA-z0-9]+$', url)
        print(start)
        print(end)
        return 'https://www.{:s}page-{:d}{:s}'.format(start.group(0), page, end.group(0))

    # parse the "current ads/max ads"
    # check if current ads == max ads
    def _is_last_cat_page(self):
        # parsed text will give "Showing <Nat> - <Nat> out of <Nat> Ads"
        text = self._html_tree.xpath('//div[@class="col-2"]//div[@class="top-bar"]//div[@class="showing"]/text()')[
            0].strip()
        matches = re.findall('[0-9]+', text)
        if matches:
            cur = matches[1]
            print(cur)
            max = matches[2]
            print(max)
        else:
            raise ValueError('Page number not found')

        return cur == max

    # get listing urls from the current category
    # called in category parsing
    def get_cat_urls(self):
        # extract listing urls into a list of urls
        raws = self._html_tree.xpath(
            '//div[@class="container-results large-images"]//div[@data-ad-id and @data-vip-url]/@data-vip-url')
        logger.debug('Category urls extraction successful')
        return raws

    # scrape all listings on a category page
    # compile all listings into a list of Listing objects.
    def get_cat_page_listings(self):
        logger.info('Scraping listings from {:s}'.format(self._cur_url))
        # get all the urls on the page
        urls = self.get_cat_urls()

        # initiate list of Listing objects
        listings = []

        for i in range(len(urls)):
            url = 'https://www.' + self.KIJIJI_URL_PREFIX + str(urls[i])
            listing = self.scrape_listing(url)
            listings += [listing]
            time.sleep(0.5)

        logger.info('Category successfully scraped')
        return listings

    @staticmethod
    def get_html_tree(url):
        page = requests.get(url)
        html_tree = html.fromstring(page.content)
        return html_tree

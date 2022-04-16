import requests
import os
import re
import datetime
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as soup


class Scraper():
    def __init__(self, urls=None, headers=None, webdriver=None, save=True):
        """
        Parameter Setting

        :param urls: the target websites' urls
        :param headers; custom headers for accessing website request
        :param webdriver: specific selenium webdriver suitable to your browser
        :param save: default True; True means the listings are going to be saved and False otherwise
        """
        self.htmls = []
        self.file_path = f'zillow_listings_{datetime.datetime.now().date()}'
        self.save = save

        # url for La Jolla renting list
        if urls is None:
            self.urls = ["https://www.zillow.com/la-jolla-san-diego-ca/rentals"]
        else:
            self.urls = urls

        # taken header from browser http request
        if headers is None:
            self.headers = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.53',
                'refer': urls[0]
            }
        else:
            self.headers = headers

        # specify selenium webdriver
        if webdriver is None:
            self.webdriver = None # TODO: Update this after importing the package
        self.webdriver = webdriver

    def get_listings(self):
        """
        Get all listings elements from the landing page
        """
        # request website listing urls
        for url in self.urls:
            html = requests.get(url, headers=self.headers)

            # handle request failure
            if html.status_code != 200:
                print(f"""
                    Server non-responsive; URL: {url}.\n
                    The URL provided might be false or website service is temporarily unavailable; Check the URL.\n
                """)
            else:
                self.htmls.append(html.text)

        # save the listing elements [OPTIONAL]
        if self.save:
            with open(self.file_path, 'a') as file:
                for html in self.htmls:
                    file.write(html.text)
        else:
            self.htmls = [soup(html.text, 'html.parser') for html in self.htmls]


    def parse_file(self, fp=None):
        """
        Parse saved html record
        :param fp: filepath; if None, use the stored filepath
        :return: soup parsed element
        """
        # check if a file path is given
        if fp is None:
            fp = self.file_path
        # parse the html
        with open(fp, mode='r') as file:
            html_txt = file.readlines()
        return soup(''.join(html_txt), 'html.parser')


    def parse_general_info(self, html):
        """
        Get General Information with given listing html
        :param html: the entire soup parsed html object
        :return: the target information
        """
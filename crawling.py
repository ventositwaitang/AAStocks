import re
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import json
import os

import pandas as pd
import numpy as np

# !pip install selenium
# !apt-get -y update # to update ubuntu to correctly run apt install
# !apt install -y chromium-chromedriver
# !cp /usr/lib/chromium-browser/chromedriver /usr/bin
import sys

sys.path.insert(0, '/usr/lib/chromium-browser/chromedriver')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class Crawling:
        def __init__(self, url: str,scroll_pause_time: int):
            self.url = url
            self.scroll_pause_time = scroll_pause_time
            if not self.url.startswith('http'):
                raise Exception('URLs need to start with "http"')

        def Sentiment(self):
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            browser = webdriver.Chrome('chromedriver', options=chrome_options)
            print('Hi, I am digging "Sentiment" for a while, Please take a break or have a cup of tea ;)')

            browser.get(self.url)
            time.sleep(2)  # Allow 2 seconds for the web page to open
            scroll_pause_time = 3 # load all weekly news (15 pages)
            previous_height = browser.execute_script("return document.body.scrollHeight;")  # starting height
            counter = 1

            while True: # load all info in initial page
                # scroll one screen height each time
                browser.execute_script("window.scrollTo(0, {previous_height}*{i});".format(previous_height=previous_height, i=counter))
                time.sleep(scroll_pause_time) # load all weekly news (15 pages)

                counter += 1
                # Break the loop when the height we need to scroll to is larger than the total scroll height
                if counter > scrolls_to_bottum:  #if (screen_height) * i > scroll_height:
                  break

            # after loading all documents..
            self.whens = [tve.text for i,tve in enumerate(browser.find_elements(By.CSS_SELECTOR,'div.inline_block')) if len(tve.text)==16]
            print(len(self.whens),'whens inserted: [..,"'+self.whens[-1]+'"],',counter-1,'pages done')
            self.pos = [] # self.pos = [int(tve.text.replace('Positive','')) for i,tve in enumerate(browser.find_elements(By.CLASS_NAME,'divBullish'))]# if i%2 == 0]# even i for Bullish ,odd i for Bearish
            self.neg = [] # self.neg = [int(tve.text.replace('Negative','')) for i,tve in enumerate(browser.find_elements(By.CLASS_NAME,'divBearish'))]# if i%2 != 0]# even i for Bullish ,odd i for Bearish
            self.Polarity = []
            for tve in list(browser.find_elements(By.CLASS_NAME,'div_VoteTotal')): # even i divBullish ,odd i for Bearish

              Bullish = int(tve.text.split('tive')[1].replace('Nega',''))
              Bearish = int(tve.text.split('tive')[2])
              VE = Bullish-Bearish

              self.pos.append(Bullish)
              self.neg.append(Bearish)
              self.Polarity.append('positive' if VE > 0 else 'negative' if VE < 0 else 'neutral')
            print(len(self.Polarity),'Polarity inserted: [..,"'+self.Polarity[-1]+'"],',counter-1,'pages done')

            ## get ['Headline'] & news follow links
            self.headlines = [] #self.headlines = [h.text for h in list(browser.find_elements(By.CLASS_NAME,'newshead4'))]
            self.links = []
            for h in list(browser.find_elements(By.XPATH,"//div[contains(@class, 'newshead4')]/a")):
              self.headlines.append(h.text)
              self.links.append(h.get_attribute('href'))
            browser.close()
            print(len(self.headlines),'headlines inserted: [..,"'+self.headlines[-1]+'"],',counter-1,'pages done')
            print(len(self.links),'links inserted: [..,"'+self.links[-1]+'"],',counter-1,'pages done')
            print('Thank you for your patience :)')


        def Symbol_fol(self):
            fol_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
                "Referer": "http://www.aastocks.com/en/stocks/news/aafn-company-news"
            }
            self.symbols = []
            self.names = []
            self.abstracts = []
            browser = webdriver.Chrome('chromedriver', options=chrome_options)
            print('Hi, I am further digging Symbols for a while, Please take a break or have a cup of tea ;)')
            # 300 links requiring ~1hr (including 10 mins time.sleep), ~12 sec/link to retrieve [name], [symbol] & [abstract]
            for link in self.links:  # follow each news links to get [name], [symbol] & [abstract]
                print(link)
                browser.get(link)
                print('Loading 2 sec to pretend as a human..')
                time.sleep(2)
                self.abstracts.append(browser.find_element(By.XPATH, '//p').text)
                print(len(self.abstracts), 'abstracts inserted')
                try:
                    #   sym = soup.find("a",class_='jsStock jsBmpStock')['sym']
                    button = browser.find_element(By.XPATH,
                                                  '//a[@class="jsStock jsBmpStock"]')
                except Exception as e:
                    print(e, '\nNo Ticker button appears, getting Related Symbol')
                    button = browser.find_element(By.LINK_TEXT, "Related News")  # related symbol from news' fol link

                browser.execute_script("arguments[0].click();", button)
                self.symbols.append(browser.find_element(By.XPATH, '//div[@id="SQ_Symbol"]').text[1:6])
                print(len(self.symbols), 'symbols inserted: [..,"' + self.symbols[-1] + '"],')
                self.names.append(browser.find_element(By.XPATH, '//label[@id="SQ_Name"]').text)
                print(len(self.names), 'company names inserted: [..,"' + self.names[-1] + '"]')
            browser.close()
            print('Thank you for your patience :)')


        def save_file(self):
            df = pd.DataFrame({'Headline': self.headlines, 'Releasing time': self.whens,
                               'Polarity': self.Polarity, 'Positive': self.pos, 'Negative': self.neg,
                               'Symbols':self.symbols, 'Company name':self.names, 'Abstract':self.abstracts})
            df = df.convert_dtypes()
            print(df.info())
            path = f'News Repository/AAstocksWEEKLYcompNews_{df['Releasing time'][0].strftime("%Y-%m-%d")}_{df['Releasing time'][-1].strftime("%Y-%m-%d")}.xlsx'
            try:
		df.to_excel( path, index=True, header = df.columns)
	    except:
		os.mkdir("News Repository")
		df.to_excel( path, index=True, header = df.columns)
            

if __name__ == '__main__':

    url = "http://www.aastocks.com/en/stocks/news/aafn-company-news"
    scrolls_to_bottum = 1 # times of scrolls to bottum is required in initial url
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    #     "Referer": "http://www.aastocks.com/en/stocks/news/aafn/latest-news/0"}

    AAStocks = Crawling(url, scrolls_to_bottum=scrolls_to_bottum) # times of scrolling to bottum in initial url
    AAStocks.Sentiment()
    AAStocks.Symbol_fol()
    AAStocks.save_file()

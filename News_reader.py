from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
import re
import pandas as pd
import random
import time
import numpy as np

class News():
    def __init__(self, link):
        self.options = webdriver.ChromeOptions()

        self.options.add_argument('headless')
        self.options.add_argument('window-size=1920x1080')
        self.options.add_argument("disable-gpu")

        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
        self.driver = webdriver.Chrome(chrome_options=self.options)

        self.link = link
        self.title = ""
        self.content = ""
        self.summary = ""

    def read_news(self):
        self.driver.get(self.link)
        WebDriverWait(self.driver, 10).until(expected_conditions.element_to_be_clickable((By.XPATH, '// *[ @ id = "content"] / div[2] / table / tbody / tr[1] / th / strong')))
        xpath = self.driver.find_element_by_xpath('// *[ @ id = "content"] / div[2] / table / tbody / tr[1] / th / strong')
        self.title = xpath.text
        xpath = self.driver.find_element_by_xpath('//*[@id="news_read"]')
        children = xpath.find_elements_by_xpath('.//child::*')
        self.content = xpath.text
        for obj in children:
            if obj.get_attribute('class') in ['link_news', 'end_btn _end_btn']:
                self.content = self.content.replace(obj.text, "")

    def summarize(self, num=3):
        import collections
        import jpype
        from konlpy.tag import Twitter
        from konlpy import jvm

        if not jpype.isJVMStarted():
            jvm.init_jvm()

        def split(*delimiters):
            return lambda value: re.split('|'.join([re.escape(delimiter) for delimiter in delimiters]), value)

        nlp = Twitter()
        morphs = nlp.morphs(self.title)
        sentences = split('. ', '? ', '! ', '\n', '.\n')(self.content)
        dic = {}
        sentence_keys = []

        for i, sentence in enumerate(sentences):
            score = 0
            for morph in morphs:
                if sentence.find(morph)>=0 and len(morph) > 1:
                    score += len(morph)
            dic[i] = score

        dic = collections.OrderedDict(sorted(dic.items(), key=lambda t: t[1], reverse=True))

        for key in dic.keys():
            if num == 0:
                break
            else:
                sentence_keys.append(key)
                num -= 1

        sentence_keys = sorted(sentence_keys)

        #print("Title :", self.title)
        for key in sentence_keys:
            self.summary += sentences[key] + ". "

    def __del__(self):
        self.driver.close()



if __name__ == '__main__':

    
    news = News('https://finance.naver.com/item/news_read.nhn?article_id=0004182428&office_id=009&code=000660&page=&sm=title_entity_id.basic')
    news.read_news()
    news.summarize()
    print(news.summary)
    

    
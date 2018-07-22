import os
from urllib.parse import urlparse, parse_qs

import pandas as pd


class User():
    def __init__(self, user_id):
        self.user_id = user_id
        if os.path.exists('./user_data/' + user_id):
            self.data = pd.Series.from_csv('./user_data/' + user_id)
        else:
            self.data = pd.Series(name='Symbol')

    def save_data(self):
        self.data.to_csv('./user_data/' + self.user_id)


def to_mobile_page(link):
    parsed = urlparse(link)
    parsed = parse_qs(parsed.query)
    return 'https://m.stock.naver.com/item/main.nhn#/stocks/{}/news/{}/office/{}' \
        .format(parsed['code'][0], parsed['article_id'][0], parsed['office_id'][0])

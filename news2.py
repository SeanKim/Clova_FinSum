from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd
import random
import time
import requests
import numpy as np
import json
import datetime

class Clova_News():
    def __init__(self, ticker_path=None):  # ticker_path에 Ticker라는 column이 있어야함
        self.ticker_df = pd.DataFrame()
        self.dart_api = 'd74599ed29c73354a63fa01fabb53271a717545a'
        self.options = webdriver.ChromeOptions()

        self.options.add_argument('headless')
        self.options.add_argument('window-size=1920x1080')
        self.options.add_argument("disable-gpu")

        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
        self.driver = webdriver.Chrome(chrome_options=self.options)
        self.news_df = pd.DataFrame(columns=['Date', 'Ticker', 'Title', 'Link']).set_index('Date')
        self.dart_df = pd.DataFrame(columns=['Date', 'Ticker', 'Category', 'Title']).set_index('Date')
        self.dart_dict= {'A001': '사업보고서','A002': '반기보고서', 'A003': '분기보고서', 'A004': '등록법인결산서류(자본시장법이전)', 'A005': '소액공모법인결산서류', 'B001': '주요사항보고서',
                         'B002': '주요경영사항신고(자본시장법', 'C001': '증권신고(지분증권)', 'C002': '증권신고(채무증권)', 'C003': '증권신고(파생결합증권)',
                         'C004': '증권신고(합병등)', 'C005': '증권신고(기타)', 'C006': '소액공모(지분증권)', 'C007': '소액공모(채무증권)',
                         'C008': '소액공모(파생결합증권)', 'C009': '소액공모(합병등)', 'C010': '소액공모(기타)', 'C011': '호가중개시스템을통한소액매출',
                         'D001': '주식등의대량보유상황보고서', 'D002': '임원ㆍ주요주주특정증권등소유상황보고서', 'D003': '의결권대리행사권유', 'D004': '공개매수',
                         'E001': '자기주식취득/처분', 'E002': '신탁계약체결/해지', 'E003': '합병등종료보고서', 'E004': '주식매수선택권부여에관한신고',
                         'E005': '사외이사에관한신고', 'E006': '주주총회소집공고', 'E007': '시장조성/안정조작', 'E008': '합병등신고서(자본시장법',
                         'F001': '감사보고서', 'F002': '연결감사보고서', 'F003': '결합감사보고서', 'F004': '회계법인사업보고서', 'G001': '증권신고(집합투자증권-신탁형)',
                         'G002': '증권신고(집합투자증권-회사형)', 'G003': '증권신고(집합투자증권-합병)', 'H001': '자산유동화계획/양도등록', 'H002': '사업/반기/분기보고서',
                         'H003': '증권신고(유동화증권등)', 'H004': '채권유동화계획/양도등록', 'H005': '수시보고', 'H006': '주요사항보고서', 'I001': '수시공시',
                         'I002': '공정공시', 'I003': '시장조치/안내', 'I004': '지분공시', 'I005': '증권투자회사', 'I006': '채권공시', 'J001': '대규모내부거래관련',
                         'J002': '대규모내부거래관련(구)', 'J004': '기업집단현황공시', 'J005': '비상장회사중요사항공시', 'J006': '기타공정위공시',}


        if ticker_path != None:
            self.get_ticker(ticker_path)

    def recent_news(self, ticker, recent_days=1):
        temps = []
        p = 1
        while True:
            url = 'https://finance.naver.com/item/news_news.nhn?code={}&page={}'.format(ticker,p)
            self.driver.get(url)
            self.driver.implicitly_wait(1)
            trs = self.driver.find_elements_by_xpath("/html/body/div/table[1]/tbody[1]/*")

            for tr in trs:
                try:
                    title = tr.find_element_by_class_name('title').text
                except:
                    return None
                if tr.get_attribute('class').startswith('relation_lst') or \
                        title.startswith('[한경로보') or \
                        title.startswith('[스팟') or \
                        title.startswith('[이데일리N') or \
                        title.startswith('[마켓포인'):
                    continue
                date = tr.find_element_by_class_name('date').text
                if pd.Timestamp(date) <= (pd.Timestamp(datetime.date.today()) - pd.DateOffset(days=recent_days)):
                    return pd.concat(temps) if len(temps) != 0 else None
                link = tr.find_element_by_tag_name('a').get_attribute("href")

                if len(tr.find_elements_by_class_name('title')) > 0:
                    temp = pd.DataFrame([[ticker, title, link]], columns=['Ticker', 'Title', 'Link'], index=[date])
                    temps.append(temp)
            p += 1
            time.sleep(random.randrange(float(5)/100, float(1)/10))

    def get_ticker(self, ticker_path):
        self.ticker_df = pd.read_csv(ticker_path, header=0, dtype=np.str)

    def get_news(self, max_page=1):  # 인스턴스 데이터프레임에 Profile이라는 column을 만들고, 해당 칼럼에 Ticker에 해당하는 Profile을 저장함
        for i, ticker in enumerate(self.ticker_df['Ticker'].values):
            for p in range(1, max_page+1):
                self.links = []
                print(ticker, end=' ')
                url = 'https://finance.naver.com/item/news_news.nhn?code={}&page={}'.format(ticker, p)
                print(url)
                self.driver.get(url)

                self.driver.implicitly_wait(1)
                trs = self.driver.find_elements_by_xpath("/html/body/div/table[1]/tbody[1]/*")

                for tr in trs:

                    title = tr.find_element_by_class_name('title').text
                    if tr.get_attribute('class').startswith('relation_lst') or\
                            title.startswith('[한경로보') or \
                            title.startswith('[스팟') or \
                            title.startswith('[이데일리N') or \
                            title.startswith('[마켓포인'):
                       continue
                    date = tr.find_element_by_class_name('date').text
                    link = tr.find_element_by_tag_name('a').get_attribute("href")

                    if len(tr.find_elements_by_class_name('title')) > 0:
                        if link not in self.links:
                            temp = pd.DataFrame([[ticker, title, link]], columns=['Ticker', 'Title', 'Link'], index=[date])
                            self.news_df = self.news_df.append(temp)
                            print("Date:", date, end='  ')
                            print('Title : {0}    Link : {1}'.format(title,  link))
                print(str((p + max_page * i * 100) / (len(self.ticker_df['Ticker'].values) * max_page)) + "%", "done")


                print()
                time.sleep(random.randrange(float(5) / 100, float(1) / 10))

    def get_filing(self):  # 인스턴스 데이터프레임에 Profile이라는 column을 만들고, 해당 칼럼에 Ticker에 해당하는 Profile을 저장함
        self.ticker_df['Profile'] = np.nan
        for i, ticker in enumerate(self.ticker_df['Ticker'].values):
            print(ticker, end=' ')
            url = 'https://dart.fss.or.kr/html/search/SearchCompany_M2.html?textCrpNM=' + str(ticker)
            print(url)
            try:
                if pd.isnull(self.ticker_df['Profile'][i]):
                    self.driver.get(url)
            except:
                pass

            try:
                WebDriverWait(self.driver, 10).until(expected_conditions.element_to_be_clickable((By.XPATH, '//*[@id="listContents"]/div[1]/table/tbody/tr[15]')))
                xpath = self.driver.find_element_by_xpath('//*[@id="listContents"]/div[1]/table/tbody')
                trs = xpath.find_elements_by_tag_name('tr')
                for tr in trs:
                    tds = tr.find_elements_by_tag_name('td')
                    print("Date:", tds[4].text, end='  ')
                    print('Title : {0}    Link : {1}'.format(tds[2].text,  tds[2].find_element_by_tag_name('a').get_attribute("href")))
                print(str((i + 1) / len(self.ticker_df['Ticker'].values) * 100) + "%", "done")

            except:
                print("error on :", ticker)

            print()
            time.sleep(random.randrange(float(5)/100, float(1)/10))

    def get_filing_api(self, start_date=(datetime.date.today() - datetime.timedelta(1)).strftime('%Y%m%d')):
        for i, ticker in enumerate(self.ticker_df['Ticker'].values):
            for p, key in enumerate(self.dart_dict):
                url = "http://dart.fss.or.kr/api/search.json?auth=" + self.dart_api + "&crp_cd=" + ticker +'&start_dt=' + start_date + "&bsn_tp={}".format(key)
                for tr in json.loads(requests.get(url).text)['list']:
                    temp = pd.DataFrame([[tr['crp_cd'], self.dart_dict[key], tr['rpt_nm']]], columns=['Ticker', 'Category', 'Title'], index=[tr['rcp_dt']])
                    self.dart_df = self.dart_df.append(temp)
                    print("Date:", tr['rcp_dt'], end='  ')
                    print('Title : {0}    Category : {1}'.format(tr['rpt_nm'], self.dart_dict[key]))
                print(str((p + len(self.dart_dict) * i * 100) / (len(self.ticker_df['Ticker'].values) * len(self.dart_dict))) + "%",
                    "done")

    def export_to_csv(self, csv_path, encoding_type='utf-8'):  # 인스턴스 데이터프레임을 csv로 출력함
        self.ticker_df.to_csv(csv_path, encoding=encoding_type, index=False)

    def __del__(self):
        self.driver.close()


if __name__ == '__main__':
    news = Clova_News(ticker_path = './ticker.csv')
    #news.get_news(max_page=10)
    #news.df.to_csv('./news.csv')
    #news.get_filing_api()
    #print(news.dart_df)



    #reuter.export_to_csv('out.csv', encoding_type='utf-8')


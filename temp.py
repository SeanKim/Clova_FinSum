import pandas as pd
from multiprocessing import Process
import numpy as np
from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup


def recommend(n):
    now_date = datetime.today().strftime("%Y-%m-%d")
    base_url = 'http://hkconsensus.hankyung.com/apps.analysis/analysis.list?sdate=2018-06-22&edate=' + str(
        now_date) + '&now_page=1&search_value=OFFICE_NAME&report_type=CO&pagenum=20&search_text=%B9%CC%B7%A1%BF%A1%BC%C2&business_code='

    driver = webdriver.Chrome()
    driver.get(base_url)
    # delay_time = 2
    # driver.implicitly_wait(delay_time)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    soup.findAll('td', attrs={'class': 'dv_input'})

    date = soup.findAll('td', attrs={'class': 'first txt_number'})
    stock_name = soup.findAll('div', attrs={'class': 'pop01 disNone'})
    opinion = soup.findAll('td')

    iContents = []
    for j in range(0, len(b)):
        jContents = []
        jdate = date[j].text.strip()
        jstock_name = stock_name[j].text.strip()[0:stock_name[j].text.strip().find('(')]
        jopinion = opinion[3 + 9 * j].text.strip()

        jContents.append(jdate)
        jContents.append(jstock_name)
        jContents.append(jopinion)
        iContents.append(jContents)

    driver.close()
    my_df = pd.DataFrame(iContents)
    result = my_df[my_df[2] == "Buy"][1][0:n]
    return result


recommend(3)
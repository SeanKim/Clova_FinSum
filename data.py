import pandas as pd
import os
from News_reader import News

def code_converter():
    print("아직 구현되지 않았습니다.")
    pass


def summary_all(news_df):
    summaries = pd.DataFrame(columns=['title', 'summary'])
    for i, news in news_df.iterrows():
        
        article = News(news['Link'])
        article.read_news()
        article.summarize()
        
        summaries = summaries.append(pd.DataFrame([[article.title, article.summary]], columns=['title', 'summary']))
        break
    return summaries

def load_data(user_id):
    if os.path.exists('./user_data/' + user_id):
        return pd.Series.from_csv('./user_data/' + user_id)
    else:
        return pd.Series(name='Symbol')

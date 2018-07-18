from newspaper import Article, Config
import pandas as pd
import os

def code_converter():
    print("아직 구현되지 않았습니다.")
    pass

def summary_all(news_df):
    config = Config()
    config.MAX_SUMMARY_SENT = 3
    config.language = 'ko'

    summaries = pd.DataFrame(columns=['title', 'summary'])
    for i, news in news_df.iterrows():
        article = Article(news['Link'], config=config)
        article.download()
        article.parse()
        article.set_title(news['Title'])
        article.nlp()
        summaries = summaries.append(pd.DataFrame([[article.title, article.summary]], columns=['title', 'summary']))
    return summaries

def load_data(user_id):
    if os.path.exists('./user_data/' + user_id):
        return pd.Series.from_csv('./user_data/' + user_id)
    else:
        return pd.Series(name='Symbol')

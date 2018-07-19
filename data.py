import pandas as pd
import os

def load_data(user_id):
    if os.path.exists('./user_data/' + user_id):
        return pd.Series.from_csv('./user_data/' + user_id)
    else:
        return pd.Series(name='Symbol')

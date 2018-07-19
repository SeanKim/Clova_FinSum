import pandas as pd
import os

class User():
    def __init__(self, user_id):
        self.user_id = user_id
        if os.path.exists('./user_data/' + user_id):
            self.data = pd.Series.from_csv('./user_data/' + user_id)
        else:
            self.data = pd.Series(name='Symbol')

    def save_data(self):
        self.data.to_csv('./user_data/' + self.user_id)

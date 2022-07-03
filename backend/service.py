import os
import sys
import time
import json
import threading 
import time
import requests
import twint
import pandas as pd
import yfinance as yf

from nlp import *
from constants import USERNAMES, COMPANIES, DIRECTORIES

class Service:
    LIMIT = 100

    def __init__(self, usernames):
        self.users = usernames
        # TODO: multithreading safe queue
        self.queue = []
        self._run()                
    
    def _get_user_info(self, username) -> tuple:
        '''Retrieve a user's base Twitter information
        Args:
            username - string
        Return:
            object - Twint User object
        '''
        c = twint.Config()
        c.Username = username
        c.Hide_output = True
        c.Store_object = True
        twint.run.Lookup(c)
        return twint.output, twint.output.users_list[0]

    def _tweets_by_username(self, username, limit=1, to_csv=False) -> list:
        '''Retrieve a user's tweets. Limit's increment is 100, so 1 is the latest 100 tweets.
        Args:
            username - string
            limit - tweet limit (default 1)
        Returns:
            list - array of twint.tweet objects
        '''
        c = twint.Config()  
        c.Username = username  
        c.Limit = limit
        c.Store_object = True
        c.Hide_output = True

        if to_csv:
            c.Store_csv = True
            c.Output = f'./tweets/{username}.csv'

        twint.run.Search(c)
        return twint.output.tweets_list

    def _get_historical_data(self, ticker) -> dict:
        '''Retrieve a ticker's historical data.
        Args:
            ticker - 'APPL'
        Returns:
            dict - date, low, high, open, close, volume, dividends, stock splits
        '''
        historical_data = yf.Ticker(ticker).history(period="max").reset_index().dropna()
        historical_data['Date'] = historical_data['Date'].dt.strftime('%Y-%m-%d')
        return { k.lower(): v for k, v in historical_data.to_dict('list').items() }

    def _preprocess_tweet(self, tweet) -> dict:
        '''Clean, tokenize and extract mentions/hashtags from the tweet. Calculate the 
           Vader Sentiment and determine if any companies exist through Named Entity Recognition.
        Args:
            tweet - Twint tweet object
        '''
        vs = vader_sentiment(tweet.tweet)
        clean = preprocess_tweet(tweet.tweet)
        tweet = {
            'date': tweet.datestamp,
            'time': tweet.timestamp,
            'username': tweet.username,
            'tweet': tweet.tweet,
            'companies': named_entity_recognition(tweet.tweet),
            'pos': vs['pos'],
            'neg': vs['neg'],
            'neu': vs['neu'],
            'compound': vs['compound'],
            'mentions': extract_mentions(tweet.tweet),
            'hashtags': extract_hashtags(tweet.tweet),
            'clean': clean,
            'tokens': tokenize(clean),
        }
        self.queue.append(tweet)
        return tweet

    def _fetch_new_tweets(self) -> None:
        '''Update and process latest user tweets'''
        for user in self.users:
            latest_tweet = tweets_by_username(user)[0]
            
            with open(f'./tweets/{user}.json', 'r+') as f:
                tweets = json.load(f)
                if latest_tweet.tweet != tweets[0]['tweet']:
                    tweet = self._preprocess_tweet(latest_tweet)
                    tweets.insert(0, tweet)

                f.seek(0)
                json.dump({'tweets': tweets}, f, indent=4)
                f.truncate()

    def _company_exists(self, company) -> bool:
        '''Checks if a company exists within our COMPANIES dict'''
        # TODO: better way of checking
        if company in COMPANIES or company in COMPANIES.values():
            return True
        return False

    def _queue_manager(self) -> None:
        '''Manages the company queue, determines if a company exists'''
        while True:
            if len(self.queue) > 0:
                queue_item = self.queue.pop(0)
                for company in queue_item['companies']:
                    if self._company_exists(company):
                        company_name, hist = None, None
                        try:
                            hist = self._get_historical_data(COMPANIES[company])
                            company_name = company
                        except KeyError:
                            # account for ticker values
                            hist = self._get_historical_data(company)
                            company_name = list(COMPANIES.keys())[list(COMPANIES.values()).index(company)]
                        
                        with open(f'./historical/{company_name}.json', 'w+') as f:
                            f.seek(0)
                            json.dump(hist, f, indent=4)
                            f.truncate()
                    
                        with open(f'./mentions/{queue_item["username"]}.json', 'r+') as f:
                            mentions = json.load(f)
                            if company_name not in mentions:
                                mentions[company_name] = []
                            mentions[company_name].append(queue_item)

                            f.seek(0)
                            json.dump(mentions, f, indent=4)
                            f.truncate()
                                
    def _company_manager(self) -> None:
        '''Fetches & updates historical share price data of a given ticker'''
        for fn in os.listdir(f'{os.curdir}/historical/'):
            hist = self._get_historical_data(fn.split(".")[0])        
            with open(f'./historical/{fn}', 'r+') as f:
                f.seek(0)
                json.dump(hist, f, indent=4)
                f.truncate()

    def _prerequisites(self) -> None:
        '''Ensure the required files exist. Create files & fetch base information if they do not.'''
        user_files = os.listdir(f'{os.curdir}/users')
        for i, user in enumerate(self.users):
            if f'{user}.json' not in user_files:
                tw, u = self._get_user_info(user)
                tw.clean_lists()

                user_info = {
                    'name': u.name, 
                    'username': u.username,
                    'bio': u.bio, 
                    'avatar': ''.join(u.avatar.split('_normal')),
                    'followers': u.followers,
                    'verified': u.is_verified,
                }

                with open(f'./users/{user}.json', 'w') as f:
                    json.dump(user_info, f, indent=4)
                with open(f'./tweets/{user}.json', 'w') as f:
                    json.dump([self._preprocess_tweet(tweet) for tweet in self._tweets_by_username(user, limit=self.LIMIT)], f, indent=4)
                with open(f'./mentions/{user}.json', 'w') as f:
                    json.dump({}, f, indent=4)     
                
    def _run(self) -> None:
        self._prerequisites()
        self._queue_manager()
        self._company_manager()
        # self._fetch_new_tweets()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        Service(USERNAMES)
    else:
        for directory in DIRECTORIES:
            for f in os.listdir(directory):
                os.remove(os.path.join(directory, f))


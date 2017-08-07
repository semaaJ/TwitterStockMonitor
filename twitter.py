import tweepy
import json

from main import logging
import company
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# File path to the LatestTweets folder
LATEST_TWEET = './Files/LatestTweets/'

# File path to the list of Twitter Handlers/Emails to DM/Email
TWITTER_NAMES = './Files/twitter_names.txt'
EMAILS = './Files/emails.txt'

# Twitter API constants
with open('./Files/config.json') as json_f:
    config = json.load(json_f)

CONSUMER_KEY = config["TwitterAuth"]["ConsumerKey"]
CONSUMER_KEY_SECRET = config["TwitterAuth"]["ConsumerSecret"]
ACCESS_TOKEN = config["TwitterAuth"]["AccessToken"]
ACCESS_TOKEN_SECRET = config["TwitterAuth"]["AccessTokenSecret"]


class Twitter:
    def __init__(self, handle=''):
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_KEY_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth)
        self.handle = handle
        self.tweet = ''
        self.tweet_id = ''

    def get_latest_tweet(self):
        """Checks the twitter handle for new tweets.
           If there has been a new tweet, it will return the Tweet
           to be checked for companies"""

        try:
            latest_tweet = self.api.user_timeline(screen_name=self.handle, count=1)[0]
            tweet = latest_tweet.text

            with open(f'{LATEST_TWEET}{self.handle}.txt', "r") as f:
                old_tweet = f.read()

            print(f'Old tweet: {old_tweet}')
            print(f'New tweet: {tweet}')

            if latest_tweet != old_tweet:
                with open(f'{LATEST_TWEET}{self.handle}.txt', 'w') as f:
                    f.write(tweet)

                self.tweet_id = latest_tweet.id_str
                self.tweet = tweet

                return tweet

        except tweepy.TweepError as error:
            logging.debug(error)

    def check_mentions(self):
        """Checks mentions for sign up's via email or twitter
           via "Sign up / Sign up [email]"""

        try:
            mentions = self.api.mentions_timeline(count=3)

            for mention in mentions:
                if "stop" in mention.text.lower():
                    # Unsubscribe for email
                    if len(mention.text.split()) == 3:
                        email = mention.text.split()[2]

                        with open(EMAILS, 'r') as f:
                            email_list = f.read().split()

                        if email in email_list:
                            email_list.remove(email)

                            with open(EMAILS, 'w') as f:
                                f.write(' '.join(email_list))

                    # Unsubscribe for Twitter handle
                    else:
                        twitter_name = mention.user.screen_name

                        with open(TWITTER_NAMES, 'r') as f:
                            twitter_name_list = f.read().split()

                        if twitter_name in twitter_name_list:
                            twitter_name_list.remove(twitter_name)

                            with open(TWITTER_NAMES, 'w') as f:
                                f.write(' '.join(twitter_name_list))

                elif "sign up" in mention.text.lower():
                    # Email sign up
                    if len(mention.text.split()) > 3:
                        email = mention.text.split()[3]

                        with open(EMAILS, 'r') as f:
                            email_list = f.read().split()

                        if email not in email_list:
                            with open(EMAILS, 'a') as f:
                                f.write(f' {email}')

                    # Twitter handle sign up
                    else:
                        twitter_name = mention.user.screen_name

                        with open(TWITTER_NAMES, 'r') as f:
                            twitter_name_list = f.read().split()

                        if twitter_name not in twitter_name_list:
                            with open(TWITTER_NAMES, 'a') as f:
                                f.write(f' {twitter_name}')

        except tweepy.TweepError as error:
            logging.debug(error)

    def initial_tweet(self, matches):
        """Tweets when a company is mentioned, along with it's sentiment."""

        sentiment = self.sentiment_analysis()
        sentiment_dict = {"positive": u"\U00002705",
                          "negative": u"\U0000274E",
                          "neutral": u"\U00002796"
                          }

        for comp in matches:
            try:
                self.api.update_status(f'{self.handle} just mentioned {comp.upper()} {sentiment}ly '
                                       f'in their latest tweet! {sentiment_dict[sentiment]}. Time to start '
                                       f"monitoring {comp.upper()}'s shares.. "
                                       f'https://twitter.com/{self.handle}/status/{self.tweet_id}')

            except tweepy.TweepError as error:
                logging.debug(error)

    def sentiment_analysis(self):
        """Performs a sentiment analysis on the tweet"""

        sid = SentimentIntensityAnalyzer()
        compound = sid.polarity_scores(self.tweet)["compound"]

        if compound >= 0.5:
            return "positive"
        elif compound <= -0.5:
            return "negative"
        else:
            return "neutral"

    def share_output(self):
        """Calls difference_in_shares from the Companies module,
            Outputs the data to twitter."""

        share_dict = company.get_company_dict()

        for comp in share_dict:
            try:
                self.api.update_status(
                    f'Since {share_dict["Handle"]} mentioned {comp}, {share_dict[comp]["Days"]} days ago, '
                    f'their shares have changed from {share_dict[comp]["Initial"]:.2f} to '
                    f"{share_dict[comp]['Current']:.2f} that's a {share_dict[comp]['Change']}% change!"
                    )

            except tweepy.TweepError as error:
                logging.debug(error)

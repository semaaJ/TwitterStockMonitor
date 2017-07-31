#!/usr/bin/env python3

import json
import tweepy
import datetime
import smtplib
import time
import utils
import schedule
import urllib.request
import urllib.error

from yahoo_finance import Share


config = utils.open_json("./Files/config.json")

# File names
LOG = config["Files"]["Log"]
EMAILS = config["Files"]["Emails"]
TWITTER_NAMES = config["Files"]["Twitter"]
COMPANIES = config["Files"]["Companies"]
GENERIC = config["Files"]["Generic"]
MONITOR = config["Files"]["CompaniesToMonitor"]

# Boolean value
INITIAL_START = config["Files"]["InitialStart"]

# Email/Password info
EMAIL = config["Email-Info"]["Email"]
PASSWORD = config["Email-Info"]["Password"]

# Twitter keys/names
CONSUMER_KEY = config["Twitter-Auth"]["ConsumerKey"]
CONSUMER_KEY_SECRET = config["Twitter-Auth"]["ConsumerSecret"]
ACCESS_TOKEN = config["Twitter-Auth"]["AccessToken"]
ACCESS_TOKEN_SECRET = config["Twitter-Auth"]["AccessTokenSecret"]
TWITTER_HANDLES = config["Twitter-Auth"]["Handles"]


class Twitter(object):
    def __init__(self, handle=''):
        self.handle = handle

        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_KEY_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth)

    def check_tweets(self):
        """Checks the twitter handle for new tweets.
           If there has been a new tweet, checks it in the Companies
           class to see if a company is contained in it"""

        try:
            new_tweet = self.api.user_timeline(screen_name=self.handle, count=1)

            for tweet in new_tweet:  # Need to find a fix for this loop
                old_tweet = utils.open_file(f'{GENERIC}{self.handle}.txt').strip()

                if old_tweet != tweet.text.encode('utf8'):
                    utils.write_to_file(f'{GENERIC}{self.handle}.txt', tweet.text)
                    return tweet.text.encode('utf8')

        except tweepy.TweepError as error:
            utils.write_to_log(f'Error checking for new tweets: {error}')

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
                        email_list = utils.open_file(EMAILS).split()

                        if email in email_list:
                            email_list.remove(email)
                            utils.write_to_file(EMAILS, ' '.join(email_list))

                    # Unsubscribe for Twitter handle
                    else:
                        twitter_name = mention.user.screen_name
                        twitter_name_list = utils.open_file(TWITTER_NAMES).split()

                        if twitter_name in twitter_name_list:
                            twitter_name_list.remove(twitter_name)
                            utils.write_to_file(TWITTER_NAMES, ' '.join(twitter_name_list))

                elif "sign up" in mention.text.lower():
                    # Email sign up
                    if len(mention.text.split()) > 3:
                        email = mention.text.split()[3]
                        email_list = utils.open_file(EMAILS).split()

                        if email not in email_list:
                            email_list.append(email)
                            utils.append_to_file(EMAILS, email)

                    # Twitter handle sign up
                    else:
                        twitter_name = mention.user.screen_name
                        twitter_name_list = utils.open_file(TWITTER_NAMES).split()

                        if twitter_name not in twitter_name_list:
                            twitter_name_list.append(twitter_name)
                            utils.append_to_file(TWITTER_NAMES, twitter_name)

        except tweepy.TweepError as error:
            utils.write_to_log(f'Error checking mentions: {error}')


class Companies(object):
    def __init__(self, tweet='', handle=None):
        if tweet != '':
            self.tweet = tweet.decode('utf8')
            self.original_tweet = self.tweet # Keeping a copy for later use, as self.tweet is edited
        else:
            self.tweet = tweet
        self.handle = handle

    def check_for_companies(self):
        """Checks list of companies with Trump's tweet
           seeing if any companies are listed in his tweet.
           Inputs matches into monitor.json"""

        matches = []
        punc = ("!", ",", ".", ":", ";", "@", "?", "(", ")")

        self.tweet = ''.join([letter for letter in self.tweet if letter not in punc]).lower()

        with open(COMPANIES) as f:
            companies = [line.strip() for line in f]

        for word in self.tweet.split():
            # Binary search for word
            if utils.find(companies, word):
                matches.append(word)

        company_dict = utils.open_json(MONITOR)
        comp_d = {}

        # Information that is needed by get_initial/current
        for company in matches:
            comp_d[company] = {}
            comp_d[company]["Date-mentioned"] = "{:%d-%m-%Y %H:%M:%S}".format(datetime.datetime.now())
            comp_d[company]["Mentioned by"] = self.handle
            comp_d[company]["Tweet"] = self.original_tweet
            comp_d[company]["Days-left"] = 7
            comp_d[company]["Symbol"] = "unknown"
            comp_d[company]["Initial-share-price"] = 1
            comp_d[company]["Current-share-price"] = 1
            comp_d[company]["Share-price-list"] = []

        company_dict.update(comp_d)
        utils.write_to_json(MONITOR, company_dict)

        return matches

    @staticmethod
    def get_initial_company_info():
        """Gets the initial information for each company"""

        company_dict = utils.open_json(MONITOR)

        for company in company_dict:
            # Gets symbol for company
            if company_dict[company]["Symbol"] == "unknown":
                try:
                    with urllib.request.urlopen(
                          f'https://finance.yahoo.com/_finance_doubledown/'
                          f'api/resource/searchassist;searchTerm={company}') as response:

                        html = response.read().decode()
                        d = json.loads(html)

                        company_dict[company]["Symbol"] = d['items'][0]['symbol']

                except urllib.error.HTTPError as error:
                    utils.write_to_log(f'Error opening URL: {error}')

            # Gets initial share price
            if company_dict[company]["Initial-share-price"] == 1:
                yahoo = Share(company_dict[company]["Symbol"])
                share = yahoo.get_price()
                company_dict[company]["Initial-share-price"] = float(share)
                company_dict[company]["Current-share-price"] = float(share)

        utils.write_to_json(MONITOR, company_dict)

    @staticmethod
    def get_current_shares():
        """Gets current shares, compares it to initial, finds difference.
           Returns for output to handle"""

        company_dict = utils.open_json(MONITOR)

        for company in company_dict:
            try:
                yahoo = Share(company_dict[company]["Symbol"])
                yahoo.refresh()
                share = yahoo.get_price()

                company_dict[company]["Current-share-price"] = float(share)
                company_dict[company]["Share-price-list"].append(float(share))

            except ValueError:
                # yahoo.get_price() will return None if an error occurs
                print("Could not add to the Current share/Share price list")

        utils.write_to_json(MONITOR, company_dict)

    @staticmethod
    def difference_in_shares():
        """Finds the difference in shares.
           Creates a dict to be used by Output"""

        company_dict = utils.open_json(MONITOR)

        share_difference_dict = {}

        for company in company_dict:
            share_change = 1.0 - (company_dict[company]["Initial-share-price"] /
                                  company_dict[company]["Current-share-price"])

            maximum = 1 - (company_dict[company]["Initial-share-price"] /
                           max(company_dict[company]["Share-price-list"]))

            share_difference_dict[company] = {}
            share_difference_dict[company]["Change"] = share_change
            share_difference_dict[company]["Max"] = max(company_dict[company]["Share-price-list"])
            share_difference_dict[company]["Max-change"] = maximum
            share_difference_dict[company]["Initial"] = company_dict[company]["Initial-share-price"]
            share_difference_dict[company]["Current"] = company_dict[company]["Current-share-price"]

        return share_difference_dict

    @staticmethod
    def minus_days():
        """Takes away a day from the "Days-Left",
           removes from monitor.json if == 0"""

        company_dict = utils.open_json(MONITOR)
        remove = []

        for company in company_dict:
            if company_dict[company]["Days-left"] > 0:
                company_dict[company]["Days-left"] -= 1

            elif company_dict[company]["Days-left"] == 0:
                remove.append(company)

        for company in remove:
            # Do I want to keep a record of all the companies that have been mentioned and their prices???
            # Goes here
            del company_dict[company]

        utils.write_to_json(MONITOR, company_dict)


class Output(object):
    def __init__(self, matches=None, handle=None):
        self.handle = handle
        self.matches = matches
        self.twitter = Twitter()

    def tweet(self):
        """Tweets and DMs the company that has been mentioned"""

        try:
            for company in self.matches:
                self.twitter.api.update_status(
                    f'Yelp, looks like a good time to take a look at your shares in {company.upper()}! '
                    f'{self.handle} just mentioned them!')

            twitter_users = utils.open_file(TWITTER_NAMES).split()

            for user in twitter_users:
                time.sleep(2)
                self.twitter.api.send_direct_message(screen_name=user,
                                                     text=f'{self.handle} just tweeted about {company.upper()}! '
                                                          f'Might be time to check your shares!')

        except tweepy.TweepError as error:
            utils.write_to_log(f'Error tweeting: {error}')

    def email(self):
        """Emails a list of people"""

        company_output = ', '.join(self.matches)

        try:
            email_list = utils.open_file(EMAILS).split()

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, email_list,
                            f'Trump just tweeted about {company_output}. '
                            f'Might be time to check your shares...')
            server.quit()

        except smtplib.SMTPResponseException as error:
            utils.write_to_log(f'Email error: {error}')

    @staticmethod
    def share_output():
        """Calls difference_in_shares from the Companies class,
           Outputs the data to twitter."""

        share_difference_dict = Companies().difference_in_shares()

        for company in share_difference_dict:
            try:
                # If you're following one person, this can be changed to look better
                # Remove "[Mentioned by: {company["Handle"]}" in the first line.
                Twitter().api.update_status(f'{company} [Mentioned by: {company["Handle"]} - '
                                            f'Initial Share Price: {company["Initial"]} '
                                            f'Current Share Price: {company["Current"]}'
                                            f'Change: {company["Change"]}'
                                            f'Max Change: {company["Max-change"]} '
                                            )

            except tweepy.TweepError as error:
                utils.write_to_log(f'Twitter output Error: {error}')


def main():
    global TWITTER_HANDLES

    # Checks if this is the first time running the script
    # Allows the user to choose the Twitter Handles to follow
    # Sets the TWITTER_HANDLES which is an empty list, to the new updated list
    if INITIAL_START:
        handles = utils.initial_start()
        TWITTER_HANDLES = handles

    # Sets up jobs for schedule to handle
    companies = Companies()
    output = Output()

    schedule.every().day.at("16:00").do(companies.minus_days)
    schedule.every().day.at("18:00").do(output.share_output)

    while True:
        for handle in TWITTER_HANDLES:
            twitter = Twitter(handle)
            new_tweet = twitter.check_tweets()

            # Checks if a new tweet has been posted
            if new_tweet:
                companies = Companies(new_tweet, handle)
                matches = companies.check_for_companies()

                if matches:
                    # Gets the initial company info
                    companies.get_initial_company_info()

                    # Outputs the matches via twitter/email
                    output = Output(matches, handle)
                    output.tweet()
                    output.email()

            # Gets the current shares for each company, checks mentions for sign ups/removals
            Companies().get_current_shares()
            twitter.check_mentions()

        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3

import json
import tweepy
import datetime
import smtplib
import time
import TrumpFunctions as tf

from yahoo_finance import Share
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

twitter_names_file = "./files/twitter_names.txt"
companies_file = "./files/companies.txt"
email_file = "./files/emails.txt"
monitor_file = "./files/monitor.json"
new_tweet_file = "./files/new_tweet.txt"
config = "./files/config.json"


# Parsing the config information
with open(config, "r") as f:
    config = json.load(f)

    EMAIL = config["Email-Info"]["Email"]
    PASSWORD = config["Email-Info"]["Password"]
        
    CONSUMER_KEY = config["Twitter-Auth"]["ConsumerKey"]
    CONSUMER_KEY_SECRET = config["Twitter-Auth"]["ConsumerSecret"]
    ACCESS_TOKEN = config["Twitter-Auth"]["AccessToken"]
    ACCESS_TOKEN_SECRET = config["Twitter-Auth"]["AccessTokenSecret"]
    TWITTER = config["Twitter-Auth"]["Twitter"]

    LOG = config["Files"]["Log"]
    EMAILS = config["Files"]["Emails"]
    TWITTER_NAMES = config["Files"]["TwitterNames"]
    COMPANIES = config["Files"]["Companies"]
    NEW_TWEET = config["Files"]["NewTweet"]
    MONITOR = config["Files"]["CompaniesToMonitor"]


class Twitter(object):

    def __init__(self):
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_KEY_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

        self.api = tweepy.API(auth)

    def check_tweets(self):
        """Checks for a new tweet. If there's a new tweet,
           returns it to be checked for companies"""

        try:
            # Change to TWITTER when done
            new_tweet = self.api.user_timeline(screen_name="MrTestyMctester", count=1)

            for tweet in new_tweet:
                old_tweet = tf.open_file(new_tweet_file).strip()

                if old_tweet != tweet.text.encode('utf8'):
                    tf.write_to_file(new_tweet_file, tweet.text)
                    return tweet.text

        except Exception as error:
            tf.write_to_log("Check tweets error: {}".format(error))

    def check_mentions(self):
        """Checks mentions for sign up's via email or twitter
           via "Sign up [email]"

        @DonaldTrumpStatBot Sign up == Twitter username
        @DonalTrumpStatBot Sign up hello@gmail.com == Email

        @DonaldTrumpStatBot STOP == Twitter
        @DonaldTrumpStatBot STOP hello@gmail.com == Email"""

        try:
            mentions = self.api.mentions_timeline(count=3)

            for mention in mentions:
                if "stop" in mention.text.lower():
                    # Unsubscribe for email
                    if len(mention.text.split()) == 3:
                        email = mention.text.split()[2]

                        email_list = tf.open_file(email_file).split()

                        if email in email_list:
                            # Writes everything back to file
                            email_list.remove(email)
                            tf.write_to_file_for_loop(email_file, email_list)

                    else:
                        twitter_name = mention.user.screen_name

                        twitter_name_list = tf.open_file(twitter_names_file).split()

                        if twitter_name in twitter_name_list:
                            twitter_name_list.remove(twitter_name)
                            tf.write_to_file_for_loop(twitter_names_file, twitter_name_list)

                elif "sign up" in mention.text.lower():
                    # Checks for email sign up
                    if len(mention.text.split()) > 3:
                        email = mention.text.split()[3]

                        email_list = tf.open_file(email_file).split()

                        if email not in email_list:
                            email_list.append(email)

                            tf.write_to_file_for_loop(email_file, email_list)

                    # Signs up twitter username
                    else:
                        twitter_name = mention.user.screen_name
                        twitter_name_list = tf.open_file(twitter_names_file).split()

                        if twitter_name not in twitter_name_list:
                            # Write to file doesn't work here????
                            twitter_name_list.append(twitter_name)
                            
                            tf.write_to_file_for_loop(twitter_names_file, twitter_name_list)

        except Exception as error:
            tf.write_to_log("Check mentions error: {}".format(error))


class Companies(object):

    def __init__(self, tweet):
        self.tweet = tweet
        
    # This will be run immediately after a new tweet is posted
    def check_companies(self):
        """Checks list of companies with Trump's tweet
           seeing if any companies are listed in his tweet.
           Inputs matches into a json"""

        matches = []
        punc = ["!", ",", ".", ":", ";"]

        for item in punc:
            if item in self.tweet:
                self.tweet = self.tweet.lower().replace(item, "")

        with open("./files/companies.txt") as company_lines:
            for line in company_lines:
                for word in self.tweet.split():
                    if word.lower() == line.strip():
                        matches.append(line.strip())

        company_dict = tf.open_json()

        # Information that is needed by get_initial/current
        for company in matches:
                company_dict[company] = {}
                company_dict[company]["Symbol"] = "unknown"
                company_dict[company]["Date-mentioned"] = "{:%d-%m-%Y %H:%M:%S}".format(datetime.datetime.now())
                company_dict[company]["Days-left"] = 7
                company_dict[company]["Initial-share-price"] = 1
                company_dict[company]["Current-share-price"] = 1
                company_dict[company]["Share-price-list"] = []

        tf.write_to_json(company_dict)
        return matches

    def get_initial_company_info(self):
        """Gets the initial information for each company"""
        
        company_dict = tf.open_json()

        driver = webdriver.PhantomJS("./files/PhantomJS",
                                     service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any'])

        url = "https://uk.finance.yahoo.com/"
        driver.get(url)

        for company in company_dict:
            # Gets symbol for company
            if company_dict[company]["Symbol"] == "unknown":
                time.sleep(2)  # stops it from returning an error
                try:
                    elem = driver.find_element_by_name("p")
                    elem.send_keys(company)
                    elem.send_keys(Keys.RETURN)

                    time.sleep(3)  # allows time for the page to load
                    symbol = driver.current_url.split("=")[-1]

                    company_dict[company]["Symbol"] = symbol

                except Exception:
                    pass

            # Gets initial share price
            if company_dict[company]["Initial-share-price"] == 1:
                try:
                    yahoo = Share(company_dict[company]["Symbol"])
                    share = yahoo.get_price()

                    company_dict[company]["Initial-share-price"] = float(share)

                except Exception:
                    pass

            # current-share-price
            if company_dict[company]["Current-share-price"] == 1:
                try:
                    yahoo = Share(company_dict[company]["Symbol"])
                    share = yahoo.get_price()

                    company_dict[company]["Current-share-price"] = float(share)

                except Exception:
                    pass

        # writes info back into the monitor json
        tf.write_to_json(company_dict)

    def get_current_shares(self):
        """Gets current shares, compares it to initial, finds difference.
           Returns for output to handle"""

        company_dict = tf.open_json()

        for company in company_dict:
            try:
                yahoo = Share(company_dict[company]["Symbol"])
                share = yahoo.get_price()

                company_dict[company]["Current-share-price"] = share
                company_dict[company]["Share-price-list"].append(share)

            except Exception:
                pass

        tf.write_to_json(company_dict)

    def minus_days(self):
        company_dict = tf.open_json()

        for company in company_dict:
            if company_dict[company]["Days-left"] > 0:
                company_dict[company]["Days-left"] = company_dict[company]["Days-left"] - 1

            elif company_dict[company]["Days-left"] == 0:
                del company_dict[company]


class Output(object):

    def __init__(self, matches):
        self.matches = matches
        self.twitter = Twitter()

    def tweet(self):
        try:
            for item in self.matches:
                self.twitter.api.update_status(
                    "Yelp, looks like a good time to take a look at your shares in {}! \
Trump just tweeted about them...".format(item.upper()))  # Messy fix this

            twitter_users = tf.open_file(twitter_names_file).split()

            for user in twitter_users:
                self.twitter.api.send_direct_message(screen_name=user, text="Donald just tweeted about {}. \
Might be time to check your shares...".format(",".join(self.matches)))  # This is messy needs to be fixed

        except Exception as error:
            tf.write_to_log("Check tweets error: {}".format(error))

    def email(self):
        try:
            email_list = tf.open_file(email_file)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, email_list,
                            'Trump just tweeted about {}. Might be time to check \
your shares...'.format(",".join(self.matches)))
            server.quit()

        except Exception as error:
            tf.write_to_log("Check tweets error: {}".format(error))


def main():
    while True:
        new_tweet = Twitter().check_tweets()

        if new_tweet:
            matches = Companies(new_tweet).check_companies()
            if matches:
                Output(matches).tweet()
                Output(matches).email()

                # Gets all the initial information needed
                # Only needs to be called once when a company is mentioned
                Companies(new_tweet).get_initial_company_info()


        # Change this to do it every 30 mins or 1 hour
        Companies(new_tweet).get_current_shares()

        Twitter().check_mentions()

        hour = datetime.datetime.now().hour

        if hour == 16:
            # Takes away a day at 4 everday
            Companies(new_tweet).minus_days()

        time.sleep(30)
        print(hour)


if __name__ == "__main__":
    main()

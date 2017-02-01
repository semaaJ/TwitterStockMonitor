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
            new_tweet = self.api.user_timeline(screen_name=TWITTER, count=1)

            for tweet in new_tweet:
                old_tweet = tf.open_file(new_tweet_file).strip()
                print(old_tweet)
                print(tweet.text)
    
                if old_tweet != tweet.text.encode("utf8"):
                    tf.write_to_file(new_tweet_file, tweet.text)
                    return tweet.text.encode("utf8")

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
                self.tweet = self.tweet.lower().replace(item, " ")

        with open("./files/companies.txt") as company_lines:
            for line in company_lines:
                if line.strip() in self.tweet.lower():
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

        driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any'])

        url = "https://uk.finance.yahoo.com/"

        for company in company_dict:
            driver.get(url)
            # Gets symbol for company
            if company_dict[company]["Symbol"] == "unknown":
                time.sleep(3)  # allows time for page to load

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
                yahoo.refresh()
                share = yahoo.get_price()

                company_dict[company]["Current-share-price"] = float(share)
                company_dict[company]["Share-price-list"].append(float(share))

            except Exception:
                pass

        tf.write_to_json(company_dict)

    def minus_days(self):
        company_dict = tf.open_json()
        
        for company in company_dict:
            if company_dict[company]["Days-left"] > 0:
                company_dict[company]["Days-left"] -= 1

            elif company_dict[company]["Days-left"] == 0:
                del company_dict[company]

        tf.write_to_json(company_dict)

    def difference_in_shares(self):
        company_dict = tf.open_json()

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

    def share_output(self):
        # self.matches here == share_difference_dict from difference_in_shares func
        for company in self.matches:
            try:
                self.twitter.api.update_status("{} - Initial Share Price: {} Current Share Price: {} \
Current change: {:.1%} Max change: {:.1%} (from {} to {})".format(company.capitalize(),
                                                                  self.matches[company]["Initial"],
                                                                  self.matches[company]["Current"],
                                                                  self.matches[company]["Change"],
                                                                  self.matches[company]["Max-change"],
                                                                  self.matches[company]["Initial"],
                                                                  self.matches[company]["Max"]))
                
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

        Twitter().check_mentions()

        # This is needed to substitute in the classes init
        placeholder = "x"

        # Gets the current share of the company every refresh
        Companies(placeholder).get_current_shares()

        # Outputs the difference in shares
        time_str = "{:%H:%M}".format(datetime.datetime.now())
        if time_str == "18:00":
            share_dict = Companies(placeholder).difference_in_shares()
            Output(share_dict).share_output()
        

        # Removes a day from the json file at 4 daily
        if time_str == "17:00":
            Companies(placeholder).minus_days()


        time.sleep(30)
        print(datetime.datetime.now())


if __name__ == "__main__":
    main()

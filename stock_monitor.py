#!/usr/bin/env python3

import time
import json
import utils
import tweepy
import smtplib
import schedule
import logging
import urllib.request
import urllib.error

from datetime import datetime, timedelta
from pinance import Pinance


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

# Logging setup
logging.basicConfig(filename='./Files/log.txt', level=logging.DEBUG)


##################################
#       TWITTER FUNCTIONS        #
##################################

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_KEY_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


def check_tweets(handle):
    """Checks the twitter handle for new tweets.
       If there has been a new tweet, checks it in the Companies
       class to see if a company is contained in it"""

    try:
        new_tweet = api.user_timeline(screen_name=handle, count=1)

        for tweet in new_tweet:  # Need to find a fix for this loop
            old_tweet = utils.open_file(f'{GENERIC}{handle}.txt')

            if old_tweet != tweet.text:
                utils.write_to_file(f'{GENERIC}{handle}.txt', tweet.text)
                return tweet.text

    except tweepy.TweepError as error:
        logging.debug(f'Error checking the tweets: {error}')


def check_mentions():
    """Checks mentions for sign up's via email or twitter
       via "Sign up / Sign up [email]"""

    try:
        mentions = api.mentions_timeline(count=3)

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
        logging.debug(f'Error checking the mentions: {error}')


##################################
#       COMPANY FUNCTIONS        #
##################################

def check_for_companies(tweet, handle):
    """Checks list of companies with Trump's tweet
       seeing if any companies are listed in his tweet.
       Inputs matches into monitor.json"""

    matches = []
    punc = ("!", ",", ".", ":", ";", "@", "?", "(", ")")

    edited_tweet = ''.join([letter for letter in tweet if letter not in punc]).lower()

    with open(COMPANIES) as f:
        companies = [line.strip() for line in f]

    for word in edited_tweet.split():
        # Binary search for word, using bisect module here instead
        if utils.find(companies, word):
            matches.append(word)

    company_dict = utils.open_json(MONITOR)
    comp_d = {}

    # Information that is needed by get_initial/current
    # Fix error: If a company is mentioned that is already in the json, it overwrites it.
    for company in matches:
        comp_d[company] = {}
        comp_d[company]["Date-mentioned"] = "{:%d-%m-%Y %H:%M:%S}".format(datetime.now())
        comp_d[company]["Handle"] = handle
        comp_d[company]["Tweet"] = tweet
        comp_d[company]["Day"] = 1
        comp_d[company]["Symbol"] = "unknown"
        comp_d[company]["Initial-share-price"] = 1
        comp_d[company]["Current-share-price"] = 1
        comp_d[company]["Share-price-list"] = {"1": [], "2": [], "3": [], "4": [], "5": [], "6": [], "7": []}

    company_dict.update(comp_d)
    utils.write_to_json(MONITOR, company_dict)

    return matches


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
                logging.debug(f'Error with URLLIB: {error}')

        # Gets initial share price
        if company_dict[company]["Initial-share-price"] == 1:
            stock = Pinance(company_dict[company]["Symbol"])
            stock.get_quotes()

            share = stock.quotes_data["LastTradePrice"]

            company_dict[company]["Initial-share-price"] = float(share)
            company_dict[company]["Current-share-price"] = float(share)

    utils.write_to_json(MONITOR, company_dict)


def get_current_shares():
    """Gets current shares, writes updated version back to json"""

    company_dict = utils.open_json(MONITOR)

    for company in company_dict:
        try:
            stock = Pinance(company_dict[company]["Symbol"])
            stock.get_quotes()

            share = stock.quotes_data["LastTradePrice"]

            current_day = str(company_dict[company]["Day"])
            company_dict[company]["Current-share-price"] = float(share)
            company_dict[company]["Share-price-list"][current_day].append(float(share))

        except TypeError as error:
            # Will catch the error if share returns a value other than a float
            logging.debug(f'Error with yahoo_finance: {error}')

    utils.write_to_json(MONITOR, company_dict)


def difference_in_shares():
    """Finds the difference in shares.
       Creates a dict to be used by Output"""

    company_dict = utils.open_json(MONITOR)

    share_difference_dict = {}

    for company in company_dict:
        current_day = company_dict[company]["Day"]

        share_change = 1.0 - (company_dict[company]["Initial-share-price"] /
                              company_dict[company]["Current-share-price"])

        maximum = 1 - (company_dict[company]["Initial-share-price"] /
                       max(company_dict[company]["Share-price-list"][str(current_day)]))

        share_difference_dict[company] = {}
        share_difference_dict[company]["Change"] = share_change
        share_difference_dict[company]["Max-change"] = maximum
        share_difference_dict[company]["Initial"] = company_dict[company]["Initial-share-price"]
        share_difference_dict[company]["Current"] = company_dict[company]["Current-share-price"]
        share_difference_dict[company]["Handle"] = company_dict[company]["Handle"]

    return share_difference_dict


def add_days():
    """Adds a day from the "Day",
       removes from monitor.json if day is 7"""

    company_dict = utils.open_json(MONITOR)
    remove = []

    for company in company_dict:
        if company_dict[company]["Day"] < 7:
            company_dict[company]["Day"] += 1
        else:
            remove.append(company)

    for company in remove:
        # Do I want to keep a record of all the companies that have been mentioned and their prices???
        # Create a folder called past mentions, put each company into its own file??
        # Intel_Mentioned_
        del company_dict[company]

    utils.write_to_json(MONITOR, company_dict)


##################################
#       OUTPUT FUNCTIONS         #
##################################


def tweet(handle, matches):
    """Tweets and DMs the company that has been mentioned"""

    try:
        for company in matches:
            api.update_status(
                f'Yelp, looks like a good time to take a look at your shares in {company.upper()}! '
                f'{handle} just mentioned them!')

        twitter_users = utils.open_file(TWITTER_NAMES).split()

        for user in twitter_users:
            time.sleep(2)
            api.send_direct_message(screen_name=user,
                                    text=f'{handle} just tweeted about {company.upper()}! '
                                         f'Might be time to check your shares!')

    except tweepy.TweepError as error:
        logging.debug(f'Error tweeting: {error}')


def email(handle, matches):
    """Emails a list of people"""

    company_output = ', '.join([company.upper() for company in matches])

    try:
        email_list = utils.open_file(EMAILS).split()

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, email_list,
                        f'{handle} just tweeted about {company_output}. '
                        f'Might be time to check your shares...')
        server.quit()

    except smtplib.SMTPResponseException as error:
        logging.debug(f'Email error: {error}')


def share_output():
    """Calls difference_in_shares from the Companies module,
        Outputs the data to twitter."""

    share_dict = difference_in_shares()

    for company in share_dict:
        try:
            # If you're following one person, this can be changed to look better
            # Remove "[Mentioned by: {company["Handle"]}" in the first line.
            api.update_status(f'{company.capitalize()} Mentioned by: {share_dict[company]["Handle"]}  '
                              f'Initial Share Price: {share_dict[company]["Initial"]:.2f} '
                              f'Current Share Price: {share_dict[company]["Current"]:.2f} '
                              f'Current change: {share_dict[company]["Change"]:.2f} '
                              f'Max change: {share_dict[company]["Max-change"]:.2f}'
                              )

        except tweepy.TweepError as error:
            logging.debug(f'Error tweeting (Shares): {error}')


def initial_start():
    print("Welcome to the Twitter Stock Monitor!")
    twitter_handles = input("Enter the Twitter handles you want this bot to follow, separated by spaces: \n").split()

    json_data = utils.open_json("./Files/config.json")

    json_data["Twitter-Auth"]["Handles"] = twitter_handles
    json_data["Files"]["InitialStart"] = False

    utils.write_to_json("./Files/config.json", json_data)

    print("Creating files needed..")

    for handle in twitter_handles:
        with open(f'{GENERIC}{handle}.txt', "w") as f:
            continue

    print(f'Files created! This bot will now begin to monitor: {twitter_handles}\n\n\n')

    return twitter_handles


def main():
    # Checks if this is the first time running the script
    # Allows the user to choose the Twitter Handles to follow
    # Sets the TWITTER_HANDLES which is an empty list, to the new updated list
    if INITIAL_START:
        handles = initial_start()
    else:
        handles = TWITTER_HANDLES

    # Sets up jobs for schedule to handle
    schedule.every().day.at("07:00").do(add_days)
    schedule.every().day.at("18:00").do(share_output)

    while True:
        for handle in handles:
            new_tweet = check_tweets(handle)

            # Checks if a new tweet has been posted
            # If it has, checks for companies within the tweet
            if new_tweet:
                matches = check_for_companies(new_tweet, handle)

                # If there is a company mentioned
                if matches:
                    # Gets the initial company info
                    get_initial_company_info()

                    # Outputs the matches via twitter/email
                    tweet(handle, matches)
                    email(handle, matches)

            # Checks mentions for sign ups/removals
            check_mentions()

        # Gets current share price for each company being monitored
        # Checks if there are any schedules to be run
        get_current_shares()
        schedule.run_pending()

        now = datetime.now()
        print(f'Running: {now.hour}:{now.minute} - {now.day}/{now.month}/{now.year}')
        time.sleep(30)

if __name__ == "__main__":
    main()

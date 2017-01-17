#!/usr/bin/env python3

import json
import tweepy
import datetime
import smtplib
import time

from yahoo_finance import Share
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup


CONFIG_FILE = "config.json"

class Config(object):

    with open(CONFIG_FILE, "r") as f:
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



class Log():

    config = Config()

    def write_to_log(self, input):
        with open(self.config.LOG, "r+") as f:
            f.write("{} {:%d-%m-%Y %H:%M:%S}".format(input, datetime.datetime.now()))

            
class Twitter(object):

    def __init__(self):
        self.config = Config()
        self.log = Log()

        auth = tweepy.OAuthHandler(self.config.CONSUMER_KEY, self.config.CONSUMER_KEY_SECRET)
        auth.set_access_token(self.config.ACCESS_TOKEN, self.config.ACCESS_TOKEN_SECRET)

        self.api = tweepy.API(auth)


    def check_tweets(self):
        '''Checks for a new tweet'''
        '''If there's a new tweet, returns it to be checked for companies'''

        try:
            new_tweet = self.api.user_timeline(screen_name = self.config.TWITTER, count=1) #self.config.TWITTER

            #there has to be a better way to do this...
            for tweet in new_tweet:
                #Checking if newest tweet is the same as the one stored
                with open(self.config.NEW_TWEET, "r") as f:
                    old_tweet = f.read().strip() 

                if old_tweet != tweet.text:
                    with open(self.config.NEW_TWEET, "r+") as f:
                        f.write(tweet.text)

                    return tweet.text 

        except Exception as error:
            self.log.write_to_log("Twitter error: {}".format(error))


    def check_mentions(self):
        '''Checks mentions for sign up's via email or twitter
           via "Sign up [email]" '''

        '''@DonaldTrumpStatBot Sign up == Twitter username'''
        '''@DonalTrumpStatBot Sign up hello@gmail.com == Email'''

        '''@DonaldTrumpStatBot STOP == Twitter'''
        '''@DonaldTrumpStatBot STOP hello@gmail.com == Email'''
        
        try:
            mentions = self.api.mentions_timeline(count=1)

            for mention in mentions:
                #unsubscribe feature
                if "STOP" in mention.text:
                    #email
                    if len(mention.text.split()) == 3:

                        email = mention.text.split()[2]
                        email_list = []

                        with open(self.config.EMAILS, "r") as f:
                            lines = f.read().split()
                            
                            if email in lines:
                                for line in lines:
                                    if line.strip() != email:
                                        email_list.append(line.strip())

                            with open(self.config.EMAILS, "w") as f:
                                for item in email_list:
                                    f.write("{} \n".format(item))

                    else:

                        twitter_name = mention.user.screen_name
                        twitter_list = []

                        with open(self.config.TWITTER_NAMES, "r") as f:
                            lines = f.read().split()
                            
                            if twitter_name in lines:
                                for line in lines:
                                    if line.strip() != twitter_name:
                                        twitter_list.append(line.strip())

                            with open(self.config.TWITTER_NAMES, "w") as f:
                                for item in twitter_list:
                                    f.write("{} \n".format(item))
                                    
        
                elif "Sign up" in mention.text:
                    #Checks for email sign up
                    #Adds email to subscription
                    if len(mention.text.split()) > 3:
                        email = mention.text.split()[3]

                        with open(self.config.EMAILS, "r+") as f:
                            lines = f.read().split()

                            if email not in lines:
                                f.write("{} \n".format(email.strip()))
        

                    #Adds twitter username to subscription
                    else:
                        twitter_name = mention.user.screen_name
                    
                        with open(self.config.TWITTER_NAMES, "r+") as f:
                            lines = f.read()
                        
                            if mention.user.screen_name not in lines:
                                f.write("{} \n".format(twitter_name))
                    
                    

        except ValueError as error:
            self.log.write_to_log("Twitter error: {}".format(error))



class Companies(object):
    
    def __init__(self, tweet):
        self.config = Config()
        self.log = Log()
        self.tweet = tweet
    
    def check_companies(self):
        '''Checks list of companies with Trump's tweet
           seeing if any companies are listed in his tweet

           Inputs matches into a json'''

        matches = []
        punc = ["!", ",", ".", ":", ";"]

        for item in punc:
            if item in self.tweet:
                self.tweet = self.tweet.replace(item, "")
        
        with open(self.config.COMPANIES, "r") as f:
            for line in f:
                for word in self.tweet.split():
                    if word.lower() == line.strip():
                        matches.append(line.strip())
    

        with open(self.config.MONITOR, "r") as f:
            company_dict = json.load(f)


            for company in matches:
                company_dict[company] = {}
                company_dict[company]["Symbol"] = "unknown"
                company_dict[company]["Date-mentioned"] = "{:%d-%m-%Y %H:%M:%S}".format(datetime.datetime.now())
                company_dict[company]["Days-left"] = 7
                company_dict[company]["Initial-share-price"] = 1
                company_dict[company]["Current-share-price"] = 1

            with open(self.config.MONITOR, "r+") as f:
                json.dump(company_dict, f)
            

        return matches


    def get_and_check_shares(self):
        '''Opens monitor.json dictonary and gets the initial/current
           share price/symbol. Returns current share to be outputted'''

        share_difference = {}

        with open(self.config.MONITOR, "r") as f:
            company_dict = json.load(f)


        driver = webdriver.PhantomJS("C:\Python34\Scripts\phantomjs", service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any'])
        url = "https://uk.finance.yahoo.com/"
        driver.get(url)
        
        for company in company_dict:
            #Gets company symbol using yahoo finance's website
            if company_dict[company]["Symbol"] == "unknown":
            
                time.sleep(2) #stops it from returning an error

                try:
                    elem = driver.find_element_by_name("p")
                    elem.send_keys(company)
                    elem.send_keys(Keys.RETURN)

                    time.sleep(3) #allows time for the page to load
                    symbol = driver.current_url.split("=")[-1]

                    company_dict[company]["Symbol"] = symbol

                except Exception:
                    pass

            #Gets intial share price
            if company_dict[company]["Initial-share-price"] == 1:
                try:
                    yahoo = Share(company_dict[company]["Symbol"])
                    share = yahoo.get_price()

                    company_dict[company]["Initial-share-price"] = float(share)

                except Exception:
                    pass

            #current-share-price
            try:
                yahoo = Share(company_dict[company]["Symbol"])
                share = yahoo.get_price()

                company_dict[company]["Current-share-price"] = float(share)

            except Exception:
                pass
                  

            #Days left to be monitored
            if company_dict[company]["Days-left"] > 0:
                company_dict[company]["Days-left"] - 1

            elif company_dict[company]["Days-left"] == 0:
                del company_dict[company]
                

            #Gets decrease in share price in %
            decrease_in_shares = (company_dict[company]["Current-share-price"] / company_dict[company]["Initial-share-price"])

            if decrease_in_shares > 1:
                share_difference[company] = "+{0:.2f}".format(decrease_in_shares - 1)

            else:
                share_difference[company] = "-{0:.2f}".format(1 - decrease_in_shares)
            

        with open(self.config.MONITOR, "r+") as f:
                json.dump(company_dict, f)

        
        return share_difference
    

class Output(object):

    def __init__(self, matches):
        self.config = Config()
        self.log = Log()
        self.twitter = Twitter()
        self.matches = matches


    def tweet(self):    
        try:      
            for item in self.matches:
                self.twitter.api.update_status("Yelp, looks like a good time to take a look at your shares in {}! Trump just tweeted about them...".format(item.upper()))

            with open(self.config.TWITTER_NAMES, "r") as f:
                twitter_users = f.read().split()

            for user in twitter_users:
                    self.twitter.api.send_direct_message(screen_name = user, text = "Donald just tweeted about {}. Might be time to check your shares...".format(",".join(self.matches)))
                    
            
        except Exception as error:
            self.log.write_to_log("Twitter output error: {}".format(error))
            

    def email(self):
        try:
            with open(self.config.EMAILS, "r") as f:
                email_list = f.read().split()
                  
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.config.EMAIL, self.config.PASSWORD)
            server.sendmail(self.config.EMAIL, email_list, 'Trump just tweeted about {}. Might be time to check your shares...'.format(",".join(self.matches)))
            server.quit()

        except Exception as error:
            self.log.write_to_log("Email output error: {}".format(error))
        


    def subscribe(self):
        time = datetime.datetime.now().hour

        if time == 10 or time == 17:
            try:
                self.twitter.api.update_status('''You can subscribe to be notified of Donald's activities via: "@DonaldTrumpStatsBot Sign up" or "@DonaldTrumpStatsBot Sign up [your-email]"''')

            except Exception as error:
                self.log.write_to_log("Subscribe output error: {}".format(error))

        elif time == 12 or time == 20:
            try:           
                self.twitter.api.update_status("To recieve DM updates, make sure you've subscribed and followed me!")

            except Exception as error:
                self.log.write_to_log("Subscribe output error: {}".format(error))


    def share_output(self):
        #self.matches == share_difference dict
        for item in self.matches:
            self.twitter.api.update_status("Since trump tweeted about {}, their shares have changed by {}!".format(item, self.matches[item]))
            

def main():
    #Checks for new tweets
    new_tweet = Twitter().check_tweets()
    #checks to see if any words in company list
    matches = Companies(new_tweet).check_companies()

    #if a new tweet is returned
    if new_tweet:
        #if any matches are returned
        if matches:
            Output(matches).tweet()
            Output(matches).email()


    Twitter().check_mentions()
    Output(matches).subscribe()


    #Setting up the shares to be checked at 4'o clock daily
    current_time = datetime.datetime.now().hour
    
    if current_time == 16:
        share_difference_dict = Companies(new_tweet).get_and_check_shares()
        Output(share_difference_dict).share_output()


    time.sleep(40)
    main()

if __name__ == "__main__":
    main()
        

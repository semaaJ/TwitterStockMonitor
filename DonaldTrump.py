import json
import tweepy
import datetime
import smtplib


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
            new_tweet = self.api.user_timeline(screen_name = self.config.TWITTER, count=1)

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
            self.log.write_to_log("Twitter error: ")


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
                        
                        with open("emails.txt", "r") as f:
                            lines = f.read().split()
                            
                            if email in lines:
                                for line in lines:
                                    if line.strip() != email:
                                        email_list.append(line.strip())

                            with open("emails.txt", "w") as f:
                                for item in email_list:
                                    f.write("{} \n".format(item))

                    else:

                        twitter_name = mention.user.screen_name
                        twitter_list = []
                        
                        with open("twitter_names.txt", "r") as f:
                            lines = f.read().split()
                            
                            if twitter_name in lines:
                                for line in lines:
                                    if line.strip() != twitter_name:
                                        twitter_list.append(line.strip())

                            with open("twitter_names.txt", "w") as f:
                                for item in twitter_list:
                                    f.write("{} \n".format(item))
                                    
                #Checks for email sign up
                #Adds email to subscription
                elif len(mention.text.split()) > 3:
                    email = mention.text.split()[3]

                    with open("emails.txt", "r+") as f:
                        lines = f.read().split()

                        if email not in lines:
                            f.write("{} \n".format(email.strip()))
        

                #Adds twitter username to subscription
                else:
                    twitter_name = mention.user.screen_name
                    
                    with open("twitter_names.txt", "r+") as f:
                        lines = f.read()
                        
                        if mention.user.screen_name not in lines:
                            f.write("{} \n".format(twitter_name))
                    
                    

        except ValueError as error:
            self.log.write_to_log("Twitter error: ")


class Finance(object):
    #checking if Donald's tweets include companies
    #If they are, put them into a file for another script to monitor their stocks for 7 days
    def __init__(self, tweet):
        self.tweet = tweet
    
    def check_companies(self):
        '''Checks list of companies with Trump's tweet
           seeing if any companies are listed in his tweet'''

        matches = []
        
        with open("companies.txt", "r") as f:
            for line in f:
                for word in self.tweet.split():
                    if word.lower() == line.strip():
                        matches.append(line)

        print(matches)
        return matches

            


class Output(object):

    def __init__(self, matches):
        self.config = Config()
        self.twitter = Twitter()
        self.matches = matches


    def tweet(self):
        for item in self.matches:
            self.twitter.api.update_status('''Yelp, looks like a good time to take a look at
                                              your shares in {}! Trump just tweeted about them...'''.format(item)
    

    def email(self):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('weather4castbot@gmail.com', 'cosmos2011')
        server.sendmail('weather4castbot@gmail.com', emails, message)
        server.quit()
        


    def subscribe(self):
        time = int("{:%M}".format(datetime.datetime.now()))

        if time == 00:
            self.twitter.api.update_status('''You can subscribe to be notified of Donald's activities via:
                                              "@DonaldTrumpStatsBot Sign up" or "@DonaldTrumpStatsBot Sign up [your-email]"'''
            


def main():
    Twitter().check_mentions()

    #if a new tweet is returned
    #if Twitter().check_tweets():
    #    Finance(tweets).check_companies()


if __name__ == "__main__":
    main()
        

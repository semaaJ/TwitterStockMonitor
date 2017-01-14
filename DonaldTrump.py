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
            new_tweet = self.api.user_timeline(screen_name = "testytesticals", count=1)

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
                                    
                #Checks for email sign up
                #Adds email to subscription
                elif len(mention.text.split()) > 3:
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


class Finance(object):
    
    def __init__(self, tweet):
        self.config = Config()
        self.log = Log()
        self.tweet = tweet
    
    def check_companies(self):
        '''Checks list of companies with Trump's tweet
           seeing if any companies are listed in his tweet

           Inputs files into a text file which can be monitored by
           another script'''

        matches = []
        
        with open(self.config.COMPANIES, "r") as f:
            for line in f:
                for word in self.tweet.split():
                    if word.lower() == line.strip():
                        matches.append(line.strip())
    

        with open(self.config.MONITOR, "r+") as f:
            lines = f.read().split()

            for item in matches:
                if item not in lines:
                    f.write("Company: {}    Date tweeted: {:%d-%m-%Y %H:%M:%S}   Days remaining: 7 \n".format(item, datetime.datetime.now()))

        return matches

    



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
                    self.twitter.api.send_direct_message(user, "Donald just tweeted about {}. Might be time to check your shares...".format(matches))


    
            
        except Exception as error:
            self.log.write_to_log("Twitter output error: {}".format(error))
            

    def email(self):
        try:
            with open(self.config.EMAILS, "r") as f:
                email_list = f.read().split()
                  
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.config.EMAIL, self.config.PASSWORD)
            server.sendmail(self.config.EMAIL, email_list, 'Trump just tweeted about {}. Might be time to check your shares...'.format(self.matches))
            server.quit()

        except Exception as error:
            self.log.write_to_log("Email output error: {}".format(error))
        


    def subscribe(self):
        time = int("{:%M}".format(datetime.datetime.now()))

        if time == 00:
            try:
                self.twitter.api.update_status('''You can subscribe to be notified of Donald's activities via: "@DonaldTrumpStatsBot Sign up" or "@DonaldTrumpStatsBot Sign up [your-email]"''')

            except Exception as error:
                self.log.write_to_log("Subscribe output error: {}".format(error))

        elif time == 35:
            try:           
                self.twitter.api.update_status("To recieve DM updates, make sure you've subscribed and followed me!")

            except Exception as error:
                self.log.write_to_log("Subscribe output error: {}".format(error))
            


def main():
    #Checks for new tweets
    new_tweet = Twitter().check_tweets()
    #checks to see if any words in company list
    matches = Finance(new_tweet).check_companies()

    #if a new tweet is returned
    if new_tweet:
        #if any matches are returned
        if matches:
            Output(matches).tweet()
            Output(matches).email()


    Twitter().check_mentions()
    Output(matches).subscribe()

        


if __name__ == "__main__":
    main()
        

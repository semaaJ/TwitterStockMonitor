import json
import tweepy


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

    def write_to_log(input):
        with open(config.LOG, "r+") as f:
            f.write(input)


class Twitter(object):

    def __init__(self):
        self.config = Config()
        self.log = Log()

        auth = tweepy.OAuthHandler(self.config.CONSUMER_KEY, self.config.CONSUMER_KEY_SECRET)
        auth.set_access_token(self.config.ACCESS_TOKEN, self.config.ACCESS_TOKEN_SECRET)

        self.api = tweepy.API(auth)


    def check_tweets(self):
        '''Checks for a new tweet'''
        try:
            new_tweet = self.api.user_timeline(screen_name = self.config.TWITTER, count=1)

            #there has to be a better way to do this...
            for tweet in new_tweet:
                #Checking if newest tweet is the same as the one stored
                with open(self.config.NEW_TWEET, "r") as f:
                    old_tweet = f.read().strip()

                if old_tweet == tweet.text:
                    pass
                    #this will be a function that is called to wait 20 seconds or so before rechecking.
                
                else:    
                    with open(self.config.NEW_TWEET, "r+") as f:
                        f.write(tweet.text)

                    #function here that will call in finance to check companies

        except Exception as error:
            self.log.write_to_log("Twitter error: {}".format(error))


    def tweet(self):
        pass
        

class Finance(object):
    #checking if Donald's tweets include companies
    #If they are, put them into a file for another script to monitor their stocks for 7 days
    
    pass

class Output(object):
    #Include email, tweet maybe?
    pass

def main():
    Twitter().check_tweets()

if __name__ == "__main__":
    main()
        

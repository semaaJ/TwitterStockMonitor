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

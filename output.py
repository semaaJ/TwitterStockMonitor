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

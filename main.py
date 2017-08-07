
import json
import schedule
import company
import smtplib
import logging

from time import sleep
from datetime import datetime

logging.basicConfig(filename='./Files/logs.txt', level=logging.DEBUG,
                    format='%(asctime)s :~: %(funcName)s :~: %(message)s')

with open("./Files/config.json", "r") as f:
    config = json.load(f)

# Boolean value
INITIAL_START = config["InitialStart"]

# Email/Password info
EMAIL = config["EmailInfo"]["Email"]
PASSWORD = config["EmailInfo"]["Password"]

# Twitter keys/names
CONSUMER_KEY = config["TwitterAuth"]["ConsumerKey"]
CONSUMER_KEY_SECRET = config["TwitterAuth"]["ConsumerSecret"]
ACCESS_TOKEN = config["TwitterAuth"]["AccessToken"]
ACCESS_TOKEN_SECRET = config["TwitterAuth"]["AccessTokenSecret"]
TWITTER_HANDLES = config["TwitterAuth"]["Handles"]


def email(handle, matches):
    """Emails a list of people"""

    company_output = ', '.join([comp.upper() for comp in matches])

    try:
        with open('./Files/emails.txt') as f:
            email_list = f.read().split()

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, email_list,
                        f'{handle} just tweeted about {company_output}. '
                        f'Might be time to check your shares...')
        server.quit()

    except smtplib.SMTPResponseException as error:
        logging.debug(error)


def initial_start():
    print("Welcome to the Twitter Stock Monitor!")
    twitter_handles = input("Enter the Twitter handles you want this bot to follow, separated by spaces: \n").split()

    with open('./Files/config.json') as json_f:
        json_data = json.load(json_f)

    json_data["TwitterAuth"]["Handles"] = twitter_handles
    json_data["InitialStart"] = False

    with open('./Files/config.json', 'w') as json_f:
        json.dump(json_data, json_f, sort_keys=True, indent=4, ensure_ascii=False)

    print("Creating files needed..")

    for handle in twitter_handles:
        with open(f'./Files/LatestTweets/{handle}.txt', "w") as f:
            continue

    print(f'Files created! This bot will now begin to monitor: {twitter_handles}\n\n\n')

    return twitter_handles


from twitter import Twitter


def main():
    # Checks if this is the first time running the script
    # Allows the user to choose the Twitter Handles to follow
    # Sets the TWITTER_HANDLES which is an empty list, to the new updated list
    if INITIAL_START:
        handles = initial_start()
    else:
        handles = TWITTER_HANDLES

    # Sets up share_output job
    twit = Twitter()
    schedule.every().day.at("18:00").do(twit.share_output)
    schedule.every(15).minutes.do(company.current_day)

    while True:
        for handle in handles:
            twitter = Twitter(handle)

            new_tweet = twitter.get_latest_tweet()

            # Checks if a new tweet has been posted
            # If it has, checks for companies within the tweet
            if new_tweet:
                matches = company.check_for_companies(new_tweet, handle)

                # If there is a company mentioned
                if matches:
                    # Gets the initial company info
                    company.get_initial_company_info()

                    # Outputs the matches via twitter/email
                    twitter.initial_tweet()
                    email(handle, matches)

            # Checks mentions for sign ups/removals
            twitter.check_mentions()

        # Gets current share price for each company being monitored
        # Checks if there are any schedules to be run
        company.get_current_shares()
        schedule.run_pending()

        now = datetime.now()
        print(f'Running: {now.hour}:{now.minute} - {now.day}/{now.month}/{now.year}')
        sleep(30)

if __name__ == "__main__":
    main()

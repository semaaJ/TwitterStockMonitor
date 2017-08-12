# TwitterStockMonitor
This project originally started when I noticed that if Trump mentioned a company within his tweets, their shares would either go up in price if the tweet was positive or drop if the tweet was negative. I decided to make a script to follow Trump and monitor the companies that he mentioned over a week, to see how the tweet affected the price of the company's shares. I have updated this to make it usable for multiple Twitter accounts at the same time. 

## Requirements
For this you will need:
- 
- Pinance
- Tweepy
- NLTK

These can be installed via:
```
pip install pinance
pip install tweepy
pip install nltk
```

## Setup
- You must first set up a [Twitter APP](https://themepacific.com/how-to-generate-api-key-consumer-token-access-key-for-twitter-oauth/994/)

- You need to set up an email and make sure that your account allows [less secure apps](https://support.google.com/accounts/answer/6010255?hl=en)
- Input this data into the config file with your keys and email info like so:

![Config setup](http://i.imgur.com/TBxSICC.png "") 

- If you don't want the email function, you need to remove it from the code. Remove "Output(matches).email()" from the main() function, and remove the entire def email() function inside the Output Class. 
- If you would like to use this with another Twitter user, you need to change the "Twitter" in the Config, to the users Twitter handle.
- You can change the companies you want to be monitored by removing the companies within companies.tx and adding your own, one on each line.



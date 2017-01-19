# DonaldTrumpStockMonitor
A script that montiors Trump's tweets to see if he mentions a company. 
If a company is mentioned, the script will tweet and email subscribers.

The company's share price will then be monitored for a week,
to see what effect Trump's tweet had on them. 

I noticed that when Trump mentioned Toyota in a negative light their shares dipped heavily, while when Fiat and Ford were mentioned in a positive manner they had an increase in shares. I wanted to create something to visualise this. 

## Requirements
For this you will need:
- Selenium
- Yahoo_finance 
- BeautifulSoup

These can be installed via:
```
pip install selenium
pip install yahoo_finance
pip install bs4
```

## Setup
- You must first set up a [Twitter APP](https://themepacific.com/how-to-generate-api-key-consumer-token-access-key-for-twitter-oauth/994/)
- You need to set up an email and make sure that you account allows [less secure apps](https://support.google.com/accounts/answer/6010255?hl=en)
- Input this data into the config file and run :)

Website run with Node.js is located in /site, to install and run:

`$ cd site` 

`$ apt install nodejs npm  `

`$ npm install ` 

`$ nodejs app.js`

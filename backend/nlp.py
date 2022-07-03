import re
import json
import spacy
import gensim
import pandas as pd

from gensim import corpora, models
from cleanco import basename
from nltk.stem import WordNetLemmatizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer

NER = spacy.load("en_core_web_sm")

def extract_hashtags(tweet) -> str:
    '''Extract hashtags from a tweet'''
    hashtag_re = re.compile("(?:^|\s)[＃#]{1}(\w+)", re.UNICODE)
    return hashtag_re.findall(tweet)

def extract_mentions(tweet) -> str:
    '''Extract all non link mentions from a tweet'''
    tweet = remove_links(tweet)
    mention_re = re.compile("(?:^|\s)[＠ @]{1}([^\s#<>[\]|{}]+)", re.UNICODE)
    return mention_re.findall(tweet)

def remove_links(tweet) -> str:
    '''Removes links from a tweet'''
    tweet = re.sub(r'http\S+', '', tweet)   # remove http links
    tweet = re.sub(r'bit.ly/\S+', '', tweet)  # remove bitly links
    return tweet

def preprocess_tweet(tweet) -> str:
    '''Removes links, punctuation, numbers and extra spacing from a tweet'''
    tweet = remove_links(tweet)
    tweet = tweet.lower()  # lower case
    tweet = re.sub('[!"$%&\'()*+,-./:;<=>?[\\]^_`{|}~•@]+', '', tweet)  # strip punctuation
    tweet = re.sub('\s+', ' ', tweet)  # remove double spacing
    tweet = re.sub('([0-9]+)', '', tweet)  # remove numbers
    return tweet

def lemmatize(token) -> list:
    '''Returns lemmatization of a token'''
    return WordNetLemmatizer().lemmatize(token, pos='v')

def tokenize(tweet) -> str:
    '''Returns tokenized representation of words in lemma form excluding stopwords'''
    result = []
    for token in gensim.utils.simple_preprocess(tweet):
        if token not in gensim.parsing.preprocessing.STOPWORDS:
            result.append(lemmatize(token))
    return ' '.join(result)

def vader_sentiment(text):
    """Return vader scores (neg, pos, neu and compound) of a text"""
    sid = SentimentIntensityAnalyzer()
    return sid.polarity_scores(text)

def named_entity_recognition(text):
    """Extract named entities from a text"""
    # Find a way to speed this up
    entities = NER(text)
    return [entity.text for entity in entities.ents if entity.label_ == "ORG" ]

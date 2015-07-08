#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib.request import urlopen
import random
import json
from os import environ, path
import re
import logging
from time import sleep

from lxml import html
from guess_language import guess_language, use_enchant
import tweepy

BASE_URL = 'https://news.google.com.ar'
CONSUMER_KEY = environ['DOSTITULOS_CONSUMER_KEY']
CONSUMER_SECRET = environ['DOSTITULOS_CONSUMER_SECRET']
ACCESS_TOKEN = environ['DOSTITULOS_ACCESS_TOKEN']
ACCESS_SECRET = environ['DOSTITULOS_ACCESS_TOKEN_SECRET']


DEVELOPMENT = False
if DEVELOPMENT:
    log_file = 'dostitulosbot.log'
else:
    log_file = environ['DOSTITULOS_LOG_FILE']

logging.basicConfig(filename=log_file,
                    format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def get_topics(category):
    '''
    Gets topics in a category.
    Returns a list of dictionaries with the name of the topic and the
     corresponding url.
    '''
    topics = []
    url = BASE_URL + '/news/section?ned=es_ar&topic=' + category
    sleep(1)
    tree = html.parse(urlopen(url))
    google_topics = tree.xpath("//div[@class='topic']")
    for google_topic in google_topics:
        topic = dict()
        topic['name'] = google_topic.text_content()
        topic['url'] = BASE_URL + google_topic.xpath('.//@href')[0]
        topics.append(topic)
        log.debug('Available topic: %s', topic['name'])
    return (topics)


def get_headline(topic, otit, topic_1_name):
    '''
    Gets the url of the topic.
    Parses the html for all the titles.
    Checks each title:
        wasn't used recently to generat a title,
        contains the topic,
        doesn't end in ellipsis (...),
        is in spanish.
        doesn't already contain the text that will be used as replacement
    If at least one title is valid it selects one randomly and returns it.
    '''
    valid_headlines = []
    sleep(1)
    tree = html.parse(urlopen(topic['url']))
    headlines = tree.xpath("//span[@class='titletext']")
    while len(headlines) > 0:
        headline = headlines.pop()
        regex = re.compile(r'\b{0}\b'.format(topic['name']), re.IGNORECASE)
        if headline.text_content() in otit:
            log.info('Headline recently used to generate title: %s',
                     headline.text_content())
            continue
        if regex.search(headline.text_content()) is None:
            log.debug('Invalid headline, regex failed on: %s',
                      headline.text_content())
            continue
        if headline.text_content()[-3:] == '...':
            log.debug('Invalid headline, ellipsis on: %s',
                      headline.text_content())
            continue
        if guess_language(headline.text_content()) != 'es':
            log.debug('Invalid headline, not spanish on: %s',
                      headline.text_content())
            continue
        if topic_1_name in headline.text_content():
            log.debug('Invalid headline %s, contains replacement: %s',
                      headline.text_content(), topic_1_name)
            continue
        valid_headlines.append(headline.text_content())
        log.debug('Valid headline: %s', headline.text_content())

    if len(valid_headlines) > 0:
        log.info('%s valid headlines found for topic %s',
                 len(valid_headlines), topic['name'])
        return (random.choice(valid_headlines))
    else:
        log.info('No valid headlines found for topic %s', topic['name'])
        return False


def find_title(ltit, otit, ltop, otop):
    '''
    Selects a random category.
    Selects a topic on that category.
    If the topic was used recently the previous steps are repeated.
    Removes the first used category.
    Selects a second random category.
    Removes topics in category 2 present on category 1.
    Selects a second random topic from the filtered topics list.
    Check topic not recently used.
    Gets a title from the selected second topic.
    Replaces the second topic in the title with the first topic.
    Checks that the generated title wasn't tweeted recently.
    Saves the original titles file.
    Returns the new title.
    '''
    use_enchant(True)
    categories = ['w', 'n', 'b', 't', 'e', 's']
    valid_topic = False
    count = 0
    while not valid_topic:
        category = random.choice(categories)
        topics_1 = get_topics(category)
        while len(topics_1) > 1 and not valid_topic:
            topic_1 = random.choice(topics_1)
            topics_1.remove(topic_1)
            if topic_1['name'] not in ltop:
                valid_topic = True
            else:
                log.info('Skipping recently used topic: %s',
                         topic_1['name'])
        count += 1
        if count >= 100:
            log.warning('Exited script with no new topics found')

    categories.remove(category)
    log.info('Category 1:  %s', category)
    log.info('Topic 1: %s', topic_1['name'])

    category = random.choice(categories)
    log.info('Category 2:  %s', category)
    topics_2 = get_topics(category)
    for top_1 in topics_1:
        for top_2 in topics_2:
            if top_1['name'] == top_2['name']:
                topics_2.remove(top_2)
                log.info('Remove duplicate topic: %s', top_2['name'])

    for i, top_2 in enumerate(topics_2):
        if topic_1['name'] == top_2['name']:
            topics_2.pop(i)
            log.info('Removed chosen topic 1 from topic list 2: %s',
                     topic_1['name'])
        elif top_2['name'] in otop:
            topics_2.pop(i)
            log.info('Removed recently used topic as original: %s',
                     top_2['name'])
    if len(topics_2) > 0:
        topic_2 = random.choice(topics_2)
    else:
        log.info('No topics left after filtering')
        return False
    log.info('Topic 2: %s', topic_2['name'])

    headline = get_headline(topic_2, otit, topic_1['name'])
    if headline is not False:
        log.info('Original title: %s', headline)
        regex = re.compile(r'\b{0}\b'.format(topic_2['name']), re.IGNORECASE)
        new_headline = re.sub(regex, topic_1['name'], headline, count=1)
        if new_headline not in ltit:
            otit.append(headline)
            ltop.append(topic_1['name'])
            otop.append(topic_2['name'])
            with open('original_titles.txt', 'w') as original_titles:
                json.dump(otit[-240:], original_titles, ensure_ascii=False)
            with open('last_topics.txt', 'w') as last_topics:
                json.dump(ltop[-40:], last_topics, ensure_ascii=False)
            with open('original_topics.txt', 'w') as original_topics:
                json.dump(otop[-30:], original_topics, ensure_ascii=False)
            return new_headline
        else:
            log.info('Generated headline tweeted recently: %s', headline)
            return False
    else:
        log.info('Invalid headline discarded')
        return False
    log.warning('Script should not reach this point')
    return False


def tweet(text):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.secure = True
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth)
    log.info('About to tweet: %s', text)
    if not DEVELOPMENT:
        api.update_status(status=text)
    else:
        api.me()
    log.info('Tweeted succesfully')
    return


def main():
    log.info('Starting script')

    # File with json of last tweeted titles
    if path.isfile('last_titles.txt'):
        with open('last_titles.txt', 'r') as last_titles:
            ltit = json.load(last_titles)
    else:
        ltit = list()

    # File with json of last original titles
    if path.isfile('original_titles.txt'):
        with open('original_titles.txt', 'r') as original_titles:
            otit = json.load(original_titles)
    else:
        otit = list()

    # File with json of last used topics as replace
    if path.isfile('last_topics.txt'):
        with open('last_topics.txt', 'r') as last_topics:
            ltop = json.load(last_topics)
    else:
        ltop = list()

    # File with json of last used topics as original
    if path.isfile('original_topics.txt'):
        with open('original_topics.txt', 'r') as original_topics:
            otop = json.load(original_topics)
    else:
        otop = list()

    next_headline = False
    retries = 0
    while next_headline is False and retries < 30:
        next_headline = find_title(ltit, otit, ltop, otop)
        if next_headline is False:
            sleep(5)
        retries += 1
    if retries == 30:
        log.info('Reached max retries, exiting')
        exit()
    log.info('After %d try, title selected: %s', retries, next_headline)

    tweet(next_headline)

    # Save json to files
    ltit.append(next_headline)
    with open('last_titles.txt', 'w') as last_titles:
        json.dump(ltit[-240:], last_titles, ensure_ascii=False)
    log.info('Finished script')

if __name__ == '__main__':
    main()

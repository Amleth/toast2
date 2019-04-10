import argparse
import configparser
from pymongo import MongoClient
import requests
from selenium.webdriver.common.keys import Keys
from scrapy.selector import Selector
from selenium import webdriver
import time
from twitter_common import get_tweet_url

###############################################################################
#
# CONF
#
###############################################################################

# Paramètres passés au script
parser = argparse.ArgumentParser()
parser.add_argument("--db")
parser.add_argument("--coll")
args = parser.parse_args()

# Paramètres lus dans le fichier de configuration
config = configparser.ConfigParser()
config.read("toast.conf")
symbol = config.get("Conversations", "symbol")
geckodriver_path = config.get("Conversations", "geckodriver_path")

# MongoDB
database_name = args.db
collection_name = args.coll
client = MongoClient()
db = client[database_name]
tweets_collection = db[collection_name]
conversations_collection = db[collection_name + "_conversations"]

###############################################################################
#
# FUNCTIONS
#
###############################################################################


def get_root_tweet_id(tweet_id):
    try:
        response = requests.get(get_tweet_url(tweet_id))
        print(f"{symbol} getting url          : {get_tweet_url(tweet_id)}")
        print(f"{symbol} redirected to        : {response.url}")
        selector = Selector(text=response.content)
        root_tweet_id = selector.css(
            "div.permalink-inner div.tweet ::attr(data-item-id)"
        ).extract_first()
        print(f"{symbol} root tweet id scraped: {get_tweet_url(root_tweet_id)}")
        return root_tweet_id
    except:
        print(f"{symbol} error")
        return False


wait_state = "+"


def next_watit_state():
    global wait_state
    wait_state = {"+": "×", "×": "+"}[wait_state]
    return wait_state


def save_tweet_in_conversation(
    root_tweet_id,
    tweet_id,
    conversation_id,
    tweet_timestamp,
    tweet_text,
    user_id,
    user_name,
    user_screenname,
):
    print(
        symbol,
        root_tweet_id,
        tweet_id,
        conversation_id,
        tweet_timestamp,
        tweet_text,
        user_id,
        user_name,
        user_screenname,
    )
    if not conversations_collection.find_one({"tweet_id": tweet_id}):
        doc = {
            "root_tweet_id": root_tweet_id,
            "tweet_id": tweet_id,
            "conversation_id": conversation_id,
            "tweet_timestamp": tweet_timestamp,
            "tweet_text": tweet_text,
            "user_id": user_id,
            "user_name": user_name,
            "user_screenname": user_screenname,
        }
        conversations_collection.insert_one(doc)


def scrape(root_tweet_id):
    #
    # AJAX REQUESTS TRIGGERED BY MOUSE GESTURES (SCROLLING & CLICKS)
    # AUTOMATISATION
    #

    print(f"{symbol} scraping {get_tweet_url(root_tweet_id)} …")

    browser = webdriver.Firefox(executable_path=geckodriver_path)
    browser.get(get_tweet_url(root_tweet_id))
    page = browser.find_element_by_tag_name("body")

    try:
        # Critère permettant de distinguer les tweets seuls des racines de conversation
        if browser.find_element_by_css_selector("div.stream").is_displayed():
            while not browser.find_element_by_css_selector(
                "div.stream-end-inner"
            ).is_displayed():
                page.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.5)
                print(f"{symbol} appui sur la touche page down {next_watit_state()}")

        more_replies_links = browser.find_elements_by_class_name(
            "ThreadedConversation-moreRepliesLink"
        )
        for x in range(0, len(more_replies_links)):
            if more_replies_links[x].is_displayed():
                print(
                    f"{symbol} clic pour déplier des réponses cachées {next_watit_state()}"
                )
                more_replies_links[x].click()

        #
        # TWEETS SELECTION
        #

        selector = Selector(text=browser.page_source)

        # Root tweet

        root_user_screenname = selector.css(
            "div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-screen-name)"
        ).extract_first()
        root_user_name = selector.css(
            "div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-name)"
        ).extract_first()
        root_user_userid = selector.css(
            "div.permalink-inner.permalink-tweet-container > div.tweet.permalink-tweet ::attr(data-user-id)"
        ).extract_first()
        root_text = (
            selector.css("div.permalink-inner.permalink-tweet-container")
            .css(".TweetTextSize ::text")
            .extract_first()
        )
        root_timestamp = (
            selector.css(".permalink-header")
            .css(".time")
            .css("span ::attr(data-time)")
            .extract_first()
        )

        save_tweet_in_conversation(
            root_tweet_id,
            root_tweet_id,
            0,
            root_timestamp,
            root_text,
            root_user_userid,
            root_user_name,
            root_user_screenname,
        )

        # Conversations

        count = 0
        conversations_count = 0
        lone_tweets_count = 0

        for conversation in selector.css(".ThreadedConversation"):
            conversations_count += 1
            for tweet in conversation.css(".ThreadedConversation-tweet"):
                count += 1
                tweet_id = tweet.css("div.tweet ::attr(data-tweet-id)").extract_first()
                tweet_user_screenname = tweet.css(
                    "div.tweet ::attr(data-screen-name)"
                ).extract_first()
                tweet_user_name = tweet.css(
                    "div.tweet ::attr(data-name)"
                ).extract_first()
                tweet_user_id = tweet.css(
                    "div.tweet ::attr(data-user-id)"
                ).extract_first()
                tweet_text = tweet.css(".TweetTextSize ::text").extract()
                tweet_text = "".join(tweet_text)
                tweet_text = tweet_text.replace("\n", "")
                tweet_timestamp = tweet.css(
                    "span._timestamp ::attr(data-time)"
                ).extract_first()
                save_tweet_in_conversation(
                    root_tweet_id,
                    tweet_id,
                    conversations_count,
                    tweet_timestamp,
                    tweet_text,
                    tweet_user_id,
                    tweet_user_name,
                    tweet_user_screenname,
                )

        for tweet in selector.css(".ThreadedConversation--loneTweet"):
            count += 1
            lone_tweets_count += 1
            tweet_id = tweet.css("div.tweet ::attr(data-tweet-id)").extract_first()
            tweet_user_screenname = tweet.css(
                "div.tweet ::attr(data-screen-name)"
            ).extract_first()
            tweet_user_name = tweet.css("div.tweet ::attr(data-name)").extract_first()
            tweet_user_id = tweet.css("div.tweet ::attr(data-user-id)").extract_first()
            tweet_text = tweet.css(".TweetTextSize ::text").extract()
            tweet_text = "".join(tweet_text)
            tweet_text = tweet_text.replace("\n", "")
            tweet_timestamp = tweet.css(
                "span._timestamp ::attr(data-time)"
            ).extract_first()

            save_tweet_in_conversation(
                root_tweet_id,
                tweet_id,
                conversations_count,
                tweet_timestamp,
                tweet_text,
                tweet_user_id,
                tweet_user_name,
                tweet_user_screenname,
            )

        browser.close()

        print(
            f"{symbol} collecte : {count} tweets, {conversations_count} conversations, {lone_tweets_count} tweets solitaires"
        )

    except Exception as e:
        print(f"{symbol} {e}")
        browser.close()


##############################################################################
#
# GO
#
##############################################################################

for doc in tweets_collection.find():
    if "root_tweet_id" in doc:
        continue

    print("=" * 80)

    root_tweet_id = None
    error = False

    if "in_reply_to" in doc:
        root_tweet_id = get_root_tweet_id(doc["source"]["id_str"])
        if not root_tweet_id:
            error = True
    else:
        root_tweet_id = doc["source"]["id_str"]

    scrape(root_tweet_id)
    query = {"source.id_str": doc["source"]["id_str"]}
    tweets_collection.update_one(
        query, {"$set": {"root_tweet_id": root_tweet_id, "root_tweet_error": error}}
    )

# scrape("673770575018463232")  # longue conversation
# scrape("1115715666797948928") # tweet solo

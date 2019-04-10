import argparse
import signal
from pymongo import MongoClient
import tweepy
from datetime import datetime
import configparser
from twitter_common import get_tweet_url, get_video_url_from_media

###############################################################################
#
# CONF
#
###############################################################################

# Paramètres lus dans le fichier de configuration secret
# (Twitter API keys & tokens)
secret_config = configparser.ConfigParser()
secret_config.read("secret.conf")
consumer_key = secret_config.get("Twitter", "consumer_key")
consumer_secret = secret_config.get("Twitter", "consumer_secret")
access_key = secret_config.get("Twitter", "access_key")
access_secret = secret_config.get("Twitter", "access_secret")

# Paramètres passés au script
parser = argparse.ArgumentParser()
parser.add_argument("--track")
parser.add_argument("--db")
parser.add_argument("--coll")
args = parser.parse_args()

# Lecture du fichier de configuration
config = configparser.ConfigParser()
config.read("toast.conf")

# MongoDB
database_name = args.db
collection_name = args.coll
client = MongoClient()
db = client[database_name]
collection = db[collection_name]

# Streaming
track = args.track.split(",")
track = list(map(str.strip, track))
streaming_symbol = config.get("Streaming", "symbol")
retweet_symbol = config.get("Streaming", "retweet_symbol")
quoted_tweet_symbol = config.get("Streaming", "quoted_tweet_symbol")

# Symboles
picture_symbol = config.get("Pictures", "symbol")
video_symbol = config.get("Videos", "symbol")
conversation_symbol = config.get("Conversations", "symbol")


###############################################################################
#
# GO
#
###############################################################################

print()

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(
    auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True
)


class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        source_json = status._json
        date = datetime.fromtimestamp(float(status.timestamp_ms) / 1000)

        #######################################################################
        # Le tweet courant est-il un retweet ?
        #######################################################################

        is_rt = hasattr(status, "retweeted_status")

        #######################################################################
        # Extraction du texte complet
        # https://developer.twitter.com/en/docs/tweets/tweet-updates.html
        #######################################################################

        fulltext = None
        if not is_rt:
            fulltext = status.text
            if hasattr(status, "extended_tweet"):
                fulltext = status.extended_tweet["full_text"]
        else:
            fulltext = status.retweeted_status.text
            if hasattr(status.retweeted_status, "extended_tweet"):
                fulltext = status.retweeted_status.extended_tweet["full_text"]

        ########################################################################
        # Inventaire des médas (images & vidéos)
        ########################################################################

        media = None
        if not is_rt:
            if not hasattr(status, "extended_tweet"):
                # Tweet non retweeté et < 140 caractères
                if "media" in status.entities:
                    media = status.entities["media"]
            else:
                # Tweet non retweeté et > 140 caractères
                if "media" in status.extended_tweet["entities"]:
                    media = status.extended_tweet["entities"]["media"]
        else:
            if not hasattr(status.retweeted_status, "extended_tweet"):
                # Tweet retweeté et < 140 caractères
                if "media" in status.retweeted_status.entities:
                    media = status.retweeted_status.entities["media"]
            else:
                # Tweet retweeté et > 140 caractères
                if "media" in status.retweeted_status.extended_tweet["entities"]:
                    media = status.retweeted_status.extended_tweet["entities"]["media"]

        pictures = []
        videos = []

        if media:
            for m in media:
                # Le média est une vidéo
                if "video_info" in m:
                    videos.append({"url": get_video_url_from_media(m)})
                # Le média est une image
                else:
                    pictures.append({"url": m["media_url"]})

        #######################################################################
        # Le tweet est-il dans une conversation ?
        #######################################################################

        in_reply_to = status.in_reply_to_status_id_str
        if is_rt:
            if status.retweeted_status.in_reply_to_status_id_str:
                in_reply_to = status.retweeted_status.in_reply_to_status_id_str

        #######################################################################
        # Le tweet contient-il un tweet cité ?
        #######################################################################

        quoted_tweet = hasattr(status, "quoted_status")
        if quoted_tweet:
            pass  # TODO

        #######################################################################
        # Écriture du tweet dans MongoDB
        #######################################################################

        doc = {
            "fulltext": fulltext,
            "in_reply_to": in_reply_to,
            "source": source_json,
            "track": track,
        }
        if media:
            doc["media"] = media
        id = collection.insert_one(doc).inserted_id

        #######################################################################
        # Affichage
        #######################################################################

        print("=" * 80)
        print(
            "{0}  🐦  {1}  🕓  {2}  💾  {3} {4}{5}{6}{7}{8}".format(
                streaming_symbol,
                get_tweet_url(status.id_str),
                date,
                id,
                retweet_symbol if is_rt else "",
                picture_symbol * len(pictures),
                video_symbol * len(videos),
                conversation_symbol if in_reply_to else "",
                quoted_tweet_symbol if quoted_tweet else "",
            )
        )
        print(f"{fulltext}")

    def on_error(self, status_code):
        print(f"{streaming_symbol}  ERROR: {status_code}")
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False


stream_listener = StreamListener()
stream = tweepy.Stream(auth=api.auth, listener=stream_listener)


def signal_handler(sig, frame):
    print("You pressed Ctrl+C!")
    client.close()
    stream.disconnect()
    print("Ciao!")


signal.signal(signal.SIGINT, signal_handler)
stream.filter(track=track)  # , is_async=True

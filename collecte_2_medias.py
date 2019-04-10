import argparse
import configparser
import hashlib
from pymongo import MongoClient
import os
from pathlib import Path
import requests
from twitter_common import get_tweet_url, get_video_url_from_media

###############################################################################
#
# CONF
#
###############################################################################

# Paramètres passés au script
parser = argparse.ArgumentParser()
parser.add_argument("--db")
parser.add_argument("--coll")
parser.add_argument("--dldir")
args = parser.parse_args()

# Configuration de trucs de moindre importance
config = configparser.ConfigParser()
config.read("toast.conf")

# MongoDB
database_name = args.db
collection_name = args.coll
client = MongoClient()
db = client[database_name]
collection = db[collection_name]

# Dossiers de téléchargement des fichiers
pictures_download_directory = Path(args.dldir, 'pictures')
videos_download_directory = Path(args.dldir, 'videos')
if not os.path.exists(pictures_download_directory):
    os.makedirs(pictures_download_directory)
if not os.path.exists(videos_download_directory):
    os.makedirs(videos_download_directory)

# Symboles
picture_symbol = config.get('Pictures', 'symbol')
video_symbol = config.get('Videos', 'symbol')

###############################################################################
#
# HELPERS
#
###############################################################################

MEDIA_TYPE_PICTURE = 'p'
MEDIA_TYPE_VIDEO = 'v'


def get_file_extension(type, url):
    if type == MEDIA_TYPE_PICTURE:
        return Path(url.split('/')[-1]).suffix
    elif type == MEDIA_TYPE_VIDEO:
        p = url.split('/')[-1]
        p = p.split('?')[0]
        return Path(p).suffix
    else:
        return None


def download_media(tweet_id, dir, url):
    try:
        response = requests.get(url, timeout=20)
        sha1 = hashlib.sha1()
        sha1.update(response.content)
        sha1 = sha1.hexdigest()
        extension = get_file_extension(type, url)
        filename = sha1 + extension

        file_path = Path(dir, filename)

        with open(file_path, 'wb') as fout:
            fout.write(response.content)

        print(f"media url: {url}")
        print(f"file path: {file_path}")
        return (sha1, extension)

    except requests.exceptions.RequestException as e:
        print(e)
        return (None, None)


###############################################################################
#
# ITÉRATIONS SUR LES TWEETS DE LA BDD
#
###############################################################################

for doc in collection.find({"media": {'$exists': True}}):
    pictures = []
    videos = []

    nb_pictures_downloaded = len(doc["pictures"]) if "pictures" in doc else 0
    nb_videos_downloaded = len(doc["videos"]) if "videos" in doc else 0

    if nb_pictures_downloaded + nb_videos_downloaded == len(doc["media"]):
        print("Media already downloaded for tweet {0}".format(
            get_tweet_url(doc['source']['id_str'])
        ))
        continue

    for m in doc["media"]:
        dir = None
        media_list = None
        symbol = None
        type = None
        url = None

        # Le média est une vidéo
        if "video_info" in m:
            dir = videos_download_directory
            media_list = videos
            symbol = video_symbol
            type = MEDIA_TYPE_VIDEO
            url = get_video_url_from_media(m)
        # Le média est une image
        else:
            dir = pictures_download_directory
            media_list = pictures
            symbol = picture_symbol
            type = MEDIA_TYPE_PICTURE
            url = m["media_url"]

        print("\n" + symbol)
        print("Trying to download {0} (from tweet {1}) …".format(
            url,
            get_tweet_url(doc['source']['id_str'])
         ))

        (sha1, extension) = download_media(doc["source"]["id_str"],
                                           dir,
                                           url)

        if sha1 and extension:
            media_list.append({
                "media_id_str": m["id_str"],
                "sha1": sha1,
                "extension": extension
            })
        else:
            if type == MEDIA_TYPE_PICTURE:
                media_list.append({
                    "media_id_str": m["id_str"],
                    "error": True
                })

        if len(pictures) > 0:
            collection.update_one(
                {"source.id_str": doc["source"]["id_str"]},
                {"$set": {"pictures": pictures}}
            )

        if len(videos) > 0:
            collection.update_one(
                {"source.id_str": doc["source"]["id_str"]},
                {"$set": {"videos": videos}}
            )

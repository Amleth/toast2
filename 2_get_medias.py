import configparser
import hashlib
from pymongo import MongoClient
import os
from pathlib import Path
import requests
from twitter_common import get_tweet_url, get_video_url_from_media

#
# CONF
#

config = configparser.ConfigParser()
config.read('toast.conf')
database_name = config.get('General', 'prefix')
collection_name = config.get('General', 'prefix')
client = MongoClient()
db = client[database_name]
collection = db[collection_name]
pictures_download_directory = Path(
    config.get('Pictures', 'download_directory_parent_directory'),
    config.get('General', 'prefix') + '_pictures'
)
videos_download_directory = Path(
    config.get('Videos', 'download_directory_parent_directory'),
    config.get('General', 'prefix') + '_videos'
)
picture_symbol = config.get('Pictures', 'symbol')
video_symbol = config.get('Videos', 'symbol')

if not os.path.exists(pictures_download_directory):
    os.makedirs(pictures_download_directory)

if not os.path.exists(videos_download_directory):
    os.makedirs(videos_download_directory)

#
# HELPERS
#

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


def download_media(tweet_id, type, url):
    try:
        response = requests.get(url, timeout=5)
        sha1 = hashlib.sha1()
        sha1.update(response.content)
        sha1 = sha1.hexdigest()
        extension = get_file_extension(type, url)
        filename = sha1 + extension

        file_path = None
        if type == MEDIA_TYPE_PICTURE:
            file_path = Path(pictures_download_directory, filename)
        elif type == MEDIA_TYPE_VIDEO:
            file_path = Path(videos_download_directory, filename)
        else:
            print(f"Unknown media type: {type}.")
            return (None, None)

        with open(file_path, 'wb') as fout:
            fout.write(response.content)

        print(f"      file path: {file_path}")
        return (sha1, extension)

    except requests.exceptions.RequestException as e:
        print(e)
        return (None, None)


#
# ITERATE OVER TWEETS WITH MEDIA
#

for doc in collection.find({"media": {'$exists': True}}):
    pictures = []
    videos = []

    for m in doc["media"]:
        symbol = None
        type = None
        url = None

        # Le média est une vidéo
        if "video_info" in m:
            symbol = video_symbol
            type = MEDIA_TYPE_VIDEO
            url = get_video_url_from_media(m)
        # Le média est une image
        else:
            symbol = picture_symbol
            type = MEDIA_TYPE_PICTURE
            url = m["media_url"]

        print(
            f"{symbol}  Trying to download {url} (from tweet {get_tweet_url(doc['source']['id_str'])}) …"
        )
        (sha1, extension) = download_media(doc["source"]["id_str"],
                                           type,
                                           url)
        if sha1 and extension:
            if type == MEDIA_TYPE_PICTURE:
                pictures.append({
                    "media_id_str": m["id_str"],
                    "sha1": sha1,
                    "extension": extension
                })
            elif type == MEDIA_TYPE_VIDEO:
                videos.append({
                    "media_id_str": m["id_str"],
                    "sha1": sha1,
                    "extension": extension
                })
                pass
        else:
            if type == MEDIA_TYPE_PICTURE:
                pictures.append({
                    "media_id_str": m["id_str"],
                    "error": True
                })
            elif type == MEDIA_TYPE_VIDEO:
                videos.append({
                    "media_id_str": m["id_str"],
                    "error": True
                })

    if len(pictures) > 0:
        collection.update(
            {"source.id_str": doc["source"]["id_str"]},
            {"$set": {"pictures": pictures}}
        )

    if len(videos) > 0:
        collection.update(
            {"source.id_str": doc["source"]["id_str"]},
            {"$set": {"videos": videos}}
        )

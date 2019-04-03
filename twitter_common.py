def get_tweet_url(tweet_id):
    return f"https://twitter.com/statuses/{tweet_id}"


# TODO : réécrire cette fonction dans un style plus pythonique
def get_video_url_from_media(media):
    url = None
    if "video_info" in media:
        max_bitrate = -1
        for v in media["video_info"]["variants"]:
            if "bitrate" in v:
                if int(v["bitrate"]) > max_bitrate:
                    max_bitrate = int(v["bitrate"])
                    url = v["url"]
    return url

import json
import pprint
from pymongo import MongoClient
import xlsxwriter

workbook = xlsxwriter.Workbook("data.xlsx")
worksheet = workbook.add_worksheet()

bold = workbook.add_format({"bold": True})
worksheet.write(0, 0, "link", bold)
worksheet.write(0, 1, "created_at", bold)
worksheet.write(0, 2, "id_str", bold)
worksheet.write(0, 3, "retweeted_status_created_at", bold)
worksheet.write(0, 4, "retweeted_status_id_str", bold)
worksheet.write(0, 5, "source", bold)
worksheet.write(0, 6, "text", bold)
worksheet.write(0, 7, "timestamp_ms", bold)
worksheet.write(0, 8, "user_id_str", bold)
worksheet.write(0, 9, "user_name", bold)
worksheet.write(0, 10, "user_screen_name", bold)
worksheet.write(0, 11, "user_description", bold)
worksheet.write(0, 12, "hashtags", bold)
worksheet.write(0, 13, "urls", bold)

client = MongoClient()
db = client.si90_pma
collection = db.si90_pma_25soir

line = 1

for t in collection.find():
    # READ

    j = t["raw"]

    created_at = j["created_at"]

    id_str = j["id_str"]

    link = f"http://www.twitter.com/statuses/{id_str}"

    retweeted_status_created_at = None
    retweeted_status_id_str = None
    in_reply_to_status_id_str = j["in_reply_to_status_id_str"]
    if "retweeted_status" in j:
        retweeted_status_created_at = j["retweeted_status"]["created_at"]
        retweeted_status_id_str = j["retweeted_status"]["id_str"]

    source = j["source"]

    text = t["fulltext"]

    timestamp_ms = j["timestamp_ms"]

    user_id_str = j["user"]["id_str"]
    user_name = j["user"]["name"]
    user_screen_name = j["user"]["screen_name"]
    user_description = j["user"]["description"]

    hashtags = []
    if "retweeted_status" in j:
        if not 'extended_tweet' in j['retweeted_status']:
            hashtags = j['retweeted_status']['entities']['hashtags']
        else:
            hashtags = j['retweeted_status']['extended_tweet']['entities']['hashtags']
    else:
        if not 'extended_tweet' in j:
            hashtags = j['entities']['hashtags']
        else:
            hashtags = j['extended_tweet']['entities']['hashtags']
    hashtags = list(map(lambda x: f"#{x['text']}", hashtags))

    urls = []
    if "retweeted_status" in j:
        if not 'extended_tweet' in j['retweeted_status']:
            urls = j['retweeted_status']['entities']['urls']
        else:
            urls = j['retweeted_status']['extended_tweet']['entities']['urls']
    else:
        if not 'extended_tweet' in j:
            urls = j['entities']['urls']
        else:
            urls = j['extended_tweet']['entities']['urls']
    urls = list(map(lambda x: f"URL-{x['expanded_url']}", urls))

    # WRITE
    worksheet.write(line, 0, link)
    worksheet.write(line, 1, created_at)
    worksheet.write(line, 2, id_str)
    worksheet.write(line, 3, retweeted_status_created_at)
    worksheet.write(line, 4, retweeted_status_id_str)
    worksheet.write(line, 5, source)
    worksheet.write(line, 6, text)
    worksheet.write(line, 7, timestamp_ms)
    worksheet.write(line, 8, user_id_str)
    worksheet.write(line, 9, user_name)
    worksheet.write(line, 10, user_screen_name)
    worksheet.write(line, 11, user_description)
    worksheet.write(line, 12, ' '.join(hashtags))
    worksheet.write(line, 13, ' '.join(urls))

    line += 1

workbook.close()

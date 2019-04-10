import argparse
from pymongo import MongoClient
import xlsxwriter

parser = argparse.ArgumentParser()
parser.add_argument("--db")
parser.add_argument("--coll")
parser.add_argument("--xlsxfile")
args = parser.parse_args()

workbook = xlsxwriter.Workbook(args.xlsxfile)
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
db = client[args.db]
collection = db[args.coll]

line = 1

for t in collection.find():
    #
    # READ
    #

    source = t["source"]

    device = source["source"]

    created_at = source["created_at"]

    id_str = source["id_str"]

    link = f"http://www.twitter.com/statuses/{id_str}"

    retweeted_status_created_at = None
    retweeted_status_id_str = None
    in_reply_to_status_id_str = source["in_reply_to_status_id_str"]
    if "retweeted_status" in source:
        retweeted_status_created_at = source["retweeted_status"]["created_at"]
        retweeted_status_id_str = source["retweeted_status"]["id_str"]

    text = t["fulltext"]

    timestamp_ms = source["timestamp_ms"]

    user_id_str = source["user"]["id_str"]
    user_name = source["user"]["name"]
    user_screen_name = source["user"]["screen_name"]
    user_description = source["user"]["description"]

    hashtags = []
    if "retweeted_status" in source:
        if not 'extended_tweet' in source['retweeted_status']:
            hashtags = source['retweeted_status']['entities']['hashtags']
        else:
            hashtags = source['retweeted_status']['extended_tweet']['entities']['hashtags']
    else:
        if not 'extended_tweet' in source:
            hashtags = source['entities']['hashtags']
        else:
            hashtags = source['extended_tweet']['entities']['hashtags']
    hashtags = list(map(lambda x: f"#{x['text']}", hashtags))

    urls = []
    if "retweeted_status" in source:
        if not 'extended_tweet' in source['retweeted_status']:
            urls = source['retweeted_status']['entities']['urls']
        else:
            urls = source['retweeted_status']['extended_tweet']['entities']['urls']
    else:
        if not 'extended_tweet' in source:
            urls = source['entities']['urls']
        else:
            urls = source['extended_tweet']['entities']['urls']
    urls = list(map(lambda x: f"URL-{x['expanded_url']}", urls))

    #
    # WRITE
    #

    worksheet.write(line, 0, link)
    worksheet.write(line, 1, created_at)
    worksheet.write(line, 2, id_str)
    worksheet.write(line, 3, retweeted_status_created_at)
    worksheet.write(line, 4, retweeted_status_id_str)
    worksheet.write(line, 5, device)
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

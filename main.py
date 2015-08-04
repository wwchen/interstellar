#!/usr/bin/env python

import boto
import ConfigParser
import os
import time
import csv
import codecs
import sqlite3
import re
from review import Review
from review_db import ReviewDb
from review_statistics import ReviewStatistics
from utils import *

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    slack_webhook_url = config.get(CONFIG_KEY, "slack")
    package_name = config.get(CONFIG_KEY, "package_name")
    app_repo = config.get(CONFIG_KEY, "app_repo")
    type = config.get(CONFIG_KEY, "type")

    # todo connect to gsutil and cp the file
    # for now, assume that it is downloaded

    # list all the files availble
    bucket_id = "pubsite_prod_rev_11903721763109600553"
    package_name = "com.snowball.app"
    root_path = "gs://<bucket_id>"
    root_path = root_path.replace("<bucket_id>", bucket_id)

    review_root_path = "<root>/reviews"
    review_root_path = review_root_path.replace("<root>", root_path)

    review_filename = "reviews_<package_name>_<date>.csv"
    review_filename = review_filename.replace("<package_name>", package_name)
    review_filename = review_filename.replace("<date>", time.strftime("%Y%m"))

    review_url = "<review_root>/<review_filename>"
    review_url = review_url.replace("<review_root>", review_root_path)
    review_url = review_url.replace("<review_filename>", review_filename)

    print "Available review csv's"
    # os.system('gsutil list %s' % review_root_path)

    print "Copying this month's csv"
    # os.system('gsutil cp %s .' % review_url)

    print "Opening file %s" % review_filename
    db = ReviewDb()

    csvfile = open(review_filename, "rb").read()
    csvfile = csvfile.decode('utf_16_le').encode('utf-8').split("\n")
    csvreader = csv.reader(csvfile)
    csvreader.next()  # skip the header
    count = 0
    reviews = []
    for row in csvreader:
        try:
            review = Review(row)
            reviews.append(review)
            db.insert(review)
            db.save()
            count += 1
        except ValueError:
            pass
    db.close()
    print "====="
    print ReviewStatistics(reviews)
    print "Processed %d ratings" % count

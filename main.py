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
from review_processor import ReviewProcessor
from utils import *


def process_csv_row(row):
    headers = [
        'package_name',
        'app_version',
        'review_lang',
        'device_type',
        'review_date',
        'review_epoch',
        'review_update_date',
        'review_update_epoch',
        'review_rating',
        'review_title',
        'review_text',
        'dev_reply_date',
        'dev_reply_epoch',
        'dev_reply_text',
        'review_link'
    ]
    assert isinstance(row, list)
    if len(row) is not len(headers):
        print "Row is not valid:", row
        return
    data = {}
    for i, header in enumerate(headers):
        data[header] = row[i]
    return data

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)
    slack_webhook_url = config.get(CONFIG_KEY, "slack")
    package_name = config.get(CONFIG_KEY, "package_name")
    app_repo = config.get(CONFIG_KEY, "app_repo")
    what_type = config.get(CONFIG_KEY, "type")

    # todo connect to gsutil and cp the file
    # for now, assume that it is downloaded

    # remote path configuration
    bucket_id = "pubsite_prod_rev_11903721763109600553"
    package_name = "com.snowball.app"
    gs_root_path = "gs://<bucket_id>"
    gs_root_path = gs_root_path.replace("<bucket_id>", bucket_id)

    remote_review_root_path = "<root>/reviews"
    remote_review_root_path = remote_review_root_path.replace("<root>", gs_root_path)

    remote_review_filename = "reviews_<package_name>_<date>.csv"
    remote_review_filename = remote_review_filename.replace("<package_name>", package_name)
    remote_review_filename = remote_review_filename.replace("<date>", time.strftime("%Y%m"))

    remote_review_path = "<review_root>/<review_filename>"
    remote_review_path = remote_review_path.replace("<review_root>", remote_review_root_path)
    remote_review_path = remote_review_path.replace("<review_filename>", remote_review_filename)

    # local path configuration
    local_review_root_path = "reviews"

    local_review_filename = "reviews_<package_name>_<date>.csv"
    local_review_filename = local_review_filename.replace("<package_name>", package_name)
    local_review_filename = local_review_filename.replace("<date>", time.strftime("%Y%m%d"))

    local_review_path = "<review_root>/<review_filename>"
    local_review_path = local_review_path.replace("<review_root>", local_review_root_path)
    local_review_path = local_review_path.replace("<review_filename>", local_review_filename)

    # check if the file is downloaded already
    if not os.path.exists(local_review_root_path):
        os.makedirs(local_review_root_path)

    if os.path.isfile(local_review_path):
        print "Review file already exists locally. Not fetching again."
    else:
        print "Available review csv's"
        os.system('gsutil list %s' % remote_review_root_path)

        print "Copying this month's csv to %s" % local_review_path
        os.system('gsutil cp %s %s' % (remote_review_path, local_review_path))

    print "Opening file %s" % local_review_path
    csvfile = open(local_review_path, "rb").read()
    csvfile = csvfile.decode('utf_16_le').encode('utf-8').split("\n")
    csvreader = csv.reader(csvfile)
    csvreader.next()  # skip the header
    count = 0
    db = ReviewDb()
    reviews = []
    processor = ReviewProcessor(db)
    for row in csvreader:
        if not row:
            continue
        review_data = process_csv_row(row)
        review = Review(review_data)
        reviews.append(review)
        processor.add(review)
        count += 1
    processor.process()
    print "====="
    print processor
    print "Processed %d reviews" % count
    db.close()



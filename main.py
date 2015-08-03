#!/usr/bin/env python

import boto
import ConfigParser
import os
import time
import csv
import codecs
import sqlite3
import re

DB_FILE = "database.sqlite3"
CONFIG_FILE = "secrets/secrets.conf"
CONFIG_KEY = "interstellar"
ENCODING = "UTF_16_LE"
BLACK_STAR = u'\u2605'
WHITE_STAR = u'\u2606'


def get_time(epoch_time, fmt="%b %d %H:%M"):
    epoch_time /= 1000 # time in millis
    return time.strftime(fmt, time.localtime(epoch_time))


def get_rating_stars(stars, max_stars=5):
    return BLACK_STAR * stars + WHITE_STAR * (max_stars - stars)


class Review:
    def __init__(self, cols):
        if not isinstance(cols, list) or len(cols) != 15:
            raise ValueError
        self.data = {}
        self.id = None
        self.col_headers = [
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
        for i, header in enumerate(self.col_headers):
            value = cols[i].strip()
            try:
                value = long(value)
            except ValueError:
                value.encode(ENCODING)
            finally:
                self.data[header] = value
                setattr(self, header, value)
        try:
            self.id = re.search('revid=(gp:[a-zA-Z0-9-_]*)', self.review_link).group(1)
            assert isinstance(self.id, str) and self.id
        except AttributeError:
            print self.review_link

    def __str__(self):
        posted_time = self.review_update_epoch or self.review_epoch
        edited_string = " (edited)" if self.review_update_epoch > self.review_epoch else ""
        replied_string = " (replied)" if self.dev_reply_date else ""

        print get_rating_stars(self.review_rating)
        print "V{}, posted on {}{}{}".format(
            self.app_version if self.app_version else "?",
            get_time(posted_time),
            edited_string,
            replied_string)
        print "*{}* {}".format(self.review_title, self.review_text)
        return ""

    ###

class ReviewStatistics:
    def __init__(self, reviews):
        self._reviews = reviews

    def add(self, review):
        self._reviews.append(review)

    def process(self):
        if not len(reviews):
            return
        stars = 0
        notable_reviews = []
        for review in self._reviews:
            assert isinstance(review.review_rating, long)
            stars += review.review_rating
            if self._is_review_notable(review):
                notable_reviews.append(review)
        self._avg_stars = float(stars) / len(self._reviews)
        self._notable_reviews = notable_reviews

    def _is_review_notable(self, review):
        if review.review_lang == "en":
            if review.review_title and review.review_text:
                return True
        return False

    def __str__(self):
        if not self._reviews:
            return "No reviews accumulated"
        self.process()
        count = 4
        self._notable_reviews.sort(key=lambda r: r.review_update_epoch)
        for review in self._notable_reviews:
            if count > 0:
                print review
            else:
                break
            count -= 1
        return "Overall stats: %0.2f stars" % (self._avg_stars)


class ReviewDb:
    def __init__(self):
        self.db_conn = sqlite3.connect(DB_FILE)
        self.db_cursor = self.db_conn.cursor()
        self.table = "reviews"
        self.cols = {
            'id':                  'TEXT',
            'package_name':        'TEXT',
            'app_version':         'TEXT',
            'review_lang':         'TEXT',
            'device_type':         'TEXT',
            'review_epoch':        'INTEGER',
            'review_update_epoch': 'INTEGER',
            'review_rating':       'INTEGER',
            'review_title':        'TEXT',
            'review_text':         'TEXT',
            'dev_reply_epoch':     'INTEGER',
            'dev_reply_text':      'TEXT',
            'review_link':         'TEXT'
        }
        self.create_table(self.cols)

    def create_table(self, columns):
        col_descriptions = [ "%s %s" % (col_name, type) for col_name, type in columns.iteritems()]
        self.db_cursor.execute('CREATE TABLE IF NOT EXISTS {} ({})'.format(self.table, ','.join(col_descriptions)))

    def row_exists(self, review):
        assert isinstance(review, Review)
        self.db_cursor.execute('SELECT * from {} WHERE id={}'.format(self.table, review.id))
        return self.db_cursor.rowcount > 0

    def save(self, review):
        assert isinstance(review, Review)
        params = {}
        value_keys = []
        named_placeholder = []
        for col in self.cols.iterkeys():
            params[col] = getattr(review, col)
            value_keys.append(col)
            named_placeholder.append(':%s' % col)
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(self.table, ','.join(value_keys), ','.join(named_placeholder))
        self.db_cursor.execute(sql, params)
        self.db_conn.commit()

    def close(self):
        self.db_conn.commit()
        self.db_conn.close()

if __name__ == '__main__':
    db = ReviewDb()
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
            db.save(review)
            count += 1
        except ValueError:
            pass
    print "====="
    print ReviewStatistics(reviews)
    print "Processed %d ratings" % count

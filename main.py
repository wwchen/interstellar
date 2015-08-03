#!/usr/bin/env python

import boto
import ConfigParser
import os
import time
import csv
import codecs

CONFIG_FILE = "secrets/secrets.conf"
CONFIG_KEY = "interstellar"
BLACK_STAR = u'\u2605'
WHITE_STAR = u'\u2606'

class Review:
    def __init__(self, row):
        if not isinstance(row, list) or len(row) != 15:
            raise ValueError
        row = [r.strip() for r in row]
        self.package_name        = row[0]
        self.app_version         = row[1]
        self.review_lang         = row[2]
        self.device_type         = row[3]
        self.review_date         = row[4]
        self.review_epoch        = row[5]
        self.review_update_date  = row[6]
        self.review_update_epoch = row[7]
        self.review_rating       = row[8]
        self.review_title        = row[9]
        self.review_text         = row[10]
        self.dev_reply_date      = row[11]
        self.dev_reply_epoch     = row[12]
        self.dev_reply_text      = row[13]
        self.review_link         = row[14]

    def __str__(self):
        edited_string = " (edited)" if self.review_update_epoch > self.review_epoch else ""
        posted_time = self.get_review_update_date() or self.get_review_date()
        replied_string = " (replied)" if self.dev_reply_date else ""

        print self.get_rating_stars()
        print "V{}, posted on {}{}{}".format(
            self.app_version if self.app_version else "?",
            posted_time,
            edited_string,
            replied_string)
        print "*{}* {}".format(self.review_title, self.review_text)
        return ""

    def get_app_version(self, prepend = "V"):
        if self.app_version:
            return "{}{}".format(prepend, self.app_version)
        return ""

    def get_language(self):
        return self.review_lang

    def get_device_type(self):
        return self.device_type

    ###

    def get_review_epoch(self):
        if self.review_epoch:
            return long(self.review_epoch)
        return None

    def get_review_update_epoch(self):
        if self.review_update_epoch:
            return long(self.review_update_epoch)
        return None

    def get_dev_reply_epoch(self):
        if self.dev_reply_epoch:
            return long(self.dev_reply_epoch)
        return None

    def get_review_date(self, fmt="%b %d %H:%M"):
        if self.review_epoch:
            return time.strftime(fmt, time.localtime(self.get_review_epoch()))
        return ""

    def get_review_update_date(self, fmt="%b %d %H:%M"):
        if self.review_update_epoch:
            return time.strftime(fmt, time.localtime(self.get_review_update_epoch()))
        return ""

    def get_dev_reply_date(self, fmt="%b %d %H:%M"):
        if self.dev_reply_epoch:
            return time.strftime(fmt, time.localtime(self.get_dev_reply_epoch()))
        return ""

    ###

    def get_review_text(self):
        if self.review_text:
            return self.review_text
        return ""

    def get_review_title(self):
        if self.review_title:
            return self.review_title
        return ""

    def get_review_link(self):
        if self.review_link:
            return self.review_link
        return ""

    def get_rating(self):
        return int(self.review_rating)

    def get_rating_stars(self):
        return BLACK_STAR * self.get_rating() + WHITE_STAR * (5 - self.get_rating())

class ReviewStatistics:
    def __init__(self, reviews):
        self._reviews = reviews

    def add(self, review):
        self._reviews.append(review)

    def process(self):
        stars = 0
        notable_reviews = []
        for review in self._reviews:
            stars += review.get_rating()
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
        self.process()
        count = 4
        self._notable_reviews.sort(key=lambda r: r.get_review_update_epoch())
        for review in self._notable_reviews:
            if count > 0:
                print review
            else:
                break
            count -= 1
        return "====\nOverall stats: %0.2f stars" % (self._avg_stars)



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
    csvfile = open(review_filename, "rb").read()
    csvfile = csvfile.decode('utf_16_le').encode('utf-8').split("\n")
    csvreader = csv.reader(csvfile)
    csvreader.next() # skip the header
    count = 0
    reviews = []
    for row in csvreader:
        try:
            reviews.append(Review(row))
            count += 1
        except ValueError:
            pass
    print ReviewStatistics(reviews)
    print "Processed %d ratings" % count

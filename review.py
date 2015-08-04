#!/usr/bin/python

from utils import *
import re


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


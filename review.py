#!/usr/bin/python

from utils import *
from collections import OrderedDict
import re


class Review:
    def __init__(self, data):
        self._attrs_generated = [
            'id'
        ]
        self._attrs = OrderedDict([
            ('id',                  int),
            ('package_name',        str),
            ('app_version',         str),
            ('review_lang',         str),
            ('device_type',         str),
            ('review_epoch',        long),
            ('review_update_epoch', long),
            ('review_rating',       int),
            ('review_title',        str),
            ('review_text',         str),
            ('dev_reply_epoch',     long),
            ('dev_reply_text',      str),
            ('review_link',         str)
        ])

        for attr in self._attrs:
            if attr in self._attrs_generated:
                continue
            attr_type = self._attrs[attr]
            value = data[attr]
            setattr(self, attr, attr_type(value))
        self.id = self._get_id()

    def _get_id(self):
        return re.search('revid=(gp:[a-zA-Z0-9-_]*)', self.review_link).group(1)

    def get_attrs(self):
        return self._attrs.keys()

    def get_attr_with_type(self):
        return self._attrs

    def __eq__(self, other):
        if not isinstance(other, Review):
            return False
        for attr in self._attrs.keys():
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __str__(self):
        posted_time = self.review_update_epoch or self.review_epoch
        edited_string = " (edited)" if self.review_update_epoch > self.review_epoch else ""
        replied_string = " (replied)" if self.dev_reply_epoch else ""

        print get_rating_stars(self.review_rating)
        print "V{}, posted on {}{}{}".format(
            self.app_version if self.app_version else "?",
            get_time(posted_time),
            edited_string,
            replied_string)
        print "*{}* {}".format(self.review_title, self.review_text)
        return ""


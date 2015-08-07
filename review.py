#!/usr/bin/python

from utils import *
import re


class Review:
    def __init__(self, data):
        self.attrs_optional = [
            ('id',                  'TEXT'),
            ('revision',            'INTEGER')
        ]
        self.attrs_required = [
            ('package_name',        'TEXT'),
            ('app_version',         'TEXT'),
            ('review_lang',         'TEXT'),
            ('device_type',         'TEXT'),
            ('review_epoch',        'INTEGER'),
            ('review_update_epoch', 'INTEGER'),
            ('review_rating',       'INTEGER'),
            ('review_title',        'TEXT'),
            ('review_text',         'TEXT'),
            ('dev_reply_epoch',     'INTEGER'),
            ('dev_reply_text',      'TEXT'),
            ('review_link',         'TEXT')
        ]
        self.type_mapping = {
            'TEXT': str,
            'INTEGER': long
        }
        # todo input is dict, process them and store as attributes

    def __eq__(self, other):
        if not isinstance(other, Review):
            return False
        for attr_tuple in self.attrs_required:
            attr, attr_type = attr_tuple
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True


    def __init(self, cols):
        if not isinstance(cols, list) or len(cols) != 15:
            print type(cols)
            raise ValueError
        self.data = {}
        self.id = None
        # todo add revision
        self.revision = None
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


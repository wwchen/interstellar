#!/usr/bin/python

import boto
import ConfigParser
import os
import time
import csv
import codecs
import sqlite3
import re
from utils import *
from review import Review
from review_statistics import ReviewStatistics

class ReviewDb:
    def __init__(self):
        self.db_conn = sqlite3.connect(DB_FILE)
        self.db_cursor = self.db_conn.cursor()
        self.table = "reviews"
        self.cols = [
            ('id',                  'TEXT'),
            ('revision',            'INTEGER'),
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
        self.create_table(self.cols)

    def create_table(self, columns):
        col_descriptions = [" ".join(col) for col in columns]
        self.db_cursor.execute('CREATE TABLE IF NOT EXISTS {} ({})'.format(self.table, ','.join(col_descriptions)))

    def row_exists(self, review):
        assert isinstance(review, Review)
        result = self.db_cursor.execute('SELECT * from {} WHERE id="{}" ORDER BY revision DESC'.format(self.table, review.id))
        for row in result:
            for header in row.keys():
                if hasattr(review, header):
                    if getattr(review, header) == row[header]:
                        print header, "are equal"
                        print row
                        print review
                    else:
                        print header, "are not equal"
        return self.db_cursor.rowcount > 0

    def insert(self, review):
        assert isinstance(review, Review)
        if self.row_exists(review):
            return
        params = {}
        value_keys = []
        named_placeholder = []
        for col in self.cols:
            col_name = col[0]
            if hasattr(review, col_name):
                params[col_name] = getattr(review, col_name)
            elif col_name == "revision":
                params[col_name] = 1
            else:
                raise AttributeError("Unhandled column")

            value_keys.append(col_name)
            named_placeholder.append(':%s' % col_name)
            # if replace:
            #     sql = 'UPDATE {} ({}) SET {} WHERE id={}' # todo WIP. if update_if_exists is false, then breaks the uniqueness of id
            # else:
            sql = 'INSERT INTO {} ({}) VALUES ({})'.format(self.table, ','.join(value_keys), ','.join(named_placeholder))
        self.db_cursor.execute(sql, params)

    def save(self):
        self.db_conn.commit()

    def close(self):
        self.db_conn.commit()
        self.db_conn.close()


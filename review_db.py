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


class ReviewDb:
    def __init__(self):
        self.db_conn = sqlite3.connect(DB_FILE)
        self.db_conn.row_factory = sqlite3.Row
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

    def get_review_by_id(self, review_id):
        assert isinstance(review_id, str)
        self.db_cursor.execute('SELECT * from {} WHERE id="{}" ORDER BY revision DESC'.format(self.table, review_id))
        return self.db_cursor.fetchall()

    def contains_review(self, review):
        row = self.get_row_for_review(review)
        return True if row else False

    def get_row_for_review(self, review):
        assert isinstance(review, Review)
        rows = self.get_review_by_id(review.id)
        for row in rows:
            assert isinstance(row, sqlite3.Row)
            is_row_equal = True
            for col in row.keys():
                if hasattr(review, col):
                    row_value = str(row[col])
                    review_value = str(getattr(review, col))
                    if row_value != review_value:
                        is_row_equal = False
                        break
            if is_row_equal:
                return True
        return False

    def get_revision_count_for_review(self, review):
        rows = self.get_review_by_id(review.id)
        if rows:
            # NOTE: assumes that get_review_by_id is sorted in descending order
            first_row = rows[0]
            assert isinstance(first_row, sqlite3.Row)
            assert 'revision' in first_row.keys()
            return int(first_row['revision'])
        return 0

    def insert(self, review):
        assert isinstance(review, Review)
        if self.contains_review(review):
            return
        next_revision = self.get_revision_count_for_review(review) + 1
        params = {}
        value_keys = []
        named_placeholder = []
        for col in self.cols:
            col_name = col[0]
            if hasattr(review, col_name):
                params[col_name] = getattr(review, col_name)
            elif col_name == "revision":
                params[col_name] = next_revision
            else:
                raise AttributeError("Unhandled column")

            value_keys.append(col_name)
            named_placeholder.append(':%s' % col_name)
            sql = 'INSERT INTO {} ({}) VALUES ({})'.format(self.table, ','.join(value_keys), ','.join(named_placeholder))
        self.db_cursor.execute(sql, params)
        return next_revision

    def save(self):
        self.db_conn.commit()

    def close(self):
        self.db_conn.commit()
        self.db_conn.close()


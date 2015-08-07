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
        self._create_table(self.table, self.cols)

    def _get_col_headers(self):
        return [header for header, type in self.cols]

    def _create_table(self, table, columns):
        col_descriptions = [" ".join(col) for col in columns]
        self.db_cursor.execute('CREATE TABLE IF NOT EXISTS {} ({})'.format(table, ','.join(col_descriptions)))

    def create_unique_key(self, table, column):
        sql = 'CREATE UNIQUE INDEX IF NOT EXISTS {1} ON {0} ({2})'.format(table, column, ','.join(self._get_col_headers()))
        self.db_cursor.execute(sql)

    def get_rows_by_id(self, table, review_id):
        """
        :param table: target table name to perform the sql query
        :param review_id: the google play review id, starts with 'gp:'
        :return: all matching sqlite3.Row's
        """
        assert isinstance(review_id, str)
        self.db_cursor.execute('SELECT * from {} WHERE id="{}" ORDER BY revision DESC'.format(table, review_id))
        return self.db_cursor.fetchall()

    def get_review(self, review_id):
        """
        :param review_id: the google play review id, starts with 'gp:'
        :return: Review object, None if it doesn't exist
        """
        rows = self.get_rows_by_id(self.table_current, review_id)
        assert len(rows) <= 1
        return Review(rows[0]) if rows else None

    def get_review_revisions(self, review_id):
        """
        :param review_id: the google play review id, starts with 'gp:'
        :return: list of Review objects, empty if none
        """
        rows = self.get_rows_by_id(self.table_revised, review_id)
        reviews = []
        for row in rows:
            reviews.append(Review(row))
        return reviews

    def contains_review(self, review):
        assert isinstance(review, Review)
        return True if self.get_review(review.id) else False

    # todo deprecate
    # def get_row_for_review(self, review):
    #     assert isinstance(review, Review)
    #     rows = self.get_rows_by_id(review.id)
    #     for row in rows:
    #         assert isinstance(row, sqlite3.Row)
    #         is_row_equal = True
    #         for col in row.keys():
    #             if hasattr(review, col):
    #                 row_value = str(row[col])
    #                 review_value = str(getattr(review, col))
    #                 if row_value != review_value:
    #                     is_row_equal = False
    #                     break
    #         if is_row_equal:
    #             return True
    #     return False

    def insert_or_update(self, review, comparator):
        # todo unclear where to update the revision number on the review itself
        assert isinstance(review, Review)
        review_existing = self.get_review(review.id)
        if review_existing == None:
            self.insert(review)
        else:
            if review is not review_existing:
                self._update_current_review(review)

    def insert(self, review_to_insert):
        assert isinstance(review_to_insert, Review)
        review_id = review_to_insert.id
        review_current = self.get_review(review_id)
        # makes various assumptions here
        # revision count is sequential and unique
        # latest review is in current table
        # revised reviews are in revised table
        # IMPORTANT: there's no check on duplicity here. This function only inserts
        # revision count in the review to be inserted is reset
        if review_current:
            review_to_insert.revision = review_current.revision + 1
            self._update_current_review(review_to_insert)
            self._insert(self.table_revised, review_current)
        else:
            review_to_insert.revision = 1
            self._insert(self.table_current, review_to_insert)

    def _update_current_review(self, review):
        # assume unique index 'id'
        assert isinstance(review, Review)
        col_values = {}
        col_headers = []
        col_placeholders = []
        for col in self.cols:
            col_header = col[0]
            if hasattr(review, col_header):
                col_values[col_header] = getattr(review, col_header)
            else:
                raise AttributeError("Unhandled column")

            col_headers.append(col_header)
            col_placeholders.append(':%s' % col_header)
        sql = 'UPDATE {} SET ({}) VALUES ({}) WHERE id="{}"'.format(self.table_current, ','.join(col_headers), ','.join(col_placeholders))
        self.db_cursor.execute(sql, col_values)

    def _insert(self, table, review):
        assert isinstance(review, Review)
        col_values = {}
        col_headers = []
        col_placeholders = []
        for col in self.cols:
            col_header = col[0]
            if hasattr(review, col_header):
                col_values[col_header] = getattr(review, col_header)
            else:
                raise AttributeError("Unhandled column")

            col_headers.append(col_header)
            col_placeholders.append(':%s' % col_header)
        sql = 'INSERT INTO {} ({}) VALUES ({})'.format(table, ','.join(col_headers), ','.join(col_placeholders))
        self.db_cursor.execute(sql, col_values)

    def save(self):
        self.db_conn.commit()

    def close(self):
        self.db_conn.commit()
        self.db_conn.close()


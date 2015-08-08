#!/usr/bin/python

import sqlite3
from utils import *
from review import Review
from enum import Enum


class Result(Enum):
    failed = 1
    inserted = 2
    updated = 3


class ReviewDb:
    def __init__(self):
        self.db_conn = sqlite3.connect(DB_FILE)
        self.db_conn.text_factory = str
        self.db_conn.row_factory = sqlite3.Row
        self.db_cursor = self.db_conn.cursor()
        self.table = "reviews"
        self.cols = [
            ('id',                  'TEXT'),
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

    # unused
    def _create_unique_key(self, table, column):
        sql = 'CREATE UNIQUE INDEX IF NOT EXISTS {1} ON {0} ({2})'.format(table, column, ','.join(self._get_col_headers()))
        self.db_cursor.execute(sql)

    def _get_rows_by_id(self, table, review_id):
        # todo review_id is not guaranteed to be unique
        """
        :param table: target table name to perform the sql query
        :param review_id: the google play review id, starts with 'gp:'
        :return: all matching sqlite3.Row's, empty list if none found
        """
        assert isinstance(review_id, str)
        self.db_cursor.execute('SELECT * from {} WHERE id="{}"'.format(table, review_id))
        return self.db_cursor.fetchall()

    def insert(self, review):
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
        if self.contains_review(review):
            set_expr = ["{}={}".format(col_headers[i], col_placeholders[i]) for i in range(len(self.cols))]
            sql = 'UPDATE {} SET {} WHERE id="{}"'.\
                format(self.table, ','.join(set_expr), col_values['id'])
            result = Result.updated
        else:
            sql = 'INSERT INTO {} ({}) VALUES ({})'.\
                format(self.table, ','.join(col_headers), ','.join(col_placeholders))
            result = Result.inserted
        assert len(col_headers) == len(col_placeholders)
        assert len(col_headers) == len(col_values)
        try:
            self.db_cursor.execute(sql, col_values)
            return result
        except sqlite3.OperationalError as e:
            print sql
            print col_values
            raise e

    def get_review(self, review_id):
        """
        :param review_id: the google play review id, starts with 'gp:'
        :return: Review object, None if it doesn't exist
        """
        rows = self._get_rows_by_id(self.table, review_id)
        assert len(rows) <= 1
        return Review(rows[0]) if rows else None

    def contains_review(self, review):
        assert isinstance(review, Review)
        return True if self.get_review(review.id) else False

    def save(self):
        self.db_conn.commit()

    def close(self):
        self.db_conn.commit()
        self.db_conn.close()


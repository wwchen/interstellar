#!/usr/bin/python

import time

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


# -*- coding: utf-8 -*-
"""
tornado_server.db.sqlite
~~~~~~~~~~~~~~~~~~~~~~~~

This file implements the Sqlite portion of the database abstraction.

Please note: the Sqlite abstraction is NOT asynchronous. This differs from the
Postgres abstraction, which is. This should not be a problem: we do not intend
to use Sqlite in production. However, it's worth bearing in mind that testing
against Sqlite can potentially hide some production-scope bugs. You are
hereby warned.
"""
import sqlite3


class Database(object):
    """
    Defines an abstraction around the Sqlite3 database.
    """
    def __init__(self):
        self.conn = None

    def connect(self, db_path, **kwargs):
        """
        Connect to the Sqlite3 database. Returns a database connection object.

        :param db_path: The path to the database.
        """
        self.conn = sqlite3.connect(db_path)

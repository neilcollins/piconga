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

    def get(self, query, parameters=()):
        """
        Execute a query that will return data against the Sqlite3 database.
        Returns the operation result as provided by the cursor.

        :param query: The query in the form of a Python format string.
        :param parameters: The parameters to add to the query. DO NOT ADD THEM
                           YOURSELF YOU WILL GET IT WRONG.
        """
        # Munge the string, removing the %s characters and adding the ?
        # instead. There is a bug here if we ever need literal % chars: let's
        # just never need them, eh?
        query = query.replace("%s", "?")

        cursor = self.conn.cursor()
        cursor.execute(query, parameters)

        return cursor.fetchall()

    def execute(self, query, parameters):
        """
        Executes a query that will not return data against the Sqlite3
        database. Returns nothing.

        :param query: The query in the form of a Python format string.
        :param parameters: The parameters to add to the query. DO NOT ADD THEM
                           YOURSELF YOU WILL GET IT WRONG.
        """
        # Munge the string, removing the %s characters and adding the ?
        # instead. There is a bug here if we ever need literal % chars: let's
        # just never need them, eh?
        query = query.replace("%s", "?")

        cursor = self.conn.cursor()
        cursor.execute(query, parameters)

        self.conn.commit()

        return

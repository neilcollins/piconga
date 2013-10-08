# -*- coding: utf-8 -*-
"""
tornado_server.db.postgres
~~~~~~~~~~~~~~~~~~~~~~~~~~

This file implements the PostgreSQL portion of the database abstraction.
"""
import psycopg2


class Database(object):
    """
    Defines an abstraction around a PostgreSQL database.
    """
    def __init__(self):
        self.conn = None

    def connect(self, db_name, **kwargs):
        """
        Connect to the PostgreSQL database. Requires the database name.
        Optionally takes any/all of the following keyword arguments: user,
        password, host, port.

        :param db_name: The name of the PostgreSQL database.
        """
        self.conn = psycopg2.connect(database=db_name, **kwargs)

    def get(self, query, parameters=()):
        """
        Executes a query that will return data against the PostgreSQL database.
        Returns the operation result as provided by the cursor.

        :param query: The query in the form of a Python format string.
        :param parameters: The parameters to add to the query. DO NOT ADD THEM
                           YOURSELF YOU WILL GET IT WRONG.
        """
        cursor = self.conn.cursor()
        cursor.execute(query, parameters)

        return cursor.fetchall()

    def execute(self, query, parameters):
        """
        Executes a query that will not return data against the PostgreSQL
        database. Returns nothing.

        :param query: The query in the form of a Python format string.
        :param parameters: The parameters to add to the query. DO NOT ADD THEM
                           YOURSELF YOU WILL GET IT WRONG.
        """
        cursor = self.conn.cursor()
        cursor.execute(query, parameters)

        self.conn.commit()

        return

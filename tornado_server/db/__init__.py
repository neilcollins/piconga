# -*- coding: utf-8 -*-
"""
tornado_server.db
~~~~~~~~~~~~~~~~~

The db module provides an abstraction for database access to the main Tornado
server. This is necessary to hide whether we're using Sqlite or Postgres from
the main application.

At the current moment we only provide Sqlite access. Postgres will come later.
"""
from .sqlite import Database as SqliteDatabase
from .postgres import Database as PostgresDatabase

Database = SqliteDatabase

__all__ = [Database]

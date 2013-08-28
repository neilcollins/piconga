# -*- coding: utf-8 -*-
"""
tornado_server.db
~~~~~~~~~~~~~~~~~

The db module provides an abstraction for database access to the main Tornado
server. This is necessary to hide whether we're using Sqlite or Postgres from
the main application.

At the current moment we only provide Sqlite access. Postgres will come later.
"""
from .sqlite import Database

__all__ = [Database]


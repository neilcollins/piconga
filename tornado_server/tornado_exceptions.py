# -*- coding: utf-8 -*-
"""
tornado_server.tornado_exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines any Tornado Server-specific exceptions thrown. Each of these represents
a specific error condition inside the Tornado Server.
"""


class JoinError(ValueError):
    """
    An attempt to join a conga has failed.
    """
    pass

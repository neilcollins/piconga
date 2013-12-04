# -*- coding: utf-8 -*-
"""
tornado_main.py
~~~~~~~~~~~~~~~

This file contains the entry point and basic logic for the concurrent TCP
server implementation that powers the Raspberry Pi Conga server. This server
uses an open source concurrency framework called Tornado that enables us to
efficiently handle many thousands of TCP connections.

The requirement for handling so many connections is that the Conga itself is
implemented as a ring network on top of a star network. Because of the relative
pain involved in traversing domestic and commercial NATs in a ring network, it
was judged to be simpler to have each Pi in the Conga connect to the server,
and then have the server act as a proxy between each of the Pis. This
simplicity involves a large cost on the server side, which will find itself
maintaining a number of concurrent TCP connections that will have data flowing
up and down them almost continually.

To this end, we are using Tornado to build a very simple TCP proxy.
"""
from tornado.tcpserver import TCPServer
from tornado.ioloop import IOLoop
import tornado.options
from tornado.options import options
import signal
from participant import Participant
from db import SqliteDatabase, PostgresDatabase


# We need to define our command line options.
tornado.options.define("pgname", default="",
                       help="The name of the Postgres database.")
tornado.options.define("pguser", default="",
                       help="The username for the Postgres database.")
tornado.options.define("pgpass", default="",
                       help="The password for the Postgres database.")
tornado.options.define("pghost", default="",
                       help="The host for the Postgres database.")
tornado.options.define("pgport", default="",
                       help="The port for the Postgres database.")


def handle_signal(sig, frame):
    """
    Close everything down nicely.
    """
    IOLoop.instance().add_callback(IOLoop.instance().stop)


class TCPProxy(TCPServer):
    """
    TCPProxy defines the central TCP serving implementation for the Pi Conga
    server. Each time a new connection comes in, this establishes a Participant
    object that wraps that connection.
    """
    db = None

    def __init__(self, use_pg, db_path='', db_kwargs={}, *args, **kwargs):
        super(TCPProxy, self).__init__(*args, **kwargs)

        if use_pg:
            self.db = PostgresDatabase()
            self.db.connect(**db_kwargs)
        else:
            self.db = SqliteDatabase()
            self.db.connect(db_path)

    def handle_stream(self, stream, address):
        """
        When a new incoming connection is found, this function is called. Wrap
        the incoming connection in a Participant, then wait until it sends some
        data.
        """
        r = Participant(stream, self.db)
        r.wait_for_headers()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    tornado.options.parse_command_line()

    # Work out whether we're going to use a Postgres DB or the Sqlite one.
    opts = {'db_name': options.pgname, 'user': options.pguser,
            'password': options.pgpass, 'host': options.pghost,
            'port': options.pgport}

    use_pg = any(opts.values())

    if use_pg:
        # Fixup the keyword arguments dictionary.
        opts = {key: val for (key, val) in opts.items() if val}

    proxy = TCPProxy(use_pg, db_path='server/piconga.db', db_kwargs=opts)
    proxy.listen(8888)
    IOLoop.instance().start()

    IOLoop.instance().close()

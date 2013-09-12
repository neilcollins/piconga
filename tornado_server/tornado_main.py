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
import signal
from participant import Participant
from db import Database


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
    last_connection = None
    db = None

    def __init__(self, db_path, *args, **kwargs):
        super(TCPProxy, self).__init__(*args, **kwargs)

        self.db = Database()
        self.db.connect(db_path)

    def handle_stream(self, stream, address):
        """
        When a new incoming connection is found, this function is called. Wrap
        the incoming connection in a Participant, then make it the most recent
        connection. Tell the oldest connection to use the new one as its
        write target.
        """
        r = Participant(stream, self.db)

        if self.last_connection is not None:
            self.last_connection.add_destination(r)

        self.last_connection = r

        r.wait_for_headers()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    proxy = TCPProxy('server/piconga.db')
    proxy.listen(8888)
    IOLoop.instance().start()
    IOLoop.instance().close()

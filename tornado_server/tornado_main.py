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
        r = Participant(stream)

        if self.last_connection is not None:
            self.last_connection.add_destination(r)

        self.last_connection = r

        r.wait_for_headers()


class Participant(object):
    """
    Participant wraps a single incoming IOStream. It knows about the next
    participant in the Conga chain, and correctly writes to it.
    """
    def __init__(self, source):
        self.source_stream = source
        self.destination = None

    def add_destination(self, destination):
        """
        Add a new conga participant as the target for any incoming conga
        messages.
        """
        self.destination = destination

    def write(self, data):
        """
        Write data on the downstream connection. If no such connection exists,
        drop this stuff on the floor.
        """
        try:
            self.source_stream.write(data)
        except AttributeError:
            pass

    def wait_for_headers(self):
        """
        Read from the incoming stream until we receive the delimiter that tells
        us that the headers have ended.
        """
        self.source_stream.read_until(b'\r\n\r\n', self._parse_headers)

    def _parse_headers(self, header_data):
        """
        Turns the headers into a dictionary. Checks the content-length and
        reads that many bytes as the body.
        """
        headers = {}
        decoded_data = header_data.decode('utf-8')

        for line in decoded_data.split('\r\n'):
            if line:
                key, val = line.split(':', 1)
                headers[key] = val

        # Get the content-length, and then read however many bytes we need to
        # get the body.
        length = int(headers.get('Content-Length', '0'))

        self.source_stream.read_bytes(length, self._repeat_data(header_data))
        self.wait_for_headers()

    def _repeat_data(self, header_data):
        """
        Builds a closure for use as a data sending callback. We use a closure
        here to ensure that we are able to wait for the message body before
        sending the headers, just in case the message is ill-formed. That way
        we don't confuse clients by sending headers with no following body.
        """
        def callback(data):
            self.destination.write(header_data + data)

        return callback


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    proxy = TCPProxy('server/piconga.db')
    proxy.listen(8888)
    IOLoop.instance().start()
    IOLoop.instance().close()

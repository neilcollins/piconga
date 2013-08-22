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


def handle_signal(sig, frame):
    """
    Close everything down nicely.
    """
    IOLoop.instance().add_callback(IOLoop.instance().stop)


class TCPProxy(TCPServer):
    """
    TCPProxy defines the central TCP serving implementation for the Pi Conga
    server. Each time a new connection comes in, this establishes a repeater
    between that connection and the last connection that came in.
    """
    last_connection = None

    def handle_stream(self, stream, address):
        """
        When a new incoming connection is found, this function is called.
        """
        if self.last_connection is not None:
            r = Repeater(self.last_connection, stream)
            r.wait_for_headers()

        self.last_connection = stream


class Repeater(object):
    """
    Repeater defines a mapping between two different IOStreams. It provides
    functionality to pull messages off of one connection and write them down
    on another.
    """
    def __init__(self, source, destination):
        self.source_stream = source
        self.destination_stream = destination

    def wait_for_headers(self):
        """
        Read from the incoming stream until we receive the delimiter that tells
        us that the headers have ended.
        """
        self.source_stream.read_until(b'\r\n\r\n', self._parse_headers)

    def _parse_headers(self, data):
        """
        Turns the headers into a dictionary. Checks the content-length and
        reads that many bytes as the body.
        """
        headers = {}
        data = data.decode('utf-8')

        for line in data.split('\r\n'):
            if line:
                key, val = line.split(':', 1)
                headers[key] = val

        length = int(headers.get('Content-Length', '0'))
        self.source_stream.read_bytes(length, self._repeat_body)
        self.wait_for_headers()

    def _repeat_body(self, data):
        """
        Sends the body down the wire.
        """
        self.destination_stream.write(data)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    proxy = TCPProxy()
    proxy.listen(8888)
    IOLoop.instance().start()
    IOLoop.instance().close()

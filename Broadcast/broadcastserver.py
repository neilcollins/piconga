# -*- coding: utf-8 -*-
"""
broadcastserver.py
~~~~~~~~~~~~~~~~~~

A small-scale demonstration of a broadcast peer-discovery system. This file
contains a long-running server that listens for broadcasts and discovers its
peers. When a peer broadcasts its arrival, the server will print the IP address
of the peer on stdout.
"""
import socket
import sys

HOST = ''
PORT = 33333

def listen(callback):
    """
    Listens on a particular UDP port for specifically crafted broadcast packets
    that identify a Pi Conga.

    :param callback: This function is called each time a request is received.
                     Takes a single argument: the source IP address as a
                     string.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    sock.setblocking(0)

    while True:
        try:
            data, addr = sock.recvfrom(256)
        except socket.error:
            pass
        else:
            if data.startswith('PICONGA'):
                print addr


if __name__ == '__main__':
    try:
        listen(None)
    except KeyboardInterrupt:
        sys.exit(0)

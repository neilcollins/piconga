# -*- coding: utf-8 -*-
"""
broadcastclient.py
~~~~~~~~~~~~~~~~~~

A small-scale demonstration of a broadcast peer-discovery system. This file
is a very short script that blasts out a broadcast packet identifying itself
to any servers in the network.
"""
import socket

HOST = ''
BIND_PORT = 0
DEST_PORT = 33333
data = 'PICONGA'

def send():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, BIND_PORT))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.sendto(data, ('<broadcast>', DEST_PORT))


if __name__ == '__main__':
    send()

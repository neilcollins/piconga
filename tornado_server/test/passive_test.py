# -*- coding: utf-8 -*-
"""
test/passive_test.py
~~~~~~~~~~~~~~~~~~~~~~~~

Provides a basic test that a simple conga line will work.
"""
import socket
import time

target = '127.0.0.1'
target_port = 8888
hello = "HELLO\r\nContent-Length: 0\r\n\r\n"
msg = "MSG\r\nContent-Length: 13\r\n\r\nTest message."
full_len = len(msg)

sck1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck1.connect((target, target_port))
sockets = []

for i in xrange(0, 10):
    sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sck.connect((target, target_port))
    sockets.append(sck)

sck_last = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck_last.connect((target, target_port))

# Each socket needs to say hello.
sck1.send(hello)
for sck in sockets:
    sck.send(hello)
sck_last.send(hello)

# Send the initial message.
sck1.send(msg)

for sck in sockets:
    resp = sck.recv(full_len)
    assert resp == msg
    sck.send(resp)

# Get the message off the end.
resp = sck_last.recv(full_len)
assert resp == msg

# Clean up.
sck1.close()
(x.close() for x in sockets)
sck_last.close()

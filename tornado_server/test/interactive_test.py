# -*- coding: utf-8 -*-
"""
test/interactive_test.py
~~~~~~~~~~~~~~~~~~~~~~~~

Provides a small interactive test suite for the Tornado server, to confirm
its basic function.
"""
import socket
import time

target = '127.0.0.1'
target_port = 8888

sck1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck1.connect((target, target_port))
sck2.connect((target, target_port))

while True:
    message = raw_input("Type your message: ")
    length = len(message)
    send_msg = 'Content-Length: %s\r\n\r\n%s' % (length, message)
    sck1.send(send_msg)

    resp = sck2.recv(length)
    print "Response received:\n%s\n" % resp

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
hello = 'HELLO\r\nContent-Length: 0\r\n\r\n'

sck1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck1.connect((target, target_port))
sck2.connect((target, target_port))
sck1.send(hello)
sck2.send(hello)

while True:
    message = raw_input("Type your message: ")
    length = len(message)
    send_msg = 'MSG\r\nContent-Length: %s\r\n\r\n%s' % (length, message)
    full_len = len(send_msg)
    sck1.send(send_msg)

    resp = sck2.recv(full_len)
    print "Response received:\n%s\n" % resp

# -*- coding: utf-8 -*-
"""
test/interactive_test.py
~~~~~~~~~~~~~~~~~~~~~~~~

Provides a small interactive test suite for the Tornado server, to confirm
its basic function.
"""
import socket
import time
import sqlite3

target = '127.0.0.1'
target_port = 8888
hello = 'HELLO\r\nContent-Length: 0\r\nUser-ID: %s\r\n\r\n'
bye = 'BYE\r\nContent-Length: 0\r\n\r\n'

# First, add ourselves to the database.
conn = sqlite3.connect('../../server/piconga.db')
cursor = conn.cursor()

# Clear the database, just in case.
cursor.execute('DELETE FROM conga_congamember WHERE conga_id=123')
conn.commit()

for i in xrange(1, 3):
    cursor.execute('INSERT INTO conga_congamember VALUES (123, ?, ?, ?)', (i, i, i))

conn.commit()
sck1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sck1.connect((target, target_port))
sck2.connect((target, target_port))
sck1.send(hello % 1)
sck2.send(hello % 2)

while True:
    message = raw_input("Type your message: ")
    length = len(message)

    if length == 0:
        break

    send_msg = 'MSG\r\nContent-Length: %s\r\n\r\n%s' % (length, message)
    full_len = len(send_msg)
    sck1.send(send_msg)

    resp = sck2.recv(full_len)
    print "Response received:\n%s\n" % resp


sck1.send(bye)
sck2.send(bye)

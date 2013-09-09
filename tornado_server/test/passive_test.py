# -*- coding: utf-8 -*-
"""
test/passive_test.py
~~~~~~~~~~~~~~~~~~~~~~~~

Provides a basic test that a simple conga line will work.
"""
import socket
import time
import sqlite3

target = '127.0.0.1'
target_port = 8888
hello = "HELLO\r\nContent-Length: 0\r\nUser-ID: %s\r\n\r\n"
bye = "BYE\r\nContent-Length: 0\r\n\r\n"
msg = "MSG\r\nContent-Length: 13\r\n\r\nTest message."
full_len = len(msg)

# First, add ourselves to the database.
conn = sqlite3.connect('../../server/piconga.db')
cursor = conn.cursor()

# Clear the database, just in case.
cursor.execute('DELETE FROM conga_congamember WHERE conga_id=123')
conn.commit()

for i in xrange(1, 13):
    cursor.execute('INSERT INTO conga_congamember VALUES (123, ?, ?, ?)', (i, i, i))

conn.commit()

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
sck1.send(hello % 1)
for i, sck in enumerate(sockets):
    sck.send(hello % (i + 2))
sck_last.send(hello % 12)

# Send the initial message.
sck1.send(msg)

for i, sck in enumerate(sockets):
    resp = sck.recv(full_len)
    assert resp == msg
    sck.send(resp)

# Get the message off the end.
resp = sck_last.recv(full_len)
assert resp == msg

# Now say bye!
sck1.send(bye)
for sck in sockets:
    sck.send(bye)
sck_last.send(bye)

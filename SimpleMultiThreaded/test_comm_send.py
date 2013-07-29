#!/usr/bin/python

# Test script for sending data to a Pi using a Communicator object.

import socket

TARGET_IP = "192.168.1.66"
TARGET_PORT = 5005

snd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
snd_sock.connect((TARGET_IP, TARGET_PORT))

while True:
    data = raw_input()
    snd_sock.send(data.encode())
    print "Sent: %s" % data
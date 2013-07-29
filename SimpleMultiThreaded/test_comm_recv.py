#!/usr/bin/python

# Test script for receiving messages on a Pi using the Communicator object.

import communicator

RECV_PORT = 5005

comm = communicator.Communicator(5005)
comm.run()

while True:
    data = comm.recv_queue.get()
    print "Received data: %s" % data.data
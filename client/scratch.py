import socket
import sys
from Tkinter import Tk
from tkSimpleDialog import askstring

import struct
import shlex

class ScratchProxy(object):
    """
    Proxy to send messages to and receive messages from Scratch.

    To use this class, you need to enable remote sensor connections on your 
    Scratch application.  See here for details:
    http://wiki.scratch.mit.edu/wiki/Remote_Sensor_Connections.
    
    Once enabled on Scratch, you can connect this class to the running
    Scratch application and send/recieve messages as desired.  To make life
    easier, this class also tracks the latest values for all variables as 
    reported by Scratch - accessiable through the variables dictionary.

    If you want to maintain a list of sensors to send to Scratch, you can
    update the sensors dictionary and then send an update to Scratch, using
    send_changes().
    """

    def __init__(self, server):
        """
        Constructor.  Connect to the specifid Scratch server (server).  Throws
        a socket.error if Scratch is not running.
        """
        self.socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1.0)
        self.socket.connect((server, 42001))
        self.variables = {}
        self.sensors = {}
        self._last_sent = {}

    def send(self, cmd):
        """
        Send a command to the Scratch server.
        """
        msg = struct.pack('>l{}s'.format(len(cmd)), len(cmd), cmd)
        self.socket.send(msg)

    def recv(self):
        """
        Receive any messages from the Scratch server.  Returns a list of
        commands sent by Scratch, or an empty list if there are none.
        """
        messages = []
        buffer = self.socket.recv(1024)
        while len(buffer) >= 4:
            n = struct.unpack_from('>l', buffer)
            buffer = buffer[4:]
            msg = struct.unpack_from('{}s'.format(n[0]), buffer)
            messages.append(msg[0])
            buffer = buffer [n[0]:]

        for msg in messages:
            tokens = shlex.split(msg)
            if tokens[0] == "sensor-update":
                for i in range(1, len(tokens), 2):
                    self.variables[tokens[i]] = tokens[i+1]
        return messages

    def send_changes(self, kick):
        """
        Send the changed sensors to Scratch, using the specified event (kick)
        to broadcast the fact that the sensors have changed.
        """
        for (sensor, value) in self.sensors.items():
            if (sensor not in self._last_sent or
                self._last_sent[sensor] != value):
                    self.send('sensor-update "{}" "{}"'.format(sensor, value))
        self.send('broadcast "{}"'.format(kick))
        self._last_sent = self.sensors.copy()

# Temporary main loop.
root = Tk()
root.withdraw()
   
print "Connecting..."
scratch = ScratchProxy("localhost")
print "Connected!"
   
while True:
    msg = askstring('Scratch Connector', 'Send Broadcast:')
    if msg:
        print "Sending:", msg
        scratch.sensors["message"] = msg
        scratch.send_changes("kick")
        try:
            messages = scratch.recv()
            for msg in messages:
                if 'broadcast "kick_back"' in msg:
                    print "Received:", scratch.variables["message"]
        except Exception, e:
            print e
    else:
        break

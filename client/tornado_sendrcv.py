#!/usr/bin/python
"""PiConga Client Tornado Send/Receive Module

   This module handles sending and receiving Conga protocol messages to and
   from the Tornado server.
   """
   
# Python imports
import socket
import multiprocessing

class SendError(socket.error):
    """Error when sending data.  Subclasses directly from socket.error - this
    exists only so that we can distinguish send errors from receive errors.
    """
    pass

class RecvError(socket.error):
    """Error when receiving data.  Subclasses directly from socket.error - 
    this exists only so that we can distinguish send errors from receive
    errors.
    """
    pass
    
class TornadoSendRcv(object):
    """Class to talk to the Tornado server."""
    
    # Private functions
    
    def __init__(self, ip, port):
        """Constructor.  Store off the server IP and port."""
        
        self._server_ip = ip
        self._server_port = port
        
        # Create initial versions of all other internal class variables.
        self._sock = None
        self._recv_queue = None
        
        return
        
    
    def _recv_loop(self):
        """Get messages from the server."""
        
        while True:
            # Try to receive a message from the socket.  We will wait for up to
            # ten seconds to receive a message.
            try:
                data = self._sock.recv(4096)
                
                # Put this data onto the receive queue.
                self._recv_queue.put(data)
            except socket.timeout:
                # It's fine for the socket to timeout, we just don't want it
                # sitting there forever.  Go round again.
                pass
            except socket.error as e:
                # There was a problem with receiving the data.  Raise a
                # receive error to leave the loop.
                recv_error = RecvError()
                recv_error.value = e.value
                raise recv_error
        
        return

    def _parse_conga_msg(self, msg):
        """Parse a message as a Conga protocol message."""
        
        ### MORE CODE TO GO HERE
        
        return
        
        
    # Public functions
    
    def run(self):
        """Connect to the server, set up the output queue, and kick off the
        receive loop."""
        
        # Create the socket to connect to the server.  This is a standard IPv4
        # TCP socket.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect the socket to the server.
        self._sock.connect((self._server_ip, self._server_port))
        
        # This socket should block with a ten-second timeout.
        self._sock.setblocking(1)
        self._sock.settimeout(10)
        
        # Create a queue to hold received messages.
        self._recv_queue = multiprocessing.Queue()
        
        # Spin the event loop.
        try:
            self._recv_loop()
        except ## something!
            
        return
        
        
    def get_message(self):
        """Get a message from the receive queue, if one exists."""
        
        # Check for a valid socket.  We can't return any messages if one does
        # not exist, so return nothing.
        if self._sock is None:
            return None
            
        # Pull a message off the queue, if one exists.
        try:
            msg = self._recv_queue.get()
        except multiprocessing.Queue.Empty:
            # No messages to return, return None.
            return None
            
        # Parse the message as a Conga protocol message.
        conga_msg = self._parse_conga_msg(msg)
            
        return conga_msg
                
    
    def send_message(self, type, msg=""):
        """Send a message to the Tornado server.  Specify the message type
        and, if appropriate, the text to send."""
        
        ### MORE CODE TO GO HERE
        
        return
        
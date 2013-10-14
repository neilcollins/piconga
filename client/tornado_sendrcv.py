#!/usr/bin/python
"""PiConga Client Tornado Send/Receive Module

   This module handles sending and receiving Conga protocol messages to and
   from the Tornado server.
   """
   
# Python imports
import logging
import socket
import multiprocessing
import Queue

# Set up logging. Child of the core client logger.
logger = logging.getLogger("piconga.tornado")

class SendError(socket.error):
    """
    Error when sending data.  Subclasses directly from socket.error - this
    exists only so that we can distinguish send errors from receive errors.
    """
    pass

class RecvError(socket.error):
    """
    Error when receiving data.  Subclasses directly from socket.error - 
    this exists only so that we can distinguish send errors from receive
    errors.
    """
    pass
    
class TornadoSendRcv(object):
    """
    Class to talk to the Tornado server.
    """
    
    valid_verbs = ["HELLO", "MSG", "BYE"]
    
    # Private functions
    
    def __init__(self, server_ip, server_port):
        """
        Constructor.  Store off the server IP and port.
        """
 
        # Store off the server IP and port.
        self._server_ip = server_ip
        self._server_port = server_port

        # Create initial versions of all other internal class variables.
        self._sock = None
        self._send_queue = None
        self._recv_queue = None
        
        return
        
    
    def _sendrecv_loop(self):
        """
        Get messages from and send messages to the server.
        """
        
        while self._sock is not None:
            # Try to receive a message from the socket.
            try:
                data = self._sock.recv(4096)
                logger.debug("Received message: %s", data)
                
                # Parse the message as a Conga protocol message.
                conga_msg = self._parse_conga_msg(data)

                # Put this data onto the receive queue.
                if conga_msg is not None:
                    self._recv_queue.put(conga_msg)
            except socket.timeout:
                # It's fine for the socket to timeout, we just don't want it
                # sitting there forever.
                pass
            except socket.error as e:
                # There was a problem with receiving the data.  Raise a
                # receive error to leave the loop.
                recv_error = RecvError()
                recv_error.value = e.value
                raise recv_error
        
            # Now try to send any messages.  We send all of them in one go so
            # that we're not slowed down by having to timeout on receiving
            # each time.
            try:
                while True:
                    # Note that this will not loop forever because eventually
                    # the queue will be empty, dropping us into the except:
                    # branch.
                    msg = self._send_queue.get(block=False)
                    self._send_conga_message(msg)
            except Queue.Empty:
                pass
        return


    def _parse_conga_msg(self, msg):
        """
        Parse a message as a Conga protocol message.  Returns a tuple 
        containing the message's verb, a dictionary of its headers, and its
        body.
        """
        
        # A zero-length message can't be decoded, so return None.
        if len(msg) == 0:
            return None
        
        message = msg.decode("utf_8")
        lines = message.split("\r\n")
        
        # The verb must always be in the first line of the message.
        verb = lines[0]
        assert verb in self.valid_verbs
        
        # Every line onwards that is not blank is a header.
        headers = {}
        for line_no in range(1, len(lines)):
            line = lines[line_no]
            if len(line) == 0:
                # Blank line - this is the separator between the headers and
                # the body.  Store off the body and break out.
                if line_no == len(lines) - 1:
                    body = ""
                else:
                    body = "".join(lines[line_no+1:])
                break
            name, sep, value = line.partition(":")
            assert sep == ":", "No colon found in header"
            assert name not in headers.keys(), "Duplicate headers found"
            headers[name] = value
        
        # We must have made it out of the loop by setting the body variable,
        # so it's safe to return it here.        
        return (verb, headers, body)
        
        
    def _send_conga_message(self, msg):
        """
        Send a message to the Tornado server.  This function assumes that
        you have already created the message, ready to send.
        """

        assert self._sock is not None
        
        try:
            logger.debug("Sending message: %s", msg)
            bytes_sent = self._sock.send(msg)
        except socket.error as e:
            send_error = SendError()
            send_error.value = e.value
            raise send_error
        
        assert bytes_sent == len(msg)
        
        if msg.startswith("BYE"):
            # We have just closed the server-side connection.  Shut it down
            # from this side too.
            self._close_connection()
        
        return   


    def _close_connection(self):
        """
        Close the connection to the Tornado server.
        """
        
        logger.debug("Closing Tornado server")
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()
        self._sock = None
        
        return  
        
        
    # Public functions
    
    def run(self, recv_q, send_q):
        """
        Connect to the server, set up the input/output queues, and kick
        off the send/receive loop.
        """
        
        logger.debug("Starting Tornado send/recv")
    
        # Create the socket to connect to the server.  This is a standard IPv4
        # TCP socket.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect the socket to the server.
        self._sock.connect((self._server_ip, self._server_port))
        
        # This socket should block with a 100ms timeout, as both sending and
        # receiving will block on this.
        self._sock.setblocking(1)
        self._sock.settimeout(0.1)
        
        # Assign the send and receive queues from the caller.
        self._send_queue = send_q
        self._recv_queue = recv_q
        
        # Spin the event loop.
        try:
            self._sendrecv_loop()
        except RecvError:
            if self._sock is None:
                # Socket was closed by sending a BYE.  This is fine, no more
                # to do.
                pass
            else:
                # Something went badly wrong.  Shut down the socket.
                self._close_connection()
            
        return
    
                
# External functions.  These are designed to act on a TornadoSendRcv object
# through its externally-visible queues.

def get_message(recv_q):
    """
    Get a message from the receive queue, if one exists.
    """
        
    # Pull a message off the queue, if one exists.
    try:
        msg = recv_q.get(block=False)
        logger.debug("Received message: %s", msg)
    except Queue.Empty:
        # No messages to return, return None.
        return None
        
    # Parse the message as a Conga protocol message.
    conga_msg = TornadoSendRcv._parse_conga_msg(msg)
        
    return conga_msg
    
    
def create_conga_msg(verb, headers, body=""):
    """
    Create a Conga-protocol message, ready to send over the wire.
    Parameters are as follows:
    verb    - HELLO, MSG or BYE
    headers - Dictionary of headers to send.  Keys are the names of the 
              headers to send, values are the values of those headers.
              The Content-Length header should not be included.
    body    - Body of the message to send (optional).
    """
    
    message = "%s\r\n" % verb
    for name in headers.keys():
        message += "%s: %s\r\n" % (name, headers[name])
    message += "Content-Length: %d\r\n" % len(body)
    message += "\r\n"
    message += body
    
    return message.encode("utf_8")

        
def send_hello(send_q, userid):
    """
    Send a HELLO message to the Tornado server.  Requires the user ID
    of the Conga you wish to join.
    """
    
    msg = create_conga_msg("HELLO", {"User-ID": userid})
                                 
    send_q.put(msg)
    
    return
    
    
def send_msg(send_q, data):
    """
    Send a MSG message to the Tornado server.  Requires the payload of 
    the message you wish to send.
    """
    
    msg = create_conga_msg("MSG", {}, data)
    
    send_q.put(msg)
    
    return
    
    
def send_bye(send_q):
    """
    Send a BYE message to the Tornado server, then disconnect.
    """
    
    msg = create_conga_msg("BYE", {})
    
    send_q.put(msg)
    
    return

#!/usr/bin/python
"""PiConga Client Tornado Send/Receive Module

   This module handles sending and receiving Conga protocol messages to and
   from the Tornado server.
   """
   
# Python imports
import logging
import socket
import multiprocessing

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
    
    def __init__(self):
        """
        Constructor.  Store off the server IP and port.
        """
 
        # Create initial versions of all other internal class variables.
        self._server_ip = None
        self._server_port = None
        self._sock = None
        self._recv_queue = None
        
        return
        
    
    def _recv_loop(self):
        """
        Get messages from the server.
        """
        
        while self._sock is not None:
            # Try to receive a message from the socket.  We will wait for up to
            # ten seconds to receive a message.
            try:
                data = self._sock.recv(4096)
                logger.debug("Received message: %s", data)
                
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
        """
        Parse a message as a Conga protocol message.  Returns a tuple 
        containing the message's verb, a dictionary of its headers, and its
        body.
        """
        
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
        
        
    def _create_conga_msg(self, verb, headers, body=""):
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
        
        
    # Public functions
    
    def run(self, server_ip, server_port):
        """
        Connect to the server, set up the output queue, and kick off the
        receive loop.
        """
        
        logger.debug("Starting Tornado send/recv")
    
        # Store off the server IP and port.
        self._server_ip = server_ip
        self._server_port = server_port
        
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
        except RecvError:
            if self._sock is None:
                # Socket was closed by sending a BYE.  This is fine, no more
                # to do.
                pass
            else:
                # Something went badly wrong.  Shut down the socket.
                self.close_connection()
            
        return
        
        
    def get_message(self):
        """
        Get a message from the receive queue, if one exists.
        """
        
        logger.debug("Getting a message from the receive queue")
    
        # Check for a valid socket.  We can't return any messages if one does
        # not exist, so return nothing.
        if self._sock is None:
            return None
            
        # Pull a message off the queue, if one exists.
        try:
            msg = self._recv_queue.get()
            logger.debug("Received message: %s", msg)
        except multiprocessing.Queue.Empty:
            # No messages to return, return None.
            return None
            
        # Parse the message as a Conga protocol message.
        conga_msg = self._parse_conga_msg(msg)
            
        return conga_msg
                
    
    def send_conga_message(self, msg):
        """
        Send a message to the Tornado server.  This function assumes that
        you have already created the message, ready to send.
        """
    
        assert self._sock is not None
        
        try:
            logger.debug("Sending message: %s", data)
            bytes_sent = self._sock.send(msg)
        except socket.error as e:
            send_error = SendError()
            send_error.value = e.value
            raise send_error
        
        assert bytes_sent == len(msg)
        
        return
        
        
    def send_hello(self, userid):
        """
        Send a HELLO message to the Tornado server.  Requires the user ID
        of the Conga you wish to join.
        """
        
        msg = self._create_conga_msg("HELLO",
                                     {"User-ID": userid})
                                     
        self.send_conga_message(msg)
        
        return
        
        
    def send_msg(self, data):
        """
        Send a MSG message to the Tornado server.  Requires the payload of 
        the message you wish to send.
        """
        
        msg = self._create_conga_msg("MSG", {}, data)
        
        self.send_conga_message(msg)
        
        return
        
        
    def send_bye(self):
        """
        Send a BYE message to the Tornado server, then disconnect.
        """
        
        msg = self._create_conga_msg("BYE", {})
        
        self.send_conga_message(msg)
        
        # Tidy up the connection.
        self.close_connection()
        
        return
        
        
    def close_connection(self):
        """
        Close the connection to the Tornado server.  This should only be
        used externally in the case of errors - to exit cleanly, call
        send_bye.
        """
        
        logger.debug("Closing Tornado server")
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()
        self._sock = None
        
        return
        
        
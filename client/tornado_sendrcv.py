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

class QueueMsg(object):
    """
    Message container for passing information in and out of the TornadoSendRcv
    object.  Can be used for messages going to/from the Tornado server, or
    management-level messages about the connection.
    """
    
    # Types of message that can be passed in or out.
    SERVER_MSG = 0
    START_CONN = 1
    CLOSE_CONN = 2
    CONN_LOST = 3
    
    VALID_TYPES = [SERVER_MSG, START_CONN, CLOSE_CONN, CONN_LOST]
    
    def __init__(self, type, data=None):
        """
        Constructor.  Store off the message type and data.
        """
        
        assert type in self.VALID_TYPES
        
        self.type = type
        self.data = data
        
    
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
        
        while True:
            if self._sock is not None:
                # Try to receive a message from the socket.
                try:
                    data = self._sock.recv(4096)
                    if data:
                        logger.debug("Received message: %s", data)
                    
                        # Parse the message as a Conga protocol message.
                        conga_msg = self._parse_conga_msg(data)

                        # Put this data onto the receive queue.
                        if conga_msg is not None:
                            self._recv_queue.put(conga_msg)
                except socket.timeout:
                    # It's fine for the socket to timeout, we just don't 
                    # want it sitting there forever.
                    pass
                except socket.error as e:
                    # There was a problem with receiving the data.  
                    # Raise a receive error to leave the loop.
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
                    
                    logger.debug("Process message of type %d" % msg.type)
                    if msg.type == QueueMsg.SERVER_MSG:
                        # Message to send to the server.
                        self._send_conga_message(msg.data)
                    elif msg.type == QueueMsg.START_CONN:
                        # Establish the connection if it's not already up.
                        self._start_connection()
                    elif msg.type == QueueMsg.CLOSE_CONN:
                        # Close the connection.
                        self._close_connection()
                    else:
                        # This message type doesn't make any sense here!
                        raise AssertionError, \
                            "Unexpected message type: %d" % msg.type
                        
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
            headers[name] = value.lstrip()
        
        # We must have made it out of the loop by setting the body variable,
        # so it's safe to return it here.        
        return (verb, headers, body)
        
        
    def _send_conga_message(self, msg):
        """
        Send a message to the Tornado server.  This function assumes that
        you have already created the message, ready to send.
        """

        if self._sock is None:
            # Connection to the server is not active.  Drop this message.
            return
        
        try:
            logger.debug("Sending message: %s", msg)
            bytes_sent = self._sock.send(msg)
        except socket.error as e:
            send_error = SendError()
            send_error.message = e.message
            send_error.strerror = e.strerror
            send_error.errno = e.errno
            raise send_error
        
        assert bytes_sent == len(msg)
        
        return   


    def _start_connection(self):
        """
        Start the connection to the Tornado server.
        """
        
        logger.debug("Starting connection to Tornado server.")
        
        if self._sock is not None:
            # Socket is already set up, drop out.
            return
        
        # Create the socket to connect to the server.  This is a standard IPv4
        # TCP socket.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect the socket to the server.
        self._sock.connect((self._server_ip, self._server_port))
        
        # This socket should block with a 100ms timeout, as both sending and
        # receiving will block on this.
        self._sock.setblocking(1)
        self._sock.settimeout(0.1)
        
        return
        
        
    def _close_connection(self):
        """
        Close the connection to the Tornado server.
        """
        
        logger.debug("Closing connection to Tornado server")
        
        if self._sock is None:
            # Nothing to do here.
            return
            
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()
        self._sock = None
        
        return  
        
        
    # Public functions
    
    def run(self, recv_q, send_q):
        """
        Set up the input/output queues, and kick off the send/receive loop.
        """
        
        logger.debug("Starting Tornado send/recv")
        
        # Assign the send and receive queues from the caller.
        self._send_queue = send_q
        self._recv_queue = recv_q
        
        # Spin the event loop.
        try:
            self._sendrecv_loop()
        except RecvError:
            if self._sock is None:
                # Socket was closed deliberately.  This is fine, no more
                # to do.
                pass
            else:
                # Something went badly wrong.  Shut down the socket.
                self._close_connection()
                self._recv_queue.put(QueueMsg(QueueMsg.CONN_LOST))                
            
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
    
    return msg
    
    
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
        if headers[name] is not None:
            message += "%s: %s\r\n" % (name, headers[name])
    message += "Content-Length: %d\r\n" % len(body)
    message += "\r\n"
    message += body
    
    return QueueMsg(QueueMsg.SERVER_MSG, message.encode("utf_8"))

        
def send_hello(send_q, userid):
    """
    Send a HELLO message to the Tornado server.  Requires the user ID
    of the Conga you wish to join.
    """
    
    msg = create_conga_msg("HELLO", {"User-ID": userid})
                                 
    send_q.put(msg)
    
    return
    
    
def send_msg(send_q, data, headers={}):
    """
    Send a MSG message to the Tornado server.  Requires the payload of 
    the message you wish to send.
    """
    
    msg = create_conga_msg("MSG", headers, data)
    
    send_q.put(msg)
    
    return
    
    
def send_bye(send_q):
    """
    Send a BYE message to the Tornado server, then disconnect.
    """
    
    msg = create_conga_msg("BYE", {})
    
    send_q.put(msg)
    
    return


def start_connection(send_q):
    """
    Tell the SendRcv object to connect to the Tornado server via its send
    queue.
    """
    
    logger.debug("Tell SendRcv object to start connection")
    msg = QueueMsg(QueueMsg.START_CONN)
    
    send_q.put(msg)
    
    return
    
    
def close_connection(send_q):
    """
    Tell the SendRcv object to close its connection to the Tornado server via
    its send queue.
    """
    
    logger.debug("Tell SendRcv object to close connection")
    msg = QueueMsg(QueueMsg.CLOSE_CONN)
    
    send_q.put(msg)
    
    return
    

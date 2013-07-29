#!/usr/bin/python

# Library imports
from multiprocessing import Process, Queue
import socket


class CongaData(object):
    """Data sent or received on a UDP socket."""
   
    def __init__(self, data, address=None):
        """Store off the passed-in parameters."""
        
        self.data = data
        self.address = address
        return


class Communicator(object):
    """Sends and receives messages and places them in queues."""
    
    def __init__(self, port):
        """Set up the objects needed by this class."""
        
        self.udp_port = port
        self.recv_queue = Queue()
        self.send_queue = Queue()
        
        return
        
    def recv_loop(self, port, queue):
        """Loop to receive messages on a port and place them on a queue."""
    
        # Set up the receive socket.
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("", port))
            sock.listen(2)        
            client_sock, addr = sock.accept()
            
            # Now loop round, getting data from the socket and placing it on 
            # the queue.
            while True:
                data = client_sock.recv(1024)
                congadata = CongaData(data)
                queue.put(congadata)
            
        finally:
            sock.close()
            
        return
    
    def send_loop(self, port, queue):
        """Loop to take messages off a queue and send them as fast as possible.
        """
        
        # Grab messages off the queue as fast as possible.
        while True:
            congadata = queue.get()
            
            # Set up sending socket.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((congadata.address, port))
            
            # Send the data and close the socket.
            sock.send(congadata.data)
            sock.shutdown()
            sock.close()
            
        return
        
    def run(self):
        """Kick off the send and receive loops in separate threads."""
        
        # Create the processes to handle receiving and sending.
        self.receiver = Process(target=self.recv_loop,
                                args=(self.udp_port, self.recv_queue))
        self.sender = Process(target=self.send_loop,
                              args=(self.udp_port, self.send_queue))
                              
        # Start them off!
        self.receiver.start()
        self.sender.start()
        
        return
    
    def stop(self):
        """Stop all the child processes."""
        
        self.receiver.terminate()
        self.sender.terminate()
        
        return
        
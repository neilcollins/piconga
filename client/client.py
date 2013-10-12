#!/usr/bin/python
"""PiConga Client Core Module

   This is the core section of the client, which ties together all other parts
   and handles startup/shutdown.
   """
   
# Python imports
import getpass
import logging
import multiprocessing
import Queue
import sys
import time

# PiConga imports
import cli
import django_sendrcv
import tornado_sendrcv

# Set up a logging object for this module and make it log to a file.
logger = logging.getLogger("piconga")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("piconga.log", mode="w")
formatter = logging.Formatter(fmt="%(asctime)s %(name)-20s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class Client(object):
    """PiConga Client."""
    
    # Class constants.
    base_url = "http://ec2-54-229-169-49.eu-west-1.compute.amazonaws.com/conga"
    #base_url = "http://localhost:8000/conga"
    tornado_server_ip = "ec2-54-229-169-49.eu-west-1.compute.amazonaws.com"
    #tornado_server_ip = "localhost"
    tornado_server_port = 8888
    
    def __init__(self, username, password):
        """Constructor.  Create the three subcomponents."""
        
        self._cli = cli.Cli()
        self._django_sr = django_sendrcv.DjangoSendRcv(self.base_url)
        self._tornado_sr = tornado_sendrcv.TornadoSendRcv(
            self.tornado_server_ip, self.tornado_server_port)
        
        # Store off the username and password.
        self._username = username
        self._password = password
        
        return
        
        
    def main_loop(self):
        """Loop around, fetching requests from the CLI and sending them out
        via the Django and Tornado servers."""
        
        # Create the queues for any comms.
        actions = multiprocessing.Queue()
        events = multiprocessing.Queue()
        in_msgs = multiprocessing.Queue()
        out_msgs = multiprocessing.Queue()
                                                     
        # Start the CLI in its own process.
        cli_proc = multiprocessing.Process(
            target=self._cli.run, args = (actions, events))
        cli_proc.start()
        
        # Start up the Tornado loop in its own process.
        tornado_proc = multiprocessing.Process(
            target=self._tornado_sr.run, args=(in_msgs, out_msgs))
        tornado_proc.start()
        

        # Run until the CLI terminates dispatching events.
        while True:
            try:
                recvd_action = actions.get(block=False)
                logger.debug("Saw action type %d", recvd_action.type)
                if recvd_action.type == cli.Action.CREATE_CONGA:
                    # Create an existing conga
                    self._userid = self._django_sr.create_conga(
                        "<CONGA>", "<PASSWORD")
                    events.put(cli.Event(cli.Event.TEXT,
                        "Created conga"))
                elif recvd_action.type == cli.Action.JOIN_CONGA:
                    # Join an existing conga
                    self._userid = self._django_sr.join_conga(
                        "<CONGA>", "<PASSWORD")
                    events.put(cli.Event(cli.Event.TEXT,
                        "Joined conga"))
                elif recvd_action.type == cli.Action.LEAVE_CONGA:
                    # Left a conga
                    self._userid = self._django_sr.leave_conga(
                        "<CONGA>", "<PASSWORD>")
                    events.put(cli.Event(cli.Event.TEXT,
                        "Left conga"))
                elif recvd_action.type == cli.Action.CONNECT:
                    # Register the user with the Django server.
                    self._userid = self._django_sr.register_user(
                        self._username, self._password)
                    events.put(cli.Event(cli.Event.TEXT,
                        "Connected as %s (id %s)" % 
                        (self._username, self._userid)))
                elif recvd_action.type == cli.Action.DISCONNECT:
                    # Unregister the user with the Django server.
                    self._userid = self._django_sr.unregister_user(
                        self._username, self._password)
                    events.put(cli.Event(cli.Event.TEXT,
                        "Disconnected from  %s" % self.base_url))
		elif recvd_action.type == cli.Action.SEND_MSG:
		    # Send a ping along the Conga.
		    out_msgs.put("Ping!")
		    events.put(cli.Event(cli.Event.TEXT,
                        "Sent a ping along the Conga."))
                elif recvd_action.type == cli.Action.QUIT:
                    logger.debug("CLI told us to quit")
                    try:
                        cli_proc.terminate()
                        tornado_proc.terminate()
                    except Cli.ExitCli:
                        logger.debug("Saw CLI exit exception")
                    finally:
                        sys.exit()
                else:
                    events.put(cli.Event(cli.Event.TEXT,
                        "Unknown action %d" % recvd_action.type))
            except django_sendrcv.ServerError, e:
                events.put(cli.Event(cli.Event.TEXT,
                     str(e)))
            except Queue.Empty:
                pass

            try:
                # Check for any new messages.
                recvd_msg = in_msgs.get(block=False)
                if recvd_msg is not None:
                    events.pit(
                        cli.Event(cli.Event.TEXT, recvd_msg))
            except Queue.Empty:
                pass

            time.sleep(0.1)


if __name__ == "__main__":
    # Redirect stderr - we want errors to appear in their own file.
    errorlog = open("errors.log", "w")
    sys.stderr = errorlog    

    # Prompt the user for some basic information.
    print "Welcome to PiConga!\n"
    print "Please enter your name."
    username = raw_input("Username: ")
    print "Now please enter your password."
    password = getpass.getpass("Password: ")
    
    # Start up the client.
    print "Starting PiConga client..."
    client = Client(username, password)
    client.main_loop()

#!/usr/bin/python
"""PiConga Client Core Module

   This is the core section of the client, which ties together all other parts
   and handles startup/shutdown.
   """
   
# Python imports
import multiprocessing

# PiConga imports
import cli
import django_sendrcv
import tornado_sendrcv

class Client(object):
    """PiConga Client."""
    
    # Class constants.
    base_url = "http://localhost:8000/conga"
    tornado_server_ip = "127.0.0.1"
    
    def __init__(self, username, password):
        """Constructor.  Create the three subcomponents."""
        
        self._cli = cli.Cli()
        self._django_sr = django_sendrcv.DjangoSendRcv(base_url)
        self._tornado_sr = tornado_sendrcv.TornadoSendRcv()
        
        # Store off the username and password.
        self._username = username
        self._password = password
        
        return
        
        
    def main_loop():
        """Loop around, fetching requests from the CLI and sending them out
        via the Django and Tornado servers."""
        
        # Register the user with the Django server.
        self._userid = self._django_sr.register_user(self._username,
                                                     self._password)
                                                     
        # Start the CLI in its own process.
        cli_proc = multiprocessing.Process(target=self._cli.run)
        cli_proc.start()
        
        # Start up the Tornado loop in its own process.
        tornado_proc = multiprocessing.Process(target=self._tornado_sr.run,
                                               args=(tornado_server_ip,
                                                     tornado_server_port))
        tornado_proc.start()
        

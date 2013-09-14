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
    
    def __init__(self):
        """Constructor.  Create the three subcomponents."""

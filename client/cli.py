#!/usr/bin/python

# PiConga CLI Module
# 
# This CLI is designed to show everything important that happens to your 
# client, and also let you join, leave and manipulate congas.  It uses
# the curses library, which gives us a user interface entirely in text.

# Python imports
import curses
import subprocess
import multiprocessing

class Cli(object):
    """Class representing the CLI as a whole."""
    
    # Class constants.
    
    class Event(object):
        """Event that may be sent to the CLI for display."""
        
        # Event types.
        TEXT = 0          # Simple text string.
        MSG_RECVD = 1     # Message received on a conga.
        CONGA_JOINED = 2  # Client has joined a conga.
        CONGA_LEFT = 3    # Client has left a conga.
        LOST_CONN = 4     # Client lost connection to the server.
         
        # List of all allowed events.
        allowed_events = [TEXT, MSG_RECVD, CONGA_JOINED,
                          CONGA_LEFT, LOST_CONN]
        
        def __init__(self, event_type, text):
            """Constructor.  Store input parameters."""
            
            self.type = event_type
            self.text = text
            self.printed = False
            
            return
            
    # Private functions.
    
    def __init__(self):
        """Constructor."""
        
        (self._rows, self._cols) = self._get_term_dimensions()
        self._event_win = None
        self._input_win = None
        self._event_queue = multiprocessing.Queue()
        
        return
        
        
    def _get_term_dimensions(self):
        """Return the current dimensions of the terminal."""
        
        dimens_text = subprocess.check_output(["stty", "size"]).split()
        dimensions = [int(token) for token in dimens_text]
        
        return tuple(dimensions)
     
     
    def _cli_loop(self, event_win, input_win):
        """Main CLI loop.  Display any new events and look for any user input.
        
        Parameters: event_win  - Window object representing the pane that
                                 displays events.                                 
                    input_win  - Window object representing the pane that takes
                                 input from the user.
        Returns:    Nothing.
        """
        while True:
            # First, update the terminal dimensions, in case the user has 
            # resized the window.
            (self._rows, self._cols) = self._get_term_dimensions()
            
            ### MORE CODE TO GO HERE
            
        return
        
        
    def _start_cli(self, main_window):
        """Create the various CLI windows and kick off the main loop."""
        
        # First create the event window that receives events.
        
        ### MORE CODE TO GO HERE
        
    # Public functions.
    
    def run(self):
        """Start the CLI."""
        curses.wrapper(self._start_cli)
        
        return
        
    def add_event(self, event_type, text):
        """Add an event to the queue to be displayed on the CLI.
        
        Parameters: event_type  - Type of event to be displayed.  One of the
                                  event type class constants.
                    text        - Text associated with this event.  Normal
                                  string.
        Returns:    Nothing.
        """
        
        # Check that the event is permitted.
        assert event_type in self.Events.allowed_events
        
        # Add the event to the queue.
        event = self.Event(event_type, text)
        self._event_queue.put(event)
        
        return
        
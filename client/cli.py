#!/usr/bin/python
"""PiConga CLI Module
 
   This CLI is designed to show everything important that happens to your 
   client, and also let you join, leave and manipulate congas.  It uses
   the curses library, which gives us a user interface entirely in text.
"""   

# Python imports
import curses
import logging
import subprocess
import multiprocessing
import Queue
import threading
from time import sleep

# PiConga imports
from credits import credits, matrix

# Set up logging for this module. Child of the core client logger.
logger = logging.getLogger("piconga.cli")

# Menu definitions.
class Menu(object):
    """
    Menu in the CLI hierarchy.
    """
    
    def __init__(self, name):
        """
        Constructor.  Store the input parameters.
        """
        # Name of the item - this text appears in the menu.
        self.name = name
        
        # Parent menu.  Initialises to None - if this is any menu other than
        # the main menu, this MUST be changed to something else before running
        # the CLI, otherwise the client will exit on selecting it!
        self.parent = None
        
        # List of items to offer from this menu.
        self.menu_items = []
        
        return

    def verify(self, global_menu):
        """
        Assert that the menu has at least one item and that no two items
        share the same trigger.
        """
        assert len(self.menu_items) > 0
        
        # Check that the list of triggers is the same length when we remove
        # any duplicates from it.
        triggers = [item.trigger for item in
             self.menu_items + global_menu.menu_items]
        assert len(triggers) == len(set(triggers))
        
        return
        
        
class MenuItem(object):
    """
    Single item in a menu.
    """
    
    def __init__(self,
                 trigger,
                 text,
                 next_menu,
                 action,
                 hidden=False,
                 set_pending=False):
        """
        Constructor.  Store input parameters.
        """
        # Key that causes this action to be run.
        self.trigger = trigger
        
        # Text to display in the menu for this item.
        self.text = text
        
        # Next menu to move to when this item is selected.  Can be "SAME" to
        # stay in this menu.
        self.next_menu = next_menu
        
        # Action to send to the client loop on selecting this item.  Can be 
        # None to indicate that no action should be sent, or a function to run
        # that function.
        self.action = action

        # Whether this is a hidden menu item.
        self.hidden = hidden
        
        # Whether this item sets the "result pending" state in the CLI, to
        # warn the user that we're waiting for the server to say something.
        self.set_pending = set_pending
        
        return

    def get_text(self):
        """
        Get text to display, translating any dynamic functions into text as
        required.
        """
        if isinstance(self.text, str):
            return self.text
        else:
            return self.text()

class Event(object):
    """
    Event that may be sent to the CLI for display.
    """
    
    # Event types.
    TEXT = 0          # Simple text string.
    MSG_RECVD = 1     # Message received on a conga.
    CONGA_JOINED = 2  # Client has joined a conga.
    CONGA_LEFT = 3    # Client has left a conga.
    LOST_CONN = 4     # Client lost connection to the server.
    ERROR = 5         # Non-fatal server error.
     
    # List of all allowed events.
    allowed_events = [TEXT, MSG_RECVD, CONGA_JOINED,
                      CONGA_LEFT, LOST_CONN, ERROR]
    
    def __init__(self, event_type, text, conga_name=None):
        """
        Constructor.  Store input parameters.
        """
        self.type = event_type
        self.text = text
        self.conga_name = conga_name
        self.printed = False
        
        return
        
        
    def __getstate__(self):
        """
        Convert this instance into a state suitable for putting on a
        multiprocessing queue (such as the ones we use to move Events
        between the CLI and the rest of the client).
        """
        dict = {"type": self.type,
                "text": self.text,
                "conga_name": self.conga_name,
                "printed": self.printed}
        
        return dict
        
    
    def __setstate__(self, state):
        """
        Restore an instance after removing it from a queue (see Python's
        pickle module documentation to see how this works).
        """
        self.type = state["type"]
        self.text = state["text"]
        self.conga_name = state["conga_name"]
        self.printed = state["printed"]
        
        return


class Action(object):
    """
    Action generated by the CLI.
    """
    
    # Action types.
    QUIT = 0          # Exit the client.
    CONNECT = 1       # Connect to a server.
    DISCONNECT = 2    # Disconnect from a server.
    CREATE_CONGA = 3  # Create a conga.
    JOIN_CONGA = 4    # Join a conga.
    LEAVE_CONGA = 5   # Leave a conga.
    SEND_MSG = 6      # Send a message on the conga.
    
    # List of all allowed actions.
    allowed_actions = [QUIT,
                       CONNECT,
                       DISCONNECT,
                       CREATE_CONGA,
                       JOIN_CONGA,
                       LEAVE_CONGA,
                       SEND_MSG]
    
    def __init__(self, action_type, params):
        """
        Constructor.  Store action type and dictionary of params.
        """
        
        self.type = action_type
        self.params = params
        
        return
     
     
    def __getstate__(self):
        """
        Convert this instance into a state suitable for putting on a
        multiprocessing queue (such as the ones we use to move Actions
        between the CLI and the rest of the client).
        """
        dict = {"type": self.type,
                "params": self.params}
        
        return dict


    def __setstate__(self, state):
        """
        Restore an Action after removing it from a queue (see Python's
        pickle module documentation to see how this works).
        """
        self.type = state["type"]
        self.params = state["params"]
        
        return
            

class Cli(object):
    """
    Class representing the CLI as a whole.
    """
    
    # Class constants.
    _INPUT_WIN_HEIGHT = 9
            
    class LostConnection(Exception):
        """
        Exception to raise when we lose connection with the Tornado server.
        """
        
        def __init__(self):
            """
            Constructor.
            """
            self.value = "Lost connection with the Tornado server."
            return
            
            
        def __str__(self):
            """
            String representation of this error.
            """
            return repr(self.value)
    
    
    class ExitCli(Exception):
        """
        Exception to raise when we want to quit the CLI cleanly.
        """
        pass
    
    # Private functions.
    
    def __init__(self):
        """
        Constructor.
        """
        # Menu for the CLI.
        self.global_menu = Menu("Always active")
        self.start_menu = Menu("Start Menu")
        self.main_menu = Menu("Main Menu")
        self.main_menu.parent = self.start_menu
        self.in_conga = Menu("In-Conga actions")
        self.in_conga.parent = self.main_menu
        matrix = MenuItem(trigger="M",
                          text="Enter the Matrix",
                          next_menu="SAME",
                          action=self._matrix,
                          hidden=True)
        exit_menu = MenuItem(trigger="X",
                             text=self._exit_text,
                             next_menu="PARENT",
                             action=None)
        about = MenuItem(trigger="A",
                         text="About Pi Conga",
                         next_menu="SAME",
                         action=self._credits)
        connect = MenuItem(trigger="C",
                           text="Connect",
                           next_menu=self.main_menu,
                           action=Action.CONNECT)
        disconnect = MenuItem(trigger="D",
                              text="Disconnect",
                              next_menu=self.start_menu,
                              action=Action.DISCONNECT)
        join_conga = MenuItem(trigger="J",
                              text="Join a Conga",
                              next_menu="SAME",
                              action=self._join_conga,
                              set_pending=True)
        create_conga = MenuItem(trigger="C",
                                text="Create a Conga",
                                next_menu="SAME",
                                action=self._create_conga,
                                set_pending=True)
        leave_conga = MenuItem(trigger="L",
                               text="Leave the Conga",
                               next_menu=self.main_menu,
                               action=self._leave_conga,
                               set_pending=True)
        send_ping = MenuItem(trigger="P",
                             text="Send a ping over the Conga",
                             next_menu="SAME",
                             action=self._send_ping)
        send_msgs = MenuItem(trigger="F",
                             text="Send free-form text messages over the Conga",
                             next_menu="SAME",
                             action=self._spawn_free_text_thread)
        self.global_menu.menu_items = [matrix]
        self.start_menu.menu_items = [about, connect, exit_menu]
        self.main_menu.menu_items = [join_conga, create_conga, disconnect]
        self.in_conga.menu_items = [send_ping, send_msgs, leave_conga]

        # Internal state for the CLI.
        (self._rows, self._cols) = (0, 0)
        self._event_win = None
        self._input_win = None
        self._main_win = None
        self._event_queue = multiprocessing.Queue()
        self._action_queue = multiprocessing.Queue()
        self._current_menu = self.start_menu
        self._result_pending = False
        self._hide_input_win = False
        self._conga_name = None
        
        return
        
        
    def _resize_windows(self):
        """
        Get the current terminal dimensions, and if they are different 
        from the currently stored dimensions, resize the windows to fill the
        screen.

        Note that resizing sub-windows is fraught with difficulties, so we
        actually create a whole new set of windows.
        """
        (rows, cols) = self._main_win.getmaxyx()
        if ((rows == self._rows) and (cols == self._cols)):
            return
        else:
            # Note the new limits.
            self._rows = rows
            self._cols = cols

            # Delete any currently created windows so we can create a new set.
            if self._event_win is not None:
                del self._event_win
            if self._input_win is not None:
                del self._input_win
            
            # The event window fills the screen width and goes from the top of
            # the screen to the top of the input window.
            event_win_height = self._rows - self._INPUT_WIN_HEIGHT
            self._event_win = self._main_win.subwin(
                event_win_height, self._cols, 0, 0)
            self._event_win.scrollok(True)
            
            # The input window also fills the screen width, and goes from the
            # bottom of the input wondow to the bottom of the screen.
            self._input_win = self._main_win.subwin(
                self._INPUT_WIN_HEIGHT, self._cols, event_win_height, 0)
            self._input_win.scrollok(True)
            
            # The input window needs to not block when getting input.
            self._input_win.nodelay(1)
        
        return
    
    
    def _print_to_win(self, text, win, attrs=None):
        """
        Print text to the bottom of a given window, scrolling it as
        necessary.
        """
        # If there were no attributes specified, use the default colours.
        if attrs is None:
            attrs = curses.color_pair(0)
        
        # Work out where the bottom of the event window is so that we can
        # print it there.
        (height, width) = self._event_win.getmaxyx()
        bottom_line = height - 1
        
        event_lines = (len(text) / width) + 1
        printed = 0
        while printed < len(text):
            still_to_print = len(text[printed:])
            to_print_now = min(still_to_print, width)
            win.scroll(1)
            win.addstr(bottom_line,
                       1,
                       text[printed:printed+to_print_now],
                       attrs)
            printed += to_print_now 
        return
        
        
    def _process_event(self, event):
        """
        Take appropriate action for a received event.
        """
        
        logger.debug("Received Event of type %d" % event.type)
        
        # Our behaviour depends on what kind of event we have received.
        if event.type == Event.TEXT:
            # Simple text event.  Just print it to the event window.
            self._print_to_win(event.text, self._event_win)
        elif event.type == Event.MSG_RECVD:
            # Received a message on the conga.  Print a notification.
            self._print_to_win("Received a message:",
                               self._event_win,
                               curses.color_pair(1))
            
            # Now print the message itself.
            self._print_to_win(event.text, self._event_win)
        elif event.type == Event.CONGA_JOINED:
            # Joined a conga.  Print a notification.
            self._print_to_win("Joined a conga:",
                               self._event_win,
                               curses.color_pair(2))
            
            # Save off the conga's name.
            self._conga_name = event.conga_name
            
            # Now print information about the conga.
            self._print_to_win(event.text, self._event_win)
            
            # If we're not already in the in-conga menu, move there.
            self._current_menu = self.in_conga
            self._result_pending = False
        elif event.type == Event.CONGA_LEFT:
            # Left a conga.  Print a notification.
            self._print_to_win("Left the conga.",
                               self._event_win,
                               curses.color_pair(3))
            
            # Wipe the current conga name.
            self._conga_name = None
                               
            # Drop back to the main menu.
            self._current_menu = self.main_menu
            self._result_pending = False
        elif event.type == Event.LOST_CONN:
            # Lost connection with the server.  Drop out.
            raise Cli.LostConnection
        elif event.type == Event.ERROR:
            # Non-fatal error on the server side.  Print the error details
            # and ensure that we're not expecting anything more from the
            # client code.
            self._print_to_win(event.text, self._event_win)
            self._result_pending = False
        else:
            # Unhandled event.  This shouldn't happen.  Raise an exception.
            raise TypeError("Unhandled CLI event type.")
            
        return
    
    
    def _process_input(self, input):
        """
        Process a keypress from the user.
        """
        # Check that input is a single character and convert it to upper-case.
        if input > 255:
            return
        char = chr(input).upper()
        
        # Create list of possible menu items.
        current_menu = (self._current_menu.menu_items +
                       self.global_menu.menu_items)

        # If the input is not available from the current menu, ignore it.
        if char not in ([item.trigger for item in current_menu]):
            logger.debug("Character %s is not a valid menu choice." % char)
            return
        
        # The user must have pressed a key associated with one of the
        # menu items.  Trigger the associated action.
        selected_item = None
        for item in current_menu:
            if char == item.trigger:
                selected_item = item
        
        if selected_item is None:
            # Invalid input.  This should be impossible.  Assert.
            raise AssertionError, "Input invalid for this menu."
            
        self._print_to_win("Processing command: " + selected_item.get_text(),
                           self._event_win,
                           curses.color_pair(2))

        if selected_item.action is not None:
            if selected_item.action in Action.allowed_actions:
                # Put the action on the queue.  No actions currently have
                # associated parameters.
                logger.debug("Send Action of type %d." % selected_item.action)
                act = Action(selected_item.action, None)
                self._action_queue.put(act)
            else:
                # Assume that it is a function.
                selected_item.action()
            
        # Move to the menu specified by the item.
        if isinstance(selected_item.next_menu, str):
            if selected_item.next_menu == "PARENT":
                self._current_menu = self._current_menu.parent
            elif selected_item.next_menu == "SAME":
                pass
            else:
                raise AssertionError(
                    "Unsupported menu: {}".format(selected_item.next_menu))
        else:
            self._current_menu = selected_item.next_menu
        
        # Update the CLI's "pending" state from this item.
        self._result_pending = selected_item.set_pending
        
        # Check for exit from program - i.e. exit from the top-menu, which
        # has no parent.
        if self._current_menu is None:
            raise Cli.ExitCli

        return
    
    
    def _exit_text(self):
        """
        Display dynamic message for X option on menu.
        """
        if self._current_menu == self.start_menu:
            return "Exit Pi Conga"
        else:
            return "Return to previous menu"


    def _credits(self):
        """
        Invoke the credits.
        """
        credits(self._main_win)


    def _matrix(self):
        """
        Invoke the credits.
        """
        matrix(self._main_win)


    def _display_menu(self):
        """
        Print out the current menu in the input window.
        """               
        
        # Check that this menu is going to work.
        menu = self._current_menu
        menu.verify(self.global_menu)
        
        # Clear the window - we don't want bits of the previous menu hanging
        # around.
        self._input_win.erase()
        
        # Redraw the border between the windows.
        self._input_win.hline(0, 0, "=", self._cols)
        
        # Print the name of the current menu.
        self._input_win.addstr(1, 1, menu.name)
        
        # If the CLI is waiting for a response from the server, flag this
        # up next to the menu name.
        if self._result_pending:
            self._input_win.addstr(1,
                                   len(menu.name) + 2,
                                   "(WORKING...)",
                                   curses.A_STANDOUT)
        
        # Print each of the menu items in turn.
        menu_items = menu.menu_items + self.global_menu.menu_items
        line = 3  # Name is on line 1, line 2 is blank
        for item in menu_items:
            # Don't display hidden items
            if not item.hidden:
                self._input_win.addstr(
                    line, 1, "%s  %s" % (item.trigger, item.get_text()))
                line += 1
            
        # Print the input summary at the bottom of the input window.
        (height, width) = self._input_win.getmaxyx()
        avail_triggers = [item.trigger for item in menu_items if not item.hidden]
        triggers_txt_list = ", ".join(avail_triggers)
        self._input_win.addstr(height-1,
                               1,
                               "Press one of: %s." % triggers_txt_list)
        
        return
        
    def _send_ping(self):
        """Send a ping along the Conga."""
        
        self._action_queue.put(Action(Action.SEND_MSG, {"text": "Ping!"}))
        
        return
    
    def _spawn_free_text_thread(self):
        """Spawn off a new thread to do freeform text entry."""
        
        # Create the thread.
        thread = threading.Thread(target=self._get_send_free_text)
        
        # Stop the input menu from being updated.
        self._hide_input_win = True
        
        # Kick off the thread - we continue here to let the event window run.
        thread.start()
        
        return
        
    def _get_send_free_text(self):
        """
        Switch into freeform text entry mode and send messages.
        """
        
        # Create the new freeform window - this exactly covers the input window,
        # except for the top border.
        (height, width) = self._input_win.getmaxyx()
        free_win = self._input_win.derwin((height - 1), width, 1, 0)

        
        # Switch on character echo.
        curses.echo()
        
        # Loop around fetching input from the window and sending it off to the
        # client until the user leaves this mode.
        keep_looping = True
        while keep_looping:
            # Clear the window to remove any left-over text from last time.
            free_win.clear()
            
            # Redraw the window border.
            free_win.border()
            
            # Give the user instructions.
            free_win.addstr(2, 2, "Enter text to send along the Conga.")
            free_win.addstr(3, 2, "Type '/quit' to return to the menus.")
            
            # Fetch the next string from the user.
            free_win.addstr(5, 2, "> ")
            input = free_win.getstr(5, 4)
            
            # Process the input.
            if input == "/quit":
                # Leave the loop.
                keep_looping = False
            else:
                # Send this string along the Conga.
                self._action_queue.put(Action(Action.SEND_MSG,
                                              {"text": input}))
        
        # Finished sending messages. Return to no input echo, destroy the
        # window and return.
        curses.noecho()
        self._hide_input_win = False
        del free_win
        
        return
    
    def _get_conga_name(self):
        """
        Fetch the name of the conga to join/create.
        """
        
        # Create a new window over the input window to get the name.  This
        # should be visually distinct from the normal input window.
        (height, width) = self._input_win.getmaxyx()
        name_win = self._input_win.derwin(height - 1, width, 1, 0)
        name_win.erase()
        name_win.border()
        
        # Switch on character echo.
        curses.echo()
        
        # Ask the user for the name of the Conga.  Note that, unlike free text
        # entry for sending messages along the Conga, we can freeze all other
        # processing at this point because we are not in a Conga yet.
        name_win.addstr(2, 2, "Please enter the name of the Conga.")
        name_win.addstr(4, 2, ">")
        
        name = name_win.getstr(4, 4)
        
        # Destroy the window and return.
        del name_win
        
        return name
        
    def _create_conga(self):
        """Create a Conga."""
        
        # Fetch the name for the Conga we want to create from the user.
        name = self._get_conga_name()
        
        # Send this name to the client to create a new Conga.
        action = Action(Action.CREATE_CONGA, {"name": name})
        self._action_queue.put(action)
        
        return
        
    def _join_conga(self):
        """Join a Conga."""
    
        # Fetch the name for the Conga we want to join from the user.
        name = self._get_conga_name()
        
        # Send this name to the client to join a new Conga.
        action = Action(Action.JOIN_CONGA, {"name": name})
        self._action_queue.put(action)
        
        return
        
    def _leave_conga(self):
        """Leave the Conga."""
        
        # We must be in a Conga at this point.
        assert (self._conga_name is not None), "Not in a Conga"
        
        # Create an action to send to the client asking to leave the conga.
        action = Action(Action.LEAVE_CONGA, {"name": self._conga_name})
        self._action_queue.put(action)
        
        return
        
    def _cli_loop(self):
        """
        Main CLI loop.  Display any new events and look for any user input.
        
        Returns:    Nothing.
        """
        while True:
            # First, resize the windows if the user has resized the terminal
            # since the last time round the loop.
            self._resize_windows()

            # Get an event off the queue and process it, if there is one.
            try:
                next_event = self._event_queue.get(block=False)
                self._process_event(next_event)
            except Queue.Empty:
                next_event = None
            except Cli.LostConnection:
                self._action_queue.put(
                            Action(Action.QUIT,
                                   {"text": 
                                   "Lost connection to the Tornado server."}))
                return
                        
            if not self._hide_input_win:
                # Display the menu.
                self._display_menu()

                # Get user input and process it, if there is any.
                input = self._input_win.getch()
            
                if input != -1:
                    logger.debug("Got user input %c", input)
                    try:
                        self._process_input(input)            
                    except Cli.ExitCli:
                        self._action_queue.put(
                                              Action(Action.QUIT,
                                                     {"text": "Exited the CLI."}))
                        return 

                # Redraw the input window.
                self._input_win.refresh()

            # Redraw the event window.
            self._event_win.refresh()
            
            # Sleep!
            sleep(0.1)
            
        return None
        
        
    def _start_cli(self, main_window):
        """
        Create the various CLI windows and kick off the main loop.
        """
        # Remember the main window for later.
        self._main_win = main_window

        # Now create the main windows for the UI.
        self._resize_windows()
        
        # Set up some colour pairs to use for printing events.
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        
        # Make the cursor invisible to avoid it flickering.
        curses.curs_set(0)
        
        # Start off the main loop.
        rc = self._cli_loop()
        
        return
        
        
    # Public functions.
    
    def run(self, actions, events):
        """
        Start the CLI.
        """
        # Remember the specified queues for interprocess comms.
        self._action_queue = actions
        self._event_queue = events

        # Start the CLI.
        curses.wrapper(self._start_cli)
        
        return
        
        
    def add_event(self, event_type, text):
        """
        Add an event to the queue to be displayed on the CLI.
        
        Parameters: event_type  - Type of event to be displayed.  One of the
                                  event type class constants.
                    text        - Text associated with this event.  Normal
                                  string.
        Returns:    Nothing.
        """
        
        # Check that the event is permitted.
        assert event_type in Event.allowed_events
        
        # Add the event to the queue.
        event = Event(event_type, text)
        self._event_queue.put(event)
        
        return
        
        
    def get_action(self):
        """
        Check for any actions sent by the CLI.
        
        Returns an Action, or None if the queue is empty.
        """
        
        try:
            action = self._action_queue.get(block=False)
        except Queue.Empty:
            action = None
            
        return action
 
 
if __name__ == "__main__":
    # Test routine.  Create a CLI and throw some events at it.
    test_cli = Cli()
    
    # Start the CLI up in a separate process.
    cli_proc = multiprocessing.Process(target=test_cli.run)
    cli_proc.start()
    
    # Now throw some events at the CLI, and immediately report back any 
    # messages we get from it.
    from time import sleep
    import sys
    while True:
        recvd_action = test_cli.get_action()
        while recvd_action is not None:
            if recvd_action.type == Action.JOIN_CONGA:
                act_type = "Join Conga"
            elif recvd_action.type == Action.LEAVE_CONGA:
                act_type = "Leave Conga"
            elif recvd_action.type == Action.CONNECT:
                act_type = "Connect to Tornado server"
            elif recvd_action.type == Action.DISCONNECT:
                act_type = "Disconnect from Tornado server"
            elif recvd_action.type == Action.QUIT:
                try:
                    cli_proc.join()
                except Cli.ExitCli:
                    pass
                finally:
                    sys.exit()
            test_cli.add_event(Event.TEXT,
                               "Saw an action of type: %s" % act_type)
            recvd_action = test_cli.get_action()
        
        test_cli.add_event(Event.MSG_RECVD,
                           "This is a test message.")                           
        sleep(1)
    
        test_cli.add_event(Event.CONGA_JOINED,
                           "This is a test 'Conga Joined' message.")
        sleep(1)
        
        test_cli.add_event(Event.CONGA_LEFT,
                           "This is a test 'Conga Left' message.")
        sleep(1)
    
    

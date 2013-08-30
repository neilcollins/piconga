import curses
from abc import ABCMeta, abstractmethod
from random import randint

class Effect(object):
    """
    Abstract class to handle a special effect on the screen.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self, frame_no):
        """
        This effect will be called every time the mainline animator
        creates a new frame to display on the screen.
        """

class Scroll(Effect):
    """
    Special effect to scroll the screen up at a required rate.
    """

    def __init__(self, screen, rate):
        """
        Constructor.  The rate defines how many frames to wait between
        scrolling.
        """
        self._screen = screen
        self._rate = rate
        self._last_frame = 0

    def update(self, frame_no):
        """
        Scroll the screen if required.
        """
        if (frame_no - self._last_frame) >= self._rate:
            self._screen.scroll()
            self._last_frame = frame_no
        
class Star(object):
    """
    Simple class to represent a single star for the Stars special effect.
    """

    _star_chars = "..+..   ...x...  ...*...         "

    def __init__(self, screen):
        """
        Constructor.  Pick a random location for the star making sure it does
        not overwrite an existing piece of text.
        """
        self._screen = screen
        self._cycle = randint(0, len(self._star_chars))
        (height, width) = self._screen._pad.getmaxyx()
        while True: 
            self._x = randint(0, width-1)
            self._y = randint(0, height-1)
            if self._screen._pad.inch(self._y, self._x) == 32:
                break

    def update(self):
        """
        Draw the star.
        """
        self._cycle += 1
	if self._cycle >= len(self._star_chars):
            self._cycle = 0
    
        self._screen.putch(self._star_chars[self._cycle], self._x, self._y)

class Stars(Effect):
    """
    Add random stars to the screen.
    """

    def __init__(self, screen, max):
        """
        Constructor.  Create the required number of stars.
        """
        self._stars = [Star(screen) for x in range(max)]

    def update(self, frame_no):
        """
        Make those stars twinkle!
        """
        for star in self._stars:
            star.update()

class Screen(object):
    """
    Class to track basic state of the screen.
    """

    def __init__(self, win):
        """
        Constructor.  Set up basic curses windows/pads.
        """
        # Save off the screen details and se up the scrolling pad.
        self._screen = win
        (self.height, self.width) = self._screen.getmaxyx()
        self._pad = curses.newpad(1000, self.width)
        self._start_line = 0

        # Set up basic colour schemes.
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

    def scroll(self):
        """
        Scroll up one line.
        """
        self._start_line += 1

    def refresh(self):
        """
        Refresh the screen.
        """
        (self.height, self.width) = self._screen.getmaxyx()
        self._pad.refresh(self._start_line, 
                          0,
                          0,
                          0,
                          self.height - 1,
                          self.width - 1)

    def putch(self, str, x, y, attr=0):
        """
        Print the text (str) at the specified location (y, x).
        """
        self._pad.addstr(y, x, str, attr)

    def centre(self, str, y, attr=0):
        """
        Centre the text (str) on the specified line (y) using the optional
        attributes (attr).
        """
        self._pad.addstr(y, (self.width - len(str))/2, str, attr)

titles = """
 ____  _    ____                        
|  _ \(_)  / ___|___  _ __   __ _  __ _ 
| |_) | | | |   / _ \| '_ \ / _` |/ _` |
|  __/| | | |__| (_) | | | | (_| | (_| |
|_|   |_|  \____\___/|_| |_|\__, |\__,_|
                            |___/       









An open source project by:


Cory Benfield


Phil Brien


Peter Brittain


Neil Collins


Lance Robson











How many hidden features can you find?
"""

def credits(win):
    # Create the basic credits to scroll.
    screen = Screen(win)
    y = screen.height
    for line in titles.split("\n"):
        screen.centre(line, y, curses.color_pair(1))
        y += 1

    # Add in our special effects
    effects = []
    effects.append(Scroll(screen, 5))
    effects.append(Stars(screen, 1000))

    # Run those credits!
    for frame in range(500):
        for effect in effects:
            effect.update(frame)
        screen.refresh()
        curses.napms(50)

# Temporary mainline
curses.wrapper(credits)

import curses
from abc import ABCMeta, abstractmethod
from random import randint
import re


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
        scrolling the screen.
        """
        self._screen = screen
        self._rate = rate
        self._last_frame = 0

    def update(self, frame_no):
        """
        Scroll the screen if required.
        """
        # Note that the mainline is just N frames after the latest update.
        # However, we also need to handle the case where the screen is reset
        # between calls (and so look for frame numbers that are too small).
        if ((frame_no - self._last_frame) >= self._rate or
            frame_no < self._last_frame):
            self._screen.scroll()
            self._last_frame = frame_no


class Cycle(Effect):
    """
    Special effect to cycle the colours on a some specified text.
    """

    def __init__(self, screen, text, y):
        """
        Constructor.  Remember the text to cycle and the starting line (y).
        The text may be multi-lined.
        """
        self._screen = screen
        self._text = text
        self._y = y
        self._colour = 0

    def update(self, frame_no):
        """
        Cycle the text colors.
        """
        if frame_no % 2 == 0:
            return

        y = self._y
        for line in self._text.split("\n"):
            if self._screen.is_visible(0, y):
                self._screen.centre(line, y, self._colour)
            y += 1
        self._colour = (self._colour + 1) % 8


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
        self._old_char = None

    def update(self):
        """
        Draw the star.
        """
        if not self._screen.is_visible(self._x, self._y):
            return

        self._cycle += 1
        if self._cycle >= len(self._star_chars):
            self._cycle = 0

        new_char = self._star_chars[self._cycle]
        if new_char == self._old_char:
            return

        self._screen.putch(new_char, self._x, self._y)
        self._old_char = new_char


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


class Trail(object):
    """
    Track a single trail  for a falling character effect (a la Matrix).
    """

    def __init__(self, screen, x):
        """
        Constructor.  Create tral for  column (x) on the screen.
        """
        self._screen = screen
        self._x = x
        self._y = 0
        self._life = 0
        self._rate = 0
        self._clear = True
        self._maybe_reseed()

    def _maybe_reseed(self):
        """
        Randomnly create a new column once this one is finished.
        """
        self._y += self._rate
        self._life -= 1
        if self._life <= 0:
            self._clear = not self._clear
            self._rate = randint(1, 2)
            if self._clear:
                self._y = 0
                self._life = self._screen.height / self._rate
            else:
                self._y = randint(0, self._screen.height / 2)
                self._life = \
                    randint(1, self._screen.height - self._y) / self._rate

    def update(self):
        """
        Update that trail!
        """
        if self._clear:
            for i in range(0, 3):
                self._screen.putch(" ",
                                   self._x,
                                   self._screen._start_line + self._y + i)
            self._maybe_reseed()
        else:
            for i in range(0, 3):
                self._screen.putch(chr(randint(32, 126)),
                                   self._x,
                                   self._screen._start_line + self._y + i,
                                   curses.COLOR_GREEN)
            for i in range(4, 6):
                self._screen.putch(chr(randint(32, 126)),
                                   self._x,
                                   self._screen._start_line + self._y + i,
                                   curses.COLOR_GREEN,
                                   curses.A_BOLD)
            self._maybe_reseed()


class Matrix(object):
    """
    Matrix-like falling green letters.

    WARNING: this will slow down dramatically on large screens.
    """

    def __init__(self, screen):
        """
        Constructor.  Create the starting point for the falling characters.
        """
        self._screen = screen
        self._chars = [Trail(screen, x) for x in range(screen.width)]

    def update(self, frame_no):
        """
        Make those characters fall.
        """
        if (frame_no % 2 == 0):
            for char in self._chars:
                char.update()


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
        self.buffer_height = 200
        self._pad = curses.newpad(self.buffer_height, self.width)

        # Set up basic colour schemes.
        for i in range(curses.COLOR_RED, curses.COLOR_WHITE):
            curses.init_pair(i, i, curses.COLOR_BLACK)

        # Disable the cursor.
        curses.curs_set(0)

        # Non-blocking key checks.
        self._pad.nodelay(1)

        # Ensure that the screen is clear and ready to go.
        self.clear()

    def scroll(self):
        """
        Scroll up one line.
        """
        self._start_line += 1

    def clear(self):
        """
        Clear the screen of all content.
        """
        self._pad.clear()
        self._start_line = 0

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

    def getch(self):
        """
        Check for a key without waiting.
        """
        return self._pad.getch()

    def putch(self, str, x, y, colour=0, attr=0):
        """
        Print the text (str) at the specified location (y, x) using the
        specified colour and attributes.  See curses.A_... for attributes.
        """
        self._pad.addstr(y, x, str, curses.color_pair(colour) | attr)

    def centre(self, str, y, colour=0, attr=0):
        """
        Centre the text (str) on the specified line (y) using the optional
        colour (colour) and attributes (attr).  See curses.A_... for a list of
        valid attributes.

        This function will convert ${n} into colour attribute n for any
        subseqent text in the line, thus allowing multi-coloured text.
        """
        segments = [["", colour]]
        line = str
        while True:
            match = re.match(r"(.*?)\$[{](\d+)[}]", line)
            if match is None:
                break
            segments[-1][0] = match.group(1)
            segments.append(["", int(match.group(2))])
            line = line[len(match.group(0)):]
        segments[-1][0] = line
        total_width = sum([len(x[0]) for x in segments])

        x = (self.width - total_width)/2
        for (text, style) in segments:
            self._pad.addstr(y, x, text, curses.color_pair(style) | attr)
            x += len(text)

    def is_visible(self, x, y):
        """
        Return whether the specified location is on the visible screen.
        """
        return ((y >= self._start_line) and
                (y < self._start_line + self.height))

    def create_credits(self):
        # Create the basic credits to scroll.
        self.clear()
        y = self.height
        for line in piconga.split("\n"):
            self.centre(line, y, curses.COLOR_CYAN)
            y += 1
        y += 5
        self.centre("An open source project for the:", y, curses.COLOR_CYAN)
        y += 5
        for line in raspberry.split("\n"):
            self.centre(line, y)
            y += 1
        y += 5
        for line in titles.split("\n"):
            self.centre(line, y, curses.COLOR_CYAN)
            y += 1
        return y


raspberry = """
${2}   .~~.   .~~.                                                         
${2}  '. \ ' ' / .'                                                        
${1}   .~ .~~~..~.                                                         
${1}  : .~.'~'.~. :   ${0}                     _                             _ 
${1} ~ (   ) (   ) ~  ${0}    _ _ __ _ ____ __| |__  ___ _ _ _ _ _  _   _ __(_)
${1}( : '~'.~.'~' : ) ${0}   | '_/ _` (_-< '_ \ '_ \/ -_) '_| '_| || | | '_ \ |
${1} ~ .~ (   ) ~. ~  ${0}   |_| \__,_/__/ .__/_.__/\___|_| |_|  \_, | | .__/_|
${1}  (  : '~' :  )   ${0}               |_|                     |__/  |_|     
${1}   '~ .~~~. ~'                                                         
${1}       '~'                                                             
"""

piconga = """
 ____  _    ____                        
|  _ \(_)  / ___|___  _ __   __ _  __ _ 
| |_) | | | |   / _ \| '_ \ / _` |/ _` |
|  __/| | | |__| (_) | | | | (_| | (_| |
|_|   |_|  \____\___/|_| |_|\__, |\__,_|
                            |___/       
"""

titles = """
Written by:


Cory Benfield


Phil Brien


Peter Brittain


Neil Collins


Lance Robson











How many hidden features can you find?
"""


def credits(win):
    """
    Pi Conga credits!
    """

    # Speed for the scrolling credits
    SCROLL_RATE = 5

    # Create our basic screen and then prepare the special effects.
    screen = Screen(win)
    screen.create_credits()

    normal = []
    normal.append(Scroll(screen, SCROLL_RATE))
    normal.append(Stars(screen, screen.buffer_height))
    normal.append(Cycle(screen, piconga, screen.height))

    matrix = []
    matrix.append(Matrix(screen))

    # Start off with our normal set of effects active.
    effects = normal

    # Run those credits!
    while True:
        # Create the basic credits to scroll.
        FRAMES = screen.create_credits() * SCROLL_RATE

        # Run through the whole lot for one loop.
        for frame in range(FRAMES):
            for effect in effects:
                effect.update(frame)
            screen.refresh()
            c = screen.getch()
            if c in (ord("M"), ord("m")):
                effects = matrix
            elif c in (ord("N"), ord("n")):
                effects = normal
            elif c in (ord("X"), ord("x")):
                return
            curses.napms(50)


def matrix(win):
    """
    Hidden extra - watch the matrix!
    """
    # Speed for the scrolling credits
    SCROLL_RATE = 5

    # Create our basic screen and then prepare the special effects.
    screen = Screen(win)

    effects = []
    effects.append(Matrix(screen))

    # Run the scene.
    frame = 0
    while True:
        frame += 1
        for effect in effects:
            effect.update(frame)
        screen.refresh()
        c = screen.getch()
        if c in (ord("X"), ord("x")):
            return
        curses.napms(50)

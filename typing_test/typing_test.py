"""
Copyright (c) 2019 Emil Lynegaard
Distributed under the MIT software license, see the
accompanying LICENSE.md or https://opensource.org/licenses/MIT

Minimal 10fastfingers like typing game for Python2/3 with ncurses.
Supports vocab files as arguments, as well as adjustable
word length, game time and word frequency (if using sorted vocab).
"""
import argparse
import time
import random
import curses
import textwrap
import os

# Robust path to default vocabulary, which is based on word frequency
# from CNN and DailyMail articles.
VOCAB_PATH = os.path.join(os.path.dirname(__file__), "data", "vocab")

# Used for WPM calculation
CHARS_PER_WORD = 5

# Amount of words to store, for showing several future words
# Should generally be equal to at least two lines worth of words
QUEUE_SIZE = 30

MAX_WIDTH = 80

# pylint: disable=too-few-public-methods, too-many-instance-attributes
class Game:
    """
    Class encapsulating the Game.
    Includes game stats, input management, game display.
    """

    def __init__(self, args):
        self.word_generator = self._word_generator(args)
        self.game_time = args.game_time
        self.next_words = [self._get_word() for _ in range(QUEUE_SIZE)]
        self.typed = []
        self.correct = []
        self.wrong = []
        self.input = ""

        self.display = args.display

        # if using 10ff display, we keep track of extra things
        if self.display == "10ff":
            self.offset = 0
            self.current_line = []
            self.next_line = []

    @staticmethod
    def _word_generator(args):
        words = []
        for line in open(args.vocab):
            word = line.strip()
            if args.min_length <= len(word) <= args.max_length:
                words.append(word)

            if len(words) >= args.words:
                break

        while True:
            yield random.choice(words)

    def calculate_cpm(self, time_played):
        """Calculate CPM given time_played in seconds"""
        if time_played == 0:
            return 0

        correct_chars = len(" ".join(self.correct))
        cpm = 60 / time_played * correct_chars
        cpm = int(round(cpm))
        return cpm

    def calculate_wpm(self, time_played):
        """Calculate WPM given time_played in seconds"""
        if time_played == 0:
            return 0

        correct_chars = len(" ".join(self.correct))
        wpm = 60 / time_played * correct_chars / CHARS_PER_WORD
        wpm = int(round(wpm))
        return wpm

    def _get_word(self):
        return next(self.word_generator)

    def _finish_word_event(self):
        target = self.next_words.pop(0)
        self.typed.append(self.input)
        if self.input == target:
            self.correct.append(target)
        else:
            self.wrong.append(target)

        if self.display == "10ff":
            self.offset += 1

        self.next_words.append(self._get_word())
        self.input = ""

    @staticmethod
    def _get_line(words, max_chars):
        line = []
        chars = 0
        for w in words:
            length = len(w)
            if chars + length + 1 > max_chars:
                break

            line.append(w)
            chars += length + 1

        return line

    def _progressive_display(self, stdscr, time_left):
        _height, width = stdscr.getmaxyx()
        width = min(width, MAX_WIDTH)

        stdscr.clear()
        wpm = self.calculate_wpm(self.game_time - time_left)
        stdscr.addstr("Time left: {:d}, WPM: {:d}\n".format(time_left, wpm))

        line = self._get_line(self.next_words, width)
        target = " ".join(line)

        for idx, char in enumerate(self.input):
            target_char = target[idx]
            if target_char == char:
                stdscr.addstr(char, curses.color_pair(1))
            else:
                stdscr.addstr(target_char, curses.color_pair(2))

        stdscr.addstr(target[len(self.input) : width - 1])
        stdscr.addstr("\n" + self.input, curses.A_UNDERLINE)
        stdscr.refresh()

    def _10ff_display(self, stdscr, time_left):
        _height, width = stdscr.getmaxyx()
        width = min(width, MAX_WIDTH)
        stdscr.clear()

        wpm = self.calculate_wpm(self.game_time - time_left)
        stdscr.addstr("Time left: {:d}, WPM: {:d}\n".format(time_left, wpm))

        # sets up initial lines
        if not self.current_line:
            self.current_line = self._get_line(self.next_words, width)
            cur_len = len(self.current_line)
            self.next_line = self._get_line(self.next_words[cur_len:], width)

        # if we finished the current line
        if self.offset >= len(self.current_line):
            self.current_line = self.next_line
            cur_len = len(self.current_line)
            self.next_line = self._get_line(self.next_words[cur_len:], width)
            self.offset = 0

        # color the words already typed on current line
        for i in range(self.offset):
            target = self.current_line[i]
            actual = self.typed[-(self.offset - i)]
            if actual == target:
                stdscr.addstr(target, curses.color_pair(1))
            else:
                stdscr.addstr(target, curses.color_pair(2))

            stdscr.addstr(" ")

        stdscr.addstr(" ".join(self.current_line[self.offset :]))
        stdscr.addstr("\n" + " ".join(self.next_line))
        stdscr.addstr("\n" + self.input, curses.A_UNDERLINE)
        stdscr.refresh()

    def _update_display(self, stdscr, time_left):
        if self.display == "progressive":
            self._progressive_display(stdscr, time_left)
        elif self.display == "10ff":
            self._10ff_display(stdscr, time_left)

    def _handle_key(self, key):
        char = curses.keyname(key).decode()
        if char == "^R":
            self.restart()
        if key in (curses.KEY_BACKSPACE, 127):
            self.input = self.input[:-1]
        elif chr(key) == " ":
            self._finish_word_event()
        else:
            self.input += chr(key)

    @staticmethod
    def _setup_ncurses(stdscr):
        # hide cursor
        curses.curs_set(0)

        # setup colors for printing text to screen
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, 0)
        curses.init_pair(2, curses.COLOR_RED, 0)

        # don't wait for user input when calling getch()/getkey()
        stdscr.nodelay(True)

        # allow 100ms sleep on getch()/getkey() avoiding busy-wait
        # early returns when key is pressed, meaning no input delay
        stdscr.timeout(100)

    def _game_loop(self, stdscr):
        self._setup_ncurses(stdscr)
        self._update_display(stdscr, self.game_time)

        started = False
        start = time.time()
        time_left = self.game_time
        while time_left > 0:
            if not started:
                start = time.time()

            key = stdscr.getch()
            new_time_left = int(round(self.game_time - (time.time() - start)))
            if key == -1:
                # only update display when necessary
                if time_left != new_time_left:
                    time_left = new_time_left
                    self._update_display(stdscr, time_left)

                continue

            time_left = new_time_left
            started = True
            self._handle_key(key)
            self._update_display(stdscr, time_left)

    def print_stats(self):
        """Print ACC/CPM/WPM to console"""
        correct = len(self.correct)
        total = correct + len(self.wrong)
        accuracy = correct / total * 100
        print("ACC: {:.2f}%".format(accuracy))
        cpm = self.calculate_cpm(self.game_time)
        print("CPM: {:d}".format(cpm))
        wpm = self.calculate_wpm(self.game_time)
        print("WPM: {:d}".format(wpm))

    def restart(self):
        """
        Reset the Game class, effective starting a new game
        with new words, but based on same configuration.
        """
        self.input = ""
        self.correct = []
        self.wrong = []
        self.typed = []
        self.next_words = [self._get_word() for _ in range(QUEUE_SIZE)]

        if self.display == "10ff":
            self.offset = 0
            self.current_line = []
            self.next_line = []

        self.play()

    def play(self):
        """Start typing game and print results to terminal"""
        curses.wrapper(self._game_loop)
        self.print_stats()


def main():
    """Parse arguments and start game based thereof"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent(
            """\
            Start a minimal 10fastfingers-like typing game on the command line.

            Keybinds:
                CTRL+R: restart
                CTRL+C: exit
            """
        ),
    )
    parser.add_argument(
        "-v",
        "--vocab",
        type=str,
        metavar="vocab-file-path",
        default=VOCAB_PATH,
        help="path to newline separated vocab file",
    )
    parser.add_argument(
        "-t",
        "--game_time",
        type=int,
        metavar="gametime-seconds",
        default=60,
        help="the duration in seconds of the typing game",
    )
    parser.add_argument(
        "-min",
        "--min_length",
        type=int,
        metavar="min-word-length",
        default=2,
        help="the minimum word length",
    )
    parser.add_argument(
        "-max",
        "--max_length",
        type=int,
        metavar="max-word-length",
        default=10,
        help="the maximum word length",
    )
    parser.add_argument(
        "-w",
        "--words",
        type=int,
        metavar="words-to-read",
        default=1000,
        help="the amount of words to read from vocab file",
    )
    parser.add_argument(
        "-d",
        "--display",
        type=str,
        metavar="display",
        default="10ff",
        help="how to show upcoming words to type '10ff' or 'progressive'",
    )
    args = parser.parse_args()
    game = Game(args)
    try:
        game.play()
    except KeyboardInterrupt:
        pass

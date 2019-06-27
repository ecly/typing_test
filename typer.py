"""
Minimal 10fastfingers like typing game using ncurses.
Supports vocab files as arguments, as well as adjustable
word length, game time and word frequency (if using sorted vocab).
"""
import argparse
import time
import random
import curses

# Used for WPM calculation
AVG_WORD_LENGTH = 5

# pylint: disable=too-few-public-methods
class Game:
    """
    Class encapsulating the Game.
    Includes game stats, input management, game display.
    """

    def __init__(self, args):
        self.word_generator = self._word_generator(args)
        self.game_time = args.game_time
        self.next_words = [self._get_word() for _ in range(10)]
        self.correct = []
        self.wrong = []
        self.input = ""

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

    def _get_word(self):
        return next(self.word_generator)

    def _finish_word_event(self):
        target = self.next_words.pop(0)
        if self.input == target:
            self.correct.append(target)
        else:
            self.wrong.append(target)

        self.next_words.append(self._get_word())
        self.input = ""

    def _update_display(self, stdscr, time_left):
        stdscr.clear()
        stdscr.addstr(f"Time left: {time_left}\n")
        target = " ".join(self.next_words)
        for idx, char in enumerate(self.input):
            target_char = target[idx]
            if target_char == char:
                stdscr.addstr(char, curses.color_pair(1))
            else:
                stdscr.addstr(target_char, curses.color_pair(2))

        stdscr.addstr(target[len(self.input) :])
        stdscr.refresh()

    def _game_loop(self, stdscr):
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)

        stdscr.nodelay(True)
        start = time.time()
        time_left = self.game_time
        while time_left > 0:
            key = stdscr.getch()
            new_time_left = int(self.game_time - (time.time() - start))

            if key == -1:
                if new_time_left != time_left:
                    self._update_display(stdscr, new_time_left)
                    time_left = new_time_left

                continue

            if key in (curses.KEY_BACKSPACE, 127):
                self.input = self.input[:-1]
            elif chr(key) == " ":
                self._finish_word_event()
            else:
                self.input += chr(key)

            self._update_display(stdscr, time_left)
            time_left = new_time_left

    def play(self):
        """Start typing game and print results to terminal"""
        curses.wrapper(self._game_loop)

        # print stats
        correct = len(self.correct)
        wrong = len(self.wrong)
        total = correct + wrong
        print(f"Word accuracy: {correct}/{total}")

        correct_chars = len("".join(self.correct))
        correct_words = correct_chars / AVG_WORD_LENGTH
        wpm = 60 / self.game_time * correct_words
        print(f"WPM: {wpm}")


def main():
    """Parse arguments and start game based thereof"""
    parser = argparse.ArgumentParser(
        description="Start a minimal 10fastfingers-like typing game on the command line"
    )
    parser.add_argument(
        "-v",
        "--vocab",
        type=str,
        metavar="vocab-file-path",
        default="vocab",
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
    args = parser.parse_args()
    game = Game(args)
    try:
        game.play()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

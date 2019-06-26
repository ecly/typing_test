import argparse
import time
import random
import curses

WORDS = {"hello", "human", "another", "memes", "dank", "cat", "dog"}

def sample_word():
    return random.sample(WORDS, 1)[0]

class Game:
    def __init__(self, game_time=10):
        self.game_time = game_time
        self.next_words = [sample_word() for _ in range(10)]
        self.correct = []
        self.wrong = []
        self.input = ""

    def _finish_word_event(self):
        target = self.next_words.pop(0)
        if self.input == target:
            self.correct.append(target)
        else:
            self.wrong.append(target)

        self.next_words.append(sample_word())
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

        stdscr.addstr(target[len(self.input):])
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
        curses.wrapper(self._game_loop)

        # print stats
        correct = len(self.correct)
        wrong = len(self.wrong)
        total = correct + wrong
        wpm = 60 / self.game_time * correct
        print(f"Words typed (correct/total): {correct}/{total}")
        print(f"WPM: {wpm}")

def main():
    try:
        game = Game()
        game.play()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()

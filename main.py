#!/usr/bin/env/python
"""
A terminal-based Tetris game implemented in Python. 


Key Features:
- Standard Tetris board dimensions (10x20).
- 7 unique Tetromino shapes with color-coded display.
- Real-time input handling using `msvcrt` (Windows only).
- Sound effects using `winsound` for piece lock and line clears.
- Frame-based game loop with configurable fall delay.
- Collision-safe movement and rotation.
- Line clearing with score tracking.


Dependencies:
- Windows platform (for `msvcrt` and `winsound` modules).
- ANSI-compatible terminal for color display.
"""

import sys
import time
import random
import os
import msvcrt
import winsound

__author__ = "Michael"
__version__ = "1.0.0"


BOARD_X = 10
BOARD_Y = 20
FILL_CHAR = "███"

I = [
    [" ", " ", " ", " "],
    ["███", "███", "███", "███"],
    [" ", " ", " ", " "],
    [" ", " ", " ", " "]
]
O = [
    ["███", "███"],
    ["███", "███"],
]
T = [
    [" ", "███", " "],
    ["███", "███", "███"],
    [" ", " ", " "]
]
S = [
    [" ", "███", "███"],
    ["███", "███", " "],
    [" ", " ", " "]
]
Z = [
    ["███", "███", " "],
    [" ", "███", "███"],
    [" ", " ", " "]
]
J = [
    ["███", " ", " "],
    ["███", "███", "███"],
    [" ", " ", " "]
]
L = [
    [" ", " ", "███"],
    ["███", "███", "███"],
    [" ", " ", " "]
]


class Color:
    """ ANSI color codes """
    RED = "\033[0;31m"
    GREEN = "\033[38;5;034m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[38;5;055m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"
    ORANGE = "\033[38;5;208m"


class TetriminoBag:
    """
    Class that acts as a bag to draw next piece
    """

    def __init__(self):
        self.bag = []

    def next_piece(self):
        if not self.bag:
            self.bag = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']
            random.shuffle(self.bag)
        return self.bag.pop()


class Tetromino:
    def __init__(self, shape: str, start_x_pos: int, start_rotation: int):
        self.shape = eval(shape)
        if shape not in ["I", "O", "T", "S", "Z", "J", "L"]:
            raise ValueError(f"{self.shape} Not a valid shape")
        self.shape_code = shape
        self.x = start_x_pos
        self.y = BOARD_Y-len(self.shape)+1  # top
        self.rotation = start_rotation
        self.rotate(self.rotation)
        self.prepare_shape()
        self.just_spawned = True

    def __str__(self) -> str:
        return "\n".join("".join(("["+i + "]" if FILL_CHAR not in i else i) for i in j) for j in self.shape)

    def __getitem__(self, pos: tuple) -> str | int:
        return self.shape[len(self.shape) - pos[1]][pos[0]-1]

    def __setitem__(self, pos: tuple, value: str | int) -> None:
        self.shape[len(self.shape) - pos[1]][pos[0]-1] = value

    def rotate(self, degrees: int) -> None:
        if degrees % 90 != 0:
            raise ValueError(
                f"Rotation must be a multiple of 90. Got rotation {degrees}")
        for _ in range(int(degrees/90)):
            self.shape = [list(row) for row in zip(*self.shape[::-1])]

    def move_down(self) -> None:
        self.y -= 1

    def move_left(self) -> None:
        self.x -= 1

    def move_right(self) -> None:
        self.x += 1

    def set_color(self, color: str) -> None:
        for row in range(len(self.shape)):
            for col in range(len(self.shape[row])):
                if self.shape[row][col] == FILL_CHAR:
                    self.shape[row][col] = color + \
                        self.shape[row][col] + Color.END

    def prepare_shape(self) -> None:
        color_mappings = {"I": Color.CYAN, "O": Color.YELLOW,
                          "L": Color.BLUE, "J": Color.ORANGE, "S": Color.GREEN, "Z": Color.RED, "T": Color.PURPLE}
        self.set_color(color_mappings[self.shape_code])
        # print(f"Setting color to {color_mappings[self.shape_code]}{Color.END}")

    def get_leftmost(self) -> list[tuple]:
        """
        Return (x, y) positions of all left-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly to the left).
        """
        leftmost = []

        for y in range(1, len(self.shape)+1):
            for x in range(1, len(self.shape)+1):
                if FILL_CHAR in self[x, y]:
                    # Check the tile to the left
                    if x == 1 or FILL_CHAR not in self[x - 1, y]:
                        leftmost.append((x, y))
        return leftmost

    def get_bottommost(self):
        """
        Return (x, y) positions of all bottom-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly below).
        """
        bottom = []
        width = len(self.shape[0])
        height = len(self.shape)

        for x in range(1, width + 1):
            for y in range(1, height + 1):
                if FILL_CHAR in self[x, y]:
                    # Check the tile below
                    if y == 1 or FILL_CHAR not in self[x, y - 1]:
                        bottom.append((x, y))
        return bottom

    def get_rightmost(self) -> list[tuple]:
        """
        Return (x, y) positions of all left-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly to the left).
        """
        rightmost = []

        for y in range(1, len(self.shape)+1):
            for x in range(1, len(self.shape)+1):
                if FILL_CHAR in self[x, y]:
                    # Check the tile to the left
                    try:
                        if x == len(self.shape) or FILL_CHAR not in self[x + 1, y]:
                            rightmost.append((x, y))
                    except IndexError:
                        print([x + 1, y])
                        exit()
        return rightmost

    def get_stop_y(self) -> tuple:
        """
        Gets the Y coordinate where the tetromino should stop at the bottom
        since some have empty space at the bottom, this should be added onto the y
        """
        lowest = self.get_bottommost()
        min_value = 1-min(lowest, key=lambda x: x[1])[1] + 1
        return min_value

    def get_stop_left(self) -> tuple:
        """
        Gets the furthest left the tetromino can be
        before it goes of the edge of the board
        """
        lowest = self.get_leftmost()

        min_value = 1-min(lowest, key=lambda x: x[0])[0]+1
        return min_value

    def get_stop_right(self) -> tuple:
        """
        Gets the furthest right the tetromino can be
        before it goes of the edge of the board
        """
        lowest = self.get_rightmost()

        min_value = BOARD_X - len(self.shape) + (len(self.shape) - max(lowest, key=lambda x: x[0])[0]) + 1  # nopep8
        return min_value

    def get_rotated(self) -> list[tuple]:
        rotated = []
        cells = [list(row) for row in zip(*self.shape[::-1])]
        for x in range(len(cells)):
            for y in range(len(cells)):
                if FILL_CHAR in cells[x][y]:
                    rotated.append((y+1, len(self.shape)-x))
        return rotated


class Tetris:
    def __init__(self):
        self.board: list[list[str]] = [
            [" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        self.shapes: list[Tetromino] = []
        self.bag = TetriminoBag()

    def __getitem__(self, pos: tuple) -> str | int:
        return self.board[BOARD_Y - pos[1]][pos[0]-1]

    def __setitem__(self, pos: tuple, value: str | int) -> None:
        self.board[BOARD_Y - pos[1]][pos[0]-1] = value

    def __str__(self):
        return "\n".join(str(BOARD_Y-y).ljust(4)+"".join(("["+i + "]" if FILL_CHAR not in i else i) for i in j) for y, j in enumerate(self.board))

    def update(self, shape: Tetromino):
        for x in range(1, len(shape.shape)+1):
            for y in range(1, len(shape.shape)+1):
                try:
                    if self[shape.x+x-1, shape.y+y-1] == " ":
                        self[shape.x+x-1, shape.y+y -
                             1] = shape[x, y]
                except IndexError:
                    pass

    def can_move_left(self, shape: Tetromino) -> bool:
        if shape.x > shape.get_stop_left():
            free_spaces = 0
            cells = shape.get_leftmost()
            for cell in cells:
                if FILL_CHAR in self[shape.x + cell[0]-2, shape.y + cell[1]-1]:
                    return False
                else:
                    free_spaces += 1
            if free_spaces == len(cells):
                return True

    def can_move_right(self, shape: Tetromino) -> bool:
        try:
            if shape.x < shape.get_stop_right():
                free_spaces = 0
                cells = shape.get_rightmost()
                for cell in cells:
                    if FILL_CHAR in self[shape.x + cell[0], shape.y + cell[1]-1]:
                        return False
                    else:
                        free_spaces += 1
                if free_spaces == len(cells):
                    return True
        except IndexError:
            print(shape.get_stop_right())
            exit()

    def can_move_down(self, shape: Tetromino) -> bool:
        if shape.y != shape.get_stop_y():  # not at bottom
            free_spaces = 0
            cells = shape.get_bottommost()
            for cell in cells:
                if FILL_CHAR in self[shape.x + cell[0]-1, shape.y + cell[1]-2]:
                    return False
                else:
                    free_spaces += 1
            if free_spaces == len(cells):
                return True

    def can_rotate(self, shape: Tetromino) -> bool:
        free = 0
        original_cells = []
        for x in range(1, len(shape.shape)+1):
            for y in range(1, len(shape.shape)+1):
                if FILL_CHAR in shape[x, y]:
                    original_cells.append((x, y))
        num_of_cells_overlapping_with_self = len(
            set(original_cells) & set(shape.get_rotated()))
        for i in shape.get_rotated():

            if FILL_CHAR in self[shape.x+i[0]-1, shape.y+i[1]-1]:
                pass
            else:

                free += 1
        if free == len(shape.get_rotated()) - num_of_cells_overlapping_with_self:
            return True

    def game_update_loop(self):
        # check whether to move the current shape down
        current_shape = self.shapes[-1]
        if self.can_move_down(current_shape):
            current_shape.move_down()
        else:
            tetromino = Tetromino(self.bag.next_piece(), 4, 0)
            self.shapes.append(tetromino)
        self.board: list[list[str]] = [
            [" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        for shape in self.shapes:
            self.update(shape)
        print('\033[21A\033[2K', end='')
        print(self)

    def update_screen(self):
        self.board: list[list[str]] = [
            [" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        for shape in self.shapes:
            self.update(shape)
        print('\033[21A\033[2K', end='')
        print(self)

    def main(self):
        last_main_update = time.time()
        main_interval = 0.8  # seconds (1 Hz main loop)
        running = True
        current_shape = self.shapes[-1]
        while running:
            # Check for key input as fast as possible
            current_shape = self.shapes[-1]
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\xe0':
                    arrow = msvcrt.getch()
                    if arrow == b'H':
                        if self.can_rotate(current_shape):
                            current_shape.rotate(90)
                            self.update_screen()
                    elif arrow == b'P':
                        if self.can_move_down(current_shape):
                            current_shape.move_down()
                            self.update_screen()
                    elif arrow == b'M':
                        if self.can_move_right(current_shape):
                            current_shape.x += 1
                            self.update_screen()
                    elif arrow == b'K':
                        if self.can_move_left(current_shape):
                            current_shape.x -= 1
                            self.update_screen()
                elif key == b'q':
                    print("Quitting")
                    running = False

            # Run main logic at fixed interval
            now = time.time()
            if now - last_main_update >= main_interval:
                self.game_update_loop()
                last_main_update = now

            time.sleep(0.01)  # Prevent CPU hogging (100 Hz loop)

    @staticmethod
    def get_key():
        ch = msvcrt.getch()
        if ch == b'\xe0':  # Arrow or function key prefix
            ch2 = msvcrt.getch()
            if ch2 == b'H':
                return 'UP'
            elif ch2 == b'P':
                return 'DOWN'
            elif ch2 == b'M':
                return 'RIGHT'
            elif ch2 == b'K':
                return 'LEFT'
        else:
            return ch.decode()


if __name__ == "__main__":
    os.system("cls")

    winsound.PlaySound("Tetris.wav", winsound.SND_FILENAME |
                       winsound.SND_ASYNC | winsound.SND_LOOP)
    game = Tetris()
    shapes = ["I", "O", "J", "L", "T", "Z", "S"]  # possible shapes
    tetromino = Tetromino(game.bag.next_piece(), 4, 0)
    game.shapes.append(tetromino)
    game.main()

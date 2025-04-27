#!/usr/bin/env/python
"""
A terminal-based Tetris game implemented in Python.


Key Features:
- Standard Tetris board dimensions (10x20).
- 7 unique Tetromino shapes with color-letterd display.
- Real-time input handling using `msvcrt` (Windows only).
- Sound effects using `winsound` for piece lock and line clears.
- Frame-based game loop with configurable fall delay.
- Collision-safe movement and rotation.
- Line clearing with score tracking.


Dependencies:
- Windows platform (for `msvcrt` and `winsound` modules).
- ANSI-compatible terminal for color display.

Todo:
 - see notes.mkd
"""

import time
import random
import os
import msvcrt
import winsound
import copy

__author__ = "Michael Savage"
__version__ = "1.0.0"


BOARD_X = 10
BOARD_Y = 20
FILL_CHAR = "███"

I_PIECE = [
    [" ", " ", " ", " "],
    ["███", "███", "███", "███"],
    [" ", " ", " ", " "],
    [" ", " ", " ", " "]
]
O_PIECE = [
    ["███", "███"],
    ["███", "███"],
]
T_PIECE = [
    [" ", "███", " "],
    ["███", "███", "███"],
    [" ", " ", " "]
]
S_PIECE = [
    [" ", "███", "███"],
    ["███", "███", " "],
    [" ", " ", " "]
]
Z_PIECE = [
    ["███", "███", " "],
    [" ", "███", "███"],
    [" ", " ", " "]
]
J_PIECE = [
    ["███", " ", " "],
    ["███", "███", "███"],
    [" ", " ", " "]
]
L_PIECE = [
    [" ", " ", "███"],
    ["███", "███", "███"],
    [" ", " ", " "]
]


class Color:
    """ ANSI color letters """
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


TETRIS = f"""
{Color.RED}█████████\033[0m {Color.ORANGE}███████\033[0m {Color.YELLOW}█████████\033[0m {Color.GREEN}████████ \033[0m {Color.LIGHT_BLUE}███████ \033[0m {Color.PURPLE}████████\033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███    \033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}███  ███ \033[0m {Color.LIGHT_BLUE}  ███   \033[0m {Color.PURPLE}███     \033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███████\033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}█████    \033[0m {Color.LIGHT_BLUE}  ███   \033[0m {Color.PURPLE}████████\033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███    \033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}███  ███ \033[0m {Color.LIGHT_BLUE}  ███   \033[0m {Color.PURPLE}     ███\033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███████\033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}███  ███ \033[0m {Color.LIGHT_BLUE}███████ \033[0m {Color.PURPLE}████████\033[0m
"""


class TetriminoBag:
    """
    Class that acts as a bag to draw next piece
    """

    def __init__(self):
        self.bag = []

    def next_piece(self):
        """Get next piece"""
        if not self.bag:
            self.bag = ["I", "O", "T", "S", "Z", "J", "L"]
            random.shuffle(self.bag)
        return self.bag.pop()

    def peek(self):
        """Get next peice without popping"""
        if not self.bag:
            self.bag = ["I", "O", "T", "S", "Z", "J", "L"]
            random.shuffle(self.bag)
        return self.bag[-1]


class Tetromino:
    """
    Class for all tetrominoes

    Attributes:
     - shape
     - x
     - y
    """

    def __init__(self, shape: str, start_x_pos: int, start_rotation: int) -> None:
        self.shape = {"I": I_PIECE, "O": O_PIECE, "T": T_PIECE, "S": S_PIECE, "Z": Z_PIECE, "J": J_PIECE, "L": L_PIECE}[shape]
        if shape not in ["I", "O", "T", "S", "Z", "J", "L"]:
            raise ValueError(f"{self.shape} Not a valid shape")
        self.shape_letter = shape
        self.x = start_x_pos
        self.y = 0  # top
        self.rotation = start_rotation
        self.rotate(self.rotation)
        self.prepare_shape()

    def __str__(self) -> str:
        return "\n".join("".join(("["+i + "]" if FILL_CHAR not in i else i) for i in j) for j in self.shape)

    def __getitem__(self, pos: tuple) -> str | int:
        try:
            return self.shape[pos[0]][pos[1]]
        except IndexError:
            print(f"Invalid Shape position. Cannot access coordinate {pos[0], pos[1]}. Max is {self.size}")

    def __setitem__(self, pos: tuple, value: str | int) -> None:
        try:
            self.shape[pos[0]][pos[1]] = value
        except IndexError:
            print(f"Invalid Shape position. Cannot access coordinate {pos[0], pos[1]}. Max is {self.size}")

    def rotate(self, degrees: int) -> None:
        if degrees % 90 != 0:
            raise ValueError(
                f"Rotation must be a multiple of 90. Got rotation {degrees}")
        for _ in range(int(degrees/90)):
            self.shape = [list(row) for row in zip(*self.shape[::-1])]

    def move_down(self) -> None:
        self.y += 1

    def move_left(self) -> None:
        self.x -= 1

    def move_right(self) -> None:
        self.x += 1

    @property
    def size(self):
        """ Size of the shape """
        return len(self.shape)

    def set_color(self, color: str) -> None:
        for row in range(self.size):
            for col in range(self.size):
                if self[row, col] == FILL_CHAR:
                    self[row, col] = color + self[row, col] + Color.END

    def prepare_shape(self) -> None:
        """ Sets the color of the shape to the correct color (matches original tetris)"""
        color_mappings = {"I": Color.CYAN, "O": Color.YELLOW, "L": Color.BLUE, "J": Color.ORANGE, "S": Color.GREEN, "Z": Color.RED, "T": Color.PURPLE}
        self.set_color(color_mappings[self.shape_letter])

    def get_leftmost(self) -> list[tuple]:
        """
        Return (x, y) positions of all left-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly to the left).
        """
        leftmost = []

        for row in range(self.size):
            for col in range(self.size):
                if FILL_CHAR in self[row, col]:
                    # Check the tile to the left
                    if col == 0 or FILL_CHAR not in self[row, col-1]:
                        leftmost.append((row, col))
        return leftmost

    def get_bottommost(self):
        """
        Return (x, y) positions of all bottom-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly below).
        """
        bottommost = []

        for row in range(self.size):
            for col in range(self.size):
                if FILL_CHAR in self[row, col]:
                    # Check the tile below
                    if row == self.size-1 or FILL_CHAR not in self[row+1, col]:
                        bottommost.append((row, col))
        return bottommost

    def get_rightmost(self) -> list[tuple]:
        """
        Return (x, y) positions of all left-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly to the left).
        """
        rightmost = []

        for row in range(self.size):
            for col in range(self.size):
                if FILL_CHAR in self[row, col]:
                    # Check the tile to the left
                    if col == self.size-1 or FILL_CHAR not in self[row, col+1]:
                        rightmost.append((row, col))

        return rightmost

    def get_stop_y(self) -> tuple:
        """
        Gets the Y coordinate where the tetromino should stop at the bottom
        since some have empty space at the bottom, this should be added onto the y
        """
        lowest = self.get_bottommost()

        min_value = BOARD_Y - self.size + (self.size-max(lowest, key=lambda x: x[0])[0] - 1)
        return min_value

    def get_stop_left(self) -> tuple:
        """
        Gets the furthest left the tetromino can be
        before it goes of the edge of the board
        """
        lowest = self.get_leftmost()
        min_value = 0 - min(lowest, key=lambda x: x[1])[1]
        return min_value

    def get_stop_right(self) -> tuple:
        """
        Gets the furthest right the tetromino can be
        before it goes of the edge of the board
        """
        lowest = self.get_rightmost()
        min_value = BOARD_X-self.size + (self.size-max(lowest, key=lambda x: x[1])[1]) - 1
        return min_value

    def get_rotated(self) -> list[tuple]:
        rotated = []
        cells = [list(row) for row in zip(*self.shape[::-1])]
        for row in range(self.size):
            for col in range(self.size):
                if FILL_CHAR in cells[row][col]:
                    rotated.append((row, col))
        return rotated

    def get_left_rotated(self) -> list[tuple]:
        rotated = []
        cells = [list(row) for row in zip(*self.shape[::-1])]
        cells = [list(row) for row in zip(*cells[::-1])]
        cells = [list(row) for row in zip(*cells[::-1])]
        for row in range(self.size):
            for col in range(self.size):
                if FILL_CHAR in cells[row][col]:
                    rotated.append((row, col))
        return rotated


def display(func):
    def inner(*args, **kwargs):
        print("\033[30A\033[2K", end="")
        return func(*args, **kwargs)
    return inner


@display
def game_display(board: list[list], score: int, next_shape: str):
    top = f"╔════════════════{round(score, 2)}═══════════════════╗\n║                                      ║"
    board_print = ""
    tetromino_str = str(Tetromino(next_shape, 0, 0)).split("\n")

    for y, j in enumerate(board):
        board_print += "\n║  " + str(BOARD_Y-y).ljust(4)
        for x in j:
            board_print += ("["+x + "]" if FILL_CHAR not in x else x)
        board_print += "  ║"
        if 5 <= y <= 10:
            if y == 5:
                board_print += "\t╔═════Next══════╗"
            elif y == 10:
                board_print += "\t╚═══════════════╝"
            else:
                try:
                    string = tetromino_str[y-6]  # current row of tetromino
                    board_print += f"\t║ {string.ljust(len(string) + 2 + (12 - 3*Tetromino(next_shape, 0, 0).size))}║"
                except IndexError:
                    board_print += f"\t║ {(" "*(len(string) + 2 + (12 - 3*Tetromino(next_shape, 0, 0).size)))}║"
    # board = "\n".join("║\t" + str(BOARD_Y-y).ljust(4)+"".join(("["+i + "]" if FILL_CHAR not in i else i) for i in j) for y, j in enumerate(self.board))
    return TETRIS + "\n" + top + board_print


class Tetris:
    def __init__(self):
        self.board: list[list[str]] = [
            [" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        self.shapes: list[Tetromino] = []
        self.bag = TetriminoBag()
        self.fixed_board: list[list[str]] = [
            [" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        self.lines_cleared = 0

    def __getitem__(self, pos: tuple) -> str | int:
        return self.board[pos[0]][pos[1]]

    def __setitem__(self, pos: tuple, value: str | int) -> None:
        self.board[pos[0]][pos[1]] = value

    def update(self, shape: Tetromino):
        """
        updates a tetromino on the board at its specifed position
        iterates through the tetromino shape and plonks it on the board accordingly
        """
        for row in range(shape.size):
            for col in range(shape.size):
                if FILL_CHAR in shape[row, col]:
                    self[shape.y + row, shape.x+col] = shape[row, col]

    def can_move_left(self, shape: Tetromino) -> bool:
        if shape.x > shape.get_stop_left():
            free_spaces = 0
            cells = shape.get_leftmost()
            for cell in cells:
                if FILL_CHAR in self[shape.y + cell[0], shape.x + cell[1] - 1]:
                    return False
                else:
                    free_spaces += 1
            if free_spaces == len(cells):
                return True

    def can_move_right(self, shape: Tetromino) -> bool:
        if shape.x < shape.get_stop_right():
            free_spaces = 0
            cells = shape.get_rightmost()
            for cell in cells:
                if FILL_CHAR in self[shape.y + cell[0], shape.x + cell[1] + 1]:
                    return False
                else:
                    free_spaces += 1
            if free_spaces == len(cells):
                return True

    def can_move_down(self, shape: Tetromino) -> bool:
        if shape.y != shape.get_stop_y():  # not at bottom
            free_spaces = 0
            cells = shape.get_bottommost()
            for cell in cells:
                if FILL_CHAR in self[shape.y + cell[0]+1, shape.x + cell[1]]:
                    return False
                else:
                    free_spaces += 1
            if free_spaces == len(cells):
                return True

    def can_rotate(self, shape: Tetromino) -> bool:
        free = 0
        original_cells = []
        for row in range(shape.size):
            for col in range(shape.size):
                if FILL_CHAR in shape[row, col]:
                    original_cells.append((row, col))
        num_of_cells_overlapping_with_self = len(set(original_cells) & set(shape.get_rotated()))
        for i in shape.get_rotated():
            if shape.x+i[1] < 0 or shape.x+i[1] >= BOARD_X:
                return False
            if FILL_CHAR in self[shape.y+i[0], shape.x+i[1]]:
                pass
            else:

                free += 1
        
        if free == len(shape.get_rotated()) - num_of_cells_overlapping_with_self:
            return True
        
    def can_rotate_left(self,shape:Tetromino) -> bool:
        free = 0
        original_cells = []
        for row in range(shape.size):
            for col in range(shape.size):
                if FILL_CHAR in shape[row, col]:
                    original_cells.append((row, col))
        num_of_cells_overlapping_with_self = len(set(original_cells) & set(shape.get_left_rotated()))
        for i in shape.get_left_rotated():
            if shape.x+i[1] < 0 or shape.x+i[1] >= BOARD_X:
                return False
            if FILL_CHAR in self[shape.y+i[0], shape.x+i[1]]:
                pass
            else:

                free += 1
        
        if free == len(shape.get_left_rotated()) - num_of_cells_overlapping_with_self:
            return True

    def check_rows(self):
        row = BOARD_Y - 1
        while row >= 0:
            if all(FILL_CHAR in self.fixed_board[row][col] for col in range(BOARD_X)):
                winsound.Beep(1000, 100)

                # Animate from center outwards
                mid = BOARD_X // 2
                for offset in range(mid + 1):
                    left = mid - offset
                    right = mid + offset
                    if 0 <= left < BOARD_X:
                        self.fixed_board[row][left] = " "
                    if 0 <= right < BOARD_X and right != left:
                        self.fixed_board[row][right] = " "
                    self.update_screen()  # Refresh display
                    time.sleep(0.03)     # Delay per step for animation

                # Shift rows down
                for r in range(row, 0, -1):
                    self.fixed_board[r] = self.fixed_board[r - 1][:]
                self.fixed_board[0] = [" " for _ in range(BOARD_X)]

                self.lines_cleared += 1
                # Do not decrement row so we re-check this row index
            else:
                row -= 1

    def update_fixed_board(self):
        for row in range(BOARD_Y):
            for col in range(BOARD_X):
                if FILL_CHAR in self[row, col]:
                    self.fixed_board[row][col] = self[row, col]

    def advance_state(self):
        """
        Advances the state of the board

        moves the current shape down (if it can) and then gets the next peice if necessary
        """
        # check whether to move the current shape down
        current_shape = self.shapes[-1]
        if self.can_move_down(current_shape):
            current_shape.move_down()
        else:
            tetromino = Tetromino(self.bag.next_piece(), 4, 0)
            self.shapes.append(tetromino)
            self.update_fixed_board()
            self.check_rows()
        self.update_screen()

    def update_screen(self):
        """ Iterates through all the shapes and updates the board, and then prints it """
        self.board = copy.deepcopy(self.fixed_board)
        self.update(self.shapes[-1])
        print(game_display(self.board, max(0.1, 0.8 * (0.9 ** (self.lines_cleared//10))), self.bag.peek()))

    def main(self):
        last_main_update = time.time()
        main_interval = 0.8  # seconds (1 Hz main loop)
        running = True
        current_shape = self.shapes[-1]
        while running:
            main_interval = max(0.1, 0.8 * (0.9 ** (self.lines_cleared//10)))
            # Check for key input as fast as possible
            current_shape = self.shapes[-1]
            match self.get_key():
                case "UP":
                    if self.can_rotate(current_shape):
                        current_shape.rotate(90)
                        self.update_screen()
                case "DOWN":
                    if self.can_move_down(current_shape):
                        current_shape.move_down()
                        self.update_screen()
                case "LEFT":
                    if self.can_move_left(current_shape):
                        current_shape.x -= 1
                        self.update_screen()
                case "RIGHT":
                    if self.can_move_right(current_shape):
                        current_shape.x += 1
                        self.update_screen()
                case "Z":
                    if self.can_rotate_left(current_shape):
                        current_shape.rotate(270)
                        self.update_screen()
                case "QUIT":
                    running = False
            # Run main logic at fixed interval
            now = time.time()
            if now - last_main_update >= main_interval:
                self.advance_state()
                last_main_update = now

            time.sleep(0.01)  # Prevent CPU hogging (100 Hz loop)

    @staticmethod
    def get_key():
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch == b"\xe0":  # Arrow or function key prefix
                ch2 = msvcrt.getch()
                if ch2 == b"H":
                    return "UP"
                elif ch2 == b"P":
                    return "DOWN"
                elif ch2 == b"M":
                    return "RIGHT"
                elif ch2 == b"K":
                    return "LEFT"
            elif ch == b"q":
                return "QUIT"
            elif ch==b"z":
                return "Z"


if __name__ == "__main__":
    os.system("cls")
    winsound.PlaySound("Tetris.wav", winsound.SND_FILENAME |
                       winsound.SND_ASYNC | winsound.SND_LOOP)
    game = Tetris()
    shapes = ["I", "O", "J", "L", "T", "Z", "S"]  # possible shapes
    tetromino = Tetromino(game.bag.next_piece(), 4, 0)
    game.shapes.append(tetromino)
    game.main()

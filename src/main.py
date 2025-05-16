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
import re

__author__ = "Michael Savage"
__version__ = "1.0.0"

BOARD_X = 10
BOARD_Y = 20
FILL_CHAR = "███"

# store coordinates of the shapes relative to the top left corner being (0,0), standard python 2d-array coords
I_PIECE = [(1, 0), (1, 1), (1, 2), (1, 3)]
O_PIECE = [(0, 0), (0, 1), (1, 0), (1, 1)]
T_PIECE = [(1, 0), (0, 1), (1, 1), (1, 2)]
S_PIECE = [(1, 0), (1, 1), (0, 1), (0, 2)]
Z_PIECE = [(0, 0), (1, 1), (0, 1), (1, 2)]
J_PIECE = [(0, 0), (1, 0), (1, 1), (1, 2)]
L_PIECE = [(1, 0), (1, 1), (1, 2), (0, 2)]


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


# tetris logo
TETRIS = f"""
{Color.RED}█████████\033[0m {Color.ORANGE}███████\033[0m {Color.YELLOW}█████████\033[0m {Color.GREEN}████████ \033[0m {Color.LIGHT_BLUE}███████ \033[0m {Color.PURPLE}████████\033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███    \033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}███  ███ \033[0m {Color.LIGHT_BLUE}  ███   \033[0m {Color.PURPLE}███     \033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███████\033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}█████    \033[0m {Color.LIGHT_BLUE}  ███   \033[0m {Color.PURPLE}████████\033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███    \033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}███  ███ \033[0m {Color.LIGHT_BLUE}  ███   \033[0m {Color.PURPLE}     ███\033[0m
{Color.RED}   ███   \033[0m {Color.ORANGE}███████\033[0m {Color.YELLOW}   ███   \033[0m {Color.GREEN}███  ███ \033[0m {Color.LIGHT_BLUE}███████ \033[0m {Color.PURPLE}████████\033[0m
"""


class Settings:
    """
    Class for controlling the settings of the game and stored variables
    At the moment,  only highscore is implemented, but more can be added
    """
    def __init__(self):
        self.highscore = 0

        with open("src/settings.txt") as file:
            for line in file.readlines():
                matched = re.match(r'^\s*(\w+)\s*:\s*(\S+)\s*$', line)
                if matched:
                    setattr(self, matched.group(1), matched.group(2))


class TetriminoBag:
    """
    Class that acts as a bag to draw next piece

    next_piece returns the next piece
    peek returns the next piece without popping from the bag (used for the "next" counter display )
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
     - rotation
    """

    def __init__(self, shape: str, start_x_pos: int, start_rotation: int = 0) -> None:
        self.shape = shape
        if self.shape not in ["I", "O", "T", "S", "Z", "J", "L"]:
            raise ValueError(f"{self.shape} Not a valid shape")
        self.cells: list[tuple[int, int]] = {"I": I_PIECE, "O": O_PIECE, "T": T_PIECE, "S": S_PIECE, "Z": Z_PIECE, "J": J_PIECE, "L": L_PIECE}[shape]
        self.x = start_x_pos
        self.y = 0  # top
        self.rotation = start_rotation
        self.color = self.get_color()
        self.size = self.get_size()
        # set shape color
        # self.prepare_shape()

    def __str__(self) -> str:
        text = ""
        for x in range(self.size):
            for y in range(self.size):
                if (x, y) in self.cells:
                    text += self.color + FILL_CHAR + Color.END
                else:
                    text += "[ ]"
            text += "\n"
        return text

    def __getitem__(self, pos: tuple[int, int]) -> str | None:
        if pos in self.cells:
            return FILL_CHAR
        else:
            return None

    def get_color(self):
        return {"I": Color.CYAN, "O": Color.YELLOW, "L": Color.BLUE, "J": Color.ORANGE, "S": Color.GREEN, "Z": Color.RED, "T": Color.PURPLE}[self.shape]

    def get_rotated_clockwise(self) -> list[tuple[int, int]]:
        cx, cy = (self.size - 1) / 2, (self.size - 1) / 2
        return [
            (round(cx + (y - cy)), round(cy - (x - cx)))
            for (x, y) in self.cells
        ]

    def get_rotated_anticlockwise(self) -> list[tuple[int, int]]:
        cx, cy = (self.size - 1) / 2, (self.size - 1) / 2
        return [
            (round(cx - (y - cy)), round(cy + (x - cx)))
            for (x, y) in self.cells
        ]

    def rotate_clockwise(self) -> None:
        self.cells = self.get_rotated_clockwise()

    def rotate_anticlockwise(self) -> None:
        self.cells = self.get_rotated_anticlockwise()

    def move_down(self) -> None:
        self.y += 1

    def move_left(self) -> None:
        self.x -= 1

    def move_right(self) -> None:
        self.x += 1

    def get_size(self):
        """ Size of the shape (height or width) """
        return {"I": 4, "Z": 3, "S": 3, "T": 3, "L": 3, "J": 3, "O": 2}[self.shape]

    def get_leftmost(self) -> list[tuple]:
        """
        Return (x, y) positions of all left-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly to the left).
        """
        leftmost = {}
        # 0:1 1:1 2:1
        # (0,1),(1,1),(1,0)(2,1)
        for row, col in self.cells:
            if row not in leftmost:
                leftmost[row] = col
            try:
                if col < leftmost[row]:
                    leftmost[row] = col
            except IndexError:
                pass
        return [(row, col) for row, col in leftmost.items()]

    def get_bottommost(self):
        """
        Return (x, y) positions of all bottom-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly below).
        """
        bottommost = {}
        for row, col in self.cells:
            if col not in bottommost:
                bottommost[col] = row
            try:
                if row > bottommost[col]:
                    bottommost[col] = row
            except IndexError:
                pass
        return [(row, col) for col, row in bottommost.items()]

    def get_rightmost(self) -> list[tuple]:
        """
        Return (x, y) positions of all right-edge blocks in the shape (i.e., blocks with no FILL_CHAR directly to the left).
        """
        rightmost = {}
        # 0:1 1:1 2:1
        # (0,1),(1,1),(1,0)(2,1)
        for row, col in self.cells:
            if row not in rightmost:
                rightmost[row] = col
            try:
                if col > rightmost[row]:
                    rightmost[row] = col
            except IndexError:
                pass
        return [(row, col) for row, col in rightmost.items()]

    def get_stop_y(self) -> int:
        """
        Gets the Y coordinate where the tetromino should stop at the bottom
        since some have empty space at the bottom, this should be added onto the y
        """
        lowest = max(self.get_bottommost(), key=lambda x: x[0])[0]

        return BOARD_Y - lowest - 1

    def get_stop_left(self) -> int:
        """
        Gets the furthest left the tetromino can be
        before it goes of the edge of the board
        """
        return 0 - min(self.get_leftmost(), key=lambda x: x[1])[1]

    def get_stop_right(self) -> int:
        """
        Gets the furthest right the tetromino can be
        before it goes of the edge of the board
        """
        return BOARD_X-max(self.get_rightmost(), key=lambda x: x[1])[1] - 1


def display(func):
    def inner(*args, **kwargs):
        print("\033[32A\033[2K", end="")
        return func(*args, **kwargs)
    return inner


@display
def game_over_display():
    os.system("cls")
    top = "╔══════════════════════════════════════╗\n"
    for x in range(20):
        if x == 10:
            top += f"║{Color.BOLD}{Color.RED}              GAME OVER               {Color.END}║\n"
        else:
            top += "║                                      ║\n"
    top += "║                                      ║\n╚══════════════════════════════════════╝"
    return TETRIS + "\n" + top


@display
def game_display(board: list[list], score: int, next_shape: str, lines, highscore, message):
    top = "╔══════════════════════════════════════╗\n║                                      ║"
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
                    board_print += "\t║               ║"
        elif y == 11:
            board_print += f"{Color.BOLD}\t{message}                        {Color.END}"
        elif y == 13:
            board_print += f"{Color.BOLD}\tScore: {score}{Color.END}"
        elif y == 15:
            board_print += f"{Color.BOLD}\tLines: {lines}{Color.END}"
        elif y == 17:
            board_print += f"{Color.BOLD}\tLevel: {lines//10}{Color.END}"
        elif y == 19:
            board_print += f"{Color.BOLD}\tHighscore: {highscore}{Color.END}"
    # board = "\n".join("║\t" + str(BOARD_Y-y).ljust(4)+"".join(("["+i + "]" if FILL_CHAR not in i else i) for i in j) for y, j in enumerate(self.board))
    bottom = "\n║                                      ║\n╚══════════════════════════════════════╝"
    return TETRIS + "\n" + top + board_print + bottom


class Tetris:
    def __init__(self):
        self.board: list[list[str]] = [
            [" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        self.shapes: list[Tetromino] = []
        self.bag = TetriminoBag()
        self.fixed_board: list[list[str]] = [
            [" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        self.lines_cleared = 0
        self.score = 0
        self.dead: bool = False
        self.settings = Settings()
        self.highscore = self.settings.highscore
        self.message = ""

    def __getitem__(self, pos: tuple) -> str:
        return self.board[pos[0]][pos[1]]

    def __setitem__(self, pos: tuple, value: str | int) -> None:
        self.board[pos[0]][pos[1]] = value

    def save_data(self):
        with open("src/settings.txt", "w")as file:
            for attr, value in self.settings.__dict__.items():
                file.write(f"{attr} : {value}")

    def update(self, shape: Tetromino):
        """
        updates a tetromino on the board at its specifed position
        iterates through the tetromino shape and plonks it on the board accordingly
        """
        for cell in shape.cells:
            if FILL_CHAR in self[shape.y+cell[0], shape.x+cell[1]]:
                self.dead = True
            else:
                self[shape.y+cell[0], shape.x+cell[1]] = shape.color + FILL_CHAR + Color.END

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
        return False

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
        return False

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
        return False

    def can_rotate_clockwise(self, shape: Tetromino) -> bool:
        free = 0
        num_of_cells_overlapping_with_self = len(set(shape.cells) & set(shape.get_rotated_clockwise()))
        for i in shape.get_rotated_clockwise():
            if shape.x+i[1] < 0 or shape.x+i[1] >= BOARD_X:
                return False
            if FILL_CHAR in self[shape.y+i[0], shape.x+i[1]]:
                pass
            else:

                free += 1

        if free == len(shape.get_rotated_clockwise()) - num_of_cells_overlapping_with_self:
            return True
        return False

    def can_rotate_anticlockwise(self, shape: Tetromino) -> bool:
        free = 0
        num_of_cells_overlapping_with_self = len(set(shape.cells) & set(shape.get_rotated_anticlockwise()))
        for i in shape.get_rotated_anticlockwise():
            if shape.x+i[1] < 0 or shape.x+i[1] >= BOARD_X:
                return False
            if FILL_CHAR in self[shape.y+i[0], shape.x+i[1]]:
                pass
            else:

                free += 1

        if free == len(shape.get_rotated_anticlockwise()) - num_of_cells_overlapping_with_self:
            return True
        return False

    def check_rows(self):
        row = BOARD_Y - 1
        cleared_rows = 0
        while row >= 0:
            if all(FILL_CHAR in self.fixed_board[row][col] for col in range(BOARD_X)):
                winsound.Beep(1000, 100)
                cleared_rows += 1
                self.score += 50*(3*cleared_rows)
                match cleared_rows:
                    case 4:
                        self.message = "Tetris! + 500"
                        self.score += 500
                    case 3:
                        self.message = "Triple!"
                    case 2:
                        self.message = "Double!"
                    case 1:
                        self.message = "Single!"

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
        self.message = ""
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
        if not self.dead:
            print(game_display(self.board, self.score, self.bag.peek(), self.lines_cleared, self.settings.highscore, self.message))
            if self.score > int(self.settings.highscore):
                self.settings.highscore = self.score
        else:
            print(game_over_display())
            if self.score > int(self.settings.highscore):
                self.settings.highscore = self.score
            self.save_data()
            exit()

    def main(self):
        last_main_update = time.time()
        main_interval = 0.8  # seconds (1 Hz main loop)
        running = True
        current_shape = self.shapes[-1]
        while True:
            if running:
                main_interval = max(0.1, 0.8 * (0.9 ** (self.lines_cleared//10)))
                # Check for key input as fast as possible
                current_shape = self.shapes[-1]
                match self.get_key():
                    case "UP":
                        if self.can_rotate_clockwise(current_shape):
                            current_shape.rotate_clockwise()
                            self.update_screen()
                    case "DOWN":
                        if self.can_move_down(current_shape):
                            self.score += 1
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
                        if self.can_rotate_anticlockwise(current_shape):
                            current_shape.rotate_anticlockwise()
                            self.update_screen()
                    case "QUIT":
                        exit()
                    case "PAUSE":
                        if running:
                            running = False
                        else:
                            running = True
                # Run main logic at fixed interval
                now = time.time()
                if now - last_main_update >= main_interval:
                    self.advance_state()
                    last_main_update = now

                time.sleep(0.01)  # Prevent CPU hogging (100 Hz loop)
            else:
                if self.get_key() == "PAUSE":
                    if running:
                        running = False
                    else:
                        running = True
                elif self.get_key() == "QUIT":
                    exit()
                elif self.get_key() == "RESTART":
                    del self
                    game = Tetris()
                    tetromino = Tetromino(game.bag.next_piece(), 4, 0)
                    game.shapes.append(tetromino)
                    game.main()

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
            elif ch == b"z":
                return "Z"
            elif ch == b"p":
                return "PAUSE"
            elif ch == b"r":
                return 'RESTART'


if __name__ == "__main__":
    os.system("cls")
    winsound.PlaySound("Tetris.wav", winsound.SND_FILENAME |
                       winsound.SND_ASYNC | winsound.SND_LOOP)
    game = Tetris()
    shapes = ["I", "O", "J", "L", "T", "Z", "S"]  # possible shapes
    tetromino = Tetromino(game.bag.next_piece(), 4, 0)
    game.shapes.append(tetromino)
    game.main()

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
import winsound
import copy
import re
import ctypes

__author__ = "Michael Savage"
__version__ = "1.1.1"

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
    GREEN = "\033[38;5;046m"
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

ANSI_ESCAPE = re.compile(r"\033\[[0-9;]*m")


def visible_length(s: str) -> int:
    return len(ANSI_ESCAPE.sub("",s))


class Settings:
    """
    Class for controlling the settings of the game and stored variables
    At the moment,  only highscore is implemented, but more can be added
    """
    def __init__(self):
        self.highscore = 0
        self.starting = 0

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

    def __init__(self, shape: str, start_x_pos: int = 4, start_rotation: int = 0) -> None:
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
        return text.strip()

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


class Widget:
    def __init__(self, text: str):
        self.text = text.strip("\n").split("\n")  # store lines without \n

    def __iter__(self):
        return iter(self.text)  # iterator over lines without \n


class BorderWidget(Widget):
    def __init__(
        self,
        inner_widget: Widget,
        padding: int = 0,
        label: str = "",
        fixed_width: int = None,
        fixed_height: int = None
    ):
        raw_lines = list(inner_widget)
        content_width = max(visible_length(line.rstrip()) for line in raw_lines) if raw_lines else 0
        content_height = len(raw_lines)

        pad = " " * padding
        inner_width = max(content_width, 0)
        padded_width = inner_width + 2 * padding

        # Enforce fixed width
        if fixed_width is not None:
            content_width = fixed_width - 2 * padding
            padded_width = fixed_width

        # ───── Top border ─────
        if label:
            label_stripped = ANSI_ESCAPE.sub('', label)
            label_len = len(label_stripped)
            extra = padded_width - label_len - 2  # -2 for spaces around label
            left = max(0, extra // 2)
            right = max(0, extra - left)
            top_border = "╔" + "═" * left + f" {label} " + "═" * right + "╗"
        else:
            top_border = "╔" + "═" * padded_width + "╗"

        # ───── Pad vertically ─────
        visible_lines = []
        for raw_line in raw_lines:
            stripped = raw_line.rstrip()
            line_pad = content_width - visible_length(stripped)
            padded_line = pad + stripped + " " * max(0, line_pad) + pad
            visible_lines.append("║" + padded_line + "║")

        # Vertical padding: 1 empty line above and below content
        top_pad = ["║" + " " * padded_width + "║"]
        bottom_pad = ["║" + " " * padded_width + "║"]

        # Enforce fixed height
        total_inner_height = len(top_pad) + len(visible_lines) + len(bottom_pad)
        if fixed_height is not None:
            extra_lines = fixed_height - len(visible_lines)
            top_extra = extra_lines // 2
            bottom_extra = extra_lines - top_extra
            top_pad = ["║" + " " * padded_width + "║"] * max(0, top_extra)
            bottom_pad = ["║" + " " * padded_width + "║"] * max(0, bottom_extra)

        # ───── Build final ─────
        bordered_lines = [top_border]
        bordered_lines += top_pad + visible_lines + bottom_pad
        bordered_lines.append("╚" + "═" * padded_width + "╝")

        super().__init__("\n".join(bordered_lines))


class LogoWidget(Widget):
    def __init__(self):
        text = TETRIS
        super().__init__(text)


class GameBoardWidget(Widget):
    def __init__(self, board):
        text = ""
        for y, line in enumerate(board):
            text += str(BOARD_Y-y).ljust(4)
            for element in line:
                text += ("[" + element + "]" if (FILL_CHAR not in element) and (Color.END not in element) else element)
            text += "\n"
        super().__init__(text)


class HorizontalLayout(Widget):
    def __init__(self, widgets: list[Widget], spacing: int = 2):
        # Convert each widget to a list of lines
        rendered = [list(w) for w in widgets]

        # Compute the max visible height
        max_height = max(len(r) for r in rendered)

        # ANSI-aware width computation and padding
        padded_rendered = []
        for lines in rendered:
            width = max(visible_length(line) for line in lines) if lines else 0
            pad_line = " " * width
            padded_lines = lines + [pad_line] * (max_height - len(lines))
            padded_rendered.append(padded_lines)

        # Combine lines horizontally
        lines = []
        for i in range(max_height):
            line_parts = []
            for widget_lines in padded_rendered:
                line_parts.append(widget_lines[i])
            lines.append((" " * spacing).join(line_parts))

        super().__init__("\n".join(lines))


class VerticalLayout(Widget):
    def __init__(self, widgets: list[Widget]):
        lines = []
        for widget in widgets:
            lines.extend(list(widget))
        super().__init__("\n".join(lines))


class ShapeWidget(Widget):
    def __init__(self, next: Tetromino):
        text = ""
        text = str(next)
        super().__init__(text)


class InfoWidget(Widget):
    def __init__(self, score, lines, highscore, message, level):
        text = f"{message}\n"
        text += f"{Color.BOLD} Score: {score}{Color.END}\n"
        text += f"{Color.BOLD} Highscore: {highscore}{Color.END}\n"
        text += f"{Color.BOLD} lines: {lines}{Color.END}\n"
        text += f"{Color.BOLD} level: {level}{Color.END}\n"
        super().__init__(text)


class TextWidget(Widget):
    def __init__(self, text: str):
        text = text
        super().__init__(text)


class Display:
    def __init__(self):
        self.last_key_times = {}

    def get_key(self):
        GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
        now = time.time()
        VK = {
            'UP': 0x26,
            'DOWN': 0x28,
            'LEFT': 0x25,
            'RIGHT': 0x27,
            'SPACE': 0x20,
            'RESTART': 0x52,
            'Z': 0x5A,
            'QUIT': 0x51,
            'PAUSE': 0x50,
            "RESET": 0x4C,
            "HOLD": 0x43
        }
        for key, code in VK.items():
            if GetAsyncKeyState(code) & 0x8000:
                last = self.last_key_times.get(key, 0)
                if key == "DOWN":
                    if now-last >= 0.1:
                        self.last_key_times[key] = now
                        yield key
                elif key == "SPACE":
                    if now-last >= 0.8:
                        self.last_key_times[key] = now
                        yield key
                elif now - last >= 0.15:
                    self.last_key_times[key] = now
                    yield key


class GameDisplay(Display):
    def __init__(self, board, score, next_shape, hold_shape, lines, highscore, message, level):
        self.board = board
        self.score = score
        self.next_shape = next_shape
        self.hold_shape = hold_shape
        self.lines = lines
        self.highscore = highscore
        self.message = message
        self.level = level
        super().__init__()
    
    def __str__(self):
        """The basic board display"""
        print("\033[32A\033[2K", end="")  # clear the screen by moving pointer up to top left
        board_print = ""
        left = BorderWidget(GameBoardWidget(self.board), padding=2)
        right_top = BorderWidget(ShapeWidget(self.next_shape), label="next", padding=4, fixed_height=6, fixed_width=20)
        right_middle = BorderWidget(ShapeWidget(self.hold_shape), label="hold", padding=4, fixed_height=6, fixed_width=20)
        right_bottom = BorderWidget(InfoWidget(self.score, self.lines, self.highscore, self.message, self.level))
        right_column = VerticalLayout([right_top, right_middle, right_bottom])
        screen = VerticalLayout([LogoWidget(), HorizontalLayout([left, right_column], spacing=5)])
        for line in screen:
            board_print += line + "\n"
        return board_print

    def get_events(self):
        return self.get_key()


class EndDisplay:
    def __init__(self):
        pass

    def __str__(self):
        os.system("cls")
        print("\033[32A\033[2K", end="")
        board_print = ""
        for line in VerticalLayout([LogoWidget(), BorderWidget(TextWidget("             Game Over"), padding=2, fixed_height=22, fixed_width=40)]):
            board_print += line + "\n"
        return board_print


class StartDisplay:
    def __init__(self):
        pass

    def __str__(self):
        print("\033[32A\033[2K", end="")
        text = ""
        return text





class Event:
    def __init__(self, event, type):
        self.event = event
        self.type

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


class Tetris:
    last_key_times = {}

    def __init__(self):
        self.board: list[list[str]] = [[" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        self.shapes: list[Tetromino] = []
        self.bag = TetriminoBag()
        self.fixed_board: list[list[str]] = [[" " for _ in range(BOARD_X)] for i in range(BOARD_Y)]
        self.lines_cleared = 0
        self.score = 0
        self.dead: bool = False
        self.settings = Settings()
        self.message = ""
        self.highscore = self.settings.highscore
        self.level = self.settings.starting
        self.hold: Tetromino | None = None
        self.swapped_held = False # whether the player has swapped the held shape. This is so you can't swap and then unswap

    def __getitem__(self, pos: tuple) -> str:
        return self.board[pos[0]][pos[1]]

    def __setitem__(self, pos: tuple, value: str | int) -> None:
        self.board[pos[0]][pos[1]] = value

    @property
    def display(self):
        pass

    def save_data(self):
        with open("src/settings.txt", "w")as file:
            for attr, value in self.settings.__dict__.items():
                file.write(f"{attr} : {value}\n")

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
        for cell in shape.cells:
            if FILL_CHAR not in self[self.calculate_y(shape)+cell[0], shape.x+cell[1]]:
                self[self.calculate_y(shape)+cell[0], shape.x+cell[1]] = shape.color + Color.BOLD + "[ ]" + Color.END

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
        if shape.y < self.calculate_y(shape):
            return True
        else:
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
                self.level = (int(self.settings.starting) + self.lines_cleared//10)
                # Do not decrement row so we re-check this row index
            else:
                row -= 1

    def calculate_y(self, tetromino: Tetromino) -> int:
        """
        Calculate how far down the tetromino can fall before it would collide
        with either the bottom of the board or fixed blocks.
        Returns the y-coordinate where the piece should land.
        """
        # Start from current y
        start_y = tetromino.y

        while True:
            # Check if moving the tetromino down one more step would cause a collision
            for dx, dy in tetromino.cells:
                new_y = start_y + dx + 1
                new_x = tetromino.x + dy
                if new_y >= BOARD_Y or FILL_CHAR in self.fixed_board[new_y][new_x]:
                    return start_y
            # No collision, so move down one row
            start_y += 1

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
            self.swapped_held = False
        self.update_screen()

    def update_screen(self):
        """ Iterates through all the shapes and updates the board, and then prints it """
        self.board = copy.deepcopy(self.fixed_board)
        self.update(self.shapes[-1])
        if not self.dead:
            print(GameDisplay(self.board, 
                              self.score,
                              Tetromino(self.bag.peek(), 4), 
                              self.hold, 
                              self.lines_cleared, 
                              self.settings.highscore, 
                              self.message, self.level))
            #print(game_display(self.board, self.score, self.bag.peek(), self.lines_cleared, self.settings.highscore, self.message, self.level))
            if self.score > int(self.settings.highscore):
                self.settings.highscore = self.score
        else:
            print(EndDisplay())
            if self.score > int(self.settings.highscore):
                self.settings.highscore = self.score
            self.save_data()
            time.sleep(1)
            os.system("cls")
            exit()

    def main(self):
        last_main_update = time.time()
        main_interval = 0.8  # seconds (1 Hz main loop)
        running = True
        current_shape = self.shapes[-1]
        while True:
            if running:
                main_interval = 0.8 * (0.9 ** (int(self.level)))
                # Check for key input as fast as possible
                current_shape = self.shapes[-1]
                for event in self.get_key():
                    match event:
                        case "UP":
                            if self.can_rotate_clockwise(current_shape):
                                current_shape.rotate_clockwise()
                        case "DOWN":
                            if self.can_move_down(current_shape):
                                self.score += 1
                                current_shape.move_down()
                                now = time.time()
                                last_main_update = now
                        case "LEFT":
                            if self.can_move_left(current_shape):
                                current_shape.x -= 1
                        case "RIGHT":
                            if self.can_move_right(current_shape):
                                current_shape.x += 1
                        case "Z":
                            if self.can_rotate_anticlockwise(current_shape):
                                current_shape.rotate_anticlockwise()
                        case "QUIT":
                            exit()
                        case "PAUSE":
                            if running:
                                running = False
                            else:
                                running = True
                        case "SPACE":
                            fall_dist = self.calculate_y(current_shape)
                            self.score += fall_dist-current_shape.y
                            current_shape.y = fall_dist
                            last_main_update = time.time()-1  # set it lower so that the next tic runs instantly
                        case "RESET":  # resets the screen
                            os.system("cls")
                        case "HOLD":
                            if not self.swapped_held:
                                self.swapped_held = True
                                if self.hold is None:
                                    self.hold = Tetromino(current_shape.shape)
                                    tetromino = Tetromino(self.bag.next_piece(), 4, 0)
                                    self.shapes.append(tetromino) 
                                else:
                                    temp = Tetromino(self.hold.shape)
                                    self.hold = Tetromino(current_shape.shape)
                                    self.shapes[-1] = temp
          
                    self.update_screen()
                # Run main logic at fixed interval
                now = time.time()
                if now - last_main_update >= main_interval:
                    self.advance_state()
                    last_main_update = now

                time.sleep(0.01)  # Prevent CPU hogging (100 Hz loop)
            else:
                for event in self.get_key():
                    if event == "PAUSE":
                        if running:
                            running = False
                        else:
                            running = True
                    elif event == "QUIT":
                        exit()
                    elif event == "RESTART":
                        del self
                        game = Tetris()
                        tetromino = Tetromino(game.bag.next_piece(), 4, 0)
                        game.shapes.append(tetromino)
                        game.main()

    @staticmethod
    def get_key():
        GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
        now = time.time()
        VK = {
            'UP': 0x26,
            'DOWN': 0x28,
            'LEFT': 0x25,
            'RIGHT': 0x27,
            'SPACE': 0x20,
            'RESTART': 0x52,
            'Z': 0x5A,
            'QUIT': 0x51,
            'PAUSE': 0x50,
            "RESET": 0x4C,
            "HOLD": 0x43
        }
        for key, code in VK.items():
            if GetAsyncKeyState(code) & 0x8000:
                last = Tetris.last_key_times.get(key, 0)
                if key == "DOWN":
                    if now-last >= 0.1:
                        Tetris.last_key_times[key] = now
                        yield key
                elif key == "SPACE":
                    if now-last >= 0.8:
                        Tetris.last_key_times[key] = now
                        yield key
                elif now - last >= 0.15:
                    Tetris.last_key_times[key] = now
                    yield key


if __name__ == "__main__":
    os.system("cls")
    winsound.PlaySound("Tetris.wav", winsound.SND_FILENAME |
                       winsound.SND_ASYNC | winsound.SND_LOOP)
    game = Tetris()
    shapes = ["I", "O", "J", "L", "T", "Z", "S"]  # possible shapes
    tetromino = Tetromino(game.bag.next_piece(), 4, 0)
    game.shapes.append(tetromino)
    game.main()

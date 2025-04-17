import msvcrt


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

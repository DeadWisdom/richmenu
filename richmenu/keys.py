"""
This module implements `getchar()` and some functions to detect key movement, most is stolen from
the click library:

  https://github.com/pallets/click/blob/9e9fe41a53d885d96e43dec7cd9eb69e352f801a/src/click/_termui_impl.py

I simply grabbed only the necessary parts to implement `getchar()`, which is such a fundamental
function but is oddly difficult to do in a cross-platform way.
"""
import os, sys
import contextlib
import codecs
from typing import Optional, Iterator, Callable, TextIO, IO


UP_ARROW = set(["\x1b[A"])
DOWN_ARROW = set(["\x1b[B"])
OK_BUTTON = set(["\r", "\n\r", "\r\n"])
ESC_BUTTON = set(["\x1b"])
BACKSPACE = set(["\x7f"])

MSYS2 = sys.platform.startswith("win") and ("GCC" in sys.version)
APP_ENGINE = "APPENGINE_RUNTIME" in os.environ and "Development/" in os.environ.get(
    "SERVER_SOFTWARE", ""
)
WIN = sys.platform.startswith("win") and not APP_ENGINE and not MSYS2


def _isatty(stream: IO) -> bool:
    try:
        return stream.isatty()
    except Exception:
        return False


def _is_ascii_encoding(encoding: str) -> bool:
    """Checks if a given encoding is ascii."""
    try:
        return codecs.lookup(encoding).name == "ascii"
    except LookupError:
        return False


def _get_best_encoding(stream: IO) -> str:
    """Returns the default stream encoding if not found."""
    rv = getattr(stream, "encoding", None) or sys.getdefaultencoding()
    if _is_ascii_encoding(rv):
        return "utf-8"
    return rv


def _translate_ch_to_exc(ch: str) -> Optional[BaseException]:
    if ch == "\x03":
        raise KeyboardInterrupt()

    if ch == "\x04" and not WIN:  # Unix-like, Ctrl+D
        raise EOFError()

    if ch == "\x1a" and WIN:  # Windows, Ctrl+Z
        raise EOFError()

    return None


if WIN:
    import msvcrt

    @contextlib.contextmanager
    def raw_terminal() -> Iterator[int]:
        yield -1

    def getchar(echo: bool = False) -> str:
        # The function `getch` will return a bytes object corresponding to
        # the pressed character. Since Windows 10 build 1803, it will also
        # return \x00 when called a second time after pressing a regular key.
        #
        # `getwch` does not share this probably-bugged behavior. Moreover, it
        # returns a Unicode object by default, which is what we want.
        #
        # Either of these functions will return \x00 or \xe0 to indicate
        # a special key, and you need to call the same function again to get
        # the "rest" of the code. The fun part is that \u00e0 is
        # "latin small letter a with grave", so if you type that on a French
        # keyboard, you _also_ get a \xe0.
        # E.g., consider the Up arrow. This returns \xe0 and then \x48. The
        # resulting Unicode string reads as "a with grave" + "capital H".
        # This is indistinguishable from when the user actually types
        # "a with grave" and then "capital H".
        #
        # When \xe0 is returned, we assume it's part of a special-key sequence
        # and call `getwch` again, but that means that when the user types
        # the \u00e0 character, `getchar` doesn't return until a second
        # character is typed.
        # The alternative is returning immediately, but that would mess up
        # cross-platform handling of arrow keys and others that start with
        # \xe0. Another option is using `getch`, but then we can't reliably
        # read non-ASCII characters, because return values of `getch` are
        # limited to the current 8-bit codepage.
        #
        # Anyway, Click doesn't claim to do this Right(tm), and using `getwch`
        # is doing the right thing in more situations than with `getch`.
        func: Callable[[], str]

        if echo:
            func = msvcrt.getwche  # type: ignore
        else:
            func = msvcrt.getwch  # type: ignore

        rv = func()

        if rv in ("\x00", "\xe0"):
            # \x00 and \xe0 are control characters that indicate special key,
            # see above.
            rv += func()

        _translate_ch_to_exc(rv)
        return rv

else:
    import tty
    import termios

    @contextlib.contextmanager
    def raw_terminal() -> Iterator[int]:
        f: Optional[TextIO]
        fd: int

        if not _isatty(sys.stdin):
            f = open("/dev/tty")
            fd = f.fileno()
        else:
            fd = sys.stdin.fileno()
            f = None

        try:
            old_settings = termios.tcgetattr(fd)

            try:
                tty.setraw(fd)
                yield fd
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.flush()

                if f is not None:
                    f.close()
        except termios.error:
            pass

    def getchar(echo: bool = False) -> str:
        with raw_terminal() as fd:
            ch = os.read(fd, 32).decode(_get_best_encoding(sys.stdin), "replace")

            if echo and _isatty(sys.stdout):
                sys.stdout.write(ch)

            _translate_ch_to_exc(ch)
            return ch


def is_up(code):
    return code in UP_ARROW


def is_down(code):
    return code in DOWN_ARROW


def is_ok(code):
    return code in OK_BUTTON


def is_esc(code):
    return code in ESC_BUTTON


def is_backspace(code):
    return code in BACKSPACE

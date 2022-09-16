from functools import cache
from typing import Callable, Dict, Optional

from thefuzz import fuzz, process
from rich.live import Live
from rich.table import Table
from rich.console import Console

from . import keys


class QuitException(RuntimeError):
    pass


@cache
def fuzz_scorer(needle: str, option: str):
    """
    Scores how similar `neeedle` and `option` are...
    and returns an integer from 0 to 100...
    0 being not alike at all...
    100 being exactly the same.

    If option starts with needle then we return even higher than 100.
    """
    if option.startswith(needle):
        score = 100 + len(needle) * 10
    else:
        score = fuzz.WRatio(needle, option, full_process=False)
        if score >= 30:
            index = option.find(needle)
            if index > -1:
                score += len(option) - index
    return score


@cache
def search_for_matches(
    needle: str,
    haystacks: list[str],
    limit: int = 10,
    threshold: int = 46,
    scorer: Callable = fuzz_scorer,
):
    """
    Search for `needle` in `haystacks`...
    return at most `limit` items...
    with a score better than `threshold` using the `scorer` function.
    """
    items = process.extract(needle.lower(), haystacks, scorer=scorer, limit=limit)
    return [(option, score) for option, score in items if score >= threshold]


class Menu:
    def __init__(
        self,
        prompt: str,
        items: Dict[str, str],
        console: Console = None,
        searcher: Callable = search_for_matches,
        scorer: Callable = fuzz_scorer,
    ):
        self._prompt = prompt
        self._items = items
        self._items_filtered = items
        self._selected_index = 0
        self._done = False
        self._searcher = searcher
        self._scorer = scorer

        self.value = None
        self.filter = ""
        self.console = console or Console()

    @classmethod
    def prompt(self, prompt: str, items: Dict[str, str], console: Console = None):
        return Menu(prompt, items, console).run()

    def search(self):
        if self.filter:
            options = [f"{key}: {desc}" for key, desc in self._items.items()]
            results = search_for_matches(self.filter, tuple(options))
            self._items_filtered = {}
            for option, _ in results:
                key, _, _ = option.partition(":")
                desc = self._items[key]
                self._items_filtered[key] = desc
        else:
            self._items_filtered = self._items

    def print_preamble(self):
        self.console.print()
        if self._prompt:
            self.console.print(self._prompt)
        self.console.print("[dim]arrow keys move - type to filter - enter chooses - esc cancels")
        self.console.print()

    def run(self):
        self._done = False
        self._selected_index = 0
        self.print_preamble()

        try:
            with Live(self.generate(), console=self.console, auto_refresh=False) as live:
                while not self._done:
                    self.check_key()
                    live.update(self.generate())
                    live.refresh()
                return self.value
        except (KeyboardInterrupt, EOFError, QuitException):
            return None

    def check_key(self):
        items = tuple(self._items_filtered.keys())

        key = keys.getchar()
        if keys.is_esc(key):
            if self.filter:
                self.filter = ""
                self._selected_index = 0
                self.search()
                return
            raise QuitException()
        elif keys.is_ok(key) and items:
            self._done = True
            self.value = items[self._selected_index]
        elif keys.is_down(key):
            self._selected_index += 1
        elif keys.is_up(key):
            self._selected_index -= 1
        else:
            if keys.is_backspace(key):
                self.filter = self.filter[:-1]
                self._selected_index = 0
            else:
                self.filter += key.lower()
                self._selected_index = 0

            self.search()

        if self._selected_index >= len(items):
            self._selected_index = len(items) - 1
        if self._selected_index < 0:
            self._selected_index = 0

    def generate(self):
        table = Table(show_header=False, show_lines=False, show_edge=False, box=None, padding=0)
        table.add_column("selection")
        table.add_column("label")

        items = self._items_filtered.items()

        for index, (key, label) in enumerate(items):
            if self._done and not index == self._selected_index:
                continue
            if self._selected_index == index:
                if self._done:
                    table.add_row(" :heavy_check_mark: ", label, style="green")
                    table.add_row(" ", " ")
                else:
                    table.add_row(
                        " :arrow_forward: ",
                        "[underline]" + label + "[/underline]",
                        style="cyan",
                    )
            else:
                table.add_row("   ", label, style=None)

        if not items:
            table.add_row(" ", "  [italic]no items match that filter[/italic]")

        if not self._done:
            table.add_row(" ", " ")

            if self.filter:
                table.add_row("   ", ":magnifying_glass_tilted_left: " + self.filter)

            table.add_row(" ", " ")

        return table

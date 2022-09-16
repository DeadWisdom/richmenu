### Rich Menu

A menu component for command line interfaces based on the [Rich python library](https://github.com/Textualize/rich/).

![Basic features of the menu](/doc/demo.gif)

This is done with the following code:

```python
from rich.console import Console
from richmenu import Menu

console = Console()

selection = Menu.prompt(
    "[bold]Would you rather:[/bold]",
    items={
        "invisibility": "Be able to turn invisible",
        "fly": "Be able to fly",
        "read-minds": "Be able to read people's minds",
        "quit": "None of this nonsense",
    },
)

if selection is None or selection is "quit":
    console.print("[bold]:sparkles: quit[/bold]")
else:
    console.print(f"You have selected: [bold]{selection}[/bold]")
```

## Features

- Easily display a menu to the user
- Pressing up and down on the arrow keys changes the current item
- Pressing enter selects the current item, highlights it, and continues the interpreter
- Pressing esc exits the menu
- Typing letters filters the items for only items that match the given text
- Filters are matched using a search module `thefuzz` to mitigate typos

## OS Support

Tested on mac os, linux, and windows

Note: I couldn't figure out an easy way to automate tests with key inputs, so I just do it
manually for now.

## Python Support

I have as yet only tested Python 3.10, if you need something else please open up a github issue.

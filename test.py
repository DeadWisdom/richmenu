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

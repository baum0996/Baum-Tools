from __future__ import annotations

from collections.abc import Iterable

from rich import box
from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from constants import APP_NAME, APP_SUBTITLE, APP_VERSION
from utils import terminal_width


CRT_GREEN = "#00ff66"
CRT_DIM = "#0a7f35"
CRT_MUTED = "#6dff9b"
CRT_DANGER = "#ff3b3b"
CRT_WARNING = "#f5ff5c"
CRT_PANEL = "black on black"
CRT_PROMPT = f"[bold {CRT_GREEN}]>[/bold {CRT_GREEN}]"


def crt_rule(title: str = "") -> Rule:
    return Rule(title.upper() if title else "", style=CRT_DIM)


def crt_panel(
    renderable: RenderableType,
    title: str = "",
    border_style: str = CRT_GREEN,
    width: int | None = None,
    padding: tuple[int, int] = (1, 2),
) -> Panel:
    return Panel(
        renderable,
        title=f"[ {title.upper()} ]" if title else "",
        border_style=border_style,
        box=box.SQUARE,
        padding=padding,
        style=CRT_PANEL,
        width=width or min(terminal_width(), 120),
    )


def crt_header(module: str, status: str = "READY") -> Panel:
    banner = Text()
    banner.append(f"{APP_NAME}\n", style=f"bold {CRT_GREEN}")
    banner.append(APP_SUBTITLE.upper(), style=CRT_MUTED)

    meta = Table.grid(expand=True)
    meta.add_column(ratio=1)
    meta.add_column(justify="center", ratio=2)
    meta.add_column(justify="right", ratio=1)
    meta.add_row(
        Text(f"VERSION: {APP_VERSION}\nMODULE: {module.upper()}", style=CRT_MUTED),
        Align.center(banner),
        Text(f"STATUS: {status.upper()}", style=CRT_MUTED),
    )
    return crt_panel(meta, "", width=min(terminal_width(), 124), padding=(1, 1))


def crt_menu(title: str, rows: Iterable[tuple[str, str]]) -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right", style=f"bold {CRT_GREEN}", no_wrap=True)
    table.add_column(style=CRT_GREEN, no_wrap=True)
    table.add_column(style=CRT_MUTED)

    for key, label in rows:
        table.add_row(key.zfill(2), ">", label.upper())

    return crt_panel(Align.center(table), title, width=min(terminal_width(), 74))


def crt_footer(module: str, hint: str = "PRESS ENTER TO SELECT") -> Panel:
    footer = Table.grid(expand=True)
    footer.add_column(style=CRT_MUTED)
    footer.add_column(justify="center", style=CRT_MUTED)
    footer.add_column(justify="right", style=CRT_MUTED)
    footer.add_row(
        "(C) 2026 BAUM TOOLS",
        f"MODULE: {module.upper()}",
        hint.upper(),
    )
    return Panel(footer, border_style=CRT_DIM, box=box.SQUARE, style=CRT_PANEL)


def crt_data_table(title: str = "", show_header: bool = True) -> Table:
    return Table(
        title=f"[ {title.upper()} ]" if title else "",
        box=box.SQUARE,
        border_style=CRT_DIM,
        header_style=f"bold {CRT_GREEN}",
        style=CRT_PANEL,
        show_header=show_header,
    )


def crt_message(title: str, message: RenderableType, style: str = CRT_GREEN) -> Panel:
    renderable = Text(str(message), style=CRT_MUTED) if isinstance(message, str) else message
    return crt_panel(
        renderable,
        title,
        border_style=style,
        width=min(terminal_width(), 110),
    )


def crt_screen(title: str, module: str, body: RenderableType) -> Group:
    return Group(crt_header(module), crt_rule(title), body, crt_footer(module))

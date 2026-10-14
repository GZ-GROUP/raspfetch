#!/usr/bin/env python3
"""RASPFETCH interactive menu.

Each menu action runs its featureN.sh script in the current directory (the
working directory) and shows the output in a pop-up dialog.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.markup import escape
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Button, DirectoryTree, Input, OptionList, RichLog, Static, Tree
from textual.widgets.option_list import Option

from i18n import t, translator

SCRIPTS_DIR = Path(__file__).resolve().parent
TEAM = ["iangl2", "RAGG1911"]  # GitHub usernames

# --------------------------------------------------------------------------
# Raspberry Pi palette
# --------------------------------------------------------------------------
RASPBERRY = "#C51A4A"
LEAF = "#75A928"

THEME = Theme(
    name="raspberry",
    primary=RASPBERRY,
    secondary=LEAF,
    accent=LEAF,
    success=LEAF,
    warning="#F2B134",
    error="#FF4D6D",
    foreground="#E8E3E5",
    background="#0E0A0C",
    surface="#1B1316",
    panel="#261B20",
    dark=True,
)

# --------------------------------------------------------------------------
# opencode-style logo: block letters in 3 rows.
# --------------------------------------------------------------------------
FONT = {
    "R": ["█▀▀▄", "█▀▀▄", "▀  ▀"],
    "A": ["▄▀▀▄", "█▀▀█", "▀  ▀"],
    "S": ["▄▀▀▀", "▀▀▀▄", "▄▄▄▀"],
    "P": ["█▀▀▄", "█▀▀▀", "▀   "],
    "F": ["█▀▀▀", "█▀▀ ", "▀   "],
    "E": ["█▀▀▀", "█▀▀ ", "▀▀▀▀"],
    "T": ["▀▀█▀▀", "  █  ", "  ▀  "],
    "C": ["█▀▀▀", "█   ", "▀▀▀▀"],
    "H": ["█  █", "█▀▀█", "▀  ▀"],
}


def _word(word: str) -> list[str]:
    rows = ["", "", ""]
    for ch in word:
        glyph = FONT[ch]
        width = max(len(r) for r in glyph)
        for i in range(3):
            rows[i] += glyph[i].ljust(width) + " "
    return rows


def build_logo() -> str:
    left, right = _word("RASP"), _word("FETCH")
    logo = "\n".join(
        f"[{RASPBERRY}]{a}[/][bold {LEAF}]{b}[/]" for a, b in zip(left, right)
    )
    return f"{logo}\n\n[dim]{escape(t('app.subtitle', ', '.join(TEAM)))}[/]"


# --------------------------------------------------------------------------
# Menu actions. Names and descriptions come from locales/: feature<N>.name/.description
# --------------------------------------------------------------------------
FEATURES = [
    {"commands": ["hostname", "uname -r", "uptime -p"]},
    {"commands": ["free -m", "free -h"], "gauge": "mem"},
    {"commands": ["df -hP /", "df -h"], "gauge": "disk"},
    {"commands": ["ip -br address", "ip route"]},
    {"commands": ["ping -c 4 -W 2 <ip>"], "ask": "ip"},
    {"commands": ["vcgencmd measure_temp", "cat /sys/class/thermal/thermal_zone0/temp"], "gauge": "temp"},
    {"commands": ["ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu", "cat /proc/loadavg"]},
    {"commands": ["mkdir <parent>/<name>"], "ask": "directory"},
    {"commands": ["chmod u+r,u-w <file>", "chmod u+rw <file>", "ls -l <file>"], "ask": "permissions"},
    {"commands": ["date", "whoami", "hostname"]},
]

EXIT_ID = "exit"
MENU_ACTIONS = {"toggle_language", "quit"}
GAUGE_TITLES = {"mem": "gauge.memory", "disk": "gauge.disk", "temp": "gauge.temperature"}


def feature_name(index: int) -> str:
    return t(f"feature{index + 1}.name")


def run_script(number: int, *args: str) -> subprocess.CompletedProcess[str]:
    """Runs featureN.sh with the given arguments; stdout and stderr come back together."""
    env = {**os.environ, "RASPFETCH_LANG": translator.language, "RASPFETCH_TUI": "1"}
    return subprocess.run(
        ["bash", str(SCRIPTS_DIR / f"feature{number}.sh"), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        env=env,
    )


def split_output(output: str) -> tuple[list[str], dict[str, list[str]]]:
    """Separates the visible lines from the '@gauge <name> <values...>' lines."""
    lines: list[str] = []
    gauges: dict[str, list[str]] = {}
    for line in output.rstrip().splitlines():
        if line.startswith("@gauge "):
            name, *values = line.split()[1:]
            gauges[name] = values
        else:
            lines.append(line)
    return lines, gauges


def text_bar(pct: float, width: int = 20) -> str:
    """Draws a progress bar like [########............]."""
    filled = round(width * max(0.0, min(pct, 100.0)) / 100)
    return f"[{'#' * filled}{'.' * (width - filled)}]"


def thermometer(temp: float | None, rows: int = 5) -> str:
    """ASCII thermometer; temp=None means the sensor is not available."""
    level = 0 if temp is None else round(rows * max(0.0, min(temp, 85.0)) / 85.0)
    color = "grey50" if temp is None else LEAF if temp < 60 else "#F2B134" if temp < 75 else "#FF4D6D"
    lines = ["  ╭───╮"]
    for r in range(rows, 0, -1):
        lines.append(f"  │ [{color}]{'█' if r <= level else ' '}[/] │")
    lines += [" ╭─┴───┴─╮", f" │  [{color}]███[/]  │", " ╰───────╯"]
    return "\n".join(lines)


def render_gauge(kind: str, values: list[str] | None) -> str:
    """Builds the gauge content from the values reported by the script."""
    try:
        if kind == "temp":
            temp = None if not values or values[0] == "none" else float(values[0])
            label = t("gauge.no_sensor") if temp is None else f"{temp:.1f}°C"
            return f"{label}\n{thermometer(temp)}"
        used, total, pct = values or []
    except ValueError:
        return t("gauge.no_data")
    unit = " MB" if kind == "mem" else ""
    return f"{escape(text_bar(float(pct)))}\n{used} / {total}{unit} ({pct}%)"


def relative(path: Path, root: Path) -> str:
    """Path shown to the user, relative to the working directory."""
    return "./" if path == root else f"./{path.relative_to(root)}"


# --------------------------------------------------------------------------
# Dialogs
# --------------------------------------------------------------------------
class ProjectTree(DirectoryTree):
    """Working directory tree without hidden folders or the virtual environment."""

    IGNORED = {"venv", ".venv", "__pycache__", "locales"}

    def __init__(self, path: Path, dirs_only: bool = False, **kwargs) -> None:
        self.dirs_only = dirs_only
        super().__init__(path, **kwargs)

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [
            path
            for path in paths
            if not path.name.startswith(".")
            and path.name not in self.IGNORED
            and (not self.dirs_only or path.is_dir())
        ]


class TextPrompt(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "dismiss(None)", show=False)]

    def __init__(self, prompt: str, placeholder: str = "") -> None:
        super().__init__()
        self.prompt = prompt
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static(self.prompt)
            yield Input(placeholder=self.placeholder)
            yield Static(f"[dim]{t('hint.text_dialog')}[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())


class DirectoryDialog(ModalScreen[tuple[str, str] | None]):
    """Pick the parent folder in a tree and type the name of the new folder."""

    BINDINGS = [Binding("escape", "dismiss(None)", show=False)]

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root
        self.parent_dir = root

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog wide"):
            yield Static(f"[b]{escape(feature_name(7))}[/]\n{escape(t('dialog.directory_intro'))}")
            yield ProjectTree(self.root, dirs_only=True)
            yield Static(id="selected")
            yield Input(placeholder="my_folder")
            with Horizontal(classes="buttons"):
                yield Button(t("button.create"), variant="success", id="ok")
                yield Button(t("button.cancel"), id="cancel")
            yield Static(f"[dim]{t('hint.directory_dialog')}[/]")

    def on_mount(self) -> None:
        self.show_selection()

    def show_selection(self) -> None:
        self.query_one("#selected", Static).update(
            f"[b {LEAF}]{escape(t('dialog.destination'))}[/] {escape(relative(self.parent_dir, self.root))}"
        )

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        if event.node.data is not None:
            self.parent_dir = event.node.data.path
            self.show_selection()

    def accept(self) -> None:
        self.dismiss((self.query_one(Input).value.strip(), str(self.parent_dir)))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.accept()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.accept()
        else:
            self.dismiss(None)


class PermissionDialog(ModalScreen[tuple[str, str] | None]):
    """Pick a file in a tree and the permission for its owner."""

    BINDINGS = [Binding("escape", "dismiss(None)", show=False)]

    def __init__(self, root: Path, default_file: Path) -> None:
        super().__init__()
        self.root = root
        self.file = default_file

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog wide"):
            yield Static(f"[b]{escape(feature_name(8))}[/]\n{escape(t('dialog.permission_intro'))}")
            yield ProjectTree(self.root)
            yield Static(id="selected")
            with Horizontal(classes="buttons"):
                yield Button(t("button.read_only"), variant="warning", id="read")
                yield Button(t("button.read_write"), variant="success", id="readwrite")
                yield Button(t("button.cancel"), id="cancel")
            yield Static(f"[dim]{t('hint.permission_dialog')}[/]")

    def on_mount(self) -> None:
        self.show_selection()

    def show_selection(self) -> None:
        self.query_one("#selected", Static).update(
            f"[b {LEAF}]{escape(t('dialog.file'))}[/] {escape(relative(self.file, self.root))}"
        )

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        # Only files can be selected; folders are just browsed.
        if event.node.data is not None and event.node.data.path.is_file():
            self.file = event.node.data.path
            self.show_selection()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ("read", "readwrite"):
            self.dismiss((str(self.file), event.button.id))
        else:
            self.dismiss(None)


class ResultDialog(ModalScreen[None]):
    """Pop-up that runs an action and shows its output (and gauge, if any)."""

    BINDINGS = [Binding("escape", "dismiss(None)", show=False)]

    def __init__(self, index: int, args: tuple[str, ...] = (), result: subprocess.CompletedProcess[str] | None = None) -> None:
        super().__init__()
        self.index = index
        self.args = args
        self.result = result
        self.gauge = FEATURES[index].get("gauge")

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog result"):
            yield Static(f"[b]{self.index + 1}. {escape(feature_name(self.index))}[/]")
            with Horizontal(id="result-body"):
                # No wrapping: tables (free, df, ps) keep their columns and scroll sideways.
                yield RichLog(id="output", markup=True)
                yield Static(id="gauge")
            with Horizontal(classes="buttons"):
                yield Button(t("button.close"), variant="primary", id="close")
                yield Static(f"[dim]{t('hint.result_dialog')}[/]", id="result-hint")

    def on_mount(self) -> None:
        gauge = self.query_one("#gauge", Static)
        gauge.display = self.gauge is not None
        if self.gauge:
            gauge.border_title = t(GAUGE_TITLES[self.gauge])
        output = self.query_one("#output", RichLog)
        output.focus()
        if self.result is not None:
            self.show_result(self.result)
        else:
            output.write(f"[dim]{t('result.running')}[/]")
            self.run_action()

    @work(exclusive=True)
    async def run_action(self) -> None:
        # Runs in a worker of this dialog: closing the dialog cancels it.
        try:
            result = await asyncio.to_thread(run_script, self.index + 1, *self.args)
        except OSError as exc:
            self.query_one("#output", RichLog).write(f"[bold red]{escape(str(exc))}[/]")
            return
        self.show_result(result)

    def show_result(self, result: subprocess.CompletedProcess[str]) -> None:
        lines, gauges = split_output(result.stdout)
        output = self.query_one("#output", RichLog)
        output.clear()
        error_prefix = f"{t('error.prefix')}:"
        for line in lines or [t("result.no_output")]:
            output.write(f"[bold red]{escape(line)}[/]" if line.startswith(error_prefix) else escape(line))
        if result.returncode != 0:
            output.write(f"\n[{RASPBERRY}]{escape(t('result.exit_code', result.returncode))}[/]")
        if self.gauge:
            self.query_one("#gauge", Static).update(render_gauge(self.gauge, gauges.get(self.gauge)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


# --------------------------------------------------------------------------
# Application
# --------------------------------------------------------------------------
class RASPFETCH(App):
    TITLE = "RASPFETCH"

    CSS = """
    Screen { background: $background; align-horizontal: center; }

    #logo {
        height: 7; width: 100%;
        content-align: center middle; text-align: center;
    }

    #body { height: 1fr; width: 100%; max-width: 150; padding: 0 2; }

    #menu, #detail {
        background: $surface; border: round $primary; padding: 0 1;
    }
    /* Minimum widths: on narrow terminals the menu text would get 0 columns. */
    #menu   { width: 2fr; min-width: 26; }
    #detail { width: 3fr; min-width: 20; }
    #menu > .option-list--option-highlighted,
    #menu:focus > .option-list--option-highlighted {
        background: $primary; color: white; text-style: bold;
    }
    #menu > .option-list--option { padding: 0 1; }

    #statusbar { dock: bottom; height: 1; padding: 0 2; }
    #cwd  { width: 1fr; color: $text-muted; }
    #hints { width: auto; margin-left: 2; }

    ModalScreen { align: center middle; background: $background 70%; }
    .dialog {
        width: 50; max-width: 100%; height: auto; max-height: 100%; padding: 1 2;
        background: $surface; border: thick $primary;
    }
    .dialog.wide { width: 70; }
    .dialog Input { margin: 1 0; }
    .dialog DirectoryTree { height: 14; margin: 1 0 0 0; background: $panel; }
    .dialog .buttons { height: auto; margin: 1 0 0 0; }
    .dialog .buttons Button { margin-right: 1; }

    .dialog.result { width: 95%; max-width: 130; height: 90%; padding: 0 1; }
    #result-body { height: 1fr; margin: 1 0 0 0; }
    #output { width: 1fr; min-width: 20; background: $panel; }
    #gauge {
        width: 28; height: auto; margin-left: 1;
        background: $surface; border: round $secondary; padding: 0 1;
    }
    #result-hint { width: 1fr; height: 3; content-align: right middle; }
    """

    BINDINGS = [
        Binding("l", "toggle_language", "Language", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Static(id="logo")
        with Horizontal(id="body"):
            yield OptionList(id="menu")
            yield Static(id="detail")
        with Horizontal(id="statusbar"):
            yield Static(str(Path.cwd()), id="cwd")
            yield Static(id="hints")

    def on_mount(self) -> None:
        self.register_theme(THEME)
        self.theme = "raspberry"
        self.refresh_texts()
        self.query_one("#menu", OptionList).focus()

    def refresh_texts(self) -> None:
        """(Re)writes every translated text of the main screen."""
        menu = self.query_one("#menu", OptionList)
        highlighted = menu.highlighted or 0
        menu.clear_options()
        menu.add_options(
            [Option(f"{index + 1}. {escape(feature_name(index))}", id=str(index)) for index in range(len(FEATURES))]
            + [None, Option(f"0. {escape(t('exit.name'))}", id=EXIT_ID)]
        )
        menu.highlighted = highlighted
        menu.border_title = t("panel.menu")
        self.query_one("#detail").border_title = t("panel.description")
        self.query_one("#logo", Static).update(build_logo())
        self.query_one("#hints", Static).update(
            f"[b]↑↓[/b] [dim]{t('hint.navigate')}[/]  [b]enter[/b] [dim]{t('hint.run')}[/]  "
            f"[b]l[/b] [dim]{t('hint.language')} ({escape(t('language.name'))})[/]  "
            f"[b]q[/b] [dim]{t('hint.quit')}[/]"
        )
        option = menu.get_option_at_index(highlighted)
        self.show_detail(option.id)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        # While a dialog is open, the main screen keys do not apply.
        if action in MENU_ACTIONS and isinstance(self.screen, ModalScreen):
            return False
        return True

    def action_toggle_language(self) -> None:
        translator.next_language()
        self.refresh_texts()

    def show_detail(self, option_id: str | None) -> None:
        detail = self.query_one("#detail", Static)
        if option_id == EXIT_ID:
            detail.update(f"[b]{escape(t('exit.name'))}[/]\n\n{escape(t('exit.description'))}")
            return
        index = int(option_id or "0")
        commands = "\n".join(f"  [b {LEAF}]$[/] {escape(command)}" for command in FEATURES[index]["commands"])
        detail.update(
            f"[b]{escape(feature_name(index))}[/]\n\n{escape(t(f'feature{index + 1}.description'))}\n\n"
            f"[b {RASPBERRY}]{escape(t('panel.script'))}[/]\n  feature{index + 1}.sh\n\n"
            f"[b {RASPBERRY}]{escape(t('panel.commands'))}[/]\n{commands}"
        )

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "menu":
            self.show_detail(event.option.id)

    def show_result(self, index: int, *args: str) -> None:
        self.push_screen(ResultDialog(index, args))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "menu":
            return
        if event.option.id == EXIT_ID:
            self.exit()
            return

        index = int(event.option.id or "0")
        ask = FEATURES[index].get("ask")
        root = Path.cwd()

        if ask == "ip":
            self.push_screen(
                TextPrompt(t("dialog.ip_prompt"), "192.168.1.10"),
                lambda ip: self.show_result(index, ip) if ip is not None else None,
            )
        elif ask == "directory":
            self.push_screen(
                DirectoryDialog(root),
                lambda choice: self.show_result(index, *choice) if choice else None,
            )
        elif ask == "permissions":
            # feature9.sh without arguments creates the test file and prints its path.
            prepared = run_script(index + 1)
            if prepared.returncode != 0:
                self.push_screen(ResultDialog(index, result=prepared))
                return
            self.push_screen(
                PermissionDialog(root, Path(prepared.stdout.strip())),
                lambda choice: self.show_result(index, *choice) if choice else None,
            )
        else:
            self.show_result(index)


if __name__ == "__main__":
    RASPFETCH().run()

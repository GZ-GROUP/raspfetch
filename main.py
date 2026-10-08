#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.markup import escape
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Button, Input, Label, LoadingIndicator, OptionList, RichLog, Static
from textual.widgets.option_list import Option

# --------------------------------------------------------------------------
# Paleta Raspberry Pi
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
# Logo estilo opencode: letras de bloque en 3 filas.
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
    return "\n".join(
        f"[{RASPBERRY}]{a}[/][bold {LEAF}]{b}[/]" for a, b in zip(left, right)
    )


# --------------------------------------------------------------------------
# Datos de las funciones
# --------------------------------------------------------------------------
FUNCTIONS = [
    {
        "name": "Información del sistema",
        "desc": "Muestra nombre del equipo, versión del kernel y tiempo de funcionamiento.",
        "cmds": ["hostname", "uname -a", "uptime"],
        "ask": None,
        "gauge": None,
        "script": "./feature1.sh",
    },
    {
        "name": "Diagnóstico de memoria",
        "desc": "Consulta la memoria RAM total, utilizada y disponible.",
        "cmds": ["free -h"],
        "ask": None,
        "gauge": "#mem",
        "script": "./feature2.sh",
    },
    {
        "name": "Diagnóstico de almacenamiento",
        "desc": "Muestra el espacio utilizado y disponible en los sistemas de archivos.",
        "cmds": ["df -h"],
        "ask": None,
        "gauge": "#disk",
        "script": "./feature3.sh",
    },
    {
        "name": "Configuración de red",
        "desc": "Consulta interfaces de red, direcciones IP y rutas configuradas.",
        "cmds": ["ip -br addr", "ip route"],
        "ask": None,
        "gauge": None,
        "script": "./feature4.sh",
    },
    {
        "name": "Prueba de conectividad",
        "desc": "Solicita la IP de otro equipo de la LAN y comprueba si responde.",
        "cmds": ["ping -c 4 <ip>"],
        "ask": "text",
        "gauge": None,
        "script": "./feature5.sh",
        "prompt": "IP del equipo a probar:",
        "placeholder": "192.168.1.1",
    },
    {
        "name": "Temperatura del procesador",
        "desc": "Muestra la temperatura en °C o indica que el sensor no está disponible.",
        "cmds": ["vcgencmd measure_temp"],
        "ask": None,
        "gauge": "#temp",
        "script": "./feature6.sh",
    },
    {
        "name": "Procesos activos",
        "desc": "Muestra procesos en ejecución e identifica su consumo de recursos.",
        "cmds": ["ps aux --sort=-%cpu | head"],
        "ask": None,
        "gauge": None,
        "script": "./feature7.sh",
    },
    {
        "name": "Creación de directorios",
        "desc": "Solicita un nombre y crea una carpeta dentro del directorio de trabajo del proyecto.",
        "cmds": ["mkdir <nombre>"],
        "ask": "text",
        "gauge": None,
        "script": "./feature8.sh",
        "prompt": "Nombre del directorio:",
        "placeholder": "mi_carpeta",
    },
    {
        "name": "Configuración de permisos",
        "desc": "Permite elegir entre solo lectura o lectura y escritura para el propietario de un archivo de prueba.",
        "cmds": ["chmod 400 <archivo>", "chmod 600 <archivo>"],
        "ask": "choice",
        "gauge": None,
        "script": "./feature9.sh",
        "prompt": "Permisos del propietario:",
        "choices": ["Solo lectura (400)", "Lectura y escritura (600)"],
    },
    {
        "name": "Informe de diagnóstico",
        "desc": "Guarda en un archivo de texto un resumen del estado del equipo: fecha, usuario y nombre de la Raspberry Pi.",
        "cmds": ["date", "whoami", "hostname"],
        "ask": None,
        "gauge": None,
        "script": "./feature10.sh",
    },
]

GAUGES = ("#mem", "#disk", "#temp")


def text_bar(pct: float, width: int = 20) -> str:
    """Dibuja una barra de progreso tipo [########............]."""
    filled = round(width * max(0.0, min(pct, 100.0)) / 100)
    return f"[{'#' * filled}{'.' * (width - filled)}]"


def thermometer(temp: float | None, rows: int = 5) -> str:
    """Termómetro ASCII; temp=None -> sensor no disponible."""
    level = 0 if temp is None else round(rows * max(0.0, min(temp, 85.0)) / 85.0)
    color = "grey50" if temp is None else LEAF if temp < 60 else "#F2B134" if temp < 75 else "#FF4D6D"
    lines = ["  ╭───╮"]
    for r in range(rows, 0, -1):
        lines.append(f"  │ [{color}]{'█' if r <= level else ' '}[/] │")
    lines += [" ╭─┴───┴─╮", f" │  [{color}]███[/]  │", " ╰───────╯"]
    return "\n".join(lines)


class TextPrompt(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "dismiss(None)", "Cancelar")]

    def __init__(self, prompt: str, placeholder: str = "") -> None:
        super().__init__()
        self.prompt = prompt
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static(self.prompt)
            yield Input(placeholder=self.placeholder)
            yield Static("[dim]enter aceptar · esc cancelar[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)


class ChoicePrompt(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "dismiss(None)", "Cancelar")]

    def __init__(self, prompt: str, choices: list[str]) -> None:
        super().__init__()
        self.prompt = prompt
        self.choices = choices

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static(self.prompt)
            yield OptionList(*[Option(choice, id=str(idx)) for idx, choice in enumerate(self.choices)])
            yield Static("[dim]↑↓ elegir · enter aceptar · esc cancelar[/]")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(self.choices[event.option_index])


class InputBox(ModalScreen[str | None]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self.message)
            yield Input(placeholder="Escribe aquí...", id="user_input")
            yield Button("Aceptar", id="accept")
            yield Button("Cancelar", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "accept":
            value = self.query_one("#user_input", Input).value.strip()
            self.dismiss(value or None)
        else:
            self.dismiss(None)


class LoadingBox(ModalScreen[None]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield LoadingIndicator()
            yield Label(self.message)


class MessageBox(ModalScreen[None]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static(self.message)
            yield Button("Cerrar", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss(None)


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
    #menu   { width: 2fr; }
    #detail { width: 3fr; }
    #menu > .option-list--option-highlighted,
    #menu:focus > .option-list--option-highlighted {
        background: $primary; color: white; text-style: bold;
    }
    #menu > .option-list--option { padding: 0 1; }

    #info {
        display: none; width: 2fr;
        background: $surface; border: round $secondary; padding: 0 1;
    }
    #gauges { display: none; width: 30; }
    .gauge { display: none; background: $surface; border: round $secondary; padding: 0 1; }
    #mem, #disk { height: 5; }
    #temp { height: 12; }

    #statusbar { dock: bottom; height: 1; padding: 0 2; }
    #cwd  { width: 1fr; color: $text-muted; }
    #hints { width: auto; }

    ModalScreen { align: center middle; background: $background 70%; }
    .dialog {
        width: 50; height: auto; padding: 1 2;
        background: $surface; border: thick $primary;
    }
    .dialog Input { margin: 1 0; }
    .dialog OptionList { margin: 1 0; height: auto; background: $surface; }
    """

    BINDINGS = [
        Binding("up", "menu_up", "Arriba", show=False),
        Binding("down", "menu_down", "Abajo", show=False),
        Binding("enter", "menu_run", "Ejecutar", show=False),
        Binding("escape", "close_panels", "Cerrar", show=False),
        Binding("q", "quit", "Salir", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Static(build_logo(), id="logo")
        with Horizontal(id="body"):
            yield OptionList(
                *[Option(f"{index + 1}. {func['name']}", id=str(index)) for index, func in enumerate(FUNCTIONS)],
                id="menu",
            )
            yield Static(id="detail")
            yield RichLog(id="info", wrap=True, markup=True)
            with Vertical(id="gauges"):
                yield Static(id="mem", classes="gauge")
                yield Static(id="disk", classes="gauge")
                yield Static(id="temp", classes="gauge")
        with Horizontal(id="statusbar"):
            yield Static(os.getcwd(), id="cwd")
            yield Static(
                "[b]↑↓[/b] [dim]navegar[/]  [b]enter[/b] [dim]ejecutar[/]  "
                "[b]esc[/b] [dim]cerrar[/]  [b]q[/b] [dim]salir[/]",
                id="hints",
            )

    def on_mount(self) -> None:
        self.register_theme(THEME)
        self.theme = "raspberry"
        self.query_one("#menu").border_title = "Funciones"
        self.query_one("#detail").border_title = "Descripción"
        self.query_one("#info").border_title = "Info"
        self.query_one("#mem").border_title = "Memoria en uso"
        self.query_one("#disk").border_title = "Almacenamiento en uso"
        self.query_one("#temp").border_title = "Temperatura"
        self.query_one("#menu", OptionList).focus()
        self.show_detail(0)

    def action_menu_up(self) -> None:
        self.query_one("#menu", OptionList).action_cursor_up()

    def action_menu_down(self) -> None:
        self.query_one("#menu", OptionList).action_cursor_down()

    def action_menu_run(self) -> None:
        self.query_one("#menu", OptionList).action_select()

    def action_close_panels(self) -> None:
        self.query_one("#info").display = False
        self.query_one("#gauges").display = False

    def show_detail(self, index: int) -> None:
        func = FUNCTIONS[index]
        cmds = "\n".join(f"  [b {LEAF}]$[/] {escape(command)}" for command in func["cmds"])
        self.query_one("#detail", Static).update(
            f"[b]{func['name']}[/]\n\n{func['desc']}\n\n[b {RASPBERRY}]Comandos[/]\n{cmds}"
        )

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "menu" and event.option is not None and event.option.id is not None:
            self.show_detail(int(event.option.id))

    def refresh_gauge(self, which: str) -> None:
        if which == "#mem":
            pct, txt = 42.0, "1.6 GB / 3.8 GB"
            self.query_one(which, Static).update(f"{escape(text_bar(pct))}\n{txt}")
        elif which == "#disk":
            pct, txt = 63.0, "18 GB / 29 GB"
            self.query_one(which, Static).update(f"{escape(text_bar(pct))}\n{txt}")
        elif which == "#temp":
            temp = 52.1
            label = "?°C" if temp is None else f"{temp:.1f}°C"
            self.query_one(which, Static).update(f"{label}\n{thermometer(temp)}")

    def reveal(self, idx: int) -> None:
        self.query_one("#info").display = True
        target = FUNCTIONS[idx]["gauge"]
        for gauge in GAUGES:
            self.query_one(gauge).display = gauge == target
        self.query_one("#gauges").display = target is not None
        if target:
            self.refresh_gauge(target)

    def _build_command(self, idx: int, arg: str | None = None) -> list[str]:
        func = FUNCTIONS[idx]
        script = func.get("script")
        if script:
            cmd = ["bash", script]
            if arg:
                cmd.append(arg)
            return cmd
        if arg:
            resolved = "\n".join(
                command.replace("<ip>", arg).replace("<nombre>", arg).replace("<archivo>", arg)
                for command in func["cmds"]
            )
            return ["bash", "-lc", resolved]
        return ["bash", "-lc", " && ".join(func["cmds"])]

    async def run_function(self, idx: int, arg: str | None = None) -> None:
        func = FUNCTIONS[idx]
        self.reveal(idx)
        log = self.query_one("#info", RichLog)
        log.clear()
        log.write(f"[b]{idx + 1}. {func['name']}[/]")
        if arg:
            log.write(f"[{LEAF}]Entrada:[/] {escape(arg)}")

        command = self._build_command(idx, arg)
        try:
            result = await asyncio.to_thread(subprocess.run, command, capture_output=True, text=True, check=False)
        except OSError as exc:
            log.write(f"[bold red]Error:[/] {escape(str(exc))}")
            return

        output = result.stdout.strip() if result.returncode == 0 else (result.stderr or result.stdout).strip()
        if not output:
            output = "Comando ejecutado sin salida." if result.returncode == 0 else f"Comando finalizado con código {result.returncode}."
        log.write(escape(output))

    def _trigger_for_selected(self, idx: int, value: str | None) -> None:
        if value is not None:
            asyncio.create_task(self.run_function(idx, value))
        elif FUNCTIONS[idx].get("ask") is None:
            asyncio.create_task(self.run_function(idx))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "menu":
            return

        idx = int(event.option.id or "0")
        func = FUNCTIONS[idx]
        ask = func.get("ask")

        if ask == "text":
            self.push_screen(
                TextPrompt(func.get("prompt", "Introduce un valor."), func.get("placeholder", "")),
                lambda value: self._trigger_for_selected(idx, value),
            )
        elif ask == "choice":
            self.push_screen(
                ChoicePrompt(func.get("prompt", "Elige una opción."), func.get("choices", [])),
                lambda value: self._trigger_for_selected(idx, value),
            )
        else:
            asyncio.create_task(self.run_function(idx))


if __name__ == "__main__":
    RASPFETCH().run()

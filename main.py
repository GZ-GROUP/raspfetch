import asyncio
import subprocess
from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label, LoadingIndicator, Static, OptionList
from textual.widgets.option_list import Option
from textual.screen import ModalScreen
from textual.containers import Container
from textual.widgets import Input
from textual import on, work

@dataclass
class menuItem:
    name: str
    cmd: str
    interactive: bool = False
    input_required: bool = False
    prompt: str = ""

COMMANDS = [
    menuItem("System Info", "./feature1.sh"),
    menuItem("RAM Usage", "./feature2.sh"),
    menuItem("Disk Usage", "./feature3.sh"),
    menuItem("Network Info", "./feature4.sh"),
    menuItem("Ping Host", "./feature5.sh", input_required=True, prompt="Enter host to ping"),
    menuItem("CPU Temp", "./feature6.sh"),
    menuItem("Running Processes", "./feature7.sh"),
    menuItem("Create Directory", "./feature8.sh", input_required=True, prompt="Enter directory name"),
    menuItem("Generate Report", "./feature10.sh")
]
#TODO: Add InputBox
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
            value = self.query_one("#user_input", Input).value
            self.dismiss(value)
        else:
            self.dismiss(None)

#Boilerplate code for a simple modal message box
class MessageBox(ModalScreen[bool]):
    """Un cuadro de mensaje modal simple de tipo Sí/No."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self.message)
            yield Button("Cerrar", variant="error", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
            self.dismiss(True)

class LoadingBox(ModalScreen[None]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield LoadingIndicator()
            yield Label(self.message)

class RASPFETCH(App):

    CSS = """
    Screen {
        align: center middle;
    }
    """

    
    def compose(self) -> ComposeResult:
            yield Static("RASPFETCH", id="mainTitle")

            # With this element you make the list of options to select from
            yield OptionList(
                *[Option(item.name, id=item.cmd) for item in COMMANDS]
            )

    #Async function to run the command selected by the user
    @work
    async def run_command(self, selectedOption: int) -> None:
        if 0 <= selectedOption < len(COMMANDS):
            selectedItem = COMMANDS[selectedOption]
        else:
            return
        user_input = None
        if selectedItem.input_required:
            user_input = await self.push_screen_wait(
                InputBox(selectedItem.prompt)
            )
            if user_input is None:
                return

        args = ["bash", selectedItem.cmd]
        if user_input is not None:
            args.append(user_input)

        await self.push_screen(LoadingBox(f"Ejecutando {selectedItem.name}..."))
        try:
            result = await asyncio.to_thread(
                subprocess.run, args, capture_output=True, text=True
            )
        except OSError as error:
            output = f"No se pudo ejecutar el comando: {error}"
        else:
            output = result.stdout if result.returncode == 0 else result.stderr or result.stdout

        await self.pop_screen()
        self.push_screen(MessageBox(output))
    #Event handler
    @on(OptionList.OptionSelected)
    def option_selected(self, event: OptionList.OptionSelected) -> None:
        self.run_command(event.option_index)
    

RASPFETCH().run()
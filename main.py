from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Label, Static, OptionList
from textual.widgets.option_list import Option
from textual.screen import ModalScreen
from textual.containers import Container
from textual import on
from dataclasses import dataclass

@dataclass
class menuItem:
    name: str
    cmd: str
    interactive: bool = False
    input_required: bool = False

COMANDOS = [
    menuItem("System Info", "./feature1.sh"),
]
#TODO: Add InputBox
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
                *[Option(item.name, id=item.cmd) for item in COMANDOS]
            )

    #Async function to run the command selected by the user
    async def run_command(self, selectedOption: int) -> None:
        import subprocess
        if 0 <= selectedOption < len(COMANDOS):
            selectedItem = COMANDOS[selectedOption]
        else:
            return
        cmd = selectedItem.cmd
        if selectedItem.input_required:
            # TODO: Implement input handling  
            # when input is captured  just concatenate the result to the command 
            #   like this: cmd += " " + user_input
            pass

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout if result.returncode == 0 else result.stderr
        self.push_screen(MessageBox(output))
    #Event handler
    @on(OptionList.OptionSelected)
    async def option_selected(self, event: OptionList.OptionSelected) -> None:
        await self.run_command(event.option_index)
    

RASPFETCH().run()
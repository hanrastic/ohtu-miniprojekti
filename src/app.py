import sys
from ui.app_ui import app_ui

class App:
    def __init__(self, ui=app_ui):
        self.ui = ui

    def run(self):
        self.ui.welcome()
        while True:

            command = self.ui.read_input()
            self.ui.parse_command(command)
            self.ui.execute_command()

app = App()

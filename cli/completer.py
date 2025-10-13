from prompt_toolkit.completion import Completer, Completion

class MimirCompleter(Completer):
    def __init__(self, commands):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lstrip()
        if " " not in text and not text.startswith(" "):
            for cmd in self.commands:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
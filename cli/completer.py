from prompt_toolkit.completion import Completer, Completion

class MimirCompleter(Completer):
    def __init__(self, commands):
        self.commands = commands

        self.subcommands = {
            "case": ["-n", "-o", "-c"],
            "hash": ["-h"],
            "lookup": [],
            "ipcheck": [],
            "urlcheck": [],
        }

    def get_completions(self, document, complete_event):

        text = document.text_before_cursor.lstrip()
        words = text.split()

        if not words:
            for cmd in self.commands:
                yield Completion(cmd, start_position=0)
            return

        if len(words) == 1 and not text.endswith(" "):
            current = words[0].lower()
            for cmd in self.commands:
                if cmd.lower().startswith(current):
                    yield Completion(cmd, start_position=-len(current))
            return

        if len(words) >= 2:
            main_cmd = words[0].lower()
            if main_cmd in self.subcommands and not text.endswith(" "):
                last = words[-1]
                for opt in self.subcommands[main_cmd]:
                    if opt.startswith(last):
                        yield Completion(opt, start_position=-len(last))
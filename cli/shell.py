import os
import getpass
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from .history import HistoryManager
from .handler import CommandHandler
from .case import CaseManager
from .prompt import Prompt
from .completer import MimirCompleter
from integrations import abuseIPDB, urlHaus, malwareBazaar
import shlex

def mimir():
    path = os.path.expanduser(os.getenv("MIMIR_PATH"))
    history_file = os.path.expanduser(os.getenv("MIMIR_HIST"))
    user = getpass.getuser()

    commands = ['help', 'exit', 'hash', 'ipcheck', 'clear', 'mhistory', 'urlcheck', 'case']
    integrations = {
        "malwareBazaar": malwareBazaar,
        "abuseIPDB": abuseIPDB,
        "urlHaus": urlHaus
    }
    completer = MimirCompleter(commands)
    case_manager = CaseManager(path)
    history_manager = HistoryManager(history_file)
    command_handler = CommandHandler(history_manager, integrations)
    current_case = None

    while True:
        prompt = Prompt.get_prompt(user, current_case)
        session = PromptSession(message=prompt, history=FileHistory(history_file), completer=completer)
        try:
            raw = session.prompt().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Mimir...")
            break
        if not raw:
            continue
        history_manager.save_history(raw)
        try:
            parts = shlex.split(raw)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            continue
        if not parts:
            continue
        command, *args = parts
        continue_shell, current_case = command_handler.execute(command, args, case_manager, current_case)
        if not continue_shell:
            break


if __name__ == "__main__":
    mimir()

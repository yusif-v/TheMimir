import os
import getpass
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from cli.history import HistoryManager
from .handler import CommandHandler
from .case import CaseManager
from .prompt import Prompt
from .completer import MimirCompleter
from integrations import abuseIPDB, urlHaus, malwareBazaar

try:
    from .setup import SetupManager
except ImportError:
    SetupManager = None


def mimir():
    base_path = os.path.expanduser(os.getenv("MIMIR_PATH", "~/Mimir"))
    history_file = os.path.expanduser(os.getenv("MIMIR_HIST", "~/.mimir_history"))
    user = getpass.getuser()

    if SetupManager:
        setup = SetupManager()
        success, messages = setup.setup()
        if messages and not success:
            # Only print setup warnings/errors
            print("\n--- Mimir Setup Diagnostics ---")
            for msg in messages:
                print(msg)
            print("-------------------------------\n")

    commands = [
        "help", "exit", "clear", "mhistory",
        "case", "hash", "ipcheck", "urlcheck", "lookup"
    ]
    integrations = {
        "malwareBazaar": malwareBazaar,
        "abuseIPDB": abuseIPDB,
        "urlHaus": urlHaus
    }

    completer = MimirCompleter(commands)
    history_manager = HistoryManager(history_file)
    case_manager = CaseManager(base_path)
    command_handler = CommandHandler(history_manager, integrations)

    # === Persistent session ===
    session = PromptSession(
        message="",
        history=FileHistory(history_file),
        completer=completer
    )

    print("🧠 Welcome to Mimir — Forensic Terminal v0.3")
    print("Type 'help' for available commands.\n")

    current_case = None

    while True:
        prompt_text = Prompt.get_prompt(user, case_manager.current_case)
        session.message = prompt_text

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
            print(f"[!] Error parsing command: {e}")
            continue

        if not parts:
            continue

        command, *args = parts

        try:
            continue_shell, current_case = command_handler.execute(
                command, args, case_manager, current_case
            )
            if not continue_shell:
                break
        except Exception as e:
            print(f"[!] Command error: {e}")


if __name__ == "__main__":
    mimir()
import os
import getpass
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from .history import HistoryManager
from .handler import CommandHandler
from .case import CaseManager
from .prompt import Prompt
from .completer import MimirCompleter
from integrations import abuseIPDB, urlHaus, malwareBazaar

def mimir():
    # === Environment setup ===
    base_path = os.path.expanduser(os.getenv("MIMIR_PATH", "~/Mimir"))
    history_file = os.path.expanduser(os.getenv("MIMIR_HIST", "~/.mimir_history"))
    user = getpass.getuser()

    # === Core components ===
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
        # Dynamic prompt
        prompt_text = Prompt.get_prompt(user, case_manager.current_case)
        session.message = prompt_text

        try:
            raw = session.prompt().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Mimir...")
            break

        if not raw:
            continue

        # Save to history
        history_manager.save_history(raw)

        try:
            parts = shlex.split(raw)
        except ValueError as e:
            print(f"Error parsing command: {e}")
            continue

        if not parts:
            continue

        command, *args = parts

        # === Built-in commands ===
        if command in ("exit", "quit"):
            print("Goodbye, examiner.")
            break

        elif command == "clear":
            os.system("clear" if os.name == "posix" else "cls")
            continue

        elif command == "help":
            print("""Available commands:
  case create <name>       Create new forensic case
  case open <name>         Open existing case
  case close               Close current case
  case list                List all cases
  case info [name]         Show case metadata
  hash <file>              Compute file hashes
  ipcheck <ip>             Lookup IP in AbuseIPDB
  urlcheck <url>           Lookup URL in URLHaus
  lookup <artifact>        Auto-detect and lookup hash/IP/URL
  clear                    Clear the screen
  mhistory                 Show command history
  exit / quit              Exit the shell
""")
            continue

        elif command == "case":
            if not args:
                print("Usage: case <create|open|close|list|info> [name]")
                continue

            action = args[0]
            case_name = args[1] if len(args) > 1 else None
            result = case_manager.handle(case_name, action)
            current_case = result or case_manager.current_case
            continue

        # === Delegate other commands to CommandHandler ===
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
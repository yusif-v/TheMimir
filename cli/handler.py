import os
import subprocess
from typing import Dict, Tuple, Any
from .history import HistoryManager
import logging

logger = logging.getLogger("Mimir")
logger.setLevel(logging.INFO)
logfile = os.path.expanduser("~/Mimir/Logs/mimir.log")
os.makedirs(os.path.dirname(logfile), exist_ok=True)
handler = logging.FileHandler(logfile)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class CommandHandler:
    def __init__(self, history_manager: HistoryManager, integrations: Dict[str, Any]):
        self.history_manager = history_manager
        self.integrations = integrations
        self.commands = {
            "help": self.help,
            "exit": self.exit,
            "clear": self.clear,
            "mhistory": self.mhistory,
            "hash": self.hash,
            "ipcheck": self.ipcheck,
            "urlcheck": self.urlcheck,
            "lookup": self.lookup,
            "case": self.case
        }

    # ---------------------------------------------------------
    # Core shell commands
    # ---------------------------------------------------------
    @staticmethod
    def help() -> None:
        print("""Available commands:
  case -n <name>         Create a new case
  case -o <name>         Open an existing case
  case -c <name>         Close the current case
  hash <file|hash>       Compute file hash or lookup MalwareBazaar
  ipcheck <ip>           Lookup IP reputation (AbuseIPDB)
  urlcheck <url>         Lookup URL in URLHaus
  lookup <artifact>      Auto-detect IP / hash / URL and query
  mhistory               Show command history
  clear                  Clear the terminal
  exit                   Exit Mimir
""")

    @staticmethod
    def exit() -> bool:
        print("Exiting Mimir...")
        return False

    @staticmethod
    def clear() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def mhistory(self) -> None:
        self.history_manager.display_history()

    # ---------------------------------------------------------
    # Hash / MalwareBazaar Commands
    # ---------------------------------------------------------
    def hash(self, args: list) -> None:
        """Compute hash of a file or lookup a known hash."""
        if not args:
            print("Usage: hash <filename> | hash -h <hash>")
            return

        mb = self.integrations.get("malwareBazaar")

        if "-h" in args:
            try:
                idx = args.index("-h")
                hash_value = args[idx + 1]
            except IndexError:
                print("Usage: hash -h <hash>")
                return

            if not mb.HASH_REGEX.match(hash_value):
                print(f"Invalid hash format: {hash_value}")
                return
            mb.mb_lookup(hash_value)
            return

        file_path = args[0]
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        try:
            import hashlib
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            hash_value = sha256.hexdigest()
            print(f"[+] SHA256: {hash_value}")
            print("[i] Querying MalwareBazaar...")
            mb.mb_lookup(hash_value)
        except Exception as e:
            print(f"Error hashing file: {e}")

    # ---------------------------------------------------------
    # AbuseIPDB (IP reputation)
    # ---------------------------------------------------------
    def ipcheck(self, args: list) -> None:
        if len(args) != 1:
            print("Usage: ipcheck <ip address>")
            return
        ip = args[0]
        ab = self.integrations.get("abuseIPDB")
        if ab.IP_REGEX.match(ip):
            ab.abuse_ip(ip)
        else:
            print(f"Invalid IP address format: {ip}")

    # ---------------------------------------------------------
    # URLHaus (URL analysis)
    # ---------------------------------------------------------
    def urlcheck(self, args: list) -> None:
        if len(args) != 1:
            print("Usage: urlcheck <url>")
            return
        url = args[0]
        uh = self.integrations.get("urlHaus")
        if not uh.URL_REGEX.match(url):
            print(f"Invalid URL format: {url}")
            return
        uh.url_lookup(url)

    # ---------------------------------------------------------
    # Unified lookup (auto-detect IP / hash / URL)
    # ---------------------------------------------------------
    def lookup(self, args: list) -> None:
        if len(args) != 1:
            print("Usage: lookup <artifact>")
            return
        target = args[0]
        ab = self.integrations.get("abuseIPDB")
        mb = self.integrations.get("malwareBazaar")
        uh = self.integrations.get("urlHaus")

        if ab.IP_REGEX.match(target):
            ab.abuse_ip(target)
        elif mb.HASH_REGEX.match(target):
            mb.mb_lookup(target)
        elif uh.URL_REGEX.match(target):
            uh.url_lookup(target)
        else:
            print(f"Unrecognized artifact type: {target}")

    # ---------------------------------------------------------
    # Case Management
    # ---------------------------------------------------------
    @staticmethod
    def case(args: list, case_manager, current_case: str) -> str:
        """Manage forensic cases (create, open, close)."""
        options = ["-n", "-o", "-c"]
        if len(args) < 1 or args[0] not in options:
            print(f"Usage: case [{' | '.join(options)}] \"case name\"")
            return current_case

        action = {"-n": "create", "-o": "open", "-c": "close"}[args[0]]
        case_name = args[1].strip('"') if len(args) > 1 else None

        if action != "close" and (not case_name or any(c in case_name for c in r'<>:"/\\|?*')):
            print("Invalid or missing case name.")
            return current_case

        new_case = case_manager.handle(case_name, action)
        return None if action == "close" else new_case or current_case

    # ---------------------------------------------------------
    # Dispatcher
    # ---------------------------------------------------------
    def execute(self, command: str, args: list, case_manager, current_case: str) -> Tuple[bool, str]:
        """Dispatch user commands and handle unknown shell calls."""
        cmd = command.lower()
        if cmd in self.commands:
            if cmd == "case":
                return True, self.case(args, case_manager, current_case)
            elif cmd == "exit":
                return self.exit(), current_case
            else:
                try:
                    if cmd in ["hash", "ipcheck", "urlcheck", "lookup"]:
                        self.commands[cmd](args)
                    else:
                        self.commands[cmd]()
                except Exception as e:
                    print(f"[!] Error executing command '{cmd}': {e}")
                return True, current_case
        else:
            try:
                result = subprocess.run(
                    [command] + args, capture_output=True, text=True, check=True
                )
                if result.stdout:
                    print(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                err = e.stderr.strip() or e.stdout.strip()
                print(f"[!] System command failed: {err}")
            except FileNotFoundError:
                print(f"[!] Unknown command: {command}")
            return True, current_case
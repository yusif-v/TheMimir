import os
import subprocess
import logging
from typing import Dict, Tuple, Any, Callable, Optional

from .history import HistoryManager

# -----------------------------
# Logger (avoid duplicate handlers)
# -----------------------------
logger = logging.getLogger("Mimir")
logger.setLevel(logging.INFO)
logfile = os.path.expanduser("~/Mimir/Logs/mimir.log")
os.makedirs(os.path.dirname(logfile), exist_ok=True)
if not logger.handlers:
    fh = logging.FileHandler(logfile)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
logger.propagate = False

CommandFunc = Callable[[Optional[list]], Any]


class CommandHandler:
    def __init__(self, history_manager: HistoryManager, integrations: Dict[str, Any]):
        self.history_manager = history_manager
        self.integrations = integrations

        self._docmap: Dict[str, Callable[..., Any]] = {
            "help": self.help,
            "exit": self.exit,
            "clear": self.clear,
            "mhistory": self.mhistory,
            "hash": self.hash,
            "ipcheck": self.ipcheck,
            "urlcheck": self.urlcheck,
            "lookup": self.lookup,
            "case": self.case,
        }

        self.commands: Dict[str, CommandFunc] = {
            "help": self._wrap_args(self.help),
            "exit": self._wrap_noargs(self.exit),
            "clear": self._wrap_noargs(self.clear),
            "mhistory": self._wrap_noargs(self.mhistory),
            "hash": self._wrap_args(self.hash),
            "ipcheck": self._wrap_args(self.ipcheck),
            "urlcheck": self._wrap_args(self.urlcheck),
            "lookup": self._wrap_args(self.lookup),
            # 'case' handled specially in execute()
        }

    @staticmethod
    def _wrap_noargs(func: Callable[[], Any]) -> CommandFunc:
        def _inner(_args: Optional[list] = None):
            return func()
        return _inner

    @staticmethod
    def _wrap_args(func: Callable[[list], Any]) -> CommandFunc:
        def _inner(args: Optional[list] = None):
            return func(args or [])
        return _inner

    # ---------------------------------------------------------
    # Core shell commands
    # ---------------------------------------------------------
    def help(self, args: list | None = None) -> None:
        """
        Display available commands or detailed help for a specific one.
        Automatically pulls descriptions from command docstrings.

        Usage:
          help                # overview
          help <command>      # detailed docstring for a command
        """
        if args:
            cmd = (args[0] or "").lower()
            func = self._docmap.get(cmd)
            if not func:
                print(f"No such command: {cmd}")
                return
            doc = func.__doc__ or "No documentation available."
            print(f"\n{cmd} — details:\n{doc.strip()}\n")
            logger.info(f"Help viewed for command: {cmd}")
            return

        print("Available commands:\n")
        for name in sorted(self._docmap.keys()):
            docsrc = self._docmap[name]
            doc = docsrc.__doc__ or ""
            first_line = doc.strip().splitlines()[0] if doc else "No description provided."
            print(f"  {name:<10} - {first_line}")
        print()
        logger.info("Displayed general help menu.")

    @staticmethod
    def exit() -> bool:
        """Exit Mimir."""
        print("Exiting Mimir...")
        return False

    @staticmethod
    def clear() -> None:
        """Clear the terminal screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def mhistory(self) -> None:
        """Show recent commands from history."""
        self.history_manager.display_history()

    # ---------------------------------------------------------
    # Hash / MalwareBazaar Commands
    # ---------------------------------------------------------
    def hash(self, args: list) -> None:
        """Compute SHA256 of a file or query MalwareBazaar with an existing hash.

        Usage:
          hash <filename>
          hash -h <hash>     # MD5/SHA1/SHA256
        """
        if not args:
            print("Usage: hash <filename> | hash -h <hash>")
            return

        mb = self.integrations.get("malwareBazaar")
        if mb is None:
            print("[!] MalwareBazaar integration not available.")
            return

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
        """Lookup IP reputation using AbuseIPDB.

        Usage:
          ipcheck <ip>
        """
        if len(args) != 1:
            print("Usage: ipcheck <ip address>")
            return
        ab = self.integrations.get("abuseIPDB")
        if ab is None:
            print("[!] AbuseIPDB integration not available.")
            return

        ip = args[0]
        if ab.IP_REGEX.match(ip):
            ab.abuse_ip(ip)
        else:
            print(f"Invalid IP address format: {ip}")

    # ---------------------------------------------------------
    # URLHaus (URL analysis)
    # ---------------------------------------------------------
    def urlcheck(self, args: list) -> None:
        """Check malicious URLs in URLHaus.

        Usage:
          urlcheck <url>
        """
        if len(args) != 1:
            print("Usage: urlcheck <url>")
            return
        uh = self.integrations.get("urlHaus")
        if uh is None:
            print("[!] URLHaus integration not available.")
            return

        url = args[0]
        if not uh.URL_REGEX.match(url):
            print(f"Invalid URL format: {url}")
            return
        uh.url_lookup(url)

    # ---------------------------------------------------------
    # Unified lookup (auto-detect IP / hash / URL)
    # ---------------------------------------------------------
    def lookup(self, args: list) -> None:
        """Auto-detect artifact type (IP, URL, hash) and perform lookup.

        Usage:
          lookup <artifact>
        """
        if len(args) != 1:
            print("Usage: lookup <artifact>")
            return

        ab = self.integrations.get("abuseIPDB")
        mb = self.integrations.get("malwareBazaar")
        uh = self.integrations.get("urlHaus")
        if not all([ab, mb, uh]):
            print("[!] One or more integrations are not available.")
            return

        target = args[0]
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
        """Manage forensic cases (create, open, close).

        Usage:
          case -n "<name>"   # create
          case -o "<name>"   # open
          case -c "<name>"   # close
        """
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
        """
        Dispatch user commands and handle unknown shell calls.

        Returns:
            (continue_shell, new_current_case)
        """
        cmd = command.lower()

        if cmd == "case":
            return True, self.case(args, case_manager, current_case)

        if cmd in {"exit", "quit"}:
            return self.exit(), current_case

        if cmd in self.commands:
            try:
                self.commands[cmd](args)
            except Exception as e:
                print(f"[!] Error executing command '{cmd}': {e}")
            return True, current_case

        try:
            result = subprocess.run([command] + args, capture_output=True, text=True, check=True)
            if result.stdout:
                print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() or e.stdout.strip()
            print(f"[!] System command failed: {err}")
        except FileNotFoundError:
            print(f"[!] Unknown command: {command}")

        return True, current_case
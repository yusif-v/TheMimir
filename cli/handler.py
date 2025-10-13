import os
import subprocess
from typing import Dict, Tuple, Any
from .history import HistoryManager

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
            "case": self.case
        }

    def help(self) -> None:
        print("Available commands: " + ", ".join(self.commands.keys()))

    @staticmethod
    def exit() -> bool:
        print("Exiting Mimir...")
        return False

    @staticmethod
    def clear() -> None:
        os.system("clear" if os.name != "nt" else "cls")

    def mhistory(self) -> None:
        self.history_manager.display_history()

    def hash(self, args: list) -> None:
        if not args:
            print("Usage: hash <filename>, hash -h <hashstring>")
            return
        if "-h" in args:
            try:
                hashindex = args.index("-h")
                if hashindex + 1 >= len(args):
                    print("Usage: hash -h <hashstring>")
                    return
                hashstring = args[hashindex + 1]
                self.integrations["malwareBazaar"].mb_hash(hashstring)
            except ValueError:
                print("Invalid hash format")
        else:
            try:
                self.integrations["malwareBazaar"].get_hash(args)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr.strip()}")

    def ipcheck(self, args: list) -> None:
        if len(args) != 1:
            print("Usage: ipcheck <ip address>")
            return
        ip = args[0]
        if self.integrations["abuseIPDB"].ip_regex.match(ip):
            self.integrations["abuseIPDB"].abuse_ip(ip)
        else:
            print("Invalid IP address")

    def urlcheck(self, args: list) -> None:
        if len(args) != 1:
            print("Usage: urlcheck <url>")
            return
        url = args[0]
        self.integrations["urlHaus"].urlcheck(url)

    @staticmethod
    def case(args: list, case_manager, current_case: str) -> str:
        case_options = ["-n", "-o", "-c"]
        if len(args) < 2 or args[0] not in case_options:
            print(f"Usage: case [{' | '.join(case_options)}] \"case name\"")
            return current_case
        action = {"-n": "create", "-o": "open", "-c": "close"}.get(args[0])
        case_name = args[1].strip('"')
        if not case_name or any(c in case_name for c in r'<>:"/\|?*'):
            print("Invalid case name")
            return current_case
        new_case = case_manager.handle(case_name, action)
        return None if action == "close" else new_case or current_case

    def execute(self, command: str, args: list, case_manager, current_case: str) -> Tuple[bool, str]:
        cmd = command.lower()
        if cmd in self.commands:
            if cmd == "case":
                return True, self.case(args, case_manager, current_case)
            elif cmd == "exit":
                return self.exit(), current_case
            else:
                if cmd in ["hash", "ipcheck", "urlcheck"]:
                    self.commands[cmd](args)
                else:
                    self.commands[cmd]()
                return True, current_case
        else:
            try:
                result = subprocess.run(
                    [command] + args, capture_output=True, text=True, check=True
                )
                print(result.stdout)
                return True, current_case
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr.strip()}")
                return True, current_case
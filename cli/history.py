import os
from datetime import datetime
from typing import List, Tuple
from dotenv import load_dotenv


class HistoryManager:
    def __init__(self, history_file: str | None = None, max_entries: int = 50):
        load_dotenv()
        self.history_file = history_file or os.getenv("MIMIR_HIST") or os.path.join(os.path.expanduser("~"), "Mimir", ".mhistory")
        self.max_entries = max_entries
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            open(self.history_file, "w").close()

    def parse_history(self) -> List[Tuple[str, str]]:
        try:
            with open(self.history_file, "r") as f:
                entries = [
                    line.strip().split("|", 1)
                    for line in f
                    if line.strip() and not line.startswith(("#", "+"))
                ]
            entries = [(cmd, ts) for cmd, ts in entries if len([cmd, ts]) == 2]
            seen = {}
            for cmd, ts in entries:
                seen[cmd] = ts
            return [(cmd, seen[cmd]) for cmd in list(seen.keys())[-self.max_entries:]][::-1]
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error reading history: {e}")
            return []

    def display_history(self) -> None:
        entries = self.parse_history()
        if not entries:
            print("No history found.")
            return
        max_cmd_len = max(len(cmd) for cmd, _ in entries)
        header = f"{'Num':<4} {'Command':<{max_cmd_len}}  Timestamp"
        print(header)
        print("-" * len(header))
        for i, (cmd, timestamp) in enumerate(entries, 1):
            print(f"{i:<4} {cmd:<{max_cmd_len}}  {timestamp}")

    def save_history(self, command: str) -> None:
        if not command or command.isspace():
            return
        command = command.strip()
        if any(c in command for c in "\n|"):
            print("Invalid command: contains newline or pipe character.")
            return
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.history_file, "a") as f:
                f.write(f"{command}|{timestamp}\n")
            entries = self.parse_history()
            if len(entries) > self.max_entries:
                with open(self.history_file, "w") as f:
                    for cmd, ts in entries[:self.max_entries]:
                        f.write(f"{cmd}|{ts}\n")
        except Exception as e:
            print(f"Error saving history: {e}")
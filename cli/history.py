import os
from datetime import datetime
from typing import List, Optional, Dict
from dotenv import load_dotenv
import tempfile


class HistoryManager:
    """
    Persists interactive commands to a history file.

    Line format (new):
      command|YYYY-MM-DD HH:MM:SS|case

    Backward compatibility:
      command|YYYY-MM-DD HH:MM:SS
    """

    def __init__(self, history_file: Optional[str] = None, max_entries: int = 200):
        load_dotenv()
        self.history_file = (
            history_file
            or os.getenv("MIMIR_HIST")
            or os.path.join(os.path.expanduser("~"), "Mimir", ".mhistory")
        )
        self.max_entries = max_entries
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            open(self.history_file, "w", encoding="utf-8").close()

    # ---------------- Public API ----------------

    def parse_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Returns a list of dicts: [{'cmd': str, 'ts': str, 'case': str}, ...]
        Most-recent-first. Resilient to malformed lines.
        """
        items: List[Dict[str, str]] = []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith(("#", "+")):
                        continue
                    rec = self._parse_line(line)
                    if rec:
                        items.append(rec)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error reading history: {e}")
            return []

        # Keep chronological order then reverse to most-recent-first
        items = items[-(limit or len(items)) :][::-1]
        return items

    def display_history(self, limit: Optional[int] = None) -> None:
        rows = self.parse_history(limit)
        if not rows:
            print("No history found.")
            return

        # Column widths
        max_cmd = max(len(r["cmd"]) for r in rows)
        max_case = max((len(r.get("case") or "") for r in rows), default=0)
        max_cmd = min(max_cmd, 120)  # keep table tidy
        max_case = min(max_case, 40)

        has_case = any(r.get("case") for r in rows)

        if has_case:
            header = f"{'Num':<4} {'Command':<{max_cmd}}  {'Case':<{max_case}}  Timestamp"
        else:
            header = f"{'Num':<4} {'Command':<{max_cmd}}  Timestamp"

        print(header)
        print("-" * len(header))
        for idx, r in enumerate(rows, 1):
            cmd = r["cmd"][:max_cmd]
            ts = r["ts"]
            case = (r.get("case") or "")[:max_case]
            if has_case:
                print(f"{idx:<4} {cmd:<{max_cmd}}  {case:<{max_case}}  {ts}")
            else:
                print(f"{idx:<4} {cmd:<{max_cmd}}  {ts}")

    def save_history(self, command: str, case: Optional[str] = None) -> None:
        """
        Append a command to history. `case` is optional.
        """
        if not command or command.isspace():
            return

        command = command.strip()
        # Disallow the separator to avoid parse ambiguity
        if "|" in command or "\n" in command:
            print("Invalid command for history: contains '|' or newline.")
            return

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = self._serialize_line(command, ts, case)

        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"Error saving history: {e}")
            return

        # Rotate if needed (keep most recent max_entries)
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                lines = [ln for ln in f if ln.strip()]
            if len(lines) > self.max_entries:
                keep = lines[-self.max_entries :]
                # atomic rewrite
                dirpath = os.path.dirname(self.history_file)
                fd, tmp = tempfile.mkstemp(dir=dirpath, prefix=".mhistory.tmp.")
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as tf:
                        tf.writelines(keep)
                    os.replace(tmp, self.history_file)
                except Exception:
                    # fallback non-atomic
                    with open(self.history_file, "w", encoding="utf-8") as f:
                        f.writelines(keep)
                    try:
                        if os.path.exists(tmp):
                            os.remove(tmp)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error rotating history: {e}")

    # ---------------- Internals ----------------

    @staticmethod
    def _serialize_line(cmd: str, ts: str, case: Optional[str]) -> str:
        if case:
            return f"{cmd}|{ts}|{case}"
        return f"{cmd}|{ts}"

    @staticmethod
    def _parse_line(line: str) -> Optional[Dict[str, str]]:
        """
        Accepts:
          command|timestamp
          command|timestamp|case
        """
        parts = line.split("|")
        if len(parts) < 2:
            return None
        cmd = parts[0].strip()
        ts = parts[1].strip()
        case = parts[2].strip() if len(parts) >= 3 else ""
        if not cmd or not ts:
            return None
        return {"cmd": cmd, "ts": ts, "case": case}
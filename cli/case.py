import os
import json
import datetime
import getpass
from typing import Optional, List


class CaseManager:
    def __init__(self, base_path: Optional[str] = None, chdir_on_open: bool = True):
        home = os.path.expanduser("~")
        resolved = base_path or os.getenv("MIMIR_PATH") or os.path.join(home, "Mimir")
        self.base_path = os.path.abspath(os.path.expanduser(resolved))
        self.investigations_path = os.path.join(self.base_path, "Investigations")
        self.chdir_on_open = chdir_on_open

        os.makedirs(self.investigations_path, exist_ok=True)
        self.current_case: Optional[str] = None
        self.current_case_path: Optional[str] = None

    def handle(self, case_name: Optional[str], action: str):
        actions = {
            "create": self.create_case,
            "open": self.open_case,
            "close": self.close_case,
            "list": self.list_cases,
            "info": self.case_info,
        }
        fn = actions.get(action)
        if not fn:
            print(f"Unknown action: {action}")
            return self.current_case
        return fn(case_name)

    def create_case(self, case_name: Optional[str]):
        if not case_name:
            print("Missing case name.")
            return None
        case_path = os.path.join(self.investigations_path, case_name)
        if os.path.exists(case_path):
            print(f"⚠️  Case '{case_name}' already exists at {case_path}")
            self.current_case = case_name
            self.current_case_path = case_path
            if self.chdir_on_open:
                os.chdir(case_path)
            self._persist_last_case(case_name)
            return case_name

        os.makedirs(case_path, exist_ok=True)
        metadata = {
            "name": case_name,
            "created": datetime.datetime.utcnow().isoformat(),
            "updated": datetime.datetime.utcnow().isoformat(),
            "examiner": getpass.getuser(),
            "evidence": [],
            "notes": [],
        }
        self._write_metadata(case_path, metadata)

        self.current_case = case_name
        self.current_case_path = case_path
        if self.chdir_on_open:
            os.chdir(case_path)
        self._persist_last_case(case_name)

        print(f"🆕 New case created: {case_name} at {case_path}")
        return case_name

    def open_case(self, case_name: Optional[str]):
        if not case_name:
            print("Missing case name.")
            return None
        case_path = os.path.join(self.investigations_path, case_name)
        meta_path = os.path.join(case_path, "case.json")
        if not os.path.exists(meta_path):
            print(f"❌ Case '{case_name}' not found at {case_path}")
            return None

        self.current_case = case_name
        self.current_case_path = case_path
        if self.chdir_on_open:
            os.chdir(case_path)
        self._persist_last_case(case_name)

        print(f"📂 Opened case: {case_name}")
        return case_name

    def close_case(self, _=None):
        if not self.current_case:
            print("No case currently open.")
            return None
        print(f"🔒 Case '{self.current_case}' closed.")
        self.current_case = None
        self.current_case_path = None
        self._persist_last_case("")
        if self.chdir_on_open:
            os.chdir(self.base_path)
        return None

    def list_cases(self, _=None) -> List[str]:
        cases = sorted(
            d for d in os.listdir(self.investigations_path)
            if os.path.isdir(os.path.join(self.investigations_path, d))
        )
        if not cases:
            print("No cases found.")
            return []
        print("📁 Existing cases:")
        for c in cases:
            print(f"  - {c}")
        return cases

    def case_info(self, case_name: Optional[str] = None):
        if not case_name and not self.current_case:
            print("No case specified or open.")
            return None
        case_name = case_name or self.current_case
        meta_path = os.path.join(self.investigations_path, case_name, "case.json")
        if not os.path.exists(meta_path):
            print(f"No metadata found for case '{case_name}'.")
            return None
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(json.dumps(data, indent=2))
        return data

    def add_evidence(self, file_path: str, description: str = ""):
        if not self.current_case_path:
            print("No case is currently open.")
            return
        meta_path = os.path.join(self.current_case_path, "case.json")
        if not os.path.exists(meta_path):
            print("Case metadata missing.")
            return
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entry = {
            "file": os.path.abspath(file_path),
            "description": description,
            "added": datetime.datetime.utcnow().isoformat(),
        }
        data["evidence"].append(entry)
        data["updated"] = datetime.datetime.utcnow().isoformat()
        self._write_metadata(self.current_case_path, data)
        print(f"📎 Added evidence: {file_path}")

    @staticmethod
    def _write_metadata(case_path: str, metadata: dict):
        meta_path = os.path.join(case_path, "case.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def _persist_last_case(self, name: str) -> None:
        try:
            with open(os.path.join(self.base_path, ".last_case"), "w", encoding="utf-8") as f:
                f.write(name or "")
        except Exception:
            pass
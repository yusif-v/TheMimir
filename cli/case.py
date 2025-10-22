import os
import json
import datetime

class CaseManager:
    def __init__(self, base_path):
        if not base_path:
            raise ValueError("MIMIR_PATH environment variable not set.")
        self.base_path = os.path.expanduser(base_path)
        self.investigations_path = os.path.join(self.base_path, "Investigations")
        os.makedirs(self.investigations_path, exist_ok=True)
        self.current_case = None
        self.current_case_path = None

    # === Public interface ===

    def handle(self, case_name, action):
        actions = {
            "create": self.create_case,
            "open": self.open_case,
            "close": self.close_case,
            "list": self.list_cases,
            "info": self.case_info
        }
        action_func = actions.get(action)
        if not action_func:
            print(f"Unknown action: {action}")
            return self.current_case

        return action_func(case_name)

    # === Case lifecycle ===

    def create_case(self, case_name):
        case_path = os.path.join(self.investigations_path, case_name)
        if os.path.exists(case_path):
            print(f"⚠️  Case '{case_name}' already exists.")
            return None

        os.makedirs(case_path)
        metadata = {
            "name": case_name,
            "created": datetime.datetime.utcnow().isoformat(),
            "updated": datetime.datetime.utcnow().isoformat(),
            "examiner": os.getenv("USER", "unknown"),
            "evidence": [],
            "notes": []
        }
        self._write_metadata(case_path, metadata)

        self.current_case = case_name
        self.current_case_path = case_path
        print(f"🆕 New case created: {case_name} at {case_path}")
        return case_name

    def open_case(self, case_name):
        case_path = os.path.join(self.investigations_path, case_name)
        meta_path = os.path.join(case_path, "case.json")
        if not os.path.exists(meta_path):
            print(f"❌ Case '{case_name}' not found.")
            return None

        self.current_case = case_name
        self.current_case_path = case_path
        print(f"📂 Opened case: {case_name}")
        return case_name

    def close_case(self, _=None):
        if not self.current_case:
            print("No case currently open.")
            return None

        print(f"🔒 Case '{self.current_case}' closed.")
        self.current_case = None
        self.current_case_path = None
        return None

    # === Case utilities ===

    def list_cases(self, _=None):
        cases = [d for d in os.listdir(self.investigations_path)
                 if os.path.isdir(os.path.join(self.investigations_path, d))]
        if not cases:
            print("No cases found.")
            return []
        print("📁 Existing cases:")
        for c in cases:
            print(f"  - {c}")
        return cases

    def case_info(self, case_name=None):
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

    # === Evidence operations ===

    def add_evidence(self, file_path, description=""):
        """Register evidence file path and hash into case metadata."""
        if not self.current_case_path:
            print("No case is currently open.")
            return

        meta_path = os.path.join(self.current_case_path, "case.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entry = {
            "file": os.path.abspath(file_path),
            "description": description,
            "added": datetime.datetime.utcnow().isoformat()
        }
        data["evidence"].append(entry)
        data["updated"] = datetime.datetime.utcnow().isoformat()

        self._write_metadata(self.current_case_path, data)
        print(f"📎 Added evidence: {file_path}")

    # === Internal helpers ===

    @staticmethod
    def _write_metadata(case_path, metadata):
        meta_path = os.path.join(case_path, "case.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
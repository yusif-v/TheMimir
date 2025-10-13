import os

class CaseManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.investigations_path = os.path.join(base_path, "Investigations")

    def handle(self, case, action):
        if not self.base_path:
            print("Error: MIMIR_PATH is not set in your environment.")
            return None
        os.makedirs(self.investigations_path, exist_ok=True)
        case_path = os.path.join(self.investigations_path, case)
        actions = {
            "create": lambda: self.create_case(case_path, case),
            "open": lambda: self.open_case(case_path, case),
            "close": lambda: self.close_case(case_path, case)
        }
        action_func = actions.get(action)
        if action_func:
            return action_func()
        print(f"Unknown action: {action}")
        return None

    @staticmethod
    def create_case(case_path, case):
        if os.path.exists(case_path):
            print(f"Case '{case}' already exists at {case_path}")
            return None
        os.makedirs(case_path)
        print(f"New case created: {case_path}")
        os.chdir(case_path)
        return case

    @staticmethod
    def open_case(case_path, case):
        if os.path.exists(case_path):
            os.chdir(case_path)
            print(f"Opened case: {case_path}")
            return case
        print(f"Case '{case}' does not exist at {case_path}")
        return None

    @staticmethod
    def close_case(case_path, case):
        print(f"{case} is closed")
        parent_dir = os.path.dirname(os.path.dirname(case_path))
        os.chdir(parent_dir)
        return None
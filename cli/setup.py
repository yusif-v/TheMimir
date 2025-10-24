import os
import subprocess
import venv
from dotenv import load_dotenv
from typing import List, Tuple

class SetupManager:
    def __init__(self):
        self.home_dir = os.path.expanduser("~")
        self.project_dir = os.path.join(self.home_dir, "Mimir")
        self.subdirs = ["Investigations", "Reports", "Logs"]
        self.api_keys = ["OTX_API_KEY", "ABUSE_API_KEY", "ACH_API_KEY", "VT_API_KEY"]
        self.venv_dir = os.path.join(self.project_dir, ".venv")
        self.requirements_file = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        self.flag_file = os.path.join(self.project_dir, ".deps_installed")
        self.env_path = os.path.join(self.project_dir, ".env")

    # -------------------------------------------------------------
    def create_structure(self) -> List[str]:
        messages = []

        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir)
            messages.append(f"[setup] Created main folder: {self.project_dir}")

        for sub in self.subdirs:
            sub_path = os.path.join(self.project_dir, sub)
            if not os.path.exists(sub_path):
                os.makedirs(sub_path)
                messages.append(f"[setup] Created subfolder: {sub}")

        if not os.path.exists(self.env_path):
            try:
                with open(self.env_path, "w") as f:
                    f.write("# Mimir Environment Variables\n")
                    for key in self.api_keys:
                        f.write(f"{key}=\n")
                messages.append(f"[setup] Created .env file at {self.env_path}")
            except Exception as e:
                messages.append(f"[setup] ❌ Failed to create .env file: {e}")

        return messages

    # -------------------------------------------------------------
    def setup_venv(self) -> List[str]:
        """Ensure virtual environment and dependencies exist."""
        messages = []

        if not os.path.exists(self.venv_dir):
            try:
                venv.create(self.venv_dir, with_pip=True)
                messages.append(f"[setup] Created virtual environment at {self.venv_dir}")
            except Exception as e:
                messages.append(f"[setup] ❌ Failed to create virtual environment: {e}")
                return messages

        if os.path.exists(self.flag_file):
            return messages

        pip_exec = (
            os.path.join(self.venv_dir, "Scripts", "pip.exe")
            if os.name == "nt"
            else os.path.join(self.venv_dir, "bin", "pip")
        )

        if os.path.exists(self.requirements_file):
            try:
                subprocess.check_call(
                    [pip_exec, "install", "--upgrade", "pip"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                subprocess.check_call(
                    [pip_exec, "install", "-r", self.requirements_file],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                with open(self.flag_file, "w") as f:
                    f.write("Dependencies installed successfully.")
                messages.append("[setup] Installed dependencies from requirements.txt")
            except subprocess.CalledProcessError as e:
                messages.append(f"[setup] ❌ pip install failed: {e}")
            except Exception as e:
                messages.append(f"[setup] ❌ Error managing dependencies: {e}")
        else:
            messages.append("[setup] ⚠️ requirements.txt not found; skipped dependency installation.")

        return messages

    # -------------------------------------------------------------
    def check_env(self) -> List[str]:
        """Verify required API keys exist."""
        messages = []
        try:
            load_dotenv(self.env_path)
            missing = [key for key in self.api_keys if not os.getenv(key)]
            if missing:
                messages.append(f"[setup] ⚠️ Missing API keys: {', '.join(missing)}")
        except Exception as e:
            messages.append(f"[setup] ❌ Error reading .env file: {e}")
        return messages

    # -------------------------------------------------------------
    def setup(self) -> Tuple[bool, List[str]]:
        """Run full setup. Returns (success, messages)."""
        messages = []
        messages.extend(self.create_structure())
        messages.extend(self.setup_venv())
        messages.extend(self.check_env())

        success = not any("❌" in msg or "Missing" in msg for msg in messages)

        if success and not messages:
            return True, []

        # Remove redundant "everything fine" notes
        visible_msgs = [m for m in messages if "✅" not in m and "already installed" not in m]
        return success, visible_msgs

# -------------------------------------------------------------
# CLI entry point (for standalone runs)
# -------------------------------------------------------------
if __name__ == "__main__":
    setup_manager = SetupManager()
    mssgs: list[str]
    sccss, mssgs = setup_manager.setup()

    if mssgs:
        print("\n--- Mimir Setup Summary ---")
        for MSG in mssgs:
            print(MSG)
        print("----------------------------")
        if sccss:
            print("✅ Setup completed successfully.")
        else:
            print("⚠️ Setup finished with warnings or errors.")
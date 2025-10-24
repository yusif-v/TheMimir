import os
import subprocess
import venv
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv

class SetupManager:
    def __init__(self, project_dir: Optional[str] = None, force_home: bool = True):
        self.home_dir = os.path.expanduser("~")
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        default_workspace = os.path.join(self.home_dir, "Mimir")
        env_path = os.getenv("MIMIR_PATH")

        if force_home:
            resolved = project_dir or default_workspace
        else:
            resolved = project_dir or env_path or default_workspace

        resolved = os.path.abspath(os.path.expanduser(resolved))
        if self._is_inside_repo(resolved):
            resolved = default_workspace  # never use repo as workspace

        self.project_dir = resolved
        self.history_file = os.path.expanduser(
            os.getenv("MIMIR_HIST", os.path.join(self.home_dir, ".mimir_history"))
        )
        self.subdirs = ["Investigations", "Reports", "Logs"]
        self.api_keys = ["OTX_API_KEY", "ABUSE_API_KEY", "ACH_API_KEY", "VT_API_KEY"]
        self.venv_dir = os.path.join(self.project_dir, ".venv")
        self.env_path = os.path.join(self.project_dir, ".env")
        self.flag_file = os.path.join(self.project_dir, ".deps_installed")
        self.requirements_file = self._find_requirements_file()
        self.repo_main = os.path.join(self.repo_root, "main.py")

    def _is_inside_repo(self, path: str) -> bool:
        try:
            common = os.path.commonpath([self.repo_root, os.path.abspath(path)])
            return common == self.repo_root
        except Exception:
            return False
    def setup(self, create_launcher: bool = True) -> Tuple[bool, List[str]]:
        messages: List[str] = []
        messages.extend(self.create_structure())
        messages.extend(self.ensure_env_file())
        messages.extend(self.setup_venv())
        messages.extend(self.check_env())
        if create_launcher:
            messages.extend(self.create_launcher_script())
        success = not any(("❌" in m or "Missing API keys" in m) for m in messages)
        if success and not messages:
            return True, []
        visible = [m for m in messages if not m.endswith(" — already ok")]
        return success, visible

    def create_structure(self) -> List[str]:
        msgs: List[str] = []
        if not os.path.exists(self.project_dir):
            os.makedirs(self.project_dir, exist_ok=True)
            msgs.append(f"[setup] Created main folder: {self.project_dir}")
        for sub in self.subdirs:
            p = os.path.join(self.project_dir, sub)
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
                msgs.append(f"[setup] Created subfolder: {sub}")
        try:
            self._touch(self.history_file)
        except Exception as e:
            msgs.append(f"[setup] ❌ Failed to ensure history file: {e}")
        return msgs

    def ensure_env_file(self) -> List[str]:
        msgs: List[str] = []
        existing: Dict[str, str] = {}
        if os.path.exists(self.env_path):
            try:
                existing = self._read_env_file(self.env_path)
            except Exception as e:
                msgs.append(f"[setup] ❌ Failed reading .env: {e}")
                existing = {}
        desired: Dict[str, str] = {
            "MIMIR_PATH": self.project_dir,
            "MIMIR_HIST": self.history_file,
            **{k: existing.get(k, "") for k in self.api_keys},
        }
        try:
            new_content = self._env_content({**existing, **desired})
            current = ""
            if os.path.exists(self.env_path):
                current = self._read_text(self.env_path)
            if new_content != current:
                os.makedirs(os.path.dirname(self.env_path), exist_ok=True)
                with open(self.env_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                msgs.append(f"[setup] Wrote .env at {self.env_path}")
        except Exception as e:
            msgs.append(f"[setup] ❌ Failed writing .env: {e}")
        return msgs

    def setup_venv(self) -> List[str]:
        msgs: List[str] = []
        if not os.path.exists(self.venv_dir):
            try:
                venv.create(self.venv_dir, with_pip=True)
                msgs.append(f"[setup] Created virtual environment at {self.venv_dir}")
            except Exception as e:
                msgs.append(f"[setup] ❌ Failed to create virtual environment: {e}")
                return msgs
        if os.path.exists(self.flag_file):
            return msgs
        pip_exec = (
            os.path.join(self.venv_dir, "Scripts", "pip.exe")
            if os.name == "nt"
            else os.path.join(self.venv_dir, "bin", "pip")
        )
        if self.requirements_file and os.path.exists(self.requirements_file):
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
                msgs.append("[setup] Installed dependencies from requirements.txt")
            except subprocess.CalledProcessError as e:
                msgs.append(f"[setup] ❌ pip install failed: {e}")
            except Exception as e:
                msgs.append(f"[setup] ❌ Error managing dependencies: {e}")
        else:
            msgs.append("[setup] ⚠️ requirements.txt not found; skipped dependency installation.")
        return msgs

    def check_env(self) -> List[str]:
        msgs: List[str] = []
        try:
            load_dotenv(self.env_path)
            missing = [k for k in self.api_keys if not os.getenv(k)]
            if missing:
                msgs.append(f"[setup] ⚠️ Missing API keys: {', '.join(missing)}")
        except Exception as e:
            msgs.append(f"[setup] ❌ Error reading .env file: {e}")
        return msgs

    def create_launcher_script(self) -> List[str]:
        msgs: List[str] = []
        if not os.path.exists(self.repo_main):
            return msgs
        if os.name == "nt":
            script_path = os.path.join(self.project_dir, "mimir.cmd")
            python_exec = os.path.join(self.venv_dir, "Scripts", "python.exe")
            content = f'@echo off\r\n"{python_exec}" "{self.repo_main}" %*\r\n'
        else:
            script_path = os.path.join(self.project_dir, "mimir")
            python_exec = os.path.join(self.venv_dir, "bin", "python")
            content = f'#!/usr/bin/env bash\n"{python_exec}" "{self.repo_main}" "$@"\n'
        try:
            current = self._read_text(script_path) if os.path.exists(script_path) else ""
            if current != content:
                with open(script_path, "w", newline="" if os.name == "nt" else None) as f:
                    f.write(content)
                if os.name != "nt":
                    os.chmod(script_path, 0o755)
                msgs.append(f"[setup] Created launcher: {script_path}")
        except Exception as e:
            msgs.append(f"[setup] ⚠️ Failed to create launcher: {e}")
        return msgs

    def _find_requirements_file(self) -> Optional[str]:
        env_path = os.getenv("MIMIR_REQUIREMENTS")
        if env_path:
            p = os.path.expanduser(env_path)
            if os.path.exists(p):
                return p
        repo_req = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "requirements.txt"))
        if os.path.exists(repo_req):
            return repo_req
        ws_req = os.path.join(self.project_dir, "requirements.txt")
        if os.path.exists(ws_req):
            return ws_req
        return None

    @staticmethod
    def _touch(path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a"):
            os.utime(path, None)

    @staticmethod
    def _read_env_file(path: str) -> Dict[str, str]:
        data: Dict[str, str] = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                data[k.strip()] = v.strip()
        return data

    @staticmethod
    def _env_content(kv: Dict[str, str]) -> str:
        lines = ["# Mimir Environment Variables\n"]
        for k in sorted(kv.keys()):
            lines.append(f"{k}={kv[k]}\n")
        return "".join(lines)

    @staticmethod
    def _read_text(path: str) -> str:
        with open(path, "r", encoding="utf-8", newline="") as f:
            return f.read()


if __name__ == "__main__":
    sm = SetupManager()
    success, messages = sm.setup(create_launcher=True)
    if messages:
        print("\n--- Mimir Setup Summary ---")
        for m in messages:
            print(m)
        print("----------------------------")
        print("✅ Setup completed successfully." if success else "⚠️ Setup finished with warnings or errors.")
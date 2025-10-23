from prompt_toolkit.formatted_text import ANSI
import os

class Prompt:
    x @staticmethod
    def get_prompt(user: str, case: str | None = None) -> ANSI:
        cwd = os.path.basename(os.getcwd()) or "/"

        green = "\033[92m"   # user
        cyan = "\033[96m"    # Mimir label
        yellow = "\033[93m"  # case name
        gray = "\033[90m"    # subtle path
        reset = "\033[0m"

        if case:
            prompt_str = (
                f"{green}[{user}]{reset}"
                f"{cyan}[Mimir]{reset}"
                f"{yellow}[{case}]{reset}"
                f"{gray}|>{reset} "
            )
        else:
            prompt_str = (
                f"{green}[{user}]{reset}"
                f"{cyan}[Mimir]{reset}"
                f"{gray}[{cwd}]{reset}"
                f"{gray}|>{reset} "
            )

        try:
            return ANSI(prompt_str)
        except (ValueError, TypeError):
            safe_case = case or cwd
            return ANSI(f"[{user}][Mimir][{safe_case}]> ")
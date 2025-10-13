from prompt_toolkit.formatted_text import ANSI
import os

class Prompt:
    @staticmethod
    def get_prompt(user, case=None):
        cwd = os.path.basename(os.getcwd()) or "/"
        if case:
            return ANSI(f"\033[92m[{user}]\033[0m\033[96m[mimir]\033[0m\033[93m[{case}]\033[0m|> ")
        return ANSI(f"\033[92m[{user}]\033[0m\033[96m[{cwd}]\033[0m|> ")
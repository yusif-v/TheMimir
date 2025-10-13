import sys
from cli.shell import mimir
from cli.setup import SetupManager

def main():
    setup_manager = SetupManager()
    success, messages = setup_manager.setup()
    for msg in messages:
        print(msg)
    if not success:
        print("Setup failed. Check environment variables and folder permissions.")
        sys.exit(1)
    mimir()

if __name__ == "__main__":
    main()
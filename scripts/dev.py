"""Development tools for LXMFy."""

import subprocess
import sys


def format():
    """Run ruff formatter."""
    return subprocess.call(["ruff", "check", "--fix", "lxmfy"])


def lint():
    """Run ruff linter."""
    return subprocess.call(["ruff", "check", "lxmfy"])


def scan():
    """Run bandit security scanner."""
    return subprocess.call(["bandit", "-r", "lxmfy"])


def main():
    """CLI entry point for development tools."""
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    commands = {
        "format": format,
        "lint": lint,
        "scan": scan,
    }
    
    if command == "help" or command not in commands:
        print("Available commands:")
        for cmd in commands:
            print(f"  {cmd}")
        return 1
    
    return commands[command]()


if __name__ == "__main__":
    sys.exit(main()) 
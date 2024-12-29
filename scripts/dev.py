#!/usr/bin/env python3

import subprocess
import sys
from typing import Tuple, List
from dataclasses import dataclass
from datetime import datetime
import os

GREEN = '\033[0;32m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'

@dataclass
class CheckResult:
    name: str
    passed: bool
    output: str
    warnings: List[str]
    info: List[str] = None

def print_header(text: str) -> None:
    print(f"\n{BLUE}=== {text} ==={NC}\n")

def run_command(command: List[str]) -> Tuple[int, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 1, str(e)

def check_black() -> CheckResult:
    print_header("Running Black formatter")
    code, output = run_command(["poetry", "run", "black", "--check", "lxmfy"])
    return CheckResult(
        name="Black",
        passed=code == 0,
        output=output,
        warnings=[]
    )

def check_pylint() -> CheckResult:
    print_header("Running Pylint")
    code, output = run_command(["poetry", "run", "pylint", "lxmfy"])
    
    warnings = []
    info = []
    
    for line in output.split('\n'):
        if 'warning' in line.lower():
            warnings.append(line.strip())
        elif any(x in line.lower() for x in ['rated at', 'previous run', 'module']):
            info.append(line.strip())
    
    return CheckResult(
        name="Pylint",
        passed=True,
        output=output,
        warnings=warnings,
        info=info
    )

def check_bandit() -> CheckResult:
    print_header("Running Bandit security checks")
    code, output = run_command(["poetry", "run", "bandit", "-r", "lxmfy"])
    return CheckResult(
        name="Bandit",
        passed=code == 0,
        output=output,
        warnings=[]
    )

def generate_report(results: List[CheckResult]) -> None:
    print("\n" + "="*50)
    print(f"{BLUE}Quality Check Report{NC}")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")

    all_passed = True
    warnings_count = 0

    for result in results:
        status = f"{GREEN}✓{NC}" if result.passed else f"{RED}✗{NC}"
        print(f"{status} {result.name}")
        
        if result.info:
            print(f"{CYAN}  Info:{NC}")
            for info in result.info:
                print(f"  {info}")
        
        if result.warnings:
            warnings_count += len(result.warnings)
            print(f"{YELLOW}  Warnings:{NC}")
            for warning in result.warnings:
                if ':' in warning:
                    file_part = warning.split(':')[0]
                    msg_part = ':'.join(warning.split(':')[1:])
                    print(f"  {CYAN}{file_part}:{NC}{msg_part}")
                else:
                    print(f"  - {warning}")
        
        if not result.passed:
            all_passed = False
            print(f"{RED}  Failed:{NC}")
            print("  " + "\n  ".join(result.output.split('\n')))
        
        print()

    # Summary
    print("="*50)
    print(f"Summary:")
    print(f"- Overall Status: {GREEN}PASSED{NC}" if all_passed else f"{RED}FAILED{NC}")
    print(f"- Warnings: {YELLOW}{warnings_count}{NC}")
    print("="*50)

    if not all_passed:
        sys.exit(1)

def main():
    if not os.path.exists("pyproject.toml"):
        print(f"{RED}Error: Must be run from project root{NC}")
        sys.exit(1)

    results = [
        check_black(),
        check_pylint(),
        check_bandit()
    ]

    generate_report(results)

if __name__ == "__main__":
    main() 
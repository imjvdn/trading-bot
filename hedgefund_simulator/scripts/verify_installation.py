#!/usr/bin/env python3
"""
Verification script for Hedge Fund Simulator installation.

This script verifies that the package is properly installed and all components
are functioning as expected.
"""

import sys
import os
import platform
import importlib.metadata
from pathlib import Path
import subprocess
import warnings

# Disable warnings for cleaner output
warnings.filterwarnings("ignore")

# Colors for console output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Checkmark and X symbols
CHECK = f"{GREEN}✓{RESET}"
WARNING = f"{YELLOW}⚠{RESET}"
CROSS = f"{RED}✗{RESET}"

def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{text.upper()}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

def print_check(condition: bool, message: str) -> None:
    """Print a checkmark or cross based on condition."""
    symbol = CHECK if condition else CROSS
    print(f"  {symbol} {message}")
    return condition

def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    required = (3, 8)
    current = sys.version_info[:2]
    is_ok = current >= required
    
    print(f"Python version: {platform.python_version()}")
    if not is_ok:
        print(f"  {CROSS} Python {required[0]}.{required[1]}+ is required")
    else:
        print(f"  {CHECK} Python version meets requirements")
    
    return is_ok

def check_import(module_name: str, package_name: str = None) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        if package_name:
            version = importlib.metadata.version(package_name or module_name)
            print(f"  {CHECK} {module_name} (v{version}) is installed")
        else:
            print(f"  {CHECK} {module_name} is installed")
        return True
    except ImportError:
        print(f"  {CROSS} {module_name} is not installed")
        return False
    except Exception as e:
        print(f"  {CROSS} Error importing {module_name}: {str(e)}")
        return False

def check_hedgefund_imports() -> bool:
    """Check if all hedgefund_simulator modules can be imported."""
    print("\nChecking hedgefund_simulator imports:")
    
    modules = [
        "hedgefund_simulator",
        "hedgefund_simulator.agents.base_agent",
        "hedgefund_simulator.agents.market_data_agent",
        "hedgefund_simulator.agents.quant_agent",
        "hedgefund_simulator.agents.risk_manager_agent",
        "hedgefund_simulator.agents.portfolio_manager_agent",
        "hedgefund_simulator.backtest_engine",
        "hedgefund_simulator.cli",
        "hedgefund_simulator.utils.config_utils",
        "hedgefund_simulator.utils.data_utils",
        "hedgefund_simulator.utils.openai_utils",
        "hedgefund_simulator.utils.performance_metrics",
        "hedgefund_simulator.utils.plotting",
    ]
    
    results = []
    for module in modules:
        try:
            __import__(module)
            print(f"  {CHECK} {module}")
            results.append(True)
        except ImportError as e:
            print(f"  {CROSS} {module}: {str(e)}")
            results.append(False)
    
    return all(results)

def check_config_files() -> bool:
    """Check if required config files exist."""
    print("\nChecking configuration files:")
    
    required_files = [
        ("pyproject.toml", "Project configuration"),
        ("setup.py", "Package installation script"),
        ("README.md", "Documentation"),
        ("CHANGELOG.md", "Version history"),
        ("CONTRIBUTING.md", "Contribution guidelines"),
        ("config/example_config.yaml", "Example configuration"),
        (".github/workflows/ci.yml", "CI/CD configuration"),
    ]
    
    results = []
    for filename, description in required_files:
        path = Path(filename)
        exists = path.exists()
        print(f"  {CHECK if exists else CROSS} {filename} ({description})")
        results.append(exists)
    
    return all(results)

def run_command(cmd: str, cwd: str = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def check_tests() -> bool:
    """Run tests and check results."""
    print("\nRunning tests...")
    success, output = run_command("python -m pytest -v --cov=hedgefund_simulator")
    
    if success:
        print(f"  {CHECK} All tests passed")
    else:
        print(f"  {CROSS} Tests failed")
        print(f"\n{output}")
    
    return success

def check_cli() -> bool:
    """Check if CLI commands work."""
    print("\nChecking CLI commands:")
    
    # Check help command
    success, output = run_command("hedgefund-simulator --help")
    if success:
        print(f"  {CHECK} CLI command works")
        print(f"\n{output[:200]}...")
        return True
    else:
        print(f"  {CROSS} CLI command failed: {output}")
        return False

def check_import_versions() -> bool:
    """Check versions of key dependencies."""
    print("\nChecking dependency versions:")
    
    dependencies = [
        "pandas",
        "numpy",
        "matplotlib",
        "yfinance",
        "scikit-learn",
        "python-dotenv",
        "openai",
    ]
    
    results = []
    for dep in dependencies:
        try:
            version = importlib.metadata.version(dep)
            print(f"  {CHECK} {dep}: v{version}")
            results.append(True)
        except importlib.metadata.PackageNotFoundError:
            print(f"  {CROSS} {dep}: Not installed")
            results.append(False)
    
    return all(results)

def main() -> int:
    """Run all verification checks."""
    print(f"\n{BOLD}HEDGE FUND SIMULATOR INSTALLATION VERIFICATION{RESET}")
    print(f"{'-' * 50}")
    
    # System information
    print(f"System: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_implementation()} {platform.python_version()}")
    
    # Run checks
    checks = {
        "Python Version": check_python_version(),
        "Package Imports": check_hedgefund_imports(),
        "Configuration Files": check_config_files(),
        "Dependency Versions": check_import_versions(),
        "CLI Commands": check_cli(),
        "Tests": check_tests(),
    }
    
    # Print summary
    print_header("Verification Summary")
    
    all_passed = True
    for name, result in checks.items():
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"{name}: {status}")
        all_passed = all_passed and result
    
    print("\n" + "=" * 60)
    if all_passed:
        print(f"{GREEN}{BOLD}✓ All checks passed! Hedge Fund Simulator is ready to use.{RESET}")
        return 0
    else:
        print(f"{RED}{BOLD}✗ Some checks failed. Please review the output above.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test runner for the Hedge Fund Simulator.

This script runs all tests and generates coverage reports.
"""

import os
import sys
import unittest
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

def run_tests(test_path: str = None, pattern: str = 'test_*.py', 
             verbosity: int = 2, coverage: bool = True) -> bool:
    """
    Run tests with optional coverage reporting.
    
    Args:
        test_path: Directory or file path to test (default: 'tests')
        pattern: Test file pattern to match
        verbosity: Test output verbosity (0=quiet, 1=dot, 2=verbose)
        coverage: Whether to generate coverage reports
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    # Default to the tests directory if no path is provided
    if test_path is None:
        test_path = str(Path(__file__).parent / 'tests')
    
    # Ensure the test directory exists
    if not os.path.exists(test_path):
        print(f"Error: Test path '{test_path}' does not exist.", file=sys.stderr)
        return False
    
    # If it's a directory, append the pattern
    if os.path.isdir(test_path):
        test_path = os.path.join(test_path, pattern)
    
    # Run tests with coverage if requested
    if coverage:
        try:
            import coverage
        except ImportError:
            print("Coverage module not found. Install with: pip install coverage")
            coverage = False
    
    if coverage:
        # Initialize coverage
        cov = coverage.Coverage(
            source=['hedgefund_simulator'],
            omit=['*/tests/*', '*/__pycache__/*']
        )
        cov.start()
    
    # Discover and run tests
    print(f"\nRunning tests from: {test_path}")
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=os.path.dirname(test_path) if os.path.isfile(test_path) else test_path,
        pattern=os.path.basename(test_path) if os.path.isfile(test_path) else pattern
    )
    
    test_runner = unittest.TextTestRunner(verbosity=verbosity)
    result = test_runner.run(test_suite)
    
    # Generate coverage report if enabled
    if coverage:
        cov.stop()
        cov.save()
        
        print("\n" + "="*80)
        print("COVERAGE REPORT")
        print("="*80)
        
        # Terminal report
        cov.report()
        
        # Generate HTML report
        html_dir = os.path.join('coverage_report')
        cov.html_report(directory=html_dir)
        print(f"\nHTML report generated at: {os.path.abspath(html_dir)}/index.html")
        
        # Generate XML report for CI
        cov.xml_report()
    
    return result.wasSuccessful()

def run_linters() -> bool:
    """Run code linters and style checkers.
    
    Returns:
        bool: True if all linters passed, False otherwise
    """
    print("\n" + "="*80)
    print("RUNNING LINTERS")
    print("="*80)
    
    # Check if flake8 is installed
    try:
        import flake8
    except ImportError:
        print("flake8 not found. Install with: pip install flake8")
        return False
    
    # Run flake8
    project_root = os.path.dirname(os.path.abspath(__file__))
    flake8_cmd = [
        'python', '-m', 'flake8',
        '--max-line-length=120',
        '--exclude=.git,__pycache__,venv,env,.venv,build,dist',
        project_root
    ]
    
    print("\nRunning flake8...")
    flake8_result = subprocess.run(flake8_cmd)
    
    # Run mypy if installed
    try:
        import mypy
        print("\nRunning mypy...")
        mypy_cmd = [
            'python', '-m', 'mypy',
            '--ignore-missing-imports',
            '--disallow-untyped-defs',
            '--no-implicit-optional',
            '--warn-redundant-casts',
            '--warn-unused-ignores',
            '--warn-return-any',
            '--no-warn-no-return',
            project_root
        ]
        mypy_result = subprocess.run(mypy_cmd)
        mypy_passed = mypy_result.returncode == 0
    except ImportError:
        print("mypy not found. Install with: pip install mypy")
        mypy_passed = True  # Don't fail if mypy isn't installed
    
    return flake8_result.returncode == 0 and mypy_passed

def run_security_checks() -> bool:
    """Run security checks using bandit.
    
    Returns:
        bool: True if security checks pass, False otherwise
    """
    print("\n" + "="*80)
    print("RUNNING SECURITY CHECKS")
    print("="*80)
    
    try:
        import bandit
    except ImportError:
        print("bandit not found. Install with: pip install bandit")
        return True  # Don't fail if bandit isn't installed
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    bandit_cmd = [
        'python', '-m', 'bandit',
        '-r',  # Recursive
        '-ll',  # Basic reporting level
        '-iii',  # Info issues included
        '-n', '3',  # Top 3 issues
        '-x', 'tests',  # Exclude tests
        project_root
    ]
    
    print("\nRunning bandit...")
    bandit_result = subprocess.run(bandit_cmd)
    return bandit_result.returncode == 0

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Run tests and generate coverage reports.')
    parser.add_argument('test_path', nargs='?', default=None, 
                       help='Test file or directory to run (default: tests/)')
    parser.add_argument('-p', '--pattern', default='test_*.py',
                       help='Pattern to match test files (default: test_*.py)')
    parser.add_argument('-v', '--verbosity', type=int, default=2,
                       help='Test output verbosity (0=quiet, 1=dot, 2=verbose)')
    parser.add_argument('--no-coverage', action='store_false', dest='coverage',
                       help='Disable coverage reporting')
    parser.add_argument('--lint-only', action='store_true',
                       help='Run only linters, not tests')
    parser.add_argument('--security-only', action='store_true',
                       help='Run only security checks')
    parser.add_argument('--all', action='store_true',
                       help='Run all checks (tests, linters, security)')
    
    args = parser.parse_args()
    
    # Run the appropriate checks
    success = True
    
    if args.security_only or args.all:
        success &= run_security_checks()
    
    if args.lint_only or args.all:
        success &= run_linters()
    
    if not (args.lint_only or args.security_only) or args.all:
        test_success = run_tests(
            test_path=args.test_path,
            pattern=args.pattern,
            verbosity=args.verbosity,
            coverage=args.coverage and not (args.lint_only or args.security_only)
        )
        success &= test_success
    
    # Print final status
    print("\n" + "="*80)
    print("TEST RUNNER SUMMARY")
    print("="*80)
    
    if success:
        print("\n✅ All checks passed!")
    else:
        print("\n❌ Some checks failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

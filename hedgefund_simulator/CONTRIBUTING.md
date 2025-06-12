# Contributing to Hedge Fund Simulator

Thank you for your interest in contributing to the Hedge Fund Simulator! This document outlines how you can contribute to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Making Changes](#making-changes)
  - [Coding Standards](#coding-standards)
  - [Testing](#testing)
  - [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Code Review Process](#code-review-process)

## Code of Conduct

This project adheres to the [Contributor Covenant](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- (Optional) A virtual environment tool (venv, conda, etc.)

### Setting Up the Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/hedgefund-simulator.git
   cd hedgefund-simulator
   ```

3. **Set up a virtual environment** (recommended):
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using conda
   # conda create -n hedgefund-simulator python=3.8
   # conda activate hedgefund-simulator
   ```

4. **Install dependencies**:
   ```bash
   pip install -e .[dev]  # Install in development mode with dev dependencies
   ```

## Making Changes

### Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all function signatures
- Write docstrings for all public functions, classes, and modules following [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Keep lines under 120 characters
- Use meaningful variable and function names

### Testing

We use `pytest` for testing. To run the test suite:

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test file
python run_tests.py tests/test_market_data_agent.py

# Run with more verbose output
python run_tests.py -v

# Run linters only
python run_tests.py --lint-only

# Run security checks only
python run_tests.py --security-only
```

### Documentation

- Update documentation when adding new features or changing behavior
- Document all public APIs
- Add examples for complex functionality
- Keep the README up to date

## Submitting Changes

1. **Create a feature branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Commit your changes** with a descriptive message:
   ```bash
   git commit -m "Add new feature: your feature description"
   ```

3. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request** on GitHub
   - Reference any related issues
   - Describe your changes and any potential impacts
   - Ensure all tests pass

## Reporting Issues

When reporting issues, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected vs. actual behavior
4. Python version and OS
5. Any error messages or logs

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists or has been requested
2. Explain why this feature would be valuable
3. Provide any relevant use cases or examples

## Code Review Process

1. A maintainer will review your PR
2. You may be asked to make changes
3. Once approved, a maintainer will merge your PR

Thank you for contributing to the Hedge Fund Simulator!

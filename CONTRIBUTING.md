# Contributing to Notion Markdown Sync

Thank you for your interest in contributing to the Notion Markdown Sync tool! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Install dependencies**:
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```
4. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

1. Configure your environment:
   - Copy `.env.example` to `.env` and fill in your Notion API credentials
   - Copy `config/config.example.yaml` to `config/config.yaml` and customize as needed

2. Run tests to verify your setup:
   ```bash
   python -m pytest
   ```

## Code Style and Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style
- Write docstrings for all public functions, classes, and methods
- Include type hints where appropriate
- Use snake_case for variables and function names
- Use PascalCase for class names

## Testing

- Add tests for new functionality
- Ensure all tests pass before submitting a pull request:
  ```bash
  python -m pytest
  ```
- Test your changes with real-world Notion pages

## Submitting Changes

1. **Commit your changes** with clear, descriptive commit messages
2. **Push your branch** to your fork
3. **Create a pull request** from your branch to the main repository
4. **Describe your changes** in the pull request:
   - What does this change accomplish?
   - How did you implement it?
   - Any additional context or notes?

## Reporting Bugs

When reporting a bug, please include:
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Error messages and stack traces (if applicable)
- Your environment (OS, Python version, etc.)

## Feature Requests

For feature requests, please:
- Clearly describe the feature
- Explain the use case and benefits
- Note which roadmap category it falls under
- Include any relevant examples or references

## Working with the Notion API

- Be mindful of rate limits
- Test with minimal permissions first
- Document any API-specific behaviors or quirks you encounter

## Questions?

If you have questions about contributing, please open an issue with the "question" label.

Thank you for contributing to Notion Markdown Sync!
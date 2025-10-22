# Contributing to OBS SFTP File Processor

Thank you for your interest in contributing to the OBS SFTP File Processor! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- Python 3.9+
- UV package manager
- Git

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/obs-sftp-file-processor-python.git
   cd obs-sftp-file-processor-python
   ```

3. **Set up the development environment**:
   ```bash
   # Install UV if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment
   uv venv
   source .venv/bin/activate
   
   # Install dependencies
   uv sync --dev
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Keep functions small and focused

### Testing
- Write tests for new functionality
- Ensure all tests pass before submitting
- Aim for high test coverage

### Code Quality
- Run linting: `uv run ruff check src/`
- Format code: `uv run black src/`
- Type checking: `uv run mypy src/`

## Submitting Changes

1. **Test your changes**:
   ```bash
   uv run pytest tests/ -v
   uv run ruff check src/
   uv run black --check src/
   uv run mypy src/
   ```

2. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub

## Commit Message Format

Use conventional commits format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

## Pull Request Guidelines

- Provide a clear description of changes
- Reference any related issues
- Ensure CI checks pass
- Request review from maintainers

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages or logs

## Security

- Never commit sensitive information (passwords, keys, tokens)
- Use environment variables for configuration
- Report security vulnerabilities privately

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

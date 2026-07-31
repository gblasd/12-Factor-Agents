# 12-Factor-Agents
12-Factor Agents methodology by building a complete agentic application in Python.

## Runtime requirements
- Python 3.10 or newer is required to run this code (the repository uses modern syntax such as `match` statements).
- Install runtime dependencies with `python3 -m pip install -r requirements.txt`.

## Docker
Build and run the app in a Python 3.12 container:

```bash
docker build -t 12-factor-agents .
docker run --rm -e OPENAI_API_KEY="$OPENAI_API_KEY" 12-factor-agents
```

## CI
A GitHub Actions workflow is included to validate dependency installation and Python syntax on every push and pull request.

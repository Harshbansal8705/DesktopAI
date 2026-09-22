# Contributing to DesktopAI 🤝

Thank you for your interest in contributing to DesktopAI! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Adding New Tools](#adding-new-tools)
  - [Submitting Pull Requests](#submitting-pull-requests)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Getting Help](#getting-help)

---

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/<your-username>/DesktopAI.git
   cd DesktopAI
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/HarshBansal8705/DesktopAI.git
   ```

## Development Setup

### Prerequisites

- **OS**: Linux (tested on Arch Linux, Ubuntu, Fedora)
- **Python**: 3.8+
- **Hardware**: Working microphone and speakers
- **Display**: X11 or Wayland with Qt support

### Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your API keys
cp .env.example .env
# Edit .env with your API keys (at minimum: GROQ_API_KEY and PORCUPINE_ACCESS_KEY)

# Record your voice for speaker verification
python setup/record_owner_voice.py

# Run the assistant
./run.sh
```

### Required API Keys

| Key | Required | Where to Get |
|-----|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | [console.groq.com](https://console.groq.com) |
| `PORCUPINE_ACCESS_KEY` | ✅ Yes | [picovoice.ai](https://picovoice.ai) (free tier available) |
| `TAVILY_API_KEY` | Optional | [tavily.com](https://tavily.com) (for web search) |
| `GOOGLE_API_KEY` | Optional | [Google AI Studio](https://aistudio.google.com) |
| `TOGETHER_API_KEY` | Optional | [together.ai](https://www.together.ai) |

## Project Architecture

```
DesktopAI/
├── main.py                     # Entry point — DesktopAssistant class
├── src/
│   ├── config.py               # Centralized configuration (env vars + defaults)
│   ├── core/                   # AI brain
│   │   ├── assistant.py        # LangGraph ReAct agent setup
│   │   ├── llm.py              # LLM provider initialization
│   │   ├── generate_prompt.py  # System prompt generation
│   │   ├── summarizer.py       # Conversation history summarization
│   │   └── tools.py            # All agent tools (shell, browser, etc.)
│   ├── audio/                  # Voice pipeline
│   │   ├── listener.py         # Wake word + speaker verification + recording
│   │   ├── audio_processor.py  # Groq Whisper transcription
│   │   ├── ttsplayer.py        # Edge TTS text-to-speech
│   │   └── vad.py              # Voice Activity Detector (future use)
│   ├── ui/
│   │   └── overlay.py          # PyQt5 transparent overlay window
│   └── utils/
│       ├── logger.py           # Colored logging with per-module log files
│       └── thread_executor.py  # Shared thread pool
├── setup/
│   └── record_owner_voice.py   # Owner voice enrollment script
├── data/
│   └── soundeffects/           # Start/stop recording sounds
└── wakewordmodels/             # Porcupine wake word model files
```

### Data Flow

```
Microphone → Wake Word Detection (Porcupine)
           → Speaker Verification (Resemblyzer)
           → Voice Activity Detection (Silero VAD)
           → Audio Recording
           → Transcription (Groq Whisper)
           → LLM Agent (LangChain/LangGraph)
           → Tool Execution (if needed)
           → Text-to-Speech Response (Edge TTS)
           → UI Update (PyQt5 Overlay)
```

## How to Contribute

### Reporting Bugs

- Use the [Bug Report](https://github.com/HarshBansal8705/DesktopAI/issues/new?template=bug_report.md) issue template
- Include your OS, Python version, and relevant logs from `logs/`
- Provide steps to reproduce the issue

### Suggesting Features

- Use the [Feature Request](https://github.com/HarshBansal8705/DesktopAI/issues/new?template=feature_request.md) issue template
- Explain the use case and why it would be valuable

### Adding New Tools

One of the easiest ways to contribute is adding new tools to the assistant. Here's how:

1. **Open** `src/core/tools.py`
2. **Add your tool** using the `@tool` decorator:

```python
@tool
def my_new_tool(parameter: str) -> str:
    """
    Clear description of what this tool does.
    The LLM reads this docstring to decide when to use the tool.
    """
    # Your implementation here
    return "Result string"
```

3. That's it! The `@tool` decorator automatically:
   - Wraps your function with logging
   - Registers it in the global tool registry
   - Makes it available to the LangChain agent

**Guidelines for tools:**
- Keep tool functions focused on a single task
- Write clear docstrings — the LLM uses them to decide when to call your tool
- Return strings (the agent processes string responses)
- Handle errors gracefully and return descriptive error messages
- Use `logger` for debugging (`from src.utils.logger import get_logger`)

### Submitting Pull Requests

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the [code style](#code-style) guidelines

3. **Test your changes** — make sure the assistant starts and your feature works:
   ```bash
   ./run.sh
   ```

4. **Commit with a descriptive message** (see [commit messages](#commit-messages))

5. **Push and create a PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub against the `main` branch.

## Code Style

- **Python version**: 3.8+ compatible
- **Formatting**: Use 4-space indentation
- **Imports**: Group stdlib, third-party, and local imports (separated by blank lines)
- **Docstrings**: Use docstrings for all classes and public functions
- **Type hints**: Encouraged for function signatures
- **Logging**: Use `get_logger()` from `src.utils.logger` — avoid bare `print()` statements
- **Configuration**: Add new settings to `src/config.py` — don't hardcode values

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code restructuring without behavior change
- `style`: Formatting, whitespace changes
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (deps, CI, etc.)

**Examples:**
```
feat: Add Spotify playback control tool
fix: Handle empty audio buffer in listener
docs: Add troubleshooting section to README
refactor: Extract speaker verification into separate module
```

## Getting Help

- **GitHub Issues**: Open an issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions or ideas
- **Email**: harsh@harshbansal.in

---

Thank you for contributing! Every improvement, no matter how small, makes DesktopAI better. 🚀

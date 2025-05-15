# Jarvis - Voice-Activated AI Assistant

A voice-activated AI assistant for Linux that uses LangChain, Edge TTS, and LLM integration to provide a responsive and helpful desktop assistant experience.

## Features

- **Voice Activation**: Responds to "Jarvis" wake word
- **Speech Recognition**: Converts your voice commands to text
- **AI-Powered Responses**: Uses LangChain with Anthropic/Groq models
- **Text-to-Speech**: Speaks responses using Edge TTS
- **Transparent Overlay UI**: Shows conversation history and status
- **System Tools**: Execute commands, open applications, and more
- **Persistent Memory**: Remembers conversation context across sessions

## Prerequisites

- Linux system (tested on Arch Linux)
- Python 3.8+
- API keys for any LLM provider (Together, Groq, etc.)

## Installation

1. **Clone the repository**

```bash
git clone git@github.com:Harshbansal8705/DesktopAI.git
cd DesktopAI
```

2. **Create and activate virtual environment**

```bash
virtualenv venv
source ./venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root with your API keys:

```
# Required: Choose at least one LLM provider
TOGETHER_API_KEY=your_anthropic_api_key
GROQ_API_KEY=your_groq_api_key

# Optional: Set logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

## Usage

1. **Run the assistant**

```bash
./run.sh
```

Or manually:

```bash
source ./venv/bin/activate
QT_QPA_PLATFORM=xcb python main.py
```

2. **Interact with Jarvis**

- Say "Jarvis" followed by your command
- Example: "Jarvis, what's the weather today?"
- Example: "Jarvis, open Chrome"
- Example: "Jarvis, run ls -la"

## Available Tools

Jarvis can perform various actions through its built-in tools:

- **run_command**: Execute shell commands on your Linux system
- **open_google_chrome**: Open Chrome browser with a specified URL
- **open_whatsapp_web**: Launch WhatsApp Web application
- **show_logs_widget/hide_logs_widget**: Control the visibility of the logs overlay

## Project Structure

- `main.py`: Entry point and voice recognition handler
- `assistant.py`: LangChain agent configuration
- `tools.py`: Tool definitions for system interactions
- `ttsplayer.py`: Text-to-speech functionality
- `widget.py`: PyQt5 overlay UI implementation
- `generate_prompt.py`: System prompt for the AI assistant
- `llm.py`: LLM provider configuration
- `summarizer.py`: Conversation summarization
- `logger.py`: Logging configuration

## Troubleshooting

- **Microphone issues**: Make sure your microphone is properly connected and permissions are set
- **API errors**: Verify your API keys in the `.env` file
- **UI problems**: Ensure PyQt5 is properly installed and X server is running
- **Log files**: Check the `logs/` directory for detailed error information

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues for bugs and feature requests.

## License

[MIT License](LICENSE)

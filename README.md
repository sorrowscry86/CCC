# CCC - Covenant Command Cycle

A multi-agent AI chat system prototype that demonstrates resonant loop interactions between different AI personalities through a secure Flask proxy server.

## Features

- **Secure OpenAI Proxy**: Flask server that safely handles OpenAI API calls
- **Multi-Agent Simulation**: Different AI agent personalities (Analyst, Synthesizer, Evaluator)
- **Interactive Web Interface**: Modern UI built with Tailwind CSS and Vanilla JavaScript
- **Real-time Chat**: Live conversation with typing indicators and smooth animations
- **Configurable Models**: Support for GPT-3.5, GPT-4, and other OpenAI models
- **Temperature Control**: Adjustable creativity/randomness settings
- **Resonant Loop Simulation**: Automated multi-agent conversations

## Architecture

```
Frontend (HTML/JS/CSS) ←→ Flask Proxy Server ←→ OpenAI API
     (Port: File)              (Port: 5111)         (External)
```

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sorrowscry86/CCC.git
   cd CCC
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Start the proxy server**
   ```bash
   python proxy_server.py
   ```

5. **Open the frontend**
   Open `resonant_loop_lab.html` in your web browser

## Usage

### Basic Chat
1. Ensure the proxy server is running (green status indicator)
2. Type your message in the input field
3. Press Enter or click Send
4. Watch the AI respond in real-time

### Multi-Agent Simulation
1. Click "Simulate Loop" to start an automated conversation
2. Three different AI agents will discuss a topic in sequence
3. Each agent has a distinct personality and perspective

### Configuration
- **Model**: Choose between GPT-3.5 Turbo, GPT-4, or GPT-4 Turbo
- **Temperature**: Adjust creativity (0.0 = focused, 2.0 = creative)
- **Clear Chat**: Reset the conversation history

## API Endpoints

### Health Check
```
GET /health
```
Returns server status and version information.

### Chat Completions
```
POST /chat/completions
```
Proxies requests to OpenAI's chat completions API with secure authentication.

## Security Features

- API keys stored securely in environment variables
- CORS properly configured for local development
- Request validation and error handling
- No sensitive data logged or exposed

## Development

### File Structure
```
CCC/
├── proxy_server.py          # Flask proxy server
├── resonant_loop_lab.html   # Frontend interface
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── CHANGELOG.md            # Version history
└── README.md               # This file
```

### Dependencies
- **Flask**: Web framework for the proxy server
- **Flask-CORS**: Cross-origin resource sharing support
- **requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [OpenAI API](https://openai.com/api/)
- UI styled with [Tailwind CSS](https://tailwindcss.com/)
- Inspired by multi-agent AI research and resonant loop theory

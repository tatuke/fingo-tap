# Ghost in the Shell

**Ghost in the Shell** is a cross-platform command-line assistant that lets you use natural language to run shell commands. Whether you’re on macOS, Linux, or Windows, just type what you want to do — AI Shell will suggest the correct shell command, ask for your confirmation, and optionally execute it.

Supports both:
- **One-shot mode**: `ai "archive.tar"` → returns shell command
- **Interactive mode**: `ai -i` → opens a terminal chat with the AI

---

## ✨ Features

- Natural Language to Shell Command (via OpenAI API)
- Works on macOS, Linux, and Windows (Python-based)
- Confirmation before execution
- Interactive chat mode for iterative CLI tasks
- Colored terminal output for better readability
- Optional tmux split-pane workflow (chat left, shell right)

---

## Installation

### Option 1: Install via Homebrew (recommended for macOS)

```bash
brew tap codingmoh/ghost-in-the-shell
brew install ghost-in-the-shell
```

### Option 2: Install via pip (any OS)

```bash
pip install ghost-in-the-shell
```

### Option 3: Clone & Install locally

```bash
git clone https://github.com/codingmoh/ghost_in_the_shell.git
cd ghost_in_the_shell
pip install .
```

Now you can use the `ai` command globally.

---

## 🔑 Set OpenAI API Key

You need an OpenAI API key to use this tool:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

You can also add this line to your `.bashrc`, `.zshrc`, or `.bash_profile`.

---

## Usage

### One-shot prompt

```bash
ai "untar backup.tar.gz"
```

✅ AI suggests a shell command  
✅ Asks for confirmation  
✅ Runs the command if you approve

---

### Interactive mode

```bash
ai -i
```

🧠 Open a chat session right in the terminal.  
💬 Type natural language instructions like:

```
You: compress all PNGs in this folder
AI: tar -czvf images.tar.gz *.png
```

Type `exit` or `quit` to leave.

---

### 🪟 tmux Split Mode (optional)

Want to split your terminal into chat + shell?

```bash
tmux
# Then split horizontally:
Ctrl-B %
# In left pane:
ai -i
# In right pane:
use your normal shell
```

---

## 🛡️ Security Notice

Always review AI-generated commands before executing them.

---

## 🧱 Future Plans

- Voice input via Whisper
- Local LLM support (e.g., llama.cpp)
- Fancy TUI with textual or rich
- Command history and undo
- Plugin system for workflows

---

## Contributing

PRs welcome! Ideas, issues, improvements — all appreciated.

---

## 📝 License

MIT

---

❤️ Built with love and caffeine by [codingmoh](https://github.com/codingmoh).
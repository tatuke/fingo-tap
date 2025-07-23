# Open Codex

<h1 align="center">Fingo-tap</h1>
<h2 align="center">Fork from <a href="https://github.com/codingmoh/open-codex">Open Codex</a></h2>
<p align="center">Lightweight Unix like system CLI agent that runs in your terminal</p>


![Codex demo GIF using: codex "explain this codebase to me"](./.github/demo.gif)

---

**Fingo-tap** This is a CLI assistant as an exercise project for me, designed to help the user, from an initialized system (which of course requires a python environment) to installing every component, preparing various system development and dependency environments.... Help you do everything you want on your current system (not windows, not today), a lightweight AI command line assistant.

**Online LLM** - Sometimes we would like to have a powerful LLM as our assistant to help us output more accurate and executable system commands. Limited by local hardware environment, we can only use it through API. But like most consensus, it is very dangerous to directly expose your working system environment condition and working situation to the service providers on public network. This branch provides Litellm as a proxy connection option, but I still hope you'd better use the online model only for testing or learning system environment, and take care to protect your personal email and password and other real data. This is important!

**Locally**- Apart from preparing the hardware yourself, one of the best ways to use a powerful LLM assistant is to request the deployment of one of the more powerful open source **“coder LLM”** available on the market at your organization or at your employer's place of work. Then you can carry out your tasks in a networked environment trusted by your organization.

---

## Supports

* **One-shot mode**: `open-codex "list all folders"` -> returns shell command
* **Litellm integration** so that you can use more powerful language models on line (Only dev env, not for production)
* **Ollama integration** for (e.g., LLaMA3, Mistral)
* Native execution on **macOS, Linux, and Windows(Ah Ah not today)**
---
## ✨ Features

- Natural Language → Shell Command (via local or Ollama-hosted LLMs)
- Local&Online LLM (Be careful for your data)
- Confirmation before running any command
- Option to copy to clipboard / abort / execute
- Colored terminal output for better readability
- Ollama support: use advanced LLMs with `--ollama --model llama3`

### 🔍 Example with Ollama:

```bash
open-codex --ollama --model llama3 "find all JPEGs larger than 10MB"
# litellm(config in ~/open_codex_config/.env)
open-codex --litellm "find all JPEGs larger than 10MB"
```

Codex will:

1. Send your prompt to the Ollama API (local server, e.g. on `localhost:11434`)
2. Return a shell command suggestion (e.g., `find . -name "*.jpg" -size +10M`)
3. Prompt you to execute, copy, or abort

> 🛠️ Recommend [Ollama](https://ollama.com) installed and running locally in you organization to use this feature.

---

## 🧱 Future Plans

- Context-aware mode
- Auto detect current system situation
- less token consumption
- Command history real time local analyze and (optimize or fix) 
---

## 📦 Installation



### 🔹 Clone & install locally

```bash
git clone https://github.com/tatuke/fingo-tap.git    
cd fingo-tap
pip install .
```

Once installed, use the `open-codex` CLI globally.

---

## reinstall-xasdkljdas
Reinstall if you change config value in .env (temporary <-=->)
```bash
cd root-path/to/fingo-tap/
rm -rf build dist open_codex.egg-info
pip install build
python -m build
# You might see version after build
pip install --force-reinstall dist/open_codex-<opencodex-version>-py3-none-any.whl
```

## 🚀 Usage Examples

### ▶️ One-shot mode

```bash
open-codex "untar file abc.tar"
```
✅ Codex suggests a shell command  
✅ Asks for confirmation / add to clipboard / abort  
✅ Executes if approved

### ▶️ Using Ollama

```bash
open-codex --ollama --model llama3 "delete all .DS_Store files recursively"
```

---

## 🛡️ Security Notice

Models run **ONLINE** && **LOCAL**. Both were provided on this branch.And Again be careful for your data.It is important to note that this branch is not production-ready.
---

## 🧑‍💻 Contributing

Due to my personal capacity, I don't have the time to respond and review PRs in a timely manner at this stage. so if you have good ideas and PRs changes, code exchanges to share, please go to https://github.com/codingmoh/open-codex. i think he will be happy to talk and share your work with you. Thanks again for your interest in working on this project. You are welcome to track and follow the progress of this project

---

## 📝 License

MIT

---
❤️ Inspried by [codingmoh](https://github.com/codingmoh).



I've always wanted to build an AI assistant to help me tackle the obscure and tedious tasks involved in preparing system environments.

Thanks for the great work of talented codingmoh. Inspired by his work, I’ve decided to build upon it as part of a personal learning initiative. Please note that this is an experimental project driven by my own curiosity and growth—it involves many risks and uncertainties, and I do not recommend using it in any production or mission-critical environment.(NOT Today!)



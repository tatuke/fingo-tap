import sys
import argparse
import subprocess
import pyperclip

from open_codex.agent_builder import AgentBuilder
from open_codex.interfaces.llm_agent import LLMAgent


GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Capture single keypress (terminal) from the user
# and returns it as a string. It works on both Windows and Unix systems.
# Windows
if sys.platform == "win32":
    import msvcrt

    def get_keypress():
        return msvcrt.getch().decode("utf-8")

# Unix (Linux/macOS)
else:
    import termios
    import tty

    def get_keypress():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

def one_shot_mode(agent: LLMAgent, prompt: str):
    try:
        response = agent.one_shot_mode(prompt)
        print(f"{GREEN}: {response}{RESET}") 
        command = response.strip()

        print(f"{BLUE}What do you want to do with this command?{RESET}")
        print(f"{BLUE}[c] Copy  [e] Execute  [a] Abort{RESET}")
        print(f"{BLUE}Press key: ", end="", flush=True)
        choice = get_keypress().lower()
        print(f"{RESET}")  # Clear the line after the prompt

        if choice == "e":
            print(f"{BLUE}Executing command: {command}{RESET}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            print(f"{GREEN}Command output: {result.stdout}{RESET}")
            if result.stderr:
                print(f"{RED}Error: {result.stderr}{RESET}")

        elif choice == "c":
            pyperclip.copy(command)
            print(f"{GREEN}Command copied to clipboard! Paste it manually in your terminal.{RESET}")

        elif choice == "a":
            print(f"{BLUE}Aborted.{RESET}")
        else:
            print(f"{RED}Unknown choice. Nothing happened.{RESET}")

    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Open Codex - Natural Language to CLI commands")
    parser.add_argument("prompt", nargs="*", help="Optional prompt for one-shot mode")
    args = parser.parse_args()

    prompt = " ".join(args.prompt).strip()
    if not prompt:
        print("Please provide a prompt")
        sys.exit(1)
    
    agent = AgentBuilder.get_agent()
    one_shot_mode(agent, prompt)

if __name__ == "__main__":
    main()
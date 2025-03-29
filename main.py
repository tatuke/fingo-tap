#!/usr/bin/env python3

import os
import sys
import argparse
import openai
import subprocess

# Optional: color output via ANSI codes
# If on Windows, you might need 'colorama.init()'
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR-OPENAI-KEY-HERE")

if not openai.api_key:
    # in order to use application, you need to set OPENAI_API_KEY
    # provide example usage
    print(f"{RED}In order to use this application, you need to set OPENAI_API_KEY environment variable.{RESET} 
          \n"
          f"{RED}Example: export OPENAI_API_KEY=your_openai_key{RESET}")
    sys.exit(1)

def call_openai_for_command(user_message, chat_history=None):
    """
    Given a user message describing what we want to do,
    call the OpenAI API to get a suggested shell command.
    :param user_message: natural language instructions from user
    :param chat_history: list of dicts with 'role' and 'content'
    :return: the shell command (string)
    """
    if chat_history is None:
        chat_history = []

    # We add a system message to instruct the model to return only valid shell commands, etc.
    system_msg = {
        "role": "system",
        "content": (
            "You are a helpful AI that converts natural language instructions "
            "into valid shell commands. Always provide a concise shell command. "
            "No shebang, no explanations, no extra text. "
            "No explanations, just the command."
        )
    }
    # Then we add the user prompt
    user_msg = {"role": "user", "content": user_message}

    # Construct the full message set
    messages = [system_msg] + chat_history + [user_msg]

    # Call OpenAI API
    client = openai.OpenAI()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0,  
        )
        cmd = response.choices[0].message.content.strip()
        return cmd
    except Exception as e:
        print(f"{RED}Error calling OpenAI API: {e}{RESET}")
        return ""


def run_shell_command(cmd):
    """
    Safely run the shell command. Here we just do a basic run.
    Could add prompts or advanced safety checks here.
    """
    if not cmd:
        return
    try:
        print(f"{BLUE}Executing: {cmd}{RESET}")
        subprocess.run(cmd, shell=True)
    except Exception as e:
        print(f"{RED}Error executing command: {e}{RESET}")


def one_shot_mode(prompt, do_execute=True):
    """
    For `ai "your prompt"` usage:
      1. Call GPT to get shell command
      2. Show it to user
      3. Optionally run it
    """
    cmd = call_openai_for_command(prompt)
    if cmd:
        print(f"{GREEN}AI suggests command:{RESET} {cmd}")
        if do_execute:
            # Confirm or auto-run:
            confirm = input("Execute this command? (y/n) ").strip().lower()
            if confirm == 'y' or confirm == '':
                run_shell_command(cmd)
    else:
        print(f"{RED}No command was returned.{RESET}")


def interactive_mode():
    """
    Interactive conversation with GPT:
      - user enters natural language
      - GPT returns a shell command
      - user can confirm or skip
      - user can continue the conversation
    """
    print(f"{BLUE}Entering Interactive AI Shell mode...{RESET}")
    print(f"{BLUE}Type 'exit' or 'quit' to leave.{RESET}\n")

    chat_history = []
    while True:
        user_input = input(f"{GREEN}You:{RESET} ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break

        chat_history.append({"role": "user", "content": user_input})

        cmd = call_openai_for_command(user_input, chat_history=[])
        if not cmd:
            print(f"{RED}No command returned or error occurred.{RESET}")
            continue

        print(f"{GREEN}AI suggests:{RESET} {cmd}")
        confirm = input("Execute this command? (y/n) ").strip().lower()
        if confirm == 'y':
            run_shell_command(cmd)

        chat_history.append({"role": "assistant", "content": cmd})


def main():
    parser = argparse.ArgumentParser(description="AI Shell - Natural Language to CLI commands")
    parser.add_argument("-i", "--interactive", action="store_true", help="Run in interactive chat mode")
    parser.add_argument("prompt", nargs="*", help="Optional prompt for one-shot mode")
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    else:
        prompt = " ".join(args.prompt).strip()
        if not prompt:
            print("Please provide a prompt or use -i for interactive mode.")
            sys.exit(1)
        one_shot_mode(prompt, do_execute=True)


if __name__ == "__main__":
    main()